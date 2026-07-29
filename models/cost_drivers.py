def calculate_cost_driver_attribution(annual, assumptions):
    current = annual.iloc[0]
    final = annual.iloc[-1]
    delta = final.total_rewards - current.total_rewards
    salary = current.payroll * ((1 + assumptions["general"]["salary_increase"]) ** (len(annual)-1) - 1)
    health = current.health_welfare * ((1 + assumptions["health"]["health_trend"]) ** (len(annual)-1) - 1)
    dc = final.defined_contribution - current.defined_contribution
    pension = final.pension - current.pension
    other = final.other_benefits - current.other_benefits
    known = salary + health + dc + pension + other
    return {"Salary growth": salary, "Health-care trend": health, "Defined contribution growth": dc, "Pension cost growth": pension, "Other benefit growth": other, "Other and interaction effects": delta - known, "Final total cost": delta}
