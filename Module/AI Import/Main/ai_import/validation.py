from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import ValidateRequest, ValidateResponse, ValidationIssueDto


def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _valid_type(value: Any, data_type: str) -> bool:
    if _empty(value):
        return True
    kind = data_type.lower()
    if kind in {"string", "text"}:
        return True
    if kind in {"number", "decimal", "integer"}:
        try:
            Decimal(str(value).replace(",", ""))
            return True
        except InvalidOperation:
            return False
    if kind in {"date", "datetime"}:
        if isinstance(value, (date, datetime)):
            return True
        for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                datetime.strptime(str(value).strip(), pattern)
                return True
            except ValueError:
                pass
        return False
    if kind in {"bool", "boolean"}:
        return str(value).strip().lower() in {"true", "false", "1", "0", "có", "không", "x", ""}
    return True


class DeterministicValidator:
    def validate(self, request: ValidateRequest) -> ValidateResponse:
        issues: list[ValidationIssueDto] = []
        fields = {item.field_id: item for item in request.target_fields}
        column_map = {item.target_field_id: item.source_column for item in request.mappings if item.target_field_id}
        for field in request.target_fields:
            if field.required and field.field_id not in column_map:
                issues.append(ValidationIssueDto(row=0, field_id=field.field_id, severity="error",
                    code="REQUIRED_COLUMN_UNMAPPED", message=f"Chưa ánh xạ cột bắt buộc: {field.label}."))
        for row_index, row in enumerate(request.rows, start=1):
            for field_id, column in column_map.items():
                value = row[column] if column < len(row) else None
                field = fields.get(field_id)
                if field and field.required and _empty(value):
                    issues.append(ValidationIssueDto(row=row_index, column=column, field_id=field_id,
                        severity="error", code="REQUIRED_VALUE", message=f"{field.label} là bắt buộc.", value=value))
                if field and not _valid_type(value, field.data_type):
                    issues.append(ValidationIssueDto(row=row_index, column=column, field_id=field_id,
                        severity="error", code="INVALID_TYPE", message=f"{field.label} không đúng kiểu {field.data_type}.", value=value))
            for rule in request.rules:
                column = column_map.get(rule.field_id)
                if column is None:
                    continue
                value = row[column] if column < len(row) else None
                failed = False
                if rule.rule_type == "regex" and not _empty(value):
                    failed = re.fullmatch(str(rule.parameters.get("pattern", "")), str(value)) is None
                elif rule.rule_type == "min" and not _empty(value):
                    try:
                        failed = Decimal(str(value)) < Decimal(str(rule.parameters["value"]))
                    except (InvalidOperation, KeyError):
                        failed = True
                elif rule.rule_type == "max" and not _empty(value):
                    try:
                        failed = Decimal(str(value)) > Decimal(str(rule.parameters["value"]))
                    except (InvalidOperation, KeyError):
                        failed = True
                elif rule.rule_type == "in" and not _empty(value):
                    failed = value not in rule.parameters.get("values", [])
                if failed:
                    issues.append(ValidationIssueDto(row=row_index, column=column, field_id=rule.field_id,
                        severity=rule.severity, code=f"RULE_{rule.rule_id}", message=rule.message, value=value))
        errors = sum(item.severity.lower() == "error" for item in issues)
        warnings = sum(item.severity.lower() != "error" for item in issues)
        return ValidateResponse(valid=errors == 0, error_count=errors, warning_count=warnings, issues=issues)

