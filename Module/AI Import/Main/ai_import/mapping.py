from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rapidfuzz.fuzz import token_set_ratio

from .config import Settings
from .models import MapRequest, MapResponse, MappingCandidateDto, TargetFieldDto
from .text import fold_vietnamese, tokens


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
        corpus = [f"passage: {item.label}. {item.description}. {'; '.join(item.aliases)}" for item in targets]
        query = model.encode([f"query: {source}"], normalize_embeddings=True)
        vectors = model.encode(corpus, normalize_embeddings=True)
        return [float(item) for item in (query @ vectors.T)[0]]


class HybridFieldMapper:
    def __init__(self, config: Settings):
        self.config = config
        self.embedding = OptionalEmbeddingScorer(config)

    def _lexical(self, source: str, target: TargetFieldDto) -> _ScoredField:
        source_folded = fold_vietnamese(source)
        variants = [target.label, target.field_id, *target.aliases]
        normalized = [fold_vietnamese(item) for item in variants if item]
        if source_folded in normalized:
            return _ScoredField(1.0, target, ["exact-or-alias"])
        fuzzy = max((token_set_ratio(source_folded, item) / 100 for item in normalized), default=0.0)
        source_tokens = tokens(source)
        target_tokens = set().union(*(tokens(item) for item in variants))
        overlap = len(source_tokens & target_tokens) / max(1, len(source_tokens | target_tokens))
        score = 0.72 * fuzzy + 0.28 * overlap
        return _ScoredField(score, target, [f"fuzzy={fuzzy:.3f}", f"token-overlap={overlap:.3f}"])

    def map(self, request: MapRequest) -> MapResponse:
        result: list[MappingCandidateDto] = []
        used_fields: set[str] = set()
        for column, source in enumerate(request.headers):
            scored = [self._lexical(source, target) for target in request.target_fields]
            embedding_scores = self.embedding.score(source, request.target_fields)
            for index, item in enumerate(scored):
                if self.embedding.enabled:
                    semantic = max(0.0, min(1.0, (embedding_scores[index] + 1) / 2))
                    item.score = 0.58 * item.score + 0.42 * semantic
                    item.reasons.append(f"embedding={semantic:.3f}")
            scored.sort(key=lambda item: item.score, reverse=True)
            available = [item for item in scored if item.field.field_id not in used_fields] or scored
            best = available[0] if available else None
            runner_up = available[1].score if len(available) > 1 else 0.0
            if best is None or best.score < self.config.review_threshold:
                result.append(MappingCandidateDto(source_column=column, source_header=source, confidence=best.score if best else 0,
                    decision="unmapped", provenance=best.reasons if best else ["no-target-fields"], alternatives=[]))
                continue
            margin = best.score - runner_up
            calibrated = max(0.0, min(1.0, 0.85 * best.score + 0.15 * min(1.0, margin * 2)))
            decision = "auto" if calibrated >= self.config.auto_accept_threshold and margin >= 0.08 else "review"
            if decision == "auto":
                used_fields.add(best.field.field_id)
            alternatives = [
                {"field_id": item.field.field_id, "label": item.field.label, "score": round(item.score, 4)}
                for item in available[1:4]
            ]
            result.append(MappingCandidateDto(source_column=column, source_header=source,
                target_field_id=best.field.field_id, target_label=best.field.label,
                confidence=round(calibrated, 4), decision=decision,
                provenance=[*best.reasons, f"margin={margin:.3f}"], alternatives=alternatives))
        return MapResponse(mappings=result,
            model_version=f"hybrid-v1:{self.config.embedding_model if self.embedding.enabled else 'lexical'}",
            requires_review=any(item.decision != "auto" for item in result))

