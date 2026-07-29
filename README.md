# Total Rewards Cost Projection Dashboard

A modular Streamlit concept prototype for projecting employer total rewards costs over 5–10 years from synthetic or uploaded employee census data. The current interface is organized into Executive Outlook, Workforce, Projection Studio, Scenario Comparison, and Data & Methodology.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run tests with `pytest`.

The Executive Outlook includes six KPI cards, a stacked cost projection, current-versus-final composition, an approximate driver waterfall, and rules-based insights. The Workforce section supports business-unit and employee-group filters. Scenario definitions live in `config/scenarios.py`; shared chart and formatting utilities live under `utils/`.

## Census fields

Required: `employee_id`, `age`, `service`, `annual_base_pay`, `employee_status`, `business_unit`, `employee_group`, `retirement_plan_eligible`, `pension_plan_eligible`, `health_plan_election`, `coverage_tier`, and `other_benefit_eligible`.

## Model formulas

- Payroll = base pay + bonus + payroll taxes.
- Defined contribution = eligible pay × (match + nonelective rate) × participation.
- Pension = covered pay × normal cost rate × covered percentage + administrative expense.
- Health and welfare = tiered employer premium after employee share + dental + vision + life/disability + administration.
- Other benefits = fixed per-employee amount + pay percentage, grown annually.
- Total rewards = payroll + defined contribution + pension + health and welfare + other benefits.

## Known limitations

This is an illustrative deterministic model, not an actuarial valuation. Workforce replacement is approximated through a stable census base, and pension, health, turnover, retirement, and scenario methods are intentionally simplified. No real employee information is included.
