from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TypeVar

from rapidfuzz.fuzz import token_set_ratio

from .config import Settings
from .models import (
    HierarchyAlternativeDto,
    HierarchyIssueDto,
    HierarchyMapRequest,
    HierarchyMapResponse,
    HierarchyMappingDto,
    IndicatorDto,
    MappingDecision,
    TargetIndicatorDto,
)
from .text import fold_vietnamese


_ROMAN_RE = re.compile(r"^[IVXLCDM]+$", re.IGNORECASE)
_INTEGER_RE = re.compile(r"^\d+$")
_DECIMAL_RE = re.compile(r"^\d+(?:\.\d+)+$")
_ALPHA_RE = re.compile(r"^[a-zA-ZđĐ]$")
_MARKER_RE = re.compile(r"^(?:[-–—]|[.…]{2,})$")
_TOTAL_WORDS = ("tong so", "tong cong")
_GENERIC_LABELS = {"tong so", "tong cong", "trong do"}

TIndicator = TypeVar("TIndicator", IndicatorDto, TargetIndicatorDto)


def _clean_code(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).rstrip(".)").lstrip("(")


def _is_total(label: str) -> bool:
    folded = fold_vietnamese(label)
    return any(folded == word or folded.startswith(word + " ") for word in _TOTAL_WORDS)


def classify_indicator(code: object, label: object, has_section: bool = False) -> tuple[str, int]:
    """Phân loại cấp theo convention đang dùng ở eForm/Handsontable."""

    raw_code = _clean_code(code)
    text = str(label or "").strip()
    if _MARKER_RE.fullmatch(text) or (raw_code in {"-", "–", "—"} and not text):
        return "marker", 0
    # Ma STT the hien cap manh hon tu khoa trong nhan. Vi du dong ma "1"
    # co nhan "Tong so ho so..." van la group duoi Muc, khong phai root total.
    if raw_code and _ROMAN_RE.fullmatch(raw_code):
        return "section", 1
    if raw_code and _INTEGER_RE.fullmatch(raw_code):
        return "group", 2 if has_section else 1
    if raw_code and _DECIMAL_RE.fullmatch(raw_code):
        return "detail", (2 if has_section else 1) + raw_code.count(".")
    if raw_code and _ALPHA_RE.fullmatch(raw_code):
        return "detail", 3 if has_section else 2
    if _is_total(text):
        return "total", 0
    return "detail", -1


def enrich_indicators(items: list[TIndicator]) -> list[TIndicator]:
    """Dựng level, parent_ref và path theo thứ tự dòng, không dựa riêng vào nhãn."""

    result: list[TIndicator] = []
    stack: dict[int, TIndicator] = {}
    active_section = False
    for item in items:
        kind, inferred_level = classify_indicator(item.code, item.label, active_section)
        if kind == "section":
            active_section = True
        elif kind == "total":
            active_section = False

        if inferred_level < 0:
            folded = fold_vietnamese(item.label)
            if folded.startswith("trong do") and result:
                previous = next((row for row in reversed(result) if row.kind != "marker"), None)
                level = min(12, (previous.level + 1) if previous else 1)
            elif result and result[-1].kind in {"section", "group"}:
                level = min(12, result[-1].level + 1)
            else:
                level = 1 if any(row.kind == "total" for row in result) else 0
        else:
            level = inferred_level

        if kind == "marker":
            parent = next((row for row in reversed(result) if row.kind != "marker"), None)
            parent_ref = _ref(parent) if parent else None
            path = [*parent.path, item.label] if parent and item.label else (list(parent.path) if parent else [])
        else:
            parent = stack.get(level - 1) if level > 0 else None
            if parent is None and level > 0:
                parent = next(
                    (row for row in reversed(result) if row.kind != "marker" and row.level < level),
                    None,
                )
            parent_ref = _ref(parent) if parent else None
            path = [*(parent.path if parent else []), item.label]
            stack[level] = item
            for stale_level in [key for key in stack if key > level]:
                del stack[stale_level]

        result.append(item.model_copy(update={
            "kind": kind,
            "level": level,
            "parent_ref": parent_ref,
            "path": path,
        }))
        if kind != "marker":
            stack[level] = result[-1]
    return result


def _ref(item: IndicatorDto | TargetIndicatorDto | None) -> str | None:
    if item is None:
        return None
    return item.source_ref if isinstance(item, IndicatorDto) else item.target_ref


@dataclass(frozen=True)
class _PairScore:
    source: IndicatorDto
    target: TargetIndicatorDto
    score: float
    reasons: list[str]
    incompatible: bool


