from fastapi.testclient import TestClient

from app import Applicant, app, load_rules
from engine import check_eligibility

client = TestClient(app)


def likely_ids(result):
    """Extract set of scheme ids from check_eligibility result or API response body."""
    if isinstance(result, dict) and "likely" in result:
        return {s["id"] if isinstance(s, dict) else s.id for s in result["likely"]}
    # Legacy support: SchemeResult objects list
    return {s.id for s in result.likely}


def test_rules_file_is_valid():
    rules = load_rules()
    assert rules["schemes"], "rules.json must contain schemes"
    for s in rules["schemes"]:
        assert {"id", "name", "any_of", "documents"} <= set(s)


def test_low_income_married_family():
    a = Applicant(age=35, household_income=2000, household_size=4, children_under_18=2, marital_status="married")
    rules = load_rules()
    result = check_eligibility(a.model_dump(), rules)
    got = likely_ids(result)
    assert {"str", "sara", "jkm_kanak", "madani_medical", "ekasih"} <= got
    assert "ebelia" not in got


def test_student_gets_ebelia_only_not_str():
    a = Applicant(age=22, household_income=6000, occupation="student", has_ptptn=True)
    rules = load_rules()
    result = check_eligibility(a.model_dump(), rules)
    got = likely_ids(result)
    assert "ebelia" in got
    assert "str" not in got
    assert "ptptn_ujrah" not in got  # income above threshold


def test_senior_low_income():
    a = Applicant(age=65, household_income=1200, occupation="retired")
    rules = load_rules()
    result = check_eligibility(a.model_dump(), rules)
    got = likely_ids(result)
    assert {"str", "jkm_warga_emas", "madani_medical"} <= got


def test_high_income_gets_nothing():
    a = Applicant(age=40, household_income=15000, marital_status="married")
    rules = load_rules()
    result = check_eligibility(a.model_dump(), rules)
    assert likely_ids(result) == set()


def test_api_endpoint():
    r = client.post("/api/check", json={"age": 19, "household_income": 3000})
    assert r.status_code == 200
    body = r.json()
    assert any(s["id"] == "ebelia" for s in body["likely"])
    assert body["disclaimer"]


def test_api_validation():
    r = client.post("/api/check", json={"age": -1, "household_income": 100})
    assert r.status_code == 422
