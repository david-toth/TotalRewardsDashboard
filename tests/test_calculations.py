import json
from models.projection import project
from utils.data_loader import load_sample

def assumptions():
    with open("data/default_assumptions.json") as f: return json.load(f)

def test_projection_has_requested_years_and_balances():
    annual, segment, detail = project(load_sample(), assumptions())
    assert len(annual) == 5
    assert (annual.total_rewards == annual.payroll + annual.benefits).all()
    assert annual.total_rewards.iloc[-1] > annual.total_rewards.iloc[0]

def test_detail_is_record_level():
    annual, segment, detail = project(load_sample(), assumptions())
    assert len(detail) == 2500
    assert {"dc_cost", "pension_cost", "health_cost", "other_cost"}.issubset(detail.columns)
