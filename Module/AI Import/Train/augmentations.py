from __future__ import annotations

import random
from typing import Any

import torch

from eform_ai.schema import (
    CELL_HEADER_CODE,
    CELL_HEADER_TITLE,
    CELL_OUTSIDE,
    CELL_VALUE,
    CH_ALPHA_RATIO,
    CH_BOLD,
    CH_BORDER,
    CH_BULLET_START,
    CH_CENTERED,
    CH_CODE_SEQ_ROW,
    CH_MERGE_COLSPAN,
    CH_MERGED,
    CH_NONEMPTY,
    CH_NUMERIC,
    CH_NUMERIC_TEXT,
    CH_TEXT,
    CH_TEXT_HASH_START,
    CH_TEXT_LEN,
    COL_DATA,
    COL_LABEL,
    COL_NOTE,
    COL_OUTSIDE,
    FEATURE_CHANNELS,
    ROW_EMPTY,
    ROW_OUTSIDE_OR_HEADER,
)


def _fit_row_width(row_feat: torch.Tensor, target_w: int) -> torch.Tensor:
    """Adapt a real outside row (C, W0) to target width W without distorting left-aligned text."""
    c, w0 = row_feat.shape
    out = torch.zeros((c, target_w), dtype=torch.float32)
    copy_w = min(w0, target_w)
    out[:, :copy_w] = row_feat[:, :copy_w].float()
    return out