def _similarity(left: object, right: object) -> float:
    a, b = fold_vietnamese(left), fold_vietnamese(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return token_set_ratio(a, b) / 100.0


def _score_pair(source: IndicatorDto, target: TargetIndicatorDto) -> _PairScore:
    label_score = _similarity(source.label, target.label)
    path_score = _similarity(" > ".join(source.path), " > ".join(target.path))
    source_parent = " > ".join(source.path[:-1])
    target_parent = " > ".join(target.path[:-1])
    parent_score = _similarity(source_parent, target_parent) if source_parent or target_parent else 1.0

    source_code, target_code = _clean_code(source.code), _clean_code(target.code)
    if source_code and target_code:
        code_score = 1.0 if fold_vietnamese(source_code) == fold_vietnamese(target_code) else 0.0
    else:
        code_score = 0.5 if not source_code and not target_code else 0.0
    level_score = 1.0 if source.level == target.level else (0.25 if abs(source.level - target.level) == 1 else 0.0)
    kind_score = 1.0 if source.kind == target.kind else 0.0
    incompatible = (
        (source.kind == "total") != (target.kind == "total")
        or (source.kind == "section") != (target.kind == "section")
        or abs(source.level - target.level) > 1
    )
    score = (
        0.36 * label_score
        + 0.24 * path_score
        + 0.12 * parent_score
        + 0.12 * code_score
        + 0.10 * level_score
        + 0.06 * kind_score
    )
    if incompatible:
        score *= 0.35
    reasons = [
        f"label={label_score:.3f}",
        f"path={path_score:.3f}",
        f"parent={parent_score:.3f}",
        f"code={code_score:.3f}",
        f"level={level_score:.3f}",
    ]
    return _PairScore(source, target, max(0.0, min(1.0, score)), reasons, incompatible)


class DeterministicHierarchyMapper:
    """Baseline và lớp chặn lỗi cho kết quả LLM."""

    def __init__(self, config: Settings):
        self.config = config

    def map(self, request: HierarchyMapRequest, strategy: str = "hierarchy-deterministic-v1") -> HierarchyMapResponse:
        sources = enrich_indicators(request.source_indicators)
        targets = enrich_indicators(request.target_indicators)
        target_by_ref = {item.target_ref: item for item in targets}
        issues: list[HierarchyIssueDto] = []

        if len({item.source_ref for item in sources}) != len(sources):
            raise ValueError("source_ref bị trùng trong danh sách chỉ tiêu nguồn.")
        if len(target_by_ref) != len(targets):
            raise ValueError("target_ref bị trùng trong schema đích.")

        all_pairs = [_score_pair(source, target) for source in sources for target in targets]
        by_source: dict[str, list[_PairScore]] = {}
        for pair in all_pairs:
            by_source.setdefault(pair.source.source_ref, []).append(pair)
        for pairs in by_source.values():
            pairs.sort(key=lambda item: item.score, reverse=True)

        # Gán one-to-one toàn cục; không cho hai dòng cùng ghi vào một target row.
        assigned: dict[str, _PairScore] = {}
        used_targets: set[str] = set()
        for pair in sorted(all_pairs, key=lambda item: item.score, reverse=True):
            if pair.incompatible or pair.source.kind == "marker":
                continue
            if pair.source.source_ref in assigned or pair.target.target_ref in used_targets:
                continue
            assigned[pair.source.source_ref] = pair
            used_targets.add(pair.target.target_ref)

        mappings: list[HierarchyMappingDto] = []
        for source in sources:
            ranked = by_source.get(source.source_ref, [])
            alternatives = [
                HierarchyAlternativeDto(target_ref=item.target.target_ref, label=item.target.label, score=round(item.score, 4))
                for item in ranked[:3]
                if not item.incompatible
            ]
            if source.kind == "marker":
                mappings.append(HierarchyMappingDto(
                    source_ref=source.source_ref,
                    confidence=1.0,
                    decision=MappingDecision.unmapped,
                    reason_codes=["IGNORED_MARKER_ROW"],
                    alternatives=[],
                ))
                continue

            pair = assigned.get(source.source_ref)
            if pair is None or pair.score < self.config.review_threshold:
                mappings.append(HierarchyMappingDto(
                    source_ref=source.source_ref,
                    confidence=round(pair.score if pair else 0.0, 4),
                    decision=MappingDecision.unmapped,
                    reason_codes=["NO_COMPATIBLE_TARGET"],
                    alternatives=alternatives,
                ))
                issues.append(HierarchyIssueDto(
                    code="INDICATOR_UNMAPPED",
                    severity="warning",
                    source_ref=source.source_ref,
                    message=f"Không tìm được dòng đích đủ tin cậy cho '{source.label}'.",
                ))
                continue

            margin = pair.score - next(
                (item.score for item in ranked if item.target.target_ref != pair.target.target_ref and not item.incompatible),
                0.0,
            )
            confidence = max(0.0, min(1.0, 0.90 * pair.score + 0.10 * min(1.0, margin * 2)))
            generic = fold_vietnamese(source.label) in _GENERIC_LABELS
            source_parent_path = " > ".join(source.path[:-1])
            target_parent_path = " > ".join(pair.target.path[:-1])
            safe_generic = (
                not generic
                or (not source_parent_path and not target_parent_path)
                or _similarity(source_parent_path, target_parent_path) >= 0.90
            )
            decision = (
                MappingDecision.auto
                if confidence >= self.config.auto_accept_threshold and margin >= 0.06 and safe_generic
                else MappingDecision.review
            )
            reason_codes = ["HIERARCHY_MATCH", *pair.reasons, f"margin={margin:.3f}"]
            if generic:
                reason_codes.append("GENERIC_LABEL_REQUIRES_PARENT")
            suspected_shift = not _clean_code(source.code) and bool(re.fullmatch(r"[\d.,\s]+", source.label.strip()))
            if suspected_shift:
                decision = MappingDecision.review
                reason_codes.append("SUSPECTED_SHIFTED_VALUE")
                issues.append(HierarchyIssueDto(
                    code="SUSPECTED_SHIFTED_VALUE",
                    severity="warning",
                    source_ref=source.source_ref,
                    target_ref=pair.target.target_ref,
                    message="Nhãn chỉ chứa số nhưng không có mã phân cấp; có thể dữ liệu đã lệch sang cột chỉ tiêu.",
                ))
            mappings.append(HierarchyMappingDto(
                source_ref=source.source_ref,
                target_ref=pair.target.target_ref,
                confidence=round(confidence, 4),
                decision=decision,
                reason_codes=reason_codes,
                alternatives=[item for item in alternatives if item.target_ref != pair.target.target_ref][:3],
            ))

        # Hậu kiểm quan hệ cha/con sau khi đã có toàn bộ phép gán.
        mapping_by_source = {item.source_ref: item for item in mappings}
        source_by_ref = {item.source_ref: item for item in sources}
        for index, mapping in enumerate(mappings):
            if not mapping.target_ref:
                continue
            source = source_by_ref[mapping.source_ref]
            target = target_by_ref[mapping.target_ref]
            if source.level != target.level:
                mappings[index] = mapping.model_copy(update={
                    "decision": MappingDecision.review,
                    "reason_codes": [*mapping.reason_codes, "LEVEL_MISMATCH"],
                })
                issues.append(HierarchyIssueDto(
                    code="HIERARCHY_LEVEL_MISMATCH",
                    severity="warning",
                    source_ref=source.source_ref,
                    target_ref=target.target_ref,
                    message=f"Cấp nguồn {source.level} khác cấp đích {target.level}; bắt buộc duyệt.",
                ))
            if source.parent_ref:
                parent_mapping = mapping_by_source.get(source.parent_ref)
                mapped_parent = parent_mapping.target_ref if parent_mapping else None
                if mapped_parent != target.parent_ref:
                    mappings[index] = mappings[index].model_copy(update={
                        "decision": MappingDecision.review,
                        "reason_codes": [*mappings[index].reason_codes, "PARENT_MISMATCH"],
                    })
                    issues.append(HierarchyIssueDto(
                        code="HIERARCHY_PARENT_MISMATCH",
                        severity="warning",
                        source_ref=source.source_ref,
                        target_ref=target.target_ref,
                        message="Dòng con không thuộc dòng cha đã ánh xạ; bắt buộc duyệt.",
                    ))
            elif target.parent_ref:
                mappings[index] = mappings[index].model_copy(update={
                    "decision": MappingDecision.review,
                    "reason_codes": [*mappings[index].reason_codes, "PARENT_MISMATCH"],
                })
                issues.append(HierarchyIssueDto(
                    code="HIERARCHY_PARENT_MISMATCH",
                    severity="warning",
                    source_ref=source.source_ref,
                    target_ref=target.target_ref,
                    message="Dòng gốc bị ánh xạ vào target có dòng cha; bắt buộc duyệt.",
                ))

        requires_review = any(item.decision != MappingDecision.auto for item in mappings)
        return HierarchyMapResponse(
            doc_type_code=request.doc_type_code,
            mappings=mappings,
            issues=issues,
            valid=not any(item.severity == "error" for item in issues),
            requires_review=requires_review,
            strategy=strategy,
        )
