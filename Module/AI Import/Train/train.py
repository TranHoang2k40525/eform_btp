from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "eform-matplotlib"))
os.environ["MPLBACKEND"] = "Agg"

# Ensure Module/AI Import is importable regardless of working directory
TRAIN_DIR = Path(__file__).resolve().parent
MODULE_DIR = TRAIN_DIR.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(TRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(TRAIN_DIR))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, Sampler

from augmentations import augment_training_sample
from dataset_cache import build_or_load_cache
from eform_ai.postprocess import decode_predictions
from eform_ai.predictor import EFormPredictor
from eform_ai.schema import (
    CELL_CLASS_NAMES,
    COL_OUTSIDE,
    COL_ROLE_NAMES,
    FEATURE_CHANNELS,
    FORMAT_VERSION,
    IGNORE_INDEX,
    MODEL_FILENAME,
    MODEL_NAME,
    ROW_TYPE_NAMES,
    TEXT_HASH_DIM,
)
from model import EFormAxialTableNet


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class CachedSheetDataset(Dataset):
    def __init__(
        self,
        samples: list[dict[str, Any]],
        is_train: bool,
        top_pool: list[torch.Tensor],
        bottom_pool: list[torch.Tensor],
        repeat_factor: int = 1,
        seed: int = 20260913,
    ) -> None:
        self.samples = samples
        self.is_train = is_train
        self.top_pool = top_pool
        self.bottom_pool = bottom_pool
        self.repeat_factor = max(1, repeat_factor) if is_train else 1
        self.seed = seed
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __len__(self) -> int:
        return len(self.samples) * self.repeat_factor

    def __getitem__(self, index: int) -> dict[str, Any]:
        sample = self.samples[index % len(self.samples)]
        h, w = sample["cell_target"].shape
        base_mismatch = (
            sample["col_mismatch"].float()
            if "col_mismatch" in sample
            else torch.zeros((w,), dtype=torch.float32)
        )
        is_physical_variant = sample.get("variant_type", "original") != "original"

        if self.is_train:
            rng = random.Random(self.seed + self.epoch * 100003 + index * 97)
            # Physical Excel variants (already mutated) & ~25% of originals stay untouched
            # (with tall-sheet interior cropping only when needed for fast CPU batches).
            if is_physical_variant or (index < len(self.samples) and rng.random() < 0.25):
                item = {
                    "features": sample["features"].float(),
                    "cell_target": sample["cell_target"].long(),
                    "table_start": sample["table_start"].float(),
                    "col_role": sample["col_role"].long(),
                    "col_mismatch": base_mismatch,
                    "row_type": sample["row_type"].long(),
                }
                if item["features"].shape[1] > 48 and rng.random() < 0.65:
                    from augmentations import _crop_long_sheet
                    f, ct, ts, cr, rt = _crop_long_sheet(
                        item["features"], item["cell_target"], item["table_start"],
                        item["col_role"], item["row_type"], rng, max_rows=42
                    )
                    item["features"], item["cell_target"], item["table_start"], item["col_role"], item["row_type"] = (
                        f, ct, ts, cr, rt
                    )
            else:
                item = augment_training_sample(
                    sample, self.samples, self.top_pool, self.bottom_pool, rng
                )
        else:
            item = {
                "features": sample["features"].float(),
                "cell_target": sample["cell_target"].long(),
                "table_start": sample["table_start"].float(),
                "col_role": sample["col_role"].long(),
                "col_mismatch": base_mismatch,
                "row_type": sample["row_type"].long(),
            }

        item["metadata"] = {
            "sample_id": sample["sample_id"],
            "source_file": sample["source_file"],
            "sheet_index": sample["sheet_index"],
            "split": sample["split"],
            "variant_type": sample.get("variant_type", "original"),
            "tables": sample["tables"],
        }
        return item


