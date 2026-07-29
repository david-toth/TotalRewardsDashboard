import pandas as pd
from .data_loader import EXPECTED

def validate(df: pd.DataFrame) -> list[str]:
    warnings = [f"Missing required column: {c}" for c in EXPECTED if c not in df.columns]
    if "employee_id" in df and df["employee_id"].duplicated().any(): warnings.append("Duplicate employee IDs detected.")
    if "annual_base_pay" in df and (pd.to_numeric(df["annual_base_pay"], errors="coerce") < 0).any(): warnings.append("Negative pay detected.")
    if "age" in df and ((pd.to_numeric(df["age"], errors="coerce") < 16) | (pd.to_numeric(df["age"], errors="coerce") > 85)).any(): warnings.append("Implausible ages detected.")
    if {"age", "service"}.issubset(df.columns) and (pd.to_numeric(df["service"], errors="coerce") > pd.to_numeric(df["age"], errors="coerce")).any(): warnings.append("Service greater than age detected.")
    if "coverage_tier" in df and df["coverage_tier"].isna().any(): warnings.append("Missing benefit elections or coverage tiers detected.")
    return warnings
