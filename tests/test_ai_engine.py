import pytest
from app.pipeline.ai_engine import (
    generate_civil_expert_insights,
    run_ai_insight_generation,
    answer_drawing_query
)

def test_generate_civil_expert_insights():
    summary_data = {
        "total_piers": 56,
        "total_points": 483,
        "excluded_piers": ["P3", "P11"]
    }
    insights = generate_civil_expert_insights(summary_data)
    assert len(insights) >= 8
    
    categories = [item["category"] for item in insights]
    assert "3D_MODELING_BRIEF" in categories
    assert "STRUCTURAL_TYPOLOGY" in categories
    assert "CRITICAL_EXCLUSIONS" in categories
    assert "GEOTECHNICAL_FOUNDATION" in categories
    assert "MATERIALS_AND_STANDARDS" in categories

def test_answer_drawing_query_exclusions():
    res = answer_drawing_query("Are piers P3 and P11 included in construction?")
    assert "EXCLUDED" in res["answer"].upper() or "NOT USED" in res["answer"].upper()
    assert res["confidence"] >= 0.8

def test_answer_drawing_query_pier_dimensions():
    res = answer_drawing_query("What are the dimensions of the pier shaft?")
    assert "5,000 mm" in res["answer"]
    assert "2,500 mm" in res["answer"]
    assert "M40" in res["answer"]

def test_answer_drawing_query_pier_cap():
    res = answer_drawing_query("What is the pier cap width and cantilever?")
    assert "13,600 mm" in res["answer"]
    assert "3,000 mm" in res["answer"]

def test_answer_drawing_query_deck_slopes():
    res = answer_drawing_query("What is the crossfall slope on Section 1-1 and Section 2-2?")
    assert "2.50%" in res["answer"]
    assert "2.42%" in res["answer"]