class BucketedBatchSampler(Sampler[list[int]]):
    """Groups sheets of similar row height into batches to minimize wasted padding compute."""

    def __init__(self, samples: list[dict[str, Any]], repeat_factor: int, batch_size: int, shuffle: bool, seed: int) -> None:
        self.heights = [s["shape"][0] for s in samples] * max(1, repeat_factor)
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __iter__(self):
        rng = random.Random(self.seed + self.epoch)
        indices = list(range(len(self.heights)))
        if self.shuffle:
            # Add small jitter to heights so buckets vary across epochs
            indices.sort(key=lambda i: self.heights[i] + rng.uniform(-6.0, 6.0))
        else:
            indices.sort(key=lambda i: self.heights[i])

        batches = [
            indices[i:i + self.batch_size]
            for i in range(0, len(indices), self.batch_size)
        ]
        if self.shuffle:
            rng.shuffle(batches)
        for batch in batches:
            yield batch

    def __len__(self) -> int:
        return math.ceil(len(self.heights) / self.batch_size)


def collate_multitask(batch: list[dict[str, Any]]) -> dict[str, Any]:
    max_h = max(item["cell_target"].shape[0] for item in batch)
    max_w = max(item["cell_target"].shape[1] for item in batch)
    bsz = len(batch)

    inputs = torch.zeros((bsz, FEATURE_CHANNELS, max_h, max_w), dtype=torch.float32)
    cell_targets = torch.full((bsz, max_h, max_w), IGNORE_INDEX, dtype=torch.long)
    table_starts = torch.full((bsz, max_h), -1.0, dtype=torch.float32)
    col_roles = torch.full((bsz, max_w), IGNORE_INDEX, dtype=torch.long)
    col_mismatches = torch.full((bsz, max_w), -1.0, dtype=torch.float32)
    row_types = torch.full((bsz, max_h), IGNORE_INDEX, dtype=torch.long)
    shapes: list[tuple[int, int]] = []
    metadata: list[dict[str, Any]] = []

    for i, item in enumerate(batch):
        h, w = item["cell_target"].shape
        inputs[i, :, :h, :w] = item["features"]
        cell_targets[i, :h, :w] = item["cell_target"]
        table_starts[i, :h] = item["table_start"]
        col_roles[i, :w] = item["col_role"]
        col_mismatches[i, :w] = item["col_mismatch"]
        row_types[i, :h] = item["row_type"]
        shapes.append((h, w))
        metadata.append(item["metadata"])

    return {
        "inputs": inputs,
        "cell_targets": cell_targets,
        "table_starts": table_starts,
        "col_roles": col_roles,
        "col_mismatches": col_mismatches,
        "row_types": row_types,
        "shapes": shapes,
        "metadata": metadata,
    }


def _boundary_weight_map(cell_targets: torch.Tensor) -> torch.Tensor:
    """Give 2.5x emphasis to cells directly on class transition boundaries (top, header_bottom,
    bottom, left, right) so the model sharpens exact box boundaries."""
    valid = cell_targets != IGNORE_INDEX
    safe = torch.where(valid, cell_targets, torch.zeros_like(cell_targets))
    edge = torch.zeros_like(valid)
    # Vertical transitions
    if safe.shape[1] > 1:
        v_diff = (safe[:, 1:, :] != safe[:, :-1, :]) & valid[:, 1:, :] & valid[:, :-1, :]
        edge[:, 1:, :] |= v_diff
        edge[:, :-1, :] |= v_diff
    # Horizontal transitions
    if safe.shape[2] > 1:
        h_diff = (safe[:, :, 1:] != safe[:, :, :-1]) & valid[:, :, 1:] & valid[:, :, :-1]
        edge[:, :, 1:] |= h_diff
        edge[:, :, :-1] |= h_diff
    return torch.where(edge, 2.5, 1.0)


def _multiclass_dice_loss(
    logits: torch.Tensor, targets: torch.Tensor, num_classes: int
) -> torch.Tensor:
    valid = targets != IGNORE_INDEX
    if not bool(valid.any()):
        return logits.sum() * 0.0
    probs = torch.softmax(logits, dim=1)
    safe_t = torch.where(valid, targets, torch.zeros_like(targets))
    one_hot = F.one_hot(safe_t, num_classes=num_classes).permute(0, 3, 1, 2).float()
    mask = valid.unsqueeze(1).float()
    probs = probs * mask
    one_hot = one_hot * mask

    inter = (probs * one_hot).sum(dim=(0, 2, 3))
    denom = probs.sum(dim=(0, 2, 3)) + one_hot.sum(dim=(0, 2, 3))
    present = one_hot.sum(dim=(0, 2, 3)) > 0
    dice = (2.0 * inter + 1.0) / (denom + 1.0)
    if bool(present.any()):
        return (1.0 - dice[present]).mean()
    return (1.0 - dice).mean()