def _crop_long_sheet(
    features: torch.Tensor,
    cell_target: torch.Tensor,
    table_start: torch.Tensor,
    col_role: torch.Tensor,
    row_type: torch.Tensor,
    rng: random.Random,
    max_rows: int = 44,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Sub-sample middle value rows of very tall sheets while preserving full headers,
    top/bottom table boundaries, and footers (3x faster CPU training with zero boundary loss)."""
    h = features.shape[1]
    if h <= max_rows:
        return features, cell_target, table_start, col_role, row_type

    # Find value rows strictly inside interior (not touching top/header/bottom)
    is_val_row = (cell_target == CELL_VALUE).any(dim=1)
    val_indices = torch.nonzero(is_val_row, as_tuple=False).squeeze(-1).tolist()
    if len(val_indices) <= 20:
        return features, cell_target, table_start, col_role, row_type

    keep_head = 8
    keep_tail = 8
    interior = val_indices[keep_head:-keep_tail]
    drop_needed = min(len(interior), h - max_rows)
    if drop_needed <= 0:
        return features, cell_target, table_start, col_role, row_type

    # Drop a contiguous slice of interior value rows
    start_offset = rng.randint(0, len(interior) - drop_needed)
    drop_set = set(interior[start_offset:start_offset + drop_needed])
    keep_idx = [r for r in range(h) if r not in drop_set]
    idx_t = torch.tensor(keep_idx, dtype=torch.long)
    return (
        features[:, idx_t, :],
        cell_target[idx_t, :],
        table_start[idx_t],
        col_role,
        row_type[idx_t],
    )


def _synthesize_negative_sheet(
    top_pool: list[torch.Tensor],
    bottom_pool: list[torch.Tensor],
    rng: random.Random,
) -> dict[str, torch.Tensor]:
    """Synthesize a pure non-table sheet (e.g. instructions, cover notes, signatures)."""
    h = rng.randint(8, 22)
    w = rng.randint(6, 16)
    features = torch.zeros((FEATURE_CHANNELS, h, w), dtype=torch.float32)

    pool = top_pool + bottom_pool
    for r in range(h):
        if pool and rng.random() < 0.55:
            row_feat = _fit_row_width(rng.choice(pool), w)
            # Optionally shift text into a random left column
            shift = rng.randint(0, min(3, max(0, w - 3)))
            if shift > 0:
                shifted = torch.zeros_like(row_feat)
                shifted[:, shift:] = row_feat[:, :w - shift]
                row_feat = shifted
            # Ensure no dense table border grid sneaks in
            row_feat[CH_BORDER, :] = 0.0
            row_feat[CH_CODE_SEQ_ROW, :] = 0.0
            features[:, r, :] = row_feat

    return {
        "features": features,
        "cell_target": torch.full((h, w), CELL_OUTSIDE, dtype=torch.long),
        "table_start": torch.zeros((h,), dtype=torch.float32),
        "col_role": torch.full((w,), COL_OUTSIDE, dtype=torch.long),
        "col_mismatch": torch.zeros((w,), dtype=torch.float32),
        "row_type": torch.full((h,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long),
    }


def _crop_compact_table(sample: dict[str, Any], rng: random.Random) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Extract a compact sub-table (header + 2..6 value rows) from another train sheet for multi-table stacking."""
    feat = sample["features"].float()
    ct = sample["cell_target"].long()
    rt = sample["row_type"].long()
    tables = sample["tables"]
    t = rng.choice(tables)
    top, left = t["top"] - 1, t["left"] - 1
    bottom, right = t["bottom"], t["right"]
    hb = t["header_bottom"]

    # Keep header + up to 5 value rows so stacked sheet stays compact
    val_count = bottom - hb
    keep_vals = min(val_count, rng.randint(1, 5))
    end_row = hb + keep_vals

    sub_f = feat[:, top:end_row, left:right].clone()
    sub_ct = ct[top:end_row, left:right].clone()
    sub_ts = torch.zeros((end_row - top,), dtype=torch.float32)
    sub_ts[0] = 1.0
    sub_rt = rt[top:end_row].clone()
    return sub_f, sub_ct, sub_ts, sub_rt


def augment_training_sample(
    sample: dict[str, Any],
    all_train_samples: list[dict[str, Any]],
    top_pool: list[torch.Tensor],
    bottom_pool: list[torch.Tensor],
    rng: random.Random,
) -> dict[str, torch.Tensor]:
    """Apply comprehensive online augmentations covering all 12 real-world Excel perturbations,
    multi-table stacking, no-table instruction sheets, and column-mismatch anomalies."""
    # 1. Negative (no-table) sheet synthesis (7%)
    if (top_pool or bottom_pool) and rng.random() < 0.07:
        return _synthesize_negative_sheet(top_pool, bottom_pool, rng)

    features = sample["features"].float().clone()
    cell_target = sample["cell_target"].long().clone()
    table_start = sample["table_start"].float().clone()
    col_role = sample["col_role"].long().clone()
    row_type = sample["row_type"].long().clone()

    # Keep huge sheets fast on CPU during training (65% cropped interior, 35% full)
    if features.shape[1] > 48 and rng.random() < 0.65:
        features, cell_target, table_start, col_role, row_type = _crop_long_sheet(
            features, cell_target, table_start, col_role, row_type, rng, max_rows=42
        )

    h, w = cell_target.shape
    col_mismatch = torch.zeros((w,), dtype=torch.float32)

    # 2. Unmerge all ("Bỏ ô gộp", 30%)
    if rng.random() < 0.30:
        features[CH_MERGED:CH_MERGE_COLSPAN + 1, :, :] = 0.0

    # 3. Borderless ("Không kẻ khung", 30%) or full style drop (15%)
    r_style = rng.random()
    if r_style < 0.30:
        features[CH_BORDER, :, :] = 0.0
    elif r_style < 0.45:
        features[CH_BOLD:CH_BORDER + 1, :, :] = 0.0
    elif rng.random() < 0.25:
        # Partial random style dropout (10-40%)
        drop_p = rng.uniform(0.10, 0.40)
        mask = torch.rand((h, w)) < drop_p
        features[CH_BOLD:CH_BORDER + 1, mask] = 0.0

    # 4. Drop column-code row ("Không có dòng số thứ tự cột", 28%)
    if rng.random() < 0.28:
        code_rows = (cell_target == CELL_HEADER_CODE).any(dim=1)
        if bool(code_rows.any()):
            keep = ~code_rows
            if int(keep.sum()) >= 3:
                features = features[:, keep, :]
                cell_target = cell_target[keep, :]
                table_start = table_start[keep]
                row_type = row_type[keep]
                h = cell_target.shape[0]

    # 5. Numeric stored as text ("Số dạng chữ", 28%)
    if rng.random() < 0.28:
        num_mask = features[CH_NUMERIC] > 0.5
        if bool(num_mask.any()):
            features[CH_NUMERIC, num_mask] = 0.0
            features[CH_TEXT, num_mask] = 1.0
            features[CH_NUMERIC_TEXT, num_mask] = 1.0
            features[CH_TEXT_LEN, num_mask] = 0.03
            features[CH_ALPHA_RATIO, num_mask] = 0.0

    # 6. Interleaved blank rows inside value region ("Dòng trống xen kẽ", 25%)
    if rng.random() < 0.25:
        val_rows = torch.nonzero((cell_target == CELL_VALUE).any(dim=1), as_tuple=False).squeeze(-1).tolist()
        if len(val_rows) >= 2:
            # Find active columns of the table at the insertion point
            n_blanks = rng.randint(1, min(2, len(val_rows) - 1))
            insert_pos = rng.choice(val_rows[1:])
            active_cols = cell_target[insert_pos] == CELL_VALUE

            blank_f = torch.zeros((FEATURE_CHANNELS, n_blanks, w), dtype=torch.float32)
            # Optionally preserve border on interleaved blank row (50% with border, 50% without)
            if rng.random() < 0.50:
                blank_f[CH_BORDER, :, :] = features[CH_BORDER, insert_pos:insert_pos + 1, :]
            blank_ct = torch.full((n_blanks, w), CELL_OUTSIDE, dtype=torch.long)
            blank_ct[:, active_cols] = CELL_VALUE
            blank_ts = torch.zeros((n_blanks,), dtype=torch.float32)
            blank_rt = torch.full((n_blanks,), ROW_EMPTY, dtype=torch.long)

            features = torch.cat((features[:, :insert_pos, :], blank_f, features[:, insert_pos:, :]), dim=1)
            cell_target = torch.cat((cell_target[:insert_pos, :], blank_ct, cell_target[insert_pos:, :]), dim=0)
            table_start = torch.cat((table_start[:insert_pos], blank_ts, table_start[insert_pos:]), dim=0)
            row_type = torch.cat((row_type[:insert_pos], blank_rt, row_type[insert_pos:]), dim=0)
            h = cell_target.shape[0]

    # 7. Append an extra internal note column ("Thêm cột ghi chú", 20%)
    if rng.random() < 0.20 and w <= 28:
        fg_cols = torch.nonzero((cell_target != CELL_OUTSIDE).any(dim=0), as_tuple=False).squeeze(-1)
        if len(fg_cols) >= 3:
            last_col = int(fg_cols[-1].item())
            hdr_rows_mask = (cell_target[:, last_col] == CELL_HEADER_TITLE) | (
                cell_target[:, last_col] == CELL_HEADER_CODE
            )
            val_rows_mask = cell_target[:, last_col] == CELL_VALUE

            new_col_f = torch.zeros((FEATURE_CHANNELS, h, 1), dtype=torch.float32)
            # Header cell: text + bold + centered + same border as neighbor
            hdr_indices = torch.nonzero(hdr_rows_mask, as_tuple=False).squeeze(-1)
            if len(hdr_indices) > 0:
                top_h = int(hdr_indices[0].item())
                new_col_f[CH_NONEMPTY, top_h, 0] = 1.0
                new_col_f[CH_TEXT, top_h, 0] = 1.0
                new_col_f[CH_BOLD, top_h, 0] = features[CH_BOLD, top_h, last_col]
                new_col_f[CH_CENTERED, top_h, 0] = 1.0
                new_col_f[CH_TEXT_LEN, top_h, 0] = 0.08
                new_col_f[CH_ALPHA_RATIO, top_h, 0] = 0.85
                new_col_f[CH_BORDER, hdr_rows_mask, 0] = features[CH_BORDER, hdr_rows_mask, last_col]
            new_col_f[CH_BORDER, val_rows_mask, 0] = features[CH_BORDER, val_rows_mask, last_col]
            # Sparse note text on a few value rows
            val_indices = torch.nonzero(val_rows_mask, as_tuple=False).squeeze(-1).tolist()
            for vr in val_indices:
                if rng.random() < 0.20:
                    new_col_f[CH_NONEMPTY, vr, 0] = 1.0
                    new_col_f[CH_TEXT, vr, 0] = 1.0
                    new_col_f[CH_TEXT_LEN, vr, 0] = 0.12
                    new_col_f[CH_ALPHA_RATIO, vr, 0] = 0.80

            new_col_ct = cell_target[:, last_col:last_col + 1].clone()
            # Insert right after last_col
            pos = last_col + 1
            features = torch.cat((features[:, :, :pos], new_col_f, features[:, :, pos:]), dim=2)
            cell_target = torch.cat((cell_target[:, :pos], new_col_ct, cell_target[:, pos:]), dim=1)
            col_role = torch.cat((col_role[:pos], torch.tensor([COL_NOTE], dtype=torch.long), col_role[pos:]))
            col_mismatch = torch.cat((col_mismatch[:pos], torch.tensor([0.0], dtype=torch.float32), col_mismatch[pos:]))
            w = cell_target.shape[1]

    # 8. Valid column swap ("Đảo cột": both header + body move together -> col_mismatch = 0, 20%)
    data_cols = torch.nonzero(col_role == COL_DATA, as_tuple=False).squeeze(-1).tolist()
    if len(data_cols) >= 2 and rng.random() < 0.20:
        c1, c2 = rng.sample(data_cols, 2)
        perm = list(range(w))
        perm[c1], perm[c2] = perm[c2], perm[c1]
        p_t = torch.tensor(perm, dtype=torch.long)
        features = features[:, :, p_t]
        cell_target = cell_target[:, p_t]
        col_role = col_role[p_t]
        col_mismatch = col_mismatch[p_t]
        # Clear merged flags on swapped columns so header doesn't look brokenly merged
        features[CH_MERGED:CH_MERGE_COLSPAN + 1, :, c1] = 0.0
        features[CH_MERGED:CH_MERGE_COLSPAN + 1, :, c2] = 0.0

    # 9. Column-mismatch synthesis (body-only shift like File B of 11b -> col_mismatch = 1, 20%)
    label_cols = torch.nonzero(col_role == COL_LABEL, as_tuple=False).squeeze(-1).tolist()
    val_row_mask = (cell_target == CELL_VALUE).any(dim=1)
    if label_cols and len(data_cols) >= 1 and int(val_row_mask.sum()) >= 2 and rng.random() < 0.20:
        lc = label_cols[0]
        # Pick either a note_col or data_col to swap value-body with label_col (keeping headers fixed!)
        note_cols = torch.nonzero(col_role == COL_NOTE, as_tuple=False).squeeze(-1).tolist()
        target_pool = note_cols + data_cols
        tc = rng.choice(target_pool)
        if tc != lc:
            lc_body = features[:, val_row_mask, lc].clone()
            tc_body = features[:, val_row_mask, tc].clone()
            features[:, val_row_mask, lc] = tc_body
            features[:, val_row_mask, tc] = lc_body
            # Learned col_role follows actual content (where the row names actually live!)
            old_tc_role = int(col_role[tc].item())
            col_role[tc] = COL_LABEL
            col_role[lc] = old_tc_role
            col_mismatch[lc] = 1.0
            col_mismatch[tc] = 1.0

    # 10. Multi-table stacking ("Hai bảng", 24%)
    if all_train_samples and rng.random() < 0.24 and h <= 45:
        other = rng.choice(all_train_samples)
        if other["tables"]:
            sub_f, sub_ct, sub_ts, sub_rt = _crop_compact_table(other, rng)
            sh, sw = sub_ct.shape
            gap = rng.randint(1, 5)
            new_w = max(w, sw)

            # Pad current sheet horizontally if needed
            if new_w > w:
                pad_w = new_w - w
                features = torch.cat((features, torch.zeros((FEATURE_CHANNELS, h, pad_w))), dim=2)
                cell_target = torch.cat((cell_target, torch.full((h, pad_w), CELL_OUTSIDE, dtype=torch.long)), dim=1)
                col_role = torch.cat((col_role, torch.full((pad_w,), COL_OUTSIDE, dtype=torch.long)))
                col_mismatch = torch.cat((col_mismatch, torch.zeros((pad_w,), dtype=torch.float32)))
                w = new_w

            # Pad stacked table horizontally to new_w (optionally offset slightly)
            sub_offset = rng.randint(0, max(0, new_w - sw))
            padded_sf = torch.zeros((FEATURE_CHANNELS, sh, new_w), dtype=torch.float32)
            padded_sct = torch.full((sh, new_w), CELL_OUTSIDE, dtype=torch.long)
            padded_sf[:, :, sub_offset:sub_offset + sw] = sub_f
            padded_sct[:, sub_offset:sub_offset + sw] = sub_ct

            # Gap rows (blank + optionally a title row from top_pool)
            gap_f = torch.zeros((FEATURE_CHANNELS, gap, new_w), dtype=torch.float32)
            if gap >= 2 and top_pool and rng.random() < 0.50:
                gap_f[:, gap - 1, :] = _fit_row_width(rng.choice(top_pool), new_w)
            gap_ct = torch.full((gap, new_w), CELL_OUTSIDE, dtype=torch.long)
            gap_ts = torch.zeros((gap,), dtype=torch.float32)
            gap_rt = torch.full((gap,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long)

            # Stack below (70%) or above (30%)
            if rng.random() < 0.70:
                features = torch.cat((features, gap_f, padded_sf), dim=1)
                cell_target = torch.cat((cell_target, gap_ct, padded_sct), dim=0)
                table_start = torch.cat((table_start, gap_ts, sub_ts), dim=0)
                row_type = torch.cat((row_type, gap_rt, sub_rt), dim=0)
            else:
                features = torch.cat((padded_sf, gap_f, features), dim=1)
                cell_target = torch.cat((padded_sct, gap_ct, cell_target), dim=0)
                table_start = torch.cat((sub_ts, gap_ts, table_start), dim=0)
                row_type = torch.cat((sub_rt, gap_rt, row_type), dim=0)
            h = cell_target.shape[0]

    # 11. Prepend real metadata rows & append real long footers/notes ("Chân trang dài", 65%)
    if rng.random() < 0.65:
        if top_pool and rng.random() < 0.65:
            n_top = rng.randint(1, 5)
            extra_top_f = torch.zeros((FEATURE_CHANNELS, n_top, w), dtype=torch.float32)
            for i in range(n_top):
                if rng.random() < 0.75:
                    extra_top_f[:, i, :] = _fit_row_width(rng.choice(top_pool), w)
            features = torch.cat((extra_top_f, features), dim=1)
            cell_target = torch.cat((torch.full((n_top, w), CELL_OUTSIDE, dtype=torch.long), cell_target), dim=0)
            table_start = torch.cat((torch.zeros((n_top,), dtype=torch.float32), table_start), dim=0)
            row_type = torch.cat((torch.full((n_top,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long), row_type), dim=0)
            h = cell_target.shape[0]

        if bottom_pool and rng.random() < 0.75:
            n_bot = rng.randint(1, 8)
            extra_bot_f = torch.zeros((FEATURE_CHANNELS, n_bot, w), dtype=torch.float32)
            for i in range(n_bot):
                if rng.random() < 0.80:
                    row_f = _fit_row_width(rng.choice(bottom_pool), w)
                    # Sometimes a footnote sits right under the table with bullet/colon cues
                    if rng.random() < 0.30:
                        row_f[CH_BULLET_START, 0] = 1.0
                    extra_bot_f[:, i, :] = row_f
            features = torch.cat((features, extra_bot_f), dim=1)
            cell_target = torch.cat((cell_target, torch.full((n_bot, w), CELL_OUTSIDE, dtype=torch.long)), dim=0)
            table_start = torch.cat((table_start, torch.zeros((n_bot,), dtype=torch.float32)), dim=0)
            row_type = torch.cat((row_type, torch.full((n_bot,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long)), dim=0)
            h = cell_target.shape[0]

    # 12. Random translation & empty margin padding on all 4 sides ("Dịch vị trí", 80%)
    if rng.random() < 0.80:
        pad_top = rng.randint(0, 6)
        pad_bot = rng.randint(0, 4)
        pad_left = rng.randint(0, 6)
        pad_right = rng.randint(0, 4)
        if pad_top or pad_bot or pad_left or pad_right:
            nh = h + pad_top + pad_bot
            nw = w + pad_left + pad_right
            nf = torch.zeros((FEATURE_CHANNELS, nh, nw), dtype=torch.float32)
            nct = torch.full((nh, nw), CELL_OUTSIDE, dtype=torch.long)
            nts = torch.zeros((nh,), dtype=torch.float32)
            ncr = torch.full((nw,), COL_OUTSIDE, dtype=torch.long)
            ncm = torch.zeros((nw,), dtype=torch.float32)
            nrt = torch.full((nh,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long)

            nf[:, pad_top:pad_top + h, pad_left:pad_left + w] = features
            nct[pad_top:pad_top + h, pad_left:pad_left + w] = cell_target
            nts[pad_top:pad_top + h] = table_start
            ncr[pad_left:pad_left + w] = col_role
            ncm[pad_left:pad_left + w] = col_mismatch
            nrt[pad_top:pad_top + h] = row_type

            features, cell_target, table_start, col_role, col_mismatch, row_type = (
                nf, nct, nts, ncr, ncm, nrt
            )
            h, w = nh, nw

    # 13. Mild text-hash dropout so model stays robust to unseen wording (25%)
    if rng.random() < 0.25:
        drop_mask = torch.rand((h, w)) < rng.uniform(0.08, 0.22)
        features[CH_TEXT_HASH_START:, drop_mask] = 0.0

    return {
        "features": features,
        "cell_target": cell_target,
        "table_start": table_start,
        "col_role": col_role,
        "col_mismatch": col_mismatch,
        "row_type": row_type,
    }
