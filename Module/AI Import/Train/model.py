from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F

from eform_ai.schema import (
    CELL_CLASS_NAMES,
    COL_ROLE_NAMES,
    FEATURE_CHANNELS,
    ROW_TYPE_NAMES,
)


def _group_count(channels: int) -> int:
    for groups in (8, 4, 2):
        if channels % groups == 0:
            return groups
    return 1


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.0) -> None:
        super().__init__()
        layers: list[nn.Module] = [
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(out_channels), out_channels),
            nn.GELU(),
        ]
        if dropout > 0.0:
            layers.append(nn.Dropout2d(dropout))
        layers.extend([
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(out_channels), out_channels),
            nn.GELU(),
        ])
        self.block = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class AxialContextBlock(nn.Module):
    """Linear O(H*W) global row + column + 1D-strip context fusion block.

    Gives every cell full visibility into its entire row (e.g. sparse footer vs dense data row)
    and entire column (e.g. text-label column vs numeric column, unmerged multi-row headers)
    while staying 100% TorchScript-compatible and fast on CPU for 2,500+ row sheets.
    """

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.strip_v = nn.Conv2d(
            channels, channels, kernel_size=(5, 1), padding=(2, 0), groups=channels, bias=False
        )
        self.strip_h = nn.Conv2d(
            channels, channels, kernel_size=(1, 5), padding=(0, 2), groups=channels, bias=False
        )
        self.fuse = nn.Sequential(
            nn.Conv2d(channels * 7, channels, kernel_size=1, bias=False),
            nn.GroupNorm(_group_count(channels), channels),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        row_mean = x.mean(dim=3, keepdim=True).expand_as(x)
        row_max = x.amax(dim=3, keepdim=True).expand_as(x)
        col_mean = x.mean(dim=2, keepdim=True).expand_as(x)
        col_max = x.amax(dim=2, keepdim=True).expand_as(x)
        sv = self.strip_v(x)
        sh = self.strip_h(x)
        fused = self.fuse(torch.cat((x, row_mean, row_max, col_mean, col_max, sv, sh), dim=1))
        return x + fused


class EFormAxialTableNet(nn.Module):
    """Multi-task, translation-equivariant Axial U-Net for Excel table understanding.

    Predicts:
      - cell_logits:        (B, 4, H, W)  -> outside / header_title / header_code / value
      - table_start_logits: (B, 1, H)     -> exact top row of each table (splits stacked tables)
      - col_role_logits:    (B, 5, W)     -> outside / code_col / label_col / data_col / note_col
      - col_mismatch_logits:(B, 1, W)     -> header-vs-body contradiction per column
      - row_type_logits:    (B, 9, H)     -> outside_or_header / grand_total / section / item / ...
    """

    def __init__(
        self,
        input_channels: int = FEATURE_CHANNELS,
        base_channels: int = 40,
        dropout: float = 0.05,
    ) -> None:
        super().__init__()
        c1 = base_channels
        c2 = base_channels * 2
        c3 = base_channels * 3

        self.encoder1 = ConvBlock(input_channels, c1, dropout=dropout)
        self.axial1 = AxialContextBlock(c1)

        self.encoder2 = ConvBlock(c1, c2, dropout=dropout)
        self.axial2 = AxialContextBlock(c2)

        self.bottleneck = ConvBlock(c2, c3, dropout=dropout)
        self.axial_bot = AxialContextBlock(c3)

        self.decoder2 = ConvBlock(c3 + c2, c2, dropout=dropout)
        self.decoder1 = ConvBlock(c2 + c1, c1, dropout=dropout)
        self.axial_out = AxialContextBlock(c1)

        # Head 1: Per-cell 4-class segmentation
        self.cell_head = nn.Conv2d(c1, len(CELL_CLASS_NAMES), kernel_size=1)

        # Head 2: Row-level table-start detection
        self.table_start_head = nn.Sequential(
            nn.Conv1d(c1 * 2, c1, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(c1), c1),
            nn.GELU(),
            nn.Conv1d(c1, 1, kernel_size=1),
        )

        # Head 3 & 4: Column role & header-vs-body mismatch detection
        self.col_trunk = nn.Sequential(
            nn.Conv1d(c1 * 3, c1 * 2, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(c1 * 2), c1 * 2),
            nn.GELU(),
        )
        self.col_role_head = nn.Conv1d(c1 * 2, len(COL_ROLE_NAMES), kernel_size=1)
        self.col_mismatch_head = nn.Conv1d(c1 * 2, 1, kernel_size=1)

        # Head 5: Row hierarchy type classification (uses row summary + attended label-col feat)
        self.row_type_head = nn.Sequential(
            nn.Conv1d(c1 * 3, c1 * 2, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(c1 * 2), c1 * 2),
            nn.GELU(),
            nn.Conv1d(c1 * 2, len(ROW_TYPE_NAMES), kernel_size=1),
        )

    def forward(self, inputs: torch.Tensor) -> Dict[str, torch.Tensor]:
        e1 = self.axial1(self.encoder1(inputs))
        e2 = self.axial2(self.encoder2(F.max_pool2d(e1, 2, ceil_mode=True)))
        bot = self.axial_bot(self.bottleneck(F.max_pool2d(e2, 2, ceil_mode=True)))

        d2 = F.interpolate(bot, size=(e2.shape[2], e2.shape[3]), mode="bilinear", align_corners=False)
        d2 = self.decoder2(torch.cat((d2, e2), dim=1))

        d1 = F.interpolate(d2, size=(e1.shape[2], e1.shape[3]), mode="bilinear", align_corners=False)
        feat = self.axial_out(self.decoder1(torch.cat((d1, e1), dim=1)))

        cell_logits = self.cell_head(feat)
        cell_probs = torch.softmax(cell_logits, dim=1)

        # Row pooling for table start
        row_mean = feat.mean(dim=3)
        row_max = feat.amax(dim=3)
        row_summary = torch.cat((row_mean, row_max), dim=1)
        table_start_logits = self.table_start_head(row_summary)

        # Header-attended vs Value-attended column summaries (critical for col role & mismatch!)
        hdr_weight = (cell_probs[:, 1:2, :, :] + cell_probs[:, 2:3, :, :])
        val_weight = cell_probs[:, 3:4, :, :]
        col_hdr = (feat * hdr_weight).sum(dim=2) / (hdr_weight.sum(dim=2) + 1e-4)
        col_val = (feat * val_weight).sum(dim=2) / (val_weight.sum(dim=2) + 1e-4)
        col_all = feat.mean(dim=2)
        col_feat = self.col_trunk(torch.cat((col_hdr, col_val, col_all), dim=1))
        col_role_logits = self.col_role_head(col_feat)
        col_mismatch_logits = self.col_mismatch_head(col_feat)

        # Attended label/code column features per row for row-type classification
        col_probs = torch.softmax(col_role_logits, dim=1)
        id_col_weight = (col_probs[:, 1:2, :] + col_probs[:, 2:3, :]).unsqueeze(2)  # (B, 1, 1, W)
        row_id_feat = (feat * id_col_weight).sum(dim=3) / (id_col_weight.sum(dim=3) + 1e-4)
        row_type_logits = self.row_type_head(torch.cat((row_summary, row_id_feat), dim=1))

        return {
            "cell_logits": cell_logits,
            "table_start_logits": table_start_logits,
            "col_role_logits": col_role_logits,
            "col_mismatch_logits": col_mismatch_logits,
            "row_type_logits": row_type_logits,
        }
