from __future__ import annotations

from typing import Any

import torch

from eform_ai.schema import (
    CELL_HEADER_CODE,
    CELL_HEADER_TITLE,
    CELL_OUTSIDE,
    CELL_VALUE,
    COL_CODE,
    COL_LABEL,
    ROW_TYPE_NAMES,
)


def _split_component_by_model_starts(
    prediction: torch.Tensor,
    table_start_probs: torch.Tensor | None,
    top: int,
    bottom: int,
    left: int,
    right: int,
    header_fraction_threshold: float,
    table_start_threshold: float,
) -> list[tuple[int, int]]:
    """Split vertically adjacent tables strictly using the model's own predictions
    (table_start head + header_title transitions following value rows)."""
    if bottom - top < 2:
        return [(top, bottom)]

    split_points: list[int] = [top]
    seen_value = False
    for row in range(top, bottom + 1):
        row_pred = prediction[row, left:right + 1]
        hdr_title_frac = float((row_pred == CELL_HEADER_TITLE).float().mean())
        is_header_title = hdr_title_frac >= header_fraction_threshold
        is_value = float((row_pred == CELL_VALUE).float().mean()) >= 0.25

        start_prob = float(table_start_probs[row]) if table_start_probs is not None else 0.0
        if row > split_points[-1] + 1 and seen_value and is_header_title:
            if table_start_probs is None or start_prob >= table_start_threshold or hdr_title_frac >= 0.55:
                split_points.append(row)
                seen_value = False
                continue

        if is_value:
            seen_value = True

    segments: list[tuple[int, int]] = []
    for idx, seg_top in enumerate(split_points):
        seg_bottom = split_points[idx + 1] - 1 if idx + 1 < len(split_points) else bottom
        # Trim any pure-outside rows between split segments
        while seg_top <= seg_bottom and not bool((prediction[seg_top, left:right + 1] != CELL_OUTSIDE).any()):
            seg_top += 1
        while seg_bottom >= seg_top and not bool((prediction[seg_bottom, left:right + 1] != CELL_OUTSIDE).any()):
            seg_bottom -= 1
        if seg_top <= seg_bottom:
            segments.append((seg_top, seg_bottom))
    return segments


