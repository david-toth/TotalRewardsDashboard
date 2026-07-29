import copy

SCENARIOS = {
    "Baseline": {"description": "Expected workforce and cost development.", "multipliers": {"salary_increase": 1.0, "workforce_growth": 1.0, "health_trend": 1.0, "dc_rate": 1.0, "pension_rate": 1.0, "other_growth": 1.0}},
    "Cost Pressure": {"description": "Higher wage and medical cost growth.", "multipliers": {"salary_increase": 1.30, "workforce_growth": 1.0, "health_trend": 1.30, "dc_rate": 1.0, "pension_rate": 1.08, "other_growth": 1.20}},
    "Workforce Expansion": {"description": "A growing workforce with steady benefit trends.", "multipliers": {"salary_increase": 1.0, "workforce_growth": 2.0, "health_trend": 1.0, "dc_rate": 1.0, "pension_rate": 1.0, "other_growth": 1.0}},
    "Workforce Contraction": {"description": "A smaller workforce with moderated cost growth.", "multipliers": {"salary_increase": .85, "workforce_growth": -1.5, "health_trend": 1.0, "dc_rate": 1.0, "pension_rate": 1.0, "other_growth": .9}},
    "Benefits Redesign": {"description": "A directional redesign with lower employer benefit rates.", "multipliers": {"salary_increase": 1.0, "workforce_growth": 1.0, "health_trend": .90, "dc_rate": .80, "pension_rate": .85, "other_growth": .90}},
}

def apply_scenario(base, name):
    a = copy.deepcopy(base)
    m = SCENARIOS[name]["multipliers"]
    a["general"]["salary_increase"] *= m["salary_increase"]
    a["general"]["workforce_growth"] *= m["workforce_growth"]
    a["health"]["health_trend"] *= m["health_trend"]
    a["dc"]["employer_match_rate"] *= m["dc_rate"]
    a["pension"]["normal_cost_rate"] *= m["pension_rate"]
    a["other"]["growth_rate"] *= m["other_growth"]
    return a
