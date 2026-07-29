"""Transparent deterministic total rewards projection engine."""
from __future__ import annotations
import numpy as np
import pandas as pd

TIER_MULTIPLIERS = {"Employee Only": "employee_only", "Employee Plus Spouse": "employee_spouse", "Employee Plus Children": "employee_children", "Family": "family"}

def project(census: pd.DataFrame, assumptions: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    g, dc, pen, h, pay, other = (assumptions[k] for k in ("general", "dc", "pension", "health", "pay", "other"))
    rows = []
    for year_num in range(g["projection_years"]):
        year = g["start_year"] + year_num
        growth = (1 + g["salary_increase"]) ** year_num
        df = census.copy()
        df["pay"] = df["annual_base_pay"] * growth
        # Aggregate approximation: replacement hires keep the workforce near plan,
        # while turnover and retirement modestly dampen the growth factor.
        df["active_factor"] = (1 + g["workforce_growth"]) ** year_num * max(0.0, 1 - (g["turnover_rate"] + g["retirement_rate"]) * year_num * 0.10)
        df["pay"] *= df["active_factor"]
        df["bonus"] = df["pay"] * pay["bonus_rate"]
        df["payroll_tax"] = (df["pay"] + df["bonus"]) * pay["payroll_tax_rate"]
        df["base_pay"] = df["pay"]
        df["incentive_pay"] = df["bonus"] + df["payroll_tax"]
        df["payroll"] = df["pay"] + df["bonus"] + df["payroll_tax"]
        eligible_pay = df["pay"].where(df["retirement_plan_eligible"].eq("Yes"), 0)
        df["dc_cost"] = eligible_pay * (dc["employer_match_rate"] + dc["nonelective_rate"]) * dc["participation_rate"]
        covered_pay = df["pay"].where(df["pension_plan_eligible"].eq("Yes"), 0)
        if pen["cost_method"] == "Fixed annual cost":
            pension_total = pen["legacy_contribution"] * (1 + pen["contribution_growth"]) ** year_num
            df["pension_cost"] = 0.0
        else:
            df["pension_cost"] = covered_pay * pen["normal_cost_rate"] * pen["covered_percent"]
            pension_total = df["pension_cost"].sum() + pen["admin_expense"] * (1 + pen["contribution_growth"]) ** year_num
        health_base = df["coverage_tier"].map(lambda x: h.get(TIER_MULTIPLIERS.get(x, "employee_only"), h["employee_only"]))
        df["health_cost"] = health_base * (1 - h["employee_share"]) * (1 + h["health_trend"]) ** year_num
        df["health_cost"] += h["dental"] + h["vision"] + df["pay"] * (h["life_rate"] + h["disability_rate"]) + h["admin_per_employee"]
        df["other_cost"] = (other["fixed_per_employee"] + df["pay"] * other["pay_percentage"]) * (1 + other["growth_rate"]) ** year_num
        df["pension_cost"] = df["pension_cost"] if pen["cost_method"] != "Fixed annual cost" else 0.0
        df["benefits"] = df["dc_cost"] + df["pension_cost"] + df["health_cost"] + df["other_cost"]
        df["total_rewards"] = df["payroll"] + df["benefits"]
        df["year"] = year
        rows.append(df)
    detail = pd.concat(rows, ignore_index=True)
    annual = detail.groupby("year", as_index=False).agg(employees=("employee_id", "count"), base_pay=("base_pay", "sum"), incentive_pay=("incentive_pay", "sum"), payroll=("payroll", "sum"), defined_contribution=("dc_cost", "sum"), pension=("pension_cost", "sum"), health_welfare=("health_cost", "sum"), other_benefits=("other_cost", "sum"), benefits=("benefits", "sum"), total_rewards=("total_rewards", "sum"))
    annual["cost_per_employee"] = annual["total_rewards"] / annual["employees"]
    annual["benefits_per_employee"] = annual["benefits"] / annual["employees"]
    annual["benefits_pct_payroll"] = annual["benefits"] / annual["payroll"]
    annual["cumulative_total_rewards"] = annual["total_rewards"].cumsum()
    segment = detail.groupby(["year", "business_unit", "employee_group"], as_index=False).agg(employees=("employee_id", "count"), payroll=("payroll", "sum"), benefits=("benefits", "sum"), total_rewards=("total_rewards", "sum"))
    return annual, segment, detail

def scenario_assumptions(base: dict, scenario: str) -> dict:
    import copy
    a = copy.deepcopy(base)
    multipliers = {"Base": 1.0, "Low-cost": 0.75, "High-cost": 1.25}
    m = multipliers[scenario]
    for key in ("salary_increase", "workforce_growth", "health_trend"):
        a["general" if key in ("salary_increase", "workforce_growth") else "health"][key] *= m
    a["dc"]["employer_match_rate"] *= m
    a["pension"]["normal_cost_rate"] *= m
    a["other"]["growth_rate"] *= m
    return a