def decode_predictions(
    cell_logits: torch.Tensor,
    table_start_logits: torch.Tensor | None = None,
    col_role_logits: torch.Tensor | None = None,
    col_mismatch_logits: torch.Tensor | None = None,
    row_type_logits: torch.Tensor | None = None,
    minimum_component_cells: int = 4,
    header_fraction_threshold: float = 0.30,
    table_start_threshold: float = 0.45,
) -> list[dict[str, Any]]:
    """Decode raw neural network outputs into structured table regions with
    zero regexes or workbook heuristics."""
    cell_logits = cell_logits.detach().cpu()
    probabilities = cell_logits.softmax(dim=0)
    prediction = cell_logits.argmax(dim=0)
    rows, columns = prediction.shape

    table_start_probs = (
        table_start_logits.detach().cpu().squeeze(0).sigmoid()
        if table_start_logits is not None
        else None
    )
    col_role_probs = (
        col_role_logits.detach().cpu().softmax(dim=0)
        if col_role_logits is not None
        else None
    )
    col_mismatch_probs = (
        col_mismatch_logits.detach().cpu().squeeze(0).sigmoid()
        if col_mismatch_logits is not None
        else None
    )
    row_type_probs = (
        row_type_logits.detach().cpu().softmax(dim=0)
        if row_type_logits is not None
        else None
    )

    foreground = prediction != CELL_OUTSIDE
    visited = torch.zeros_like(foreground, dtype=torch.bool)
    components: list[list[tuple[int, int]]] = []

    for r in range(rows):
        for c in range(columns):
            if not foreground[r, c] or visited[r, c]:
                continue
            stack = [(r, c)]
            visited[r, c] = True
            component: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                component.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if 0 <= nr < rows and 0 <= nc < columns and foreground[nr, nc] and not visited[nr, nc]:
                        visited[nr, nc] = True
                        stack.append((nr, nc))
            if len(component) >= minimum_component_cells:
                components.append(component)

    tables: list[dict[str, Any]] = []
    for component in components:
        comp_rows = [r for r, _ in component]
        comp_cols = [c for _, c in component]
        comp_top, comp_bottom = min(comp_rows), max(comp_rows)
        comp_left, comp_right = min(comp_cols), max(comp_cols)

        segments = _split_component_by_model_starts(
            prediction,
            table_start_probs,
            comp_top,
            comp_bottom,
            comp_left,
            comp_right,
            header_fraction_threshold,
            table_start_threshold,
        )

        for top, bottom in segments:
            # Tight horizontal bounds strictly from model foreground cells inside this segment
            seg_fg = foreground[top:bottom + 1, comp_left:comp_right + 1]
            col_has_fg = seg_fg.any(dim=0)
            if not bool(col_has_fg.any()):
                continue
            fg_cols = torch.nonzero(col_has_fg, as_tuple=False).squeeze(-1)
            left = comp_left + int(fg_cols[0].item())
            right = comp_left + int(fg_cols[-1].item())

            fg_count = int(foreground[top:bottom + 1, left:right + 1].sum().item())
            if fg_count < minimum_component_cells:
                continue

            # Determine header_bottom and header_code rows directly from model cell predictions
            header_rows: list[int] = []
            code_rows: list[int] = []
            first_value_row: int | None = None
            for row in range(top, bottom + 1):
                row_slice = prediction[row, left:right + 1]
                hdr_frac = float(((row_slice == CELL_HEADER_TITLE) | (row_slice == CELL_HEADER_CODE)).float().mean())
                code_frac = float((row_slice == CELL_HEADER_CODE).float().mean())
                val_frac = float((row_slice == CELL_VALUE).float().mean())
                if code_frac >= header_fraction_threshold:
                    code_rows.append(row)
                if hdr_frac >= header_fraction_threshold and first_value_row is None:
                    header_rows.append(row)
                elif val_frac >= header_fraction_threshold and first_value_row is None:
                    first_value_row = row

            if header_rows:
                header_bottom = max(header_rows)
            elif first_value_row is not None and first_value_row > top:
                header_bottom = first_value_row - 1
            else:
                header_bottom = top

            # Confidence over foreground predictions inside this table
            region_pred = prediction[top:bottom + 1, left:right + 1]
            region_prob = probabilities[:, top:bottom + 1, left:right + 1]
            fg_mask = region_pred != CELL_OUTSIDE
            gathered = region_prob.gather(0, region_pred.unsqueeze(0)).squeeze(0)
            confidence = float(gathered[fg_mask].mean().item()) if bool(fg_mask.any()) else 0.0

            # Learned column roles and mismatches within [left, right]
            code_col: int | None = None
            label_col: int | None = None
            col_roles: list[int] = []
            col_mismatch_scores: list[float] = []
            if col_role_probs is not None:
                sub_col_probs = col_role_probs[:, left:right + 1]
                col_preds = sub_col_probs.argmax(dim=0)
                col_roles = [int(v) for v in col_preds.tolist()]
                code_candidates = [
                    (idx, float(sub_col_probs[COL_CODE, idx]))
                    for idx, role in enumerate(col_roles)
                    if role == COL_CODE
                ]
                if code_candidates:
                    code_col = max(code_candidates, key=lambda item: item[1])[0]

                label_candidates = [
                    (idx, float(sub_col_probs[COL_LABEL, idx]))
                    for idx, role in enumerate(col_roles)
                    if role == COL_LABEL and idx != code_col
                ]
                if label_candidates:
                    label_col = max(label_candidates, key=lambda item: item[1])[0]

            if col_mismatch_probs is not None:
                col_mismatch_scores = [
                    float(v) for v in col_mismatch_probs[left:right + 1].tolist()
                ]

            # Learned row types for rows inside the table
            row_types: list[tuple[str, float]] = []
            if row_type_probs is not None:
                for r in range(top, bottom + 1):
                    probs_r = row_type_probs[:, r]
                    # For value rows, choose among valid row types (1..8)
                    val_probs = probs_r[1:]
                    best_idx = int(val_probs.argmax().item()) + 1
                    row_types.append((ROW_TYPE_NAMES[best_idx], float(probs_r[best_idx].item())))

            tables.append({
                "top": top + 1,
                "left": left + 1,
                "bottom": bottom + 1,
                "right": right + 1,
                "header_bottom": header_bottom + 1,
                "code_rows": [r - top for r in code_rows if top <= r <= header_bottom],
                "confidence": confidence,
                "code_col": code_col,
                "label_col": label_col,
                "col_roles": col_roles,
                "col_mismatch_scores": col_mismatch_scores,
                "row_types": row_types,
            })

    tables.sort(key=lambda t: (t["top"], t["left"], t["bottom"], t["right"]))
    return tables
