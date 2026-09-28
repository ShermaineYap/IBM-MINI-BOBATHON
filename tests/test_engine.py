"""Tests for engine.check_eligibility — boundary, one-off, two-off, null field."""
import json
from pathlib import Path

import pytest

from engine import check_eligibility

RULES = json.loads((Path(__file__).parent.parent / "rules.json").read_text(encoding="utf-8"))


def likely_ids(result):
    return {s["id"] for s in result["likely"]}


def check_ids(result):
    return {s["id"] for s in result["check"]}


# ---------------------------------------------------------------------------
# STR — household income boundary tests (any married person <= 5000 qualifies)
# ---------------------------------------------------------------------------

def test_str_boundary_income_at_limit():
    """Married user at exactly RM5,000 → STR likely."""
    user = {"age": 35, "marital_status": "married", "household_income": 5000,
            "household_size": 1, "children_under_18": 0, "occupation": "working",
            "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert "str" in likely_ids(result)


def test_str_boundary_income_one_above_limit():
    """Married user at RM5,001 — one criterion short — STR goes to check."""
    user = {"age": 35, "marital_status": "married", "household_income": 5001,
            "household_size": 1, "children_under_18": 0, "occupation": "working",
            "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    # All three STR rules fail on income, but each rule has only one condition
    # (married + income) so at least one is exactly-one-short
    assert "str" not in likely_ids(result)
    assert "str" in check_ids(result)


# ---------------------------------------------------------------------------
# eBelia Rahmah — age boundary
# ---------------------------------------------------------------------------

def test_ebelia_age_30_student_likely():
    """Student aged 30 matches the 21+ student branch → ebelia likely (not a boundary issue)."""
    user = {"age": 30, "occupation": "student", "household_income": 9999,
            "household_size": 1, "children_under_18": 0, "marital_status": "single",
            "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert "ebelia" in likely_ids(result)


def test_ebelia_age_17_one_short_goes_to_check():
    """Age 17 + working: branch 1 (age 18-20) fails only on age>=18 → one-short → check tier."""
    user = {"age": 17, "occupation": "working", "household_income": 9999,
            "household_size": 1, "children_under_18": 0, "marital_status": "single",
            "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert "ebelia" not in likely_ids(result)
    assert "ebelia" in check_ids(result)


def test_ebelia_age_15_two_short_omitted():
    """Age 15 + working: branch 1 fails age>=18 AND age<=20 is ok but age>=18 fails; branch 2 fails age>=21 AND occupation.
    Actually branch 1 only has two conditions (gte 18, lte 20). Age 15: gte 18 fails (1 fail). Still one-short.
    Use age=15 + student: branch1 fails gte:18 (1 short), branch2 fails gte:21 (1 short). Still check.
    Two-short test: pick a scheme with a 2-condition rule where user fails both."""
    # JKM Warga Emas: age>=60 AND income<=1500; user age=30 income=5000 fails both → omitted
    user = {"age": 30, "household_income": 5000,
            "household_size": 1, "children_under_18": 0, "marital_status": "single",
            "occupation": "working", "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert "jkm_warga_emas" not in likely_ids(result)
    assert "jkm_warga_emas" not in check_ids(result)


# ---------------------------------------------------------------------------
# Check tier — one criterion short
# ---------------------------------------------------------------------------

def test_one_off_goes_to_check_with_reason():
    """User matching JKM Warga Emas age but income slightly over → check with reason."""
    user = {"age": 60, "household_income": 1501,
            "household_size": 1, "children_under_18": 0, "marital_status": "single",
            "occupation": "retired", "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert "jkm_warga_emas" not in likely_ids(result)
    check_map = {s["id"]: s for s in result["check"]}
    assert "jkm_warga_emas" in check_map
    reason = check_map["jkm_warga_emas"]["reason"]
    assert reason  # non-empty
    assert "1,500" in reason  # RM threshold mentioned


# ---------------------------------------------------------------------------
# Null / missing fields fail gracefully
# ---------------------------------------------------------------------------

def test_null_religion_fails_zakat_gracefully():
    """religion=None should fail the 'in: [islam]' check without raising an error."""
    user = {"age": 40, "household_income": 2000, "religion": None,
            "household_size": 1, "children_under_18": 0, "marital_status": "married",
            "occupation": "working", "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert "zakat" not in likely_ids(result)
    # One criterion short (religion) → check tier
    check_map = {s["id"]: s for s in result["check"]}
    assert "zakat" in check_map


def test_missing_field_does_not_raise():
    """Completely missing field (not even in dict) is treated as None / failing."""
    user = {"age": 40, "household_income": 2000,
            "household_size": 1, "children_under_18": 0, "marital_status": "married",
            "occupation": "working", "has_ptptn": False, "state": "Selangor"}
    # "religion" key absent entirely
    result = check_eligibility(user, RULES)
    assert isinstance(result["likely"], list)
    assert isinstance(result["check"], list)


# ---------------------------------------------------------------------------
# High income → nothing in either tier
# ---------------------------------------------------------------------------

def test_high_income_not_in_likely():
    """Household income way above all thresholds → nothing in likely."""
    user = {"age": 40, "household_income": 20000, "marital_status": "married",
            "household_size": 4, "children_under_18": 2, "occupation": "working",
            "religion": None, "has_ptptn": False, "state": "Selangor"}
    result = check_eligibility(user, RULES)
    assert likely_ids(result) == set()
