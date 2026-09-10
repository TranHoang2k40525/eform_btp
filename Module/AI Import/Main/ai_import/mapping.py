from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rapidfuzz.fuzz import token_set_ratio

from .config import Settings
from .models import MapRequest, MapResponse, MappingCandidateDto, TargetFieldDto
from .text import fold_vietnamese, tokens


_DOCTYPE_RE = re.compile(r"(?<!\d)(\d{2}[a-z]?)(?![a-z])", re.IGNORECASE)


def _short_doctype(value: str) -> str:
    match = _DOCTYPE_RE.search(value or "")
    return match.group(1).lower() if match else ""


@dataclass
class _ScoredField:
    score: float
    field: TargetFieldDto
    reasons: list[str]


class OptionalEmbeddingScorer:
    def __init__(self, config: Settings):
        self.config = config
        self._model: Any = None

    @property
    def enabled(self) -> bool:
        return self.config.embedding_enabled

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.config.embedding_model, cache_folder=self.config.embedding_cache_dir)
        return self._model

    def score(self, source: str, targets: list[TargetFieldDto]) -> list[float]:
        if not self.enabled or not targets:
            return [0.0] * len(targets)
        model = self._load()
        mode = self.config.embedding_prefix_mode.lower()
        use_e5_prefix = mode == "e5" or (mode == "auto" and "e5" in self.config.embedding_model.lower())
        prefix_query, prefix_passage = ("query: ", "passage: ") if use_e5_prefix else ("", "")
        corpus = [
            f"{prefix_passage}{' > '.join(item.header_path)}. {item.label}. "
            f"{item.description}. {'; '.join(item.aliases)}. {item.column_code}"
            for item in targets
        ]
        query = model.encode([f"{prefix_query}{source}"], normalize_embeddings=True)
        vectors = model.encode(corpus, normalize_embeddings=True)
        return [float(item) for item in (query @ vectors.T)[0]]


