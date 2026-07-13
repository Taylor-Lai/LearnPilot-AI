from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SafetyReview:
    safe: bool
    violations: tuple[str, ...]
    redaction_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "safe": self.safe,
            "violations": list(self.violations),
            "redaction_count": self.redaction_count,
        }


class ContentSafetyGuard:
    """Deterministic guard for untrusted course text, prompts, and generated output."""

    _injection_patterns = (
        re.compile(r"ignore\s+(all\s+)?(previous|prior|system|developer)\s+instructions?", re.I),
        re.compile(r"reveal\s+(the\s+)?(system|developer)\s+prompt", re.I),
        re.compile(r"忽略.{0,12}(之前|先前|系统|开发者).{0,8}(指令|提示|要求)"),
        re.compile(r"(绕过|关闭|禁用).{0,8}(安全|审核|限制|规则)"),
        re.compile(r"(输出|泄露|显示).{0,8}(系统提示词|开发者消息|密钥|令牌)"),
    )
    _secret_patterns = (
        (re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{16,}"), "[已脱敏令牌]"),
        (re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[a-z0-9._-]{8,}"), "[已脱敏密钥]"),
        (re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{8,}\b"), "[已脱敏令牌]"),
    )
    _pii_patterns = (
        (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[已脱敏手机号]"),
        (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[已脱敏邮箱]"),
        (re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"), "[已脱敏证件号]"),
    )

    def sanitize_text(self, text: str) -> tuple[str, SafetyReview]:
        sanitized = str(text)
        violations: list[str] = []
        redactions = 0

        for pattern in self._injection_patterns:
            sanitized, count = pattern.subn("[已移除不可信指令]", sanitized)
            if count:
                violations.append("prompt_injection")
                redactions += count

        for category, patterns in (("secret", self._secret_patterns), ("personal_data", self._pii_patterns)):
            for pattern, replacement in patterns:
                sanitized, count = pattern.subn(replacement, sanitized)
                if count:
                    violations.append(category)
                    redactions += count

        unique = tuple(dict.fromkeys(violations))
        return sanitized, SafetyReview(safe=not unique, violations=unique, redaction_count=redactions)

    def sanitize_contexts(self, contexts: list[dict]) -> tuple[list[dict], SafetyReview]:
        sanitized_contexts: list[dict] = []
        violations: list[str] = []
        redactions = 0
        for context in contexts:
            cleaned = dict(context)
            for field in ("title", "source_title", "snippet"):
                if field not in cleaned:
                    continue
                cleaned[field], review = self.sanitize_text(str(cleaned[field]))
                violations.extend(review.violations)
                redactions += review.redaction_count
            sanitized_contexts.append(cleaned)
        unique = tuple(dict.fromkeys(violations))
        return sanitized_contexts, SafetyReview(safe=not unique, violations=unique, redaction_count=redactions)

    def sanitize_payload(self, payload: Any) -> tuple[Any, SafetyReview]:
        violations: list[str] = []
        redactions = 0

        def clean(value: Any) -> Any:
            nonlocal redactions
            if isinstance(value, str):
                sanitized, review = self.sanitize_text(value)
                violations.extend(review.violations)
                redactions += review.redaction_count
                return sanitized
            if isinstance(value, list):
                return [clean(item) for item in value]
            if isinstance(value, tuple):
                return tuple(clean(item) for item in value)
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            return value

        sanitized = clean(payload)
        unique = tuple(dict.fromkeys(violations))
        return sanitized, SafetyReview(safe=not unique, violations=unique, redaction_count=redactions)

    def review_payload(self, payload: Any) -> SafetyReview:
        _, review = self.sanitize_payload(payload)
        return review