def compute_multitask_loss(
    outputs: dict[str, torch.Tensor],
    batch: dict[str, Any],
    cell_class_weights: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, float]]:
    cell_logits = outputs["cell_logits"]
    cell_targets = batch["cell_targets"]

    # 1. Cell segmentation: Boundary-weighted CE + Multi-class Dice
    ce_map = F.cross_entropy(
        cell_logits, cell_targets, weight=cell_class_weights, ignore_index=IGNORE_INDEX, reduction="none"
    )
    valid_cells = cell_targets != IGNORE_INDEX
    b_weights = _boundary_weight_map(cell_targets)
    ce_loss = (ce_map * b_weights * valid_cells.float()).sum() / (b_weights * valid_cells.float()).sum().clamp_min(1.0)
    dice_loss = _multiclass_dice_loss(cell_logits, cell_targets, len(CELL_CLASS_NAMES))
    cell_loss = ce_loss + 0.65 * dice_loss

    # 2. Row table-start BCE
    ts_logits = outputs["table_start_logits"].squeeze(1)
    ts_targets = batch["table_starts"]
    ts_valid = ts_targets >= 0.0
    if bool(ts_valid.any()):
        pos_w = torch.tensor(8.0, device=ts_logits.device)
        ts_loss = F.binary_cross_entropy_with_logits(
            ts_logits[ts_valid], ts_targets[ts_valid], pos_weight=pos_w
        )
    else:
        ts_loss = cell_loss * 0.0

    # 3. Column role CE
    col_role_logits = outputs["col_role_logits"]
    col_roles = batch["col_roles"]
    if bool((col_roles != IGNORE_INDEX).any()):
        col_weights = torch.tensor([0.6, 1.5, 1.8, 1.0, 1.6], device=col_role_logits.device)
        col_role_loss = F.cross_entropy(
            col_role_logits, col_roles, weight=col_weights, ignore_index=IGNORE_INDEX
        )
    else:
        col_role_loss = cell_loss * 0.0

    # 4. Column mismatch BCE (only supervised on in-table columns)
    cm_logits = outputs["col_mismatch_logits"].squeeze(1)
    cm_targets = batch["col_mismatches"]
    cm_valid = (cm_targets >= 0.0) & (col_roles != COL_OUTSIDE) & (col_roles != IGNORE_INDEX)
    if bool(cm_valid.any()):
        cm_pos_w = torch.tensor(4.0, device=cm_logits.device)
        cm_loss = F.binary_cross_entropy_with_logits(
            cm_logits[cm_valid], cm_targets[cm_valid], pos_weight=cm_pos_w
        )
    else:
        cm_loss = cell_loss * 0.0

    # 5. Row type CE
    rt_logits = outputs["row_type_logits"]
    rt_targets = batch["row_types"]
    if bool((rt_targets != IGNORE_INDEX).any()):
        rt_weights = torch.tensor(
            [0.4, 2.0, 1.8, 1.2, 1.8, 1.4, 1.0, 1.4, 1.5], device=rt_logits.device
        )
        rt_loss = F.cross_entropy(
            rt_logits, rt_targets, weight=rt_weights, ignore_index=IGNORE_INDEX
        )
    else:
        rt_loss = cell_loss * 0.0

    total = cell_loss + 0.30 * ts_loss + 0.35 * col_role_loss + 0.50 * cm_loss + 0.25 * rt_loss
    return total, {
        "total": float(total.detach()),
        "cell": float(cell_loss.detach()),
        "start": float(ts_loss.detach()),
        "col_role": float(col_role_loss.detach()),
        "col_mismatch": float(cm_loss.detach()),
        "row_type": float(rt_loss.detach()),
    }


def box_iou(first: dict[str, Any], second: dict[str, Any]) -> float:
    i_top = max(first["top"], second["top"])
    i_left = max(first["left"], second["left"])
    i_bot = min(first["bottom"], second["bottom"])
    i_right = min(first["right"], second["right"])
    inter = max(0, i_bot - i_top + 1) * max(0, i_right - i_left + 1)
    a1 = (first["bottom"] - first["top"] + 1) * (first["right"] - first["left"] + 1)
    a2 = (second["bottom"] - second["top"] + 1) * (second["right"] - second["left"] + 1)
    return inter / max(1, a1 + a2 - inter)