class HybridFieldMapper:
    def __init__(self, config: Settings):
        self.config = config
        self.embedding = OptionalEmbeddingScorer(config)

    def _lexical(self, source: str, source_path: list[str], source_code: str, target: TargetFieldDto) -> _ScoredField:
        source_folded = fold_vietnamese(source)
        variants = [target.label, target.field_id, *target.aliases]
        normalized = [fold_vietnamese(item) for item in variants if item]
        fuzzy = max((token_set_ratio(source_folded, item) / 100 for item in normalized), default=0.0)
        source_full = " > ".join(source_path) if source_path else source
        target_full = " > ".join(target.header_path) if target.header_path else target.label
        path_fuzzy = token_set_ratio(fold_vietnamese(source_full), fold_vietnamese(target_full)) / 100
        source_tokens = tokens(source)
        target_tokens = set().union(*(tokens(item) for item in variants))
        overlap = len(source_tokens & target_tokens) / max(1, len(source_tokens | target_tokens))
        code_score = 0.0
        if source_code and target.column_code:
            code_score = 1.0 if fold_vietnamese(source_code) == fold_vietnamese(target.column_code) else 0.0
        elif not source_code and not target.column_code:
            code_score = 0.5
        score = 0.38 * fuzzy + 0.34 * path_fuzzy + 0.16 * code_score + 0.12 * overlap
        if source_code and target.column_code and code_score == 0:
            score *= 0.55
        reasons = [
            f"leaf={fuzzy:.3f}", f"path={path_fuzzy:.3f}",
            f"code={code_score:.3f}", f"token-overlap={overlap:.3f}",
        ]
        # Ma cot trong template hien huu la rang buoc deterministic. Day la
        # fallback tuong thich importer positional cho cac cot ky thuat A/B
        # co nhan nhu #chitiet, nhung van can DocType/form dung o lop goi.
        if code_score == 1.0:
            score = max(score, 0.90)
            reasons.append("exact-column-code")
        return _ScoredField(score, target, reasons)

    def map(self, request: MapRequest) -> MapResponse:
        result: list[MappingCandidateDto] = []
        request_doc_type = _short_doctype(request.doc_type_code)
        target_fields = [
            field for field in request.target_fields
            if not request_doc_type
            or not _short_doctype(field.doc_type_code)
            or _short_doctype(field.doc_type_code) == request_doc_type
        ]
        ranked_by_column: dict[int, list[_ScoredField]] = {}
        for column, source in enumerate(request.headers):
            source_path = request.header_paths[column] if column < len(request.header_paths) else [source]
            source_code = request.column_codes[column] if column < len(request.column_codes) else ""
            source_text = " > ".join(source_path) or source
            scored = [self._lexical(source, source_path, source_code, target) for target in target_fields]
            embedding_scores = self.embedding.score(source_text, target_fields)
            for index, item in enumerate(scored):
                if self.embedding.enabled:
                    semantic = max(0.0, min(1.0, (embedding_scores[index] + 1) / 2))
                    item.score = 0.58 * item.score + 0.42 * semantic
                    item.reasons.append(f"embedding={semantic:.3f}")
            scored.sort(key=lambda item: item.score, reverse=True)
            ranked_by_column[column] = scored

        # Ràng buộc one-to-one cho mọi decision, kể cả review. Không sinh key __2.
        assignments: dict[int, _ScoredField] = {}
        used_fields: set[str] = set()
        pairs = [
            (item.score, column, item)
            for column, scored in ranked_by_column.items()
            for item in scored
        ]
        for _, column, item in sorted(pairs, key=lambda value: value[0], reverse=True):
            if column in assignments or item.field.field_id in used_fields:
                continue
            assignments[column] = item
            used_fields.add(item.field.field_id)

        for column, source in enumerate(request.headers):
            source_path = request.header_paths[column] if column < len(request.header_paths) else [source]
            source_code = request.column_codes[column] if column < len(request.column_codes) else ""
            scored = ranked_by_column.get(column, [])
            best = assignments.get(column)
            alternatives_ranked = [item for item in scored if best is None or item.field.field_id != best.field.field_id]
            runner_up = alternatives_ranked[0].score if alternatives_ranked else 0.0
            if best is None or best.score < self.config.review_threshold:
                result.append(MappingCandidateDto(source_column=column, source_header=source, confidence=best.score if best else 0,
                    decision="unmapped", provenance=best.reasons if best else ["no-target-fields"], alternatives=[],
                    source_header_path=source_path, source_column_code=source_code))
                continue
            margin = best.score - runner_up
            calibrated = max(0.0, min(1.0, 0.85 * best.score + 0.15 * min(1.0, margin * 2)))
            exact_code = bool(source_code and best.field.column_code
                and fold_vietnamese(source_code) == fold_vietnamese(best.field.column_code))
            generic = fold_vietnamese(source) in {"tong so", "tong cong", "ghi chu"}
            path_exact = fold_vietnamese(" > ".join(source_path)) == fold_vietnamese(
                " > ".join(best.field.header_path) if best.field.header_path else best.field.label
            )
            decision = "auto" if (
                calibrated >= self.config.auto_accept_threshold
                and margin >= 0.06
                and (not generic or path_exact or exact_code)
            ) else "review"
            alternatives = [
                {"field_id": item.field.field_id, "label": item.field.label, "score": round(item.score, 4)}
                for item in alternatives_ranked[:3]
            ]
            result.append(MappingCandidateDto(source_column=column, source_header=source,
                target_field_id=best.field.field_id, target_label=best.field.label,
                confidence=round(calibrated, 4), decision=decision,
                provenance=[*best.reasons, f"margin={margin:.3f}", "one-to-one"], alternatives=alternatives,
                source_header_path=source_path, source_column_code=source_code,
                target_column_code=best.field.column_code))
        return MapResponse(mappings=result,
            model_version=f"hybrid-v1:{self.config.embedding_model if self.embedding.enabled else 'lexical'}",
            requires_review=any(item.decision != "auto" for item in result))
