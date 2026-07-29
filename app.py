import copy
import io
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config.design import APP_TITLE, MODEL_VERSION, CATEGORY_LABELS, COST_COLORS
from config.scenarios import SCENARIOS, apply_scenario
from models.cost_drivers import calculate_cost_driver_attribution
from models.projection import project
from utils.charts import apply_chart_layout, cost_driver_waterfall, projection_area
from utils.data_loader import load_sample, load_upload
from utils.data_validation import validate
from utils.formatting import format_currency, format_currency_millions, format_percentage, format_variance, format_year_range
from utils.insights import generate_executive_insights

st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
.kpi {background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 12px; padding: 16px 18px; min-height: 112px; box-shadow: 0 1px 2px rgba(16,24,40,.04);}
.kpi-value {font-size: 1.55rem; font-weight: 700; color: #1F2933;}
.kpi-label {font-size: .82rem; color: #667085; margin-top: 5px;}
.kpi-context {font-size: .75rem; color: #98A2B3; margin-top: 8px;}
.status {color: #667085; font-size: .82rem; padding: 8px 0 14px;}
</style>""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent / "data"
SAMPLE_DATA_VERSION = 2

@st.cache_data
def default_assumptions():
    return json.loads((DATA_DIR / "default_assumptions.json").read_text())

def initialize_session_state():
    if "census" not in st.session_state or (st.session_state.get("census_source") == "Sample synthetic census" and st.session_state.get("census_version") != SAMPLE_DATA_VERSION):
        st.session_state.census = load_sample()
        st.session_state.census_source = "Sample synthetic census"
        st.session_state.census_version = SAMPLE_DATA_VERSION
    if "assumptions" not in st.session_state: st.session_state.assumptions = default_assumptions()
    if "scenario" not in st.session_state: st.session_state.scenario = "Baseline"
    if "results" not in st.session_state: st.session_state.results = project(st.session_state.census, st.session_state.assumptions)
    if "last_run" not in st.session_state: st.session_state.last_run = datetime.now()
    if "warnings" not in st.session_state: st.session_state.warnings = validate(st.session_state.census)

def run_projection(assumptions=None):
    st.session_state.assumptions = assumptions or st.session_state.assumptions
    with st.spinner("Updating projection..."):
        st.session_state.results = project(st.session_state.census, st.session_state.assumptions)
    st.session_state.last_run = datetime.now()
    st.session_state.warnings = validate(st.session_state.census)

def money(v): return format_currency(v)
def kpi(label, value, context):
    return f'<div class="kpi"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div><div class="kpi-context">{context}</div></div>'

def page_header(title, subtitle):
    st.title(title)
    st.write(subtitle)

def status_bar():
    annual = st.session_state.results[0]
    status = "Data checks passed" if not st.session_state.warnings else f"{len(st.session_state.warnings)} data warning(s)"
    st.markdown(f'<div class="status">{st.session_state.scenario} &nbsp;|&nbsp; {len(st.session_state.census):,} employees &nbsp;|&nbsp; {format_year_range(int(annual.year.iloc[0]), len(annual))} &nbsp;|&nbsp; Updated {st.session_state.last_run.strftime("%I:%M %p").lstrip("0")} &nbsp;|&nbsp; {status}</div>', unsafe_allow_html=True)

def disclaimer():
    st.caption(f"{MODEL_VERSION}. Conceptual model only; results are illustrative and are not an actuarial valuation, financial-reporting estimate, funding recommendation, or benefit decision.")

def build_export(annual, segment, detail, scenarios, warnings):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        summary = annual.iloc[[0, -1]][["year", "employees", "payroll", "benefits", "total_rewards"]]
        summary.to_excel(writer, index=False, sheet_name="Executive Summary")
        annual.to_excel(writer, index=False, sheet_name="Annual Projection")
        annual[["year", "base_pay", "incentive_pay", "defined_contribution", "pension", "health_welfare", "other_benefits"]].to_excel(writer, index=False, sheet_name="Cost Categories")
        scenarios.to_excel(writer, index=False, sheet_name="Scenario Comparison")
        pd.json_normalize(st.session_state.assumptions, sep=".").T.rename(columns={0:"value"}).to_excel(writer, sheet_name="Assumptions")
        detail.groupby("business_unit", as_index=False).agg(employees=("employee_id", "count"), payroll=("payroll", "sum"), benefits=("benefits", "sum"), total_rewards=("total_rewards", "sum")).to_excel(writer, index=False, sheet_name="Workforce Summary")
        pd.DataFrame({"warning": warnings or ["No warnings"]}).to_excel(writer, index=False, sheet_name="Data Warnings")
    return buf.getvalue()

initialize_session_state()
st.sidebar.title("Total Rewards")
page = st.sidebar.radio("Navigate", ["Executive Outlook", "Workforce", "Projection Studio", "Scenario Comparison", "Data & Methodology"])
st.sidebar.markdown(f"**Active scenario:** {st.session_state.scenario}")
st.sidebar.caption(f"{st.session_state.census_source} • {MODEL_VERSION}")

if page == "Executive Outlook":
    annual, segment, detail = st.session_state.results
    current, final = annual.iloc[0], annual.iloc[-1]
    page_header("Total Rewards Outlook", f"Projected workforce and employee reward costs through {int(final.year)}")
    status_bar()
    c1, c2, c3 = st.columns([1.2, 1.2, .9])
    selected = c1.selectbox("Active scenario", list(SCENARIOS), index=list(SCENARIOS).index(st.session_state.scenario), label_visibility="collapsed")
    if selected != st.session_state.scenario: st.session_state.scenario = selected; run_projection(apply_scenario(default_assumptions(), selected)); st.rerun()
    c2.caption(SCENARIOS[st.session_state.scenario]["description"])
    if c3.button("Run projection", type="primary", use_container_width=True): run_projection()
    delta = final.total_rewards - current.total_rewards
    growth = (final.total_rewards / current.total_rewards) ** (1 / max(1, len(annual)-1)) - 1
    cards = [("Current total rewards", money(current.total_rewards), "Starting-year employer cost"), ("Final-year projected cost", money(final.total_rewards), f"{format_variance(delta)} versus current"), ("Annualized cost growth", format_percentage(growth), "Compounded over the horizon"), ("Benefits as % of payroll", format_percentage(current.benefits_pct_payroll), "Current-year burden"), ("Cumulative cost", format_currency_millions(final.cumulative_total_rewards), f"Across {len(annual)} years")]
    cols = st.columns(5)
    for col, item in zip(cols, cards): col.markdown(kpi(*item), unsafe_allow_html=True)
    st.subheader("Projected cost outlook")
    st.plotly_chart(projection_area(annual), use_container_width=True)
    st.caption("Stacked categories reconcile to total rewards. Pay includes base pay, incentive pay, and payroll taxes.")
    st.subheader("Cost composition")
    categories = ["base_pay", "incentive_pay", "defined_contribution", "pension", "health_welfare", "other_benefits"]
    composition = pd.DataFrame({"Category":[CATEGORY_LABELS[c] for c in categories], "Current year":[current[c] for c in categories], "Final year":[final[c] for c in categories]})
    composition["Change"] = composition["Final year"] - composition["Current year"]
    st.dataframe(composition.style.format({"Current year":"${:,.0f}", "Final year":"${:,.0f}", "Change":"${:,.0f}"}), use_container_width=True, hide_index=True)
    disclaimer()

elif page == "Workforce":
    annual, segment, detail = st.session_state.results
    df = st.session_state.census.copy()
    page_header("Workforce", "Understand the population characteristics that shape total rewards cost.")
    status_bar()
    df["age_band"] = pd.cut(df.age, [0, 29, 39, 49, 59, 120], labels=["Under 30", "30–39", "40–49", "50–59", "60+"])
    df["pay_band"] = pd.cut(df.annual_base_pay, [0, 60000, 90000, 130000, float("inf")], labels=["<$60k", "$60k–$90k", "$90k–$130k", "$130k+"])
    with st.expander("Population filters", expanded=True):
        f1, f2, f3 = st.columns(3)
        units = f1.multiselect("Business unit", sorted(df.business_unit.unique()), default=sorted(df.business_unit.unique()))
        groups = f2.multiselect("Employee group", sorted(df.employee_group.unique()), default=sorted(df.employee_group.unique()))
        tiers = f3.multiselect("Coverage tier", sorted(df.coverage_tier.unique()), default=sorted(df.coverage_tier.unique()))
        f1, f2, f3 = st.columns(3)
        age_bands = f1.multiselect("Age band", list(df.age_band.cat.categories), default=list(df.age_band.cat.categories))
        pay_bands = f2.multiselect("Pay band", list(df.pay_band.cat.categories), default=list(df.pay_band.cat.categories))
        retirement = f3.multiselect("Retirement eligible", ["Yes", "No"], default=["Yes", "No"])
    filtered = df[df.business_unit.isin(units) & df.employee_group.isin(groups) & df.coverage_tier.isin(tiers) & df.age_band.isin(age_bands) & df.pay_band.isin(pay_bands) & df.retirement_plan_eligible.isin(retirement)]
    if filtered.empty:
        st.warning("No employees match the selected filters.")
        st.stop()
    current = detail[(detail.year == detail.year.min()) & detail.employee_id.isin(filtered.employee_id)]
    c = st.columns(5)
    metrics = [("Employees", f"{len(filtered):,}"), ("Annual payroll", money(current.payroll.sum())), ("Average pay", money(filtered.annual_base_pay.mean())), ("Average age", f"{filtered.age.mean():.1f}"), ("Benefits per employee", money(current.benefits.sum() / len(filtered)))]
    for col, (label, value) in zip(c, metrics): col.markdown(kpi(label, value, "Filtered population"), unsafe_allow_html=True)
    st.subheader("Population summary")
    unit_summary = current.groupby("business_unit", as_index=False).agg(employees=("employee_id", "count"), average_pay=("annual_base_pay", "mean"), payroll=("payroll", "sum"), benefits=("benefits", "sum"), total_rewards=("total_rewards", "sum"))
    unit_summary["benefits_per_employee"] = unit_summary.benefits / unit_summary.employees
    unit_summary["benefits_pct_payroll"] = unit_summary.benefits / unit_summary.payroll
    st.dataframe(unit_summary.style.format({"average_pay":"${:,.0f}", "payroll":"${:,.0f}", "benefits":"${:,.0f}", "benefits_per_employee":"${:,.0f}", "total_rewards":"${:,.0f}", "benefits_pct_payroll":"{:.1%}"}), use_container_width=True, hide_index=True)
    tabs = st.tabs(["Business unit", "Coverage tier", "Age and pay bands"])
    with tabs[0]:
        fig = px.bar(unit_summary.sort_values("benefits_per_employee"), x="benefits_per_employee", y="business_unit", orientation="h", title="Benefits per employee by business unit"); apply_chart_layout(fig, currency_axis=True); st.plotly_chart(fig, use_container_width=True)
    with tabs[1]:
        tier = current.groupby("coverage_tier", as_index=False).agg(employees=("employee_id", "count"), benefits_per_employee=("benefits", "mean"), total_benefits=("benefits", "sum")); st.dataframe(tier.style.format({"benefits_per_employee":"${:,.0f}", "total_benefits":"${:,.0f}"}), use_container_width=True, hide_index=True)
    with tabs[2]:
        band_source = current.merge(filtered[["employee_id", "age_band", "pay_band"]], on="employee_id", how="left")
        band = band_source.groupby(["age_band", "pay_band"], observed=True, as_index=False).agg(employees=("employee_id", "count"), average_pay=("annual_base_pay", "mean"), benefits=("benefits", "sum")); st.dataframe(band.style.format({"average_pay":"${:,.0f}", "benefits":"${:,.0f}"}), use_container_width=True, hide_index=True)
    with st.expander("View census records"): st.dataframe(filtered, use_container_width=True, hide_index=True)
    disclaimer()

elif page == "Projection Studio":
    page_header("Projection Studio", "Adjust the assumptions that matter most, then run a controlled projection.")
    status_bar()
    names = list(SCENARIOS)
    choice = st.radio("Scenario", names, index=names.index(st.session_state.scenario), horizontal=True)
    base = apply_scenario(default_assumptions(), choice)
    a = copy.deepcopy(st.session_state.assumptions if choice == st.session_state.scenario else base)
    with st.form("projection_form"):
        st.caption(SCENARIOS[choice]["description"])
        st.subheader("Workforce")
        c1,c2,c3 = st.columns(3); a["general"]["workforce_growth"] = c1.slider("Workforce growth", -0.10, .20, float(a["general"]["workforce_growth"]), .005, help="Annual change in workforce size."); a["general"]["turnover_rate"] = c2.slider("Turnover", 0., .5, float(a["general"]["turnover_rate"]), .005); a["general"]["retirement_rate"] = c3.slider("Retirement rate", 0., .2, float(a["general"]["retirement_rate"]), .005)
        st.subheader("Compensation")
        c1,c2,c3 = st.columns(3); a["general"]["salary_increase"] = c1.slider("Salary growth", 0., .2, float(a["general"]["salary_increase"]), .005); a["pay"]["bonus_rate"] = c2.slider("Bonus percentage", 0., .5, float(a["pay"]["bonus_rate"]), .005); a["pay"]["payroll_tax_rate"] = c3.slider("Payroll tax rate", 0., .3, float(a["pay"]["payroll_tax_rate"]), .005)
        st.subheader("Benefits")
        c1,c2,c3,c4 = st.columns(4); a["health"]["health_trend"] = c1.slider("Medical trend", 0., .3, float(a["health"]["health_trend"]), .005); a["dc"]["employer_match_rate"] = c2.slider("Employer DC rate", 0., .2, float(a["dc"]["employer_match_rate"]), .005); a["pension"]["normal_cost_rate"] = c3.slider("Pension cost rate", 0., .3, float(a["pension"]["normal_cost_rate"]), .005); a["other"]["growth_rate"] = c4.slider("Other benefit trend", 0., .3, float(a["other"]["growth_rate"]), .005)
        with st.expander("Advanced assumptions"):
            c1,c2,c3 = st.columns(3); a["general"]["projection_years"] = c1.slider("Projection years", 5, 10, int(a["general"]["projection_years"])); a["general"]["start_year"] = c2.number_input("Start year", 2024, 2100, int(a["general"]["start_year"])); a["health"]["admin_per_employee"] = c3.number_input("Health admin fee / employee", 0., 5000., float(a["health"]["admin_per_employee"]))
        submitted = st.form_submit_button("Run projection", type="primary")
    if submitted: st.session_state.scenario = choice; run_projection(a); st.success("Projection updated."); st.rerun()
    if st.button("Reset to scenario defaults"): st.session_state.scenario = choice; run_projection(base); st.rerun()
    disclaimer()

elif page == "Scenario Comparison":
    annual, segment, detail = st.session_state.results
    page_header("Scenario Comparison", "Compare the cost path and assumptions across selected planning cases.")
    selected = st.multiselect("Compare up to three scenarios", list(SCENARIOS), default=["Baseline", "Cost Pressure", "Workforce Contraction"], max_selections=3)
    tables = [project(st.session_state.census, apply_scenario(default_assumptions(), name))[0].assign(scenario=name) for name in selected]
    scenarios = pd.concat(tables) if tables else pd.DataFrame()
    if scenarios.empty: st.info("Select at least one scenario to view the comparison.")
    else:
        summary = scenarios.groupby("scenario").agg(current_cost=("total_rewards","first"), final_year_cost=("total_rewards","last"), cumulative_cost=("total_rewards","sum")).reset_index(); summary["annualized_growth"] = (summary.final_year_cost / summary.current_cost) ** (1 / max(1, len(annual)-1)) - 1; base_cost = summary.loc[summary.scenario == "Baseline", "final_year_cost"].iloc[0] if "Baseline" in summary.scenario.values else summary.final_year_cost.iloc[0]; summary["difference_from_baseline"] = summary.final_year_cost - base_cost
        low, high = summary.cumulative_cost.min(), summary.cumulative_cost.max(); c1,c2,c3 = st.columns(3); c1.metric("Lowest cumulative cost", money(low)); c2.metric("Highest cumulative cost", money(high)); c3.metric("Largest final-year variance", money(summary.difference_from_baseline.abs().max()))
        fig=px.line(scenarios, x="year", y="total_rewards", color="scenario", markers=True); apply_chart_layout(fig, height=440, currency_axis=True); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary.style.format({"current_cost":"${:,.0f}","final_year_cost":"${:,.0f}","cumulative_cost":"${:,.0f}","annualized_growth":"{:.1%}","difference_from_baseline":"${:,.0f}"}), use_container_width=True, hide_index=True)
        st.subheader("Assumption differences")
        rows = []
        for label, path in [("Salary growth", ("general","salary_increase")), ("Workforce growth", ("general","workforce_growth")), ("Medical trend", ("health","health_trend")), ("Employer DC rate", ("dc","employer_match_rate")), ("Pension cost rate", ("pension","normal_cost_rate"))]:
            values = {name: apply_scenario(default_assumptions(), name)[path[0]][path[1]] for name in selected};
            if len(set(values.values())) > 1: rows.append({"Assumption":label, **values})
        st.dataframe(pd.DataFrame(rows).style.format({n:"{:.1%}" for n in selected}), use_container_width=True, hide_index=True)
        st.download_button("Download comparison workbook", build_export(annual, segment, detail, summary, st.session_state.warnings), "total_rewards_scenario_comparison.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        disclaimer()

else:
    annual, segment, detail = st.session_state.results
    page_header("Data & Methodology", "Review data status, validation checks, formulas, assumptions, and model limitations.")
    status_bar()
    with st.expander("Load or replace census data"):
        uploaded = st.file_uploader("Upload CSV or Excel census", type=["csv", "xlsx", "xls"])
        c1, c2 = st.columns(2)
        if c1.button("Load sample census", use_container_width=True):
            st.session_state.census = load_sample(); st.session_state.census_source = "Sample synthetic census"; st.session_state.census_version = SAMPLE_DATA_VERSION; run_projection(); st.rerun()
        if uploaded and c2.button("Use uploaded census", use_container_width=True):
            try:
                st.session_state.census = load_upload(uploaded); st.session_state.census_source = uploaded.name; st.session_state.census_version = SAMPLE_DATA_VERSION; run_projection(); st.success("Census loaded."); st.rerun()
            except Exception as exc:
                st.error(f"Could not load the census: {exc}")
    st.subheader("Data status")
    st.write(f"Source: {st.session_state.census_source} | Records: {len(st.session_state.census):,} | Projection status: Current | Model version: {MODEL_VERSION}")
    if st.session_state.warnings: st.warning("Validation warnings: " + " • ".join(st.session_state.warnings))
    else: st.success("Data checks passed.")
    st.subheader("Projection methodology")
    st.markdown("Pay grows annually; turnover and retirement are represented through an aggregate active factor; replacement hires are approximated at the population level; benefit eligibility, coverage tiers, and cost rates are applied record by record; annual results are then aggregated.")
    st.subheader("Core formulas")
    st.markdown("- Payroll = base pay + bonus + payroll taxes.\n- Defined contribution = eligible pay × contribution rate × participation.\n- Pension = covered pay × normal cost rate + administrative expense.\n- Health and welfare = tiered employer premium plus ancillary benefits and administration.\n- Total rewards = payroll + all benefit categories.")
    st.subheader("Scenario definitions")
    st.dataframe(pd.DataFrame({"Scenario":list(SCENARIOS), "Description":[v["description"] for v in SCENARIOS.values()]}), use_container_width=True, hide_index=True)
    st.subheader("Known limitations")
    st.markdown("This is a deterministic concept model, not an actuarial valuation. Pension, health-care, turnover, retirement, workforce replacement, and scenario attribution methods are simplified. Results should not be used for financial reporting, funding, pricing, or benefit decisions without independent review.")
    with st.expander("Current assumptions"): st.json(st.session_state.assumptions)
    disclaimer()