def compare_table_sets(predicted: list[dict[str, Any]], expected: list[dict[str, Any]]) -> dict[str, float]:
    if not predicted and not expected:
        return {"box_iou": 1.0, "box_iou_at_50": 1.0, "exact_region": 1.0, "exact_header": 1.0}
    available = set(range(len(predicted)))
    ious: list[float] = []
    exact_count = 0
    header_exact_count = 0
    for gold in expected:
        if not available:
            ious.append(0.0)
            continue
        best = max(available, key=lambda idx: box_iou(predicted[idx], gold))
        score = box_iou(predicted[best], gold)
        ious.append(score)
        cand = predicted[best]
        exact_count += int(all(cand[k] == gold[k] for k in ("top", "left", "bottom", "right", "header_bottom")))
        header_exact_count += int(cand["top"] == gold["top"] and cand["header_bottom"] == gold["header_bottom"])
        available.remove(best)
    denom = max(1, len(expected), len(predicted))
    return {
        "box_iou": sum(ious) / denom,
        "box_iou_at_50": sum(s >= 0.50 for s in ious) / denom,
        "exact_region": float(len(predicted) == len(expected) and exact_count == len(expected)),
        "exact_header": float(len(predicted) == len(expected) and header_exact_count == len(expected)),
    }


def metrics_from_confusion(confusion: torch.Tensor) -> dict[str, float]:
    mat = confusion.to(torch.float64)
    total = mat.sum().clamp_min(1)
    metrics: dict[str, float] = {"cell_accuracy": float(mat.diag().sum() / total)}
    f1s: list[float] = []
    for idx, name in enumerate(CELL_CLASS_NAMES):
        tp = mat[idx, idx]
        fp = mat[:, idx].sum() - tp
        fn = mat[idx, :].sum() - tp
        prec = tp / (tp + fp).clamp_min(1)
        rec = tp / (tp + fn).clamp_min(1)
        f1 = 2 * prec * rec / (prec + rec).clamp_min(1e-12)
        iou = tp / (tp + fp + fn).clamp_min(1)
        metrics[f"{name}_f1"] = float(f1)
        metrics[f"{name}_iou"] = float(iou)
        f1s.append(float(f1))
    fg_tp = mat[1:, 1:].sum()
    fg_union = mat[1:, :].sum() + mat[:, 1:].sum() - fg_tp
    metrics["foreground_iou"] = float(fg_tp / fg_union.clamp_min(1))
    metrics["macro_f1"] = sum(f1s) / len(f1s)
    return metrics


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    cell_class_weights: torch.Tensor,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any = None,
    gradient_clip_norm: float = 2.0,
    evaluate_boxes: bool = True,
) -> dict[str, float]:
    training = optimizer is not None
    model.train(training)
    n_cls = len(CELL_CLASS_NAMES)
    confusion = torch.zeros((n_cls, n_cls), dtype=torch.long)
    loss_sums: defaultdict[str, float] = defaultdict(float)
    box_totals: defaultdict[str, float] = defaultdict(float)
    col_correct = 0
    col_total = 0
    row_correct = 0
    row_total = 0
    sample_count = 0

    for batch in loader:
        batch_dev = {
            k: (v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v)
            for k, v in batch.items()
        }
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            outputs = model(batch_dev["inputs"])
            loss, parts = compute_multitask_loss(outputs, batch_dev, cell_class_weights)
            if training:
                loss.backward()
                if gradient_clip_norm > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
                optimizer.step()
                if scheduler is not None:
                    scheduler.step()

        for k, v in parts.items():
            loss_sums[k] += v

        preds = outputs["cell_logits"].argmax(dim=1)
        targets = batch_dev["cell_targets"]
        valid = targets != IGNORE_INDEX
        encoded = targets[valid] * n_cls + preds[valid]
        confusion += torch.bincount(encoded.cpu(), minlength=n_cls * n_cls).reshape(n_cls, n_cls)

        col_valid = batch_dev["col_roles"] != IGNORE_INDEX
        if bool(col_valid.any()):
            col_pred = outputs["col_role_logits"].argmax(dim=1)
            col_correct += int((col_pred[col_valid] == batch_dev["col_roles"][col_valid]).sum().item())
            col_total += int(col_valid.sum().item())

        row_valid = batch_dev["row_types"] != IGNORE_INDEX
        if bool(row_valid.any()):
            row_pred = outputs["row_type_logits"].argmax(dim=1)
            row_correct += int((row_pred[row_valid] == batch_dev["row_types"][row_valid]).sum().item())
            row_total += int(row_valid.sum().item())

        if evaluate_boxes:
            for i, (h, w) in enumerate(batch["shapes"]):
                pred_tables = decode_predictions(
                    cell_logits=outputs["cell_logits"][i, :, :h, :w],
                    table_start_logits=outputs["table_start_logits"][i, :, :h],
                    col_role_logits=outputs["col_role_logits"][i, :, :w],
                    col_mismatch_logits=outputs["col_mismatch_logits"][i, :, :w],
                    row_type_logits=outputs["row_type_logits"][i, :, :h],
                )
                comp = compare_table_sets(pred_tables, batch["metadata"][i]["tables"])
                for k, v in comp.items():
                    box_totals[k] += v
                sample_count += 1

    metrics = metrics_from_confusion(confusion)
    n_batches = max(1, len(loader))
    metrics["loss"] = loss_sums["total"] / n_batches
    metrics["cell_loss"] = loss_sums["cell"] / n_batches
    metrics["col_role_acc"] = col_correct / max(1, col_total)
    metrics["row_type_acc"] = row_correct / max(1, row_total)
    if evaluate_boxes and sample_count > 0:
        for k, v in box_totals.items():
            metrics[k] = v / sample_count
    return metrics


