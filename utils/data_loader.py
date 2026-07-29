from pathlib import Path
import numpy as np
import pandas as pd

EXPECTED = ["employee_id", "age", "service", "annual_base_pay", "employee_status", "business_unit", "employee_group", "retirement_plan_eligible", "pension_plan_eligible", "health_plan_election", "coverage_tier", "other_benefit_eligible"]

def load_sample() -> pd.DataFrame:
    # Fixed seed keeps the demo reproducible while providing realistic correlations.
    rng = np.random.default_rng(20260728)
    n = 500
    units = rng.choice(["Corporate", "Operations", "Sales", "Technology", "Customer Service"], n, p=[.14, .30, .18, .20, .18])
    groups = rng.choice(["Hourly", "Salaried", "Management", "Executive"], n, p=[.46, .34, .16, .04])
    age = np.clip(np.rint(rng.normal(43, 13, n)), 18, 72).astype(int)
    age[rng.choice(n, 35, replace=False)] = rng.integers(20, 30, 35)
    age[rng.choice(n, 45, replace=False)] = rng.integers(60, 73, 45)
    max_service = np.maximum(age - 18, 0)
    service = np.minimum(np.rint(rng.gamma(2.2, 4.0, n)).astype(int), max_service)
    service = np.where(age < 25, np.minimum(service, 3), service)
    group_min = {"Hourly": 34000, "Salaried": 58000, "Management": 105000, "Executive": 190000}
    group_max = {"Hourly": 68000, "Salaried": 125000, "Management": 205000, "Executive": 360000}
    unit_factor = {"Corporate": 1.05, "Operations": .92, "Sales": 1.00, "Technology": 1.15, "Customer Service": .88}
    pay = []
    for i in range(n):
        career_factor = 1 + min(service[i], 20) * .012 + max(age[i] - 40, 0) * .003
        low, high = group_min[groups[i]], group_max[groups[i]]
        base_pay = rng.uniform(low, high) * career_factor * unit_factor[units[i]]
        pay.append(round(base_pay / 100) * 100)
    coverage = rng.choice(["Employee Only", "Employee Plus Spouse", "Employee Plus Children", "Family"], n, p=[.42, .18, .15, .25])
    retirement_eligible = np.where((service >= 1) | np.isin(groups, ["Management", "Executive"]), "Yes", "No")
    pension_eligible = np.where((np.isin(units, ["Operations", "Corporate"]) & (groups != "Executive")) | (groups == "Management"), "Yes", "No")
    return pd.DataFrame({
        "employee_id": [f"E{i+1:04d}" for i in range(n)], "age": age, "service": service,
        "annual_base_pay": pay, "employee_status": "Active", "business_unit": units,
        "employee_group": groups, "retirement_plan_eligible": retirement_eligible,
        "pension_plan_eligible": pension_eligible, "health_plan_election": "Medical",
        "coverage_tier": coverage, "other_benefit_eligible": "Yes",
    })[EXPECTED]

def load_upload(uploaded) -> pd.DataFrame:
    return pd.read_excel(uploaded) if uploaded.name.lower().endswith((".xlsx", ".xls")) else pd.read_csv(uploaded)
