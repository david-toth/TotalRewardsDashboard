import plotly.graph_objects as go
from config.design import COST_COLORS, CATEGORY_LABELS

def apply_chart_layout(fig, title=None, height=420, currency_axis=False, percent_axis=False):
    fig.update_layout(title=None if title is None else {"text": title, "x": 0, "xanchor": "left"}, height=height, margin={"l": 16, "r": 16, "t": 30, "b": 16}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"family":"Arial", "color":"#1F2933", "size":12}, legend={"orientation":"h", "y":1.08, "x":0}, hovermode="x unified")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EAECF0", zeroline=False, tickformat="$,.0f" if currency_axis else ".1%" if percent_axis else ",.0f")
    return fig

def projection_area(annual):
    fig = go.Figure()
    for col in ["base_pay", "incentive_pay", "defined_contribution", "pension", "health_welfare", "other_benefits"]:
        fig.add_trace(go.Scatter(x=annual.year, y=annual[col], name=CATEGORY_LABELS[col], stackgroup="one", mode="lines", line={"width":0.5, "color":COST_COLORS[CATEGORY_LABELS[col]]}, fillcolor=COST_COLORS[CATEGORY_LABELS[col]]))
    fig.add_trace(go.Scatter(x=annual.year, y=annual.total_rewards, name="Total Rewards", mode="lines+markers", line={"color":"#111827", "width":3}))
    return apply_chart_layout(fig, height=470, currency_axis=True)

def cost_driver_waterfall(drivers):
    fig = go.Figure(go.Waterfall(x=list(drivers.keys()), y=list(drivers.values()), measure=["relative"] * (len(drivers)-1) + ["total"], connector={"line":{"color":"#98A2B3"}}, increasing={"marker":{"color":"#2A9D8F"}}, decreasing={"marker":{"color":"#E76F51"}}, totals={"marker":{"color":"#264653"}}))
    return apply_chart_layout(fig, height=390, currency_axis=True)
