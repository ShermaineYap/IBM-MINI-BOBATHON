"""Rules evaluation engine for Bantuan Checker.

Exposes check_eligibility(user, rules) -> {"likely": [...], "check": [...]}.

Likely  = at least one any_of rule passes fully.
Check   = no any_of rule passes fully, but at least one any_of rule fails on
          exactly one condition; includes a human-readable reason for that
          single failing condition.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Operator implementations (None / missing values always fail)
# ---------------------------------------------------------------------------
_OPS: dict[str, Any] = {
    "eq":  lambda v, t: v is not None and v == t,
    "gte": lambda v, t: v is not None and v >= t,
    "lte": lambda v, t: v is not None and v <= t,
    "in":  lambda v, t: v is not None and str(v).lower() in [str(x).lower() for x in t],
}


def _eval_condition(cond: dict[str, Any], user: dict[str, Any]) -> bool:
    """Return True if the condition passes for this user dict."""
    value = user.get(cond["field"])
    for op, target in cond.items():
        if op == "field":
            continue
        fn = _OPS.get(op)
        if fn is None:
            raise ValueError(f"Unknown operator: {op!r}")
        if not fn(value, target):
            return False
    return True


# ---------------------------------------------------------------------------
# Human-readable reason generator
# ---------------------------------------------------------------------------
_RM_FORMAT = {
    "household_income": "RM{:,.0f}",
    "age": "{:.0f}",
}


def _reason(cond: dict[str, Any]) -> str:
    """Build a sentence like 'household income must be <= RM2,500'."""
    field = cond["field"]
    label = field.replace("_", " ")
    parts = []
    for op, target in cond.items():
        if op == "field":
            continue
        fmt = _RM_FORMAT.get(field, "{}")
        if op == "lte":
            parts.append(f"{label} must be ≤ {fmt.format(target)}")
        elif op == "gte":
            parts.append(f"{label} must be ≥ {fmt.format(target)}")
        elif op == "eq":
            parts.append(f"{label} must be {target}")
        elif op == "in":
            opts = " or ".join(str(x) for x in target)
            parts.append(f"{label} must be {opts}")
        else:
            parts.append(f"{label} {op} {target}")
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------
def check_eligibility(user: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    """Evaluate all schemes against the user dict.

    Returns {"likely": [scheme_dicts], "check": [scheme_dicts_with_reason]}.
    Each scheme dict contains: id, name, agency, summary, benefit, url, documents.
    "check" items additionally have a "reason" string.
    """
    likely: list[dict] = []
    check: list[dict] = []

    for scheme in rules.get("schemes", []):
        base = {k: scheme[k] for k in ("id", "name", "agency", "summary", "benefit", "url", "documents") if k in scheme}
        any_of = scheme.get("any_of", [])

        # Check for a full match across any rule branch
        for rule in any_of:
            conditions = rule.get("all_of", [])
            if all(_eval_condition(c, user) for c in conditions):
                likely.append(base)
                break
        else:
            # No full match — look for a one-condition-short branch
            best_reason: str | None = None
            for rule in any_of:
                conditions = rule.get("all_of", [])
                failed = [c for c in conditions if not _eval_condition(c, user)]
                if len(failed) == 1:
                    best_reason = _reason(failed[0])
                    break
            if best_reason is not None:
                check.append({**base, "reason": best_reason})

    return {"likely": likely, "check": check}