def save_curves(history: list[dict[str, Any]], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    epochs = [item["epoch"] for item in history]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].plot(epochs, [h["train"]["loss"] for h in history], label="train")
    axes[0].plot(epochs, [h["validation"]["loss"] for h in history], label="validation")
    axes[0].set_title("Multi-Task Loss")
    axes[1].plot(epochs, [h["validation"]["macro_f1"] for h in history], label="cell macro F1")
    axes[1].plot(epochs, [h["validation"]["col_role_acc"] for h in history], label="col role acc")
    axes[1].plot(epochs, [h["validation"]["row_type_acc"] for h in history], label="row type acc")
    axes[1].set_title("Validation Multi-Task Metrics")
    axes[2].plot(epochs, [h["validation"]["box_iou"] for h in history], label="box IoU")
    axes[2].plot(epochs, [h["validation"]["exact_region"] for h in history], label="exact region")
    axes[2].set_title("Validation Region Metrics (Raw Neural)")
    for ax in axes:
        ax.set_xlabel("Epoch")
        ax.grid(alpha=0.25)
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def export_torchscript_artifact(
    model: EFormAxialTableNet,
    metadata: dict[str, Any],
    model_path: Path,
) -> Path:
    """Export a self-contained TorchScript .eformmodel bundle that FastAPI loads directly
    via torch.jit.load() with ZERO training-code imports."""
    cpu_model = copy.deepcopy(model).cpu().eval()
    scripted = torch.jit.script(cpu_model)
    meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.jit.save(scripted, str(model_path), _extra_files={"metadata.json": meta_bytes})
    return model_path


