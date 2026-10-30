# -*- coding: utf-8 -*-
"""Low-sensitive DecisionSignal summaries for notifications and risk views."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.utils.sanitize import sanitize_decision_signal_payload, sanitize_decision_signal_text


SUMMARY_FIELDS = (
    "id",
    "stock_code",
    "stock_name",
    "market",
    "action",
    "action_label",
    "horizon",
    "status",
    "source_type",
    "source_report_id",
    "reason",
    "watch_conditions",
    "risk_summary",
    "created_at",
    "expires_at",
)


def summarize_decision_signal(item: Any) -> Optional[Dict[str, Any]]:
    """Return a low-sensitive summary from a serialized DecisionSignal item."""

    if not isinstance(item, dict):
        return None
    summary: Dict[str, Any] = {}
    for field_name in SUMMARY_FIELDS:
        value = item.get(field_name)
        if value in (None, "", [], {}):
            continue
        summary[field_name] = sanitize_decision_signal_payload(value)
    return summary or None


def format_decision_signal_excerpt(summary: Any, report_language: str = "zh") -> str:
    """Format a compact, readable public DecisionSignal excerpt for Markdown reports."""

    if not isinstance(summary, dict) or not summary:
        return ""
    language = "en" if str(report_language or "").lower().startswith("en") else "zh"
    labels = {
        "zh": {
            "heading": "AI 决策信号",
            "action": "动作",
            "horizon": "周期",
            "reason": "决策理由",
            "watch_conditions": "观察条件",
            "risk_summary": "主要风险",
            "source_report_id": "报告",
        },
        "en": {
            "heading": "AI decision signal",
            "action": "Action",
            "horizon": "Horizon",
            "reason": "Reason",
            "watch_conditions": "Watch conditions",
            "risk_summary": "Key risks",
            "source_report_id": "Report",
        },
    }[language]

    parts = []
    action_label = _public_scalar(summary.get("action_label") or summary.get("action"), max_length=32)
    if action_label:
        parts.append(f"{labels['action']}: {action_label}")
    horizon = _public_scalar(summary.get("horizon"), max_length=24)
    if horizon:
        parts.append(f"{labels['horizon']}: {horizon}")
    source_report_id = _public_scalar(summary.get("source_report_id"), max_length=24)
    if source_report_id:
        parts.append(f"{labels['source_report_id']}: #{source_report_id}")

    lines = [f"### 🤖 {labels['heading']}"]
    if parts:
        lines.append(" | ".join(parts))

    reason = _public_text(summary.get("reason"), max_length=600)
    if reason:
        lines.append(f"**{labels['reason']}**：{reason}")

    for key in ("watch_conditions", "risk_summary"):
        items = _public_items(summary.get(key))
        if not items:
            continue
        lines.append(f"**{labels[key]}**")
        # Keep a sensible upper bound on list size while preserving complete text
        # for each displayed item; do not truncate a joined JSON-like string.
        for item in items[:8]:
            lines.append(f"- {item}")

    return "\n".join(lines)


def _public_items(value: Any) -> list[str]:
    """Convert scalar/list/dict signal fields into sanitized display items."""
    if value in (None, "", [], {}):
        return []
    if isinstance(value, (list, tuple)):
        raw_items = [str(item).strip() for item in value if str(item or "").strip()]
    elif isinstance(value, dict):
        raw_items = [
            f"{key}: {item}"
            for key, item in value.items()
            if str(key or "").strip() and str(item or "").strip()
        ]
    else:
        raw_items = [str(value).strip()]

    items = []
    for raw in raw_items:
        cleaned = sanitize_decision_signal_text(raw)
        if cleaned:
            items.append(cleaned[:360])
    return items


def _public_scalar(value: Any, *, max_length: int) -> str:
    if value in (None, ""):
        return ""
    return sanitize_decision_signal_text(value)[:max_length]


def _public_text(value: Any, *, max_length: Optional[int]) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, (list, tuple)):
        text = "；".join(str(item).strip() for item in value if str(item or "").strip())
    elif isinstance(value, dict):
        text = "；".join(
            f"{key}: {item}"
            for key, item in value.items()
            if str(key or "").strip() and str(item or "").strip()
        )
    else:
        text = str(value).strip()
    sanitized = sanitize_decision_signal_text(text)
    return sanitized if max_length is None else sanitized[:max_length]
