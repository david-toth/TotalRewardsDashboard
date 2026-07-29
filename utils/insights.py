def generate_executive_insights(annual, census, detail, scenarios=None):
    current, final = annual.iloc[0], annual.iloc[-1]
    insights = []
    categories = {"Health and welfare": final.health_welfare-current.health_welfare, "Defined contribution": final.defined_contribution-current.defined_contribution, "Pension": final.pension-current.pension, "Other benefits": final.other_benefits-current.other_benefits}
    top = max(categories, key=categories.get)
    insights.append(f"{top} is the largest non-pay contributor to projected cost growth ({categories[top] / max(1, final.total_rewards-current.total_rewards):.0%} of the increase).")
    unit = detail[detail.year == detail.year.min()].groupby("business_unit").benefits.mean().idxmax()
    insights.append(f"{unit} has the highest current average benefit cost per employee.")
    older = census[census.pension_plan_eligible.eq("Yes") & (census.age >= 60)]
    covered = max(1, census.pension_plan_eligible.eq("Yes").sum())
    insights.append(f"{len(older) / covered:.0%} of pension-eligible employees are age 60 or older.")
    if scenarios is not None:
        base = scenarios[scenarios.scenario == "Baseline"].total_rewards.sum()
        pressure = scenarios[scenarios.scenario == "Cost Pressure"].total_rewards.sum()
        insights.append(f"Cost Pressure is {pressure-base:+,.0f} versus Baseline on a cumulative basis.")
    return insights[:4]
