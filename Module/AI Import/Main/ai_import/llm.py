from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .config import Settings
from .hierarchy import enrich_indicators
from .models import HierarchyMapRequest, LlmHierarchyResponse
from .prompting import build_hierarchy_messages, hierarchy_output_schema


class LlmOutputError(ValueError):
    pass


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    raise LlmOutputError("LLM không trả về nội dung JSON dạng text/object.")


def parse_json_object(content: Any) -> dict[str, Any]:
    """Lấy đúng một JSON object; chấp nhận code fence nhưng không đoán/sửa field."""

    text = _content_text(content).strip().lstrip("\ufeff")
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    if not text.startswith("{"):
        raise LlmOutputError("Output LLM có nội dung thừa trước JSON object.")
    try:
        value, end = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError as exc:
        raise LlmOutputError(f"JSON LLM không hợp lệ: {exc.msg}.") from exc
    if not isinstance(value, dict):
        raise LlmOutputError("Output LLM phải là một JSON object.")
    if text[end:].strip():
        raise LlmOutputError("Output LLM có nội dung thừa sau JSON object.")
    return value


def validate_llm_mapping(request: HierarchyMapRequest, raw: Any) -> LlmHierarchyResponse:
    try:
        response = LlmHierarchyResponse.model_validate(parse_json_object(raw))
    except (ValueError, TypeError) as exc:
        if isinstance(exc, LlmOutputError):
            raise
        raise LlmOutputError(f"Output LLM sai JSON schema: {exc}") from exc

    sources = enrich_indicators(request.source_indicators)
    targets = enrich_indicators(request.target_indicators)
    expected_sources = {item.source_ref for item in sources if item.kind != "marker"}
    target_by_ref = {item.target_ref: item for item in targets if item.kind != "marker"}
    returned_sources = [item.source_ref for item in response.mappings]
    if len(returned_sources) != len(set(returned_sources)):
        raise LlmOutputError("LLM trả trùng source_ref.")
    if set(returned_sources) != expected_sources:
        missing = sorted(expected_sources - set(returned_sources))
        extra = sorted(set(returned_sources) - expected_sources)
        raise LlmOutputError(f"Danh sách source_ref không khớp; missing={missing}, extra={extra}.")

    selected_targets = [item.target_ref for item in response.mappings if item.target_ref]
    if len(selected_targets) != len(set(selected_targets)):
        raise LlmOutputError("LLM ánh xạ nhiều source_ref vào cùng một target_ref.")
    unknown = sorted(set(selected_targets) - set(target_by_ref))
    if unknown:
        raise LlmOutputError(f"LLM tự tạo target_ref ngoài schema: {unknown}.")

    source_by_ref = {item.source_ref: item for item in sources}
    mapping_by_source = {item.source_ref: item.target_ref for item in response.mappings}
    for item in response.mappings:
        if not item.target_ref:
            continue
        source, target = source_by_ref[item.source_ref], target_by_ref[item.target_ref]
        if source.level != target.level or source.kind != target.kind:
            raise LlmOutputError(
                f"LLM nhầm cấp tại {source.source_ref}: "
                f"{source.kind}/{source.level} -> {target.kind}/{target.level}."
            )
        if source.parent_ref:
            mapped_parent = mapping_by_source.get(source.parent_ref)
            if not mapped_parent:
                raise LlmOutputError(f"LLM map dòng con nhưng bỏ trống dòng cha tại {source.source_ref}.")
            if mapped_parent != target.parent_ref:
                raise LlmOutputError(f"LLM nhầm nhánh cha/con tại {source.source_ref}.")
        elif target.parent_ref:
            raise LlmOutputError(f"LLM map dòng gốc vào target có dòng cha tại {source.source_ref}.")
    return response


class StructuredLlmClient:
    def __init__(self, config: Settings):
        self.config = config

    def map_hierarchy(self, request: HierarchyMapRequest) -> LlmHierarchyResponse:
        messages = build_hierarchy_messages(request)
        last_error: Exception | None = None
        attempts = max(1, self.config.llm_max_attempts)
        for attempt in range(attempts):
            attempt_messages = list(messages)
            if attempt and last_error:
                attempt_messages.append({
                    "role": "user",
                    "content": (
                        "Output trước bị từ chối: " + str(last_error)[:800]
                        + ". Hãy trả lại toàn bộ JSON đúng schema, không thêm nội dung khác."
                    ),
                })
            try:
                content = self._complete(attempt_messages)
                return validate_llm_mapping(request, content)
            except (LlmOutputError, urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
        raise LlmOutputError(f"Không nhận được output LLM hợp lệ sau {attempts} lần: {last_error}")

    def _complete(self, messages: list[dict[str, str]]) -> Any:
        url = self.config.llm_base_url.rstrip("/") + "/chat/completions"
        body = {
            "model": self.config.llm_model,
            "temperature": 0,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "eform_hierarchy_mapping",
                    "strict": True,
                    "schema": hierarchy_output_schema(),
                },
            },
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.config.llm_api_key:
            headers["Authorization"] = f"Bearer {self.config.llm_api_key}"
        http_request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(http_request, timeout=self.config.llm_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmOutputError("Response OpenAI-compatible thiếu choices[0].message.content.") from exc
