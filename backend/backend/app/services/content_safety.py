from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SafetyResult:
    value: Any
    violations: tuple[str, ...]
    redaction_count: int

    @property
    def refused(self) -> bool:
        return any(item in {"harmful_instruction", "academic_misconduct"} for item in self.violations)


class ContentSafetyService:
    """Local fail-closed sanitizer used before any backend LLM request."""

    PATTERNS = (
        ("prompt_injection", re.compile(r"ignore\s+(all\s+)?(previous|system|developer).{0,16}instructions?", re.I), "[已移除不可信指令]"),
        ("prompt_injection", re.compile(r"忽略.{0,12}(之前|系统|开发者).{0,8}(指令|提示|要求)"), "[已移除不可信指令]"),
        ("prompt_injection", re.compile(r"(输出|泄露|显示).{0,8}(系统提示词|开发者消息|密钥|令牌)"), "[已移除不可信指令]"),
        ("secret", re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[a-z0-9._-]{8,}"), "[已脱敏密钥]"),
        ("personal_data", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[已脱敏手机号]"),
        ("personal_data", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[已脱敏邮箱]"),
        ("personal_data", re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"), "[已脱敏证件号]"),
        ("harmful_instruction", re.compile(r"(教我|告诉我|生成|提供|写出).{0,16}(制作炸弹|自杀方法|窃取密码|勒索软件|入侵他人|投毒步骤)"), "[已拒绝不安全请求]"),
        ("academic_misconduct", re.compile(r"(替我|帮我|直接).{0,12}(完成考试|考试作弊|代写论文|写期末论文|给出考试答案)"), "[已拒绝不安全请求]"),
    )

    def sanitize(self, payload: Any) -> SafetyResult:
        violations: list[str] = []
        redactions = 0

        def clean(value: Any) -> Any:
            nonlocal redactions
            if isinstance(value, str):
                result = value
                for category, pattern, replacement in self.PATTERNS:
                    result, count = pattern.subn(replacement, result)
                    if count:
                        violations.append(category)
                        redactions += count
                return result
            if isinstance(value, list):
                return [clean(item) for item in value]
            if isinstance(value, tuple):
                return tuple(clean(item) for item in value)
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            return value

        return SafetyResult(clean(payload), tuple(dict.fromkeys(violations)), redactions)

    def refusal(self, result: SafetyResult) -> dict:
        academic = "academic_misconduct" in result.violations
        return {
            "answer": (
                "我不能替你完成考试、论文或提供作弊答案，但可以讲解知识、检查你的思路并给出提示。"
                if academic
                else "我不能提供可能伤害他人或用于未授权入侵的操作步骤，可以改为讨论安全原理和防御措施。"
            ),
            "hints": ["说明合法学习目标", "提出具体概念问题", "提供你已经尝试的思路"],
            "next_action": "将请求改写为概念讲解、思路检查或安全防御问题。",
            "refused": True,
            "refusal_reason": "academic_integrity" if academic else "content_safety",
            "safety_meta": {
                "safe": True,
                "input_violations": list(result.violations),
                "redaction_count": result.redaction_count,
            },
        }


content_safety_service = ContentSafetyService()
