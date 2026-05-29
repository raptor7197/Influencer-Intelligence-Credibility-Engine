import os

os.environ["DATABASE_URL"] = "sqlite:///./test_int.db"
os.environ["N8N_WEBHOOK_URL"] = "http://localhost:9999/webhook/test"
os.environ["LLM_MODE"] = "stub"

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import build_engine
from app.main import app


client = TestClient(app)


def setup_function():
    engine = build_engine()
    Base.metadata.create_all(bind=engine)
    conn = engine.raw_connection()
    try:
        conn.execute("ALTER TABLE influencers ADD COLUMN knocked_out BOOLEAN DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE influencers ADD COLUMN knockout_reason TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE influencers ADD COLUMN score_profile VARCHAR(32)")
    except Exception:
        pass
    conn.commit()
    conn.close()


def teardown_function():
    engine = build_engine()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_create_campaign():
    payload = {
        "org_name": "Test Org",
        "outreach_person": "Test User",
        "campaign_goal": "Reach broader audience through credible messengers",
        "language": "en",
    }
    response = client.post("/api/campaigns", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["org_name"] == "Test Org"
    assert data["outreach_person"] == "Test User"
    assert data["status"] == "draft"
    assert len(data["id"]) == 36
    return data


def test_create_campaign_full():
    payload = {
        "org_name": "Full Test",
        "outreach_person": "Jane",
        "campaign_goal": "Expand reach",
        "target_audience": "18-35 activists",
        "geo_focus": "US",
        "language": "en",
        "categories": ["environment", "food"],
        "exclusions": ["politics"],
    }
    response = client.post("/api/campaigns", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["org_name"] == "Full Test"
    assert data["categories"] == ["environment", "food"]
    assert data["exclusions"] == ["politics"]
    return data


def test_list_influencers():
    campaign = test_create_campaign()
    response = client.get(f"/api/campaigns/{campaign['id']}/influencers")
    assert response.status_code == 200
    assert response.json() == []


def test_scoring_pipeline_stub():
    from app.services.scoring.pipeline import ScoringPipeline
    import asyncio

    pipeline = ScoringPipeline()
    composite_result, dossier, dimension_results = asyncio.run(
        pipeline.run(
            campaign_context={"campaign_id": "test"},
            influencer_context={"name": "Test Influencer"},
            raw_evidence={},
        )
    )
    assert 0 <= composite_result.score <= 1
    assert len(dimension_results) == 8
    for dr in dimension_results:
        assert dr.score == 5.0

    from app.services.scoring.composite import compute_composite_score
    score = compute_composite_score(dimension_results)
    expected = (0.15*0.5 + 0.20*0.5 + 0.18*0.5 + 0.17*0.5 + 0.08*0.5 - 0.15*0.5 + 0.12*0.5 - 0.05*0.5) / (0.15+0.20+0.18+0.17+0.08+0.12)
    assert abs(score - expected) < 0.01


def test_normalization():
    from app.services.normalization import normalize_candidates

    candidates = [
        {"name": "Alice", "handle": "@alice", "platforms": ["twitter"], "evidence": {"key": "val"}},
        {"name": "Bob", "handle": "@bob"},
    ]
    result = normalize_candidates(candidates, cap=20)
    assert len(result) == 2
    assert result[0]["name"] == "Alice"
    assert result[0]["evidence_json"] == {"key": "val"}
    assert result[1]["evidence_json"] == {}

    capped = normalize_candidates(candidates * 5, cap=3)
    assert len(capped) == 3


def test_composite_score():
    from app.services.scoring.composite import compute_composite_score
    from app.services.scoring.types import DimensionResult

    results = [
        DimensionResult(dimension="D0_ANIMAL_WELFARE_ALIGNMENT", score=9.0, rationale="Strong"),
        DimensionResult(dimension="D1_VALUES_ALIGNMENT", score=9.0, rationale="Strong"),
        DimensionResult(dimension="D2_AUDIENCE_RELEVANCE", score=8.0, rationale="Good"),
        DimensionResult(dimension="D3_CREDIBILITY_TRUST", score=7.0, rationale="Credible"),
        DimensionResult(dimension="D4_REACHABILITY", score=6.0, rationale="Reachable"),
        DimensionResult(dimension="D5_RISK_CONTROVERSY", score=2.0, rationale="Low"),
        DimensionResult(dimension="D6_CAMPAIGN_FIT", score=8.0, rationale="Fit"),
        DimensionResult(dimension="D8_CONTROVERSY_VELOCITY", score=2.0, rationale="Low"),
    ]
    score = compute_composite_score(results)
    expected = (0.15*0.9 + 0.20*0.9 + 0.18*0.8 + 0.17*0.7 + 0.08*0.6 - 0.15*0.2 + 0.12*0.8 - 0.05*0.2) / (0.15+0.20+0.18+0.17+0.08+0.12)
    assert abs(score - expected) < 0.01


def test_evidence_dossier():
    from app.services.scoring.evidence import build_evidence_dossier

    raw = {
        "content_values": ["cv1"],
        "public_record": ["pr1"],
        "audience_profile": ["ap1"],
        "risk_controversy": ["rc1"],
        "sources": ["src1"],
    }
    dossier = build_evidence_dossier(raw)
    assert dossier.content_values == ["cv1"]
    assert dossier.sources == ["src1"]

    dossier2 = build_evidence_dossier({})
    assert dossier2.sources == []


def test_json_guard():
    from app.services.scoring.json_guard import safe_json_loads

    assert safe_json_loads('{"a": 1}') == {"a": 1}
    assert safe_json_loads('{"a": 1, "b": "hello"}') == {"a": 1, "b": "hello"}
    assert safe_json_loads("not json") == {}
    assert safe_json_loads("") == {}


def test_rubric_weights():
    from app.services.scoring.rubric import DIMENSIONS

    total = sum(v["weight"] for v in DIMENSIONS.values() if v["weight"] > 0)
    assert abs(total - 0.90) < 0.01
    assert len(DIMENSIONS) == 8
    assert "D0_ANIMAL_WELFARE_ALIGNMENT" in DIMENSIONS
    assert "D1_VALUES_ALIGNMENT" in DIMENSIONS
    assert "D5_RISK_CONTROVERSY" in DIMENSIONS
    assert "D8_CONTROVERSY_VELOCITY" in DIMENSIONS
    assert DIMENSIONS["D5_RISK_CONTROVERSY"]["weight"] == -0.15
    assert DIMENSIONS["D8_CONTROVERSY_VELOCITY"]["weight"] == -0.05


def test_types():
    from app.services.scoring.types import (
        CompositeResult,
        DimensionResult,
        EvidenceDossier,
        KnockoutResult,
        ScoreProfile,
    )

    d = EvidenceDossier()
    assert d.content_values == []
    assert d.sources == []

    r = DimensionResult(dimension="X", score=7.0, rationale="Test")
    assert r.score == 7.0
    assert r.evidence == []

    kr = KnockoutResult()
    assert not kr.knocked_out

    sp = ScoreProfile(label="test", description="desc", recommendation="rec")
    assert sp.label == "test"

    cr = CompositeResult(score=0.5)
    assert cr.score == 0.5
    assert not cr.knocked_out

    cr2 = CompositeResult(score=0.0, knocked_out=True, knockout_reason="bad", knockout_rule="D0 ≤ 2")
    assert cr2.score == 0.0
    assert cr2.knocked_out


if __name__ == "__main__":
    setup_function()
    tests = [
        ("campaign creation", test_create_campaign),
        ("full campaign creation", test_create_campaign_full),
        ("list influencers", test_list_influencers),
        ("scoring pipeline stub", test_scoring_pipeline_stub),
        ("normalization", test_normalization),
        ("composite score", test_composite_score),
        ("evidence dossier", test_evidence_dossier),
        ("JSON guard", test_json_guard),
        ("rubric weights", test_rubric_weights),
        ("types", test_types),
    ]
    all_pass = True
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
        except Exception as e:
            print(f"  FAIL: {name}: {e}")
            all_pass = False
    if all_pass:
        print("\nAll integration tests passed!")
    else:
        print("\nSome tests failed!")