def train_model(
    module_root: Path,
    output_dir: Path,
    epochs: int = 24,
    batch_size: int = 12,
    repeat_factor: int = 2,
    learning_rate: float = 2e-3,
    weight_decay: float = 1e-4,
    patience: int = 7,
    base_channels: int = 40,
    dropout: float = 0.05,
    device_name: str = "auto",
    seed: int = 20260913,
    rebuild_cache: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    module_root = module_root.resolve()
    output_dir = output_dir.resolve()
    seed_everything(seed)

    requested = device_name.strip().lower()
    device = torch.device(
        "cuda" if requested == "auto" and torch.cuda.is_available()
        else "cpu" if requested == "auto"
        else requested
    )
    if device.type == "cpu":
        torch.set_num_threads(max(1, min(8, os.cpu_count() or 4)))

    cache = build_or_load_cache(module_root, force_rebuild=rebuild_cache)
    samples = cache["samples"]
    top_pool = cache["top_outside_pool"]
    bottom_pool = cache["bottom_outside_pool"]

    by_split = {
        split: [s for s in samples if s["split"] == split]
        for split in ("train", "validation", "test_id", "test_ood")
    }
    print(f"Device: {device} | PyTorch: {torch.__version__}")
    print("Splits:", {k: len(v) for k, v in by_split.items()})

    train_ds = CachedSheetDataset(by_split["train"], True, top_pool, bottom_pool, repeat_factor, seed)
    val_ds = CachedSheetDataset(by_split["validation"], False, [], [], 1, seed)
    test_id_ds = CachedSheetDataset(by_split["test_id"], False, [], [], 1, seed)
    test_ood_ds = CachedSheetDataset(by_split["test_ood"], False, [], [], 1, seed)

    train_sampler = BucketedBatchSampler(by_split["train"], repeat_factor, batch_size, True, seed)
    val_sampler = BucketedBatchSampler(by_split["validation"], 1, batch_size, False, seed)
    tid_sampler = BucketedBatchSampler(by_split["test_id"], 1, batch_size, False, seed)
    tood_sampler = BucketedBatchSampler(by_split["test_ood"], 1, batch_size, False, seed)

    train_loader = DataLoader(train_ds, batch_sampler=train_sampler, collate_fn=collate_multitask)
    val_loader = DataLoader(val_ds, batch_sampler=val_sampler, collate_fn=collate_multitask)
    test_id_loader = DataLoader(test_id_ds, batch_sampler=tid_sampler, collate_fn=collate_multitask)
    test_ood_loader = DataLoader(test_ood_ds, batch_sampler=tood_sampler, collate_fn=collate_multitask)

    model = EFormAxialTableNet(
        input_channels=FEATURE_CHANNELS, base_channels=base_channels, dropout=dropout
    ).to(device)
    param_count = sum(p.numel() for p in model.parameters())
    print(f"Model: EFormAxialTableNet(base_channels={base_channels}) | Params: {param_count:,}")
    print(f"Train samples/epoch: {len(train_ds)} | Batches/epoch: {len(train_loader)} | Epochs: {epochs}")

    cell_class_weights = torch.tensor([1.0, 1.4, 1.5, 1.2], dtype=torch.float32, device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    total_steps = max(1, epochs * len(train_loader))
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=learning_rate,
        total_steps=total_steps,
        pct_start=0.15,
        anneal_strategy="cos",
    )

    history: list[dict[str, Any]] = []
    best_state = copy.deepcopy(model.state_dict())
    best_score = -1.0
    best_epoch = 0
    stale = 0

    for epoch in range(1, epochs + 1):
        t0 = time.perf_counter()
        train_ds.set_epoch(epoch)
        train_sampler.set_epoch(epoch)
        train_m = run_epoch(
            model, train_loader, device, cell_class_weights, optimizer, scheduler, evaluate_boxes=False
        )
        val_m = run_epoch(
            model, val_loader, device, cell_class_weights, optimizer=None, evaluate_boxes=True
        )
        elapsed = time.perf_counter() - t0
        # Composite score prioritizes exact_region + box_iou + multi-task accuracy,
        # using -val_loss as tie-breaker once exact_region reaches 1.0000 so augmented heads keep sharpening.
        score = (
            0.38 * val_m.get("exact_region", 0.0)
            + 0.25 * val_m.get("box_iou", 0.0)
            + 0.15 * val_m["macro_f1"]
            + 0.12 * val_m["col_role_acc"]
            + 0.05 * val_m["row_type_acc"]
            - 0.15 * min(val_m["loss"], 2.0)
        )
        history.append({"epoch": epoch, "seconds": round(elapsed, 1), "train": train_m, "validation": val_m})
        print(
            f"Epoch {epoch:02d}/{epochs} ({elapsed:4.1f}s) | "
            f"tr_loss={train_m['loss']:.4f} | val_loss={val_m['loss']:.4f} | "
            f"val_f1={val_m['macro_f1']:.4f} | box_iou={val_m['box_iou']:.4f} | "
            f"exact={val_m['exact_region']:.4f} | col_acc={val_m['col_role_acc']:.4f} | "
            f"row_acc={val_m['row_type_acc']:.4f}"
        )
        if score > best_score + 1e-4:
            best_score = score
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
            if stale >= patience and epoch >= max(10, epochs // 2):
                print(f"Early stopping at epoch {epoch} (best_epoch={best_epoch}, score={best_score:.4f})")
                break

    model.load_state_dict(best_state)
    val_final = run_epoch(model, val_loader, device, cell_class_weights, evaluate_boxes=True)
    test_id_final = run_epoch(model, test_id_loader, device, cell_class_weights, evaluate_boxes=True)
    test_ood_final = run_epoch(model, test_ood_loader, device, cell_class_weights, evaluate_boxes=True)

    metadata = {
        "format_version": FORMAT_VERSION,
        "model_name": MODEL_NAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "torch_version": str(torch.__version__),
        "parameter_count": param_count,
        "dataset_sha256": cache["dataset_sha256"],
        "clean_summary": cache["clean_summary"],
        "model_config": {
            "architecture": "EFormAxialTableNet",
            "input_channels": FEATURE_CHANNELS,
            "base_channels": base_channels,
            "cell_classes": list(CELL_CLASS_NAMES),
            "col_roles": list(COL_ROLE_NAMES),
            "row_types": list(ROW_TYPE_NAMES),
        },
        "feature_config": {
            "channels": FEATURE_CHANNELS,
            "text_hash_dimensions": TEXT_HASH_DIM,
            "translation_invariant": True,
        },
        "training_config": {
            "epochs_requested": epochs,
            "epochs_completed": len(history),
            "best_epoch": best_epoch,
            "batch_size": batch_size,
            "repeat_factor": repeat_factor,
            "learning_rate": learning_rate,
            "weight_decay": weight_decay,
            "seed": seed,
            "train_seconds": round(time.perf_counter() - started, 1),
        },
        "inference_config": {
            "minimum_component_cells": 4,
            "header_fraction_threshold": 0.30,
            "table_start_threshold": 0.45,
            "col_mismatch_threshold": 0.45,
        },
        "metrics": {
            "validation": val_final,
            "test_id": test_id_final,
            "test_ood": test_ood_final,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / MODEL_FILENAME
    export_torchscript_artifact(model, metadata, model_path)

    # Verify standalone TorchScript reload via eform_ai.predictor
    predictor = EFormPredictor(model_path, device_name="cpu")
    smoke_sample = next(s for s in by_split["test_id"] if s["tables"])
    sample_file = module_root / smoke_sample["source_file"]
    smoke_res = predictor.predict(sample_file)
    assert smoke_res["schemaVersion"] == "2.0" and smoke_res["summary"]["tableCount"] >= 1

    report = {
        "model_file": str(model_path),
        "model_size_bytes": model_path.stat().st_size,
        "artifact_reload_verified": True,
        "metadata": metadata,
        "history": history,
    }
    (output_dir / "training_report_v2.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    save_curves(history, output_dir / "training_curves_v2.png")

    print("\n=== TRAINING COMPLETE (TORCHSCRIPT EXPORTED) ===")
    print(json.dumps({
        "model_file": str(model_path),
        "model_size_kb": round(model_path.stat().st_size / 1024, 1),
        "best_epoch": best_epoch,
        "validation": {k: round(v, 4) for k, v in val_final.items() if k in ("cell_accuracy", "macro_f1", "box_iou", "exact_region", "exact_header", "col_role_acc", "row_type_acc")},
        "test_id": {k: round(v, 4) for k, v in test_id_final.items() if k in ("cell_accuracy", "macro_f1", "box_iou", "exact_region", "exact_header", "col_role_acc", "row_type_acc")},
        "test_ood": {k: round(v, 4) for k, v in test_ood_final.items() if k in ("cell_accuracy", "macro_f1", "box_iou", "exact_region", "exact_header", "col_role_acc", "row_type_acc")},
    }, ensure_ascii=False, indent=2))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train EForm Axial Multi-Task TableNet & export TorchScript")
    parser.add_argument("--module-root", type=Path, default=MODULE_DIR)
    parser.add_argument("--output-dir", type=Path, default=TRAIN_DIR / "Output_Local")
    parser.add_argument("--epochs", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--repeat-factor", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=2e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=7)
    parser.add_argument("--base-channels", type=int, default=40)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--rebuild-cache", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train_model(
        module_root=args.module_root,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        repeat_factor=args.repeat_factor,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        patience=args.patience,
        base_channels=args.base_channels,
        dropout=args.dropout,
        device_name=args.device,
        seed=args.seed,
        rebuild_cache=args.rebuild_cache,
    )
