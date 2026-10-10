"""Clearly labelled synthetic content for the dashboard interface."""

import json
from typing import Any

import plotly.graph_objects as go

DEMO_DISCLOSURE = (
    "synthetic demo data only. All figures are illustrative and are not "
    "verified real-world market data."
)

DEMO_OVERVIEW = {
    "market_size_usd_billions": 42.5,
    "year_over_year_growth_percent": 8.2,
    "competitors_tracked": 6,
    "opportunities_identified": 12,
    "data_type": "synthetic_demo_data",
    "disclosure": DEMO_DISCLOSURE,
}

TREND_QUARTERS = [
    "Q1 '24",
    "Q2 '24",
    "Q3 '24",
    "Q4 '24",
    "Q1 '25",
    "Q2 '25",
    "Q3 '25",
    "Q4 '25",
]
TREND_VALUES = [34.2, 35.1, 36.0, 37.2, 38.4, 39.6, 41.0, 42.5]

COMPETITORS = [
    {"name": "Northstar Analytics", "category": "Enterprise insights", "share": 24},
    {"name": "Meridian Systems", "category": "Data platforms", "share": 19},
    {"name": "BluePeak Intelligence", "category": "Market research", "share": 16},
    {"name": "Atlas Signal Group", "category": "Growth analytics", "share": 12},
    {"name": "Cedarline Metrics", "category": "Retail analytics", "share": 9},
    {"name": "Summit Research Labs", "category": "Industry intelligence", "share": 7},
]

OPPORTUNITIES = [
    {
        "name": "Mid-market automation",
        "segment": "Operations software",
        "signal": "Rising segment demand",
    },
    {
        "name": "Regional insight tools",
        "segment": "Local commerce",
        "signal": "Limited competitor coverage",
    },
    {
        "name": "Sustainability reporting",
        "segment": "Enterprise analytics",
        "signal": "Emerging buyer need",
    },
]


def select_market_trend_range(
    start_quarter: str,
    end_quarter: str,
) -> tuple[list[str], list[float]]:
    """Return the inclusive quarter range, rejecting unknown or reversed bounds."""
    try:
        start_index = TREND_QUARTERS.index(start_quarter)
        end_index = TREND_QUARTERS.index(end_quarter)
    except ValueError as error:
        raise ValueError("Select a valid quarter range.") from error

    if start_index > end_index:
        raise ValueError("The start quarter must not be later than the end quarter.")

    return (
        TREND_QUARTERS[start_index : end_index + 1],
        TREND_VALUES[start_index : end_index + 1],
    )


def filter_competitors(query: str) -> list[dict[str, str | int]]:
    """Match competitor profiles by name, category, or illustrative share."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return COMPETITORS.copy()

    return [
        competitor
        for competitor in COMPETITORS
        if normalized_query
        in " ".join(str(value) for value in competitor.values()).casefold()
    ]


def build_competitor_chart(
    competitors: list[dict[str, str | int]],
) -> dict[str, Any]:
    """Build a Plotly comparison chart for the selected synthetic profiles."""
    names = [str(competitor["name"]) for competitor in competitors]
    shares = [int(competitor["share"]) for competitor in competitors]
    categories = [str(competitor["category"]) for competitor in competitors]
    figure = go.Figure(
        go.Bar(
            x=shares,
            y=names,
            customdata=categories,
            orientation="h",
            marker={"color": "#287d78"},
            text=[f"{share}%" for share in shares],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>%{customdata}<br>"
                "Illustrative market share: %{x:.0f}%<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        autosize=True,
        margin={"l": 12, "r": 45, "t": 8, "b": 32},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#52606d"},
        xaxis={
            "title": {"text": "Illustrative market share (%)", "font": {"size": 11}},
            "range": [0, max(shares, default=1) * 1.25],
            "ticksuffix": "%",
            "gridcolor": "#edf1f5",
            "fixedrange": True,
            "tickfont": {"size": 10},
        },
        yaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": names[::-1],
            "automargin": True,
            "fixedrange": True,
            "tickfont": {"size": 10},
        },
    )
    return json.loads(figure.to_json())


def calculate_market_trend_metrics(
    quarters: list[str],
    values: list[float],
) -> dict[str, float | str]:
    """Calculate the change across a selected synthetic quarterly range."""
    if not quarters or len(quarters) != len(values):
        raise ValueError("At least one matching quarter and value is required.")

    first_value = values[0]
    last_value = values[-1]
    absolute_change = last_value - first_value
    percentage_change = absolute_change / first_value * 100
    return {
        "start_quarter": quarters[0],
        "end_quarter": quarters[-1],
        "start_value": first_value,
        "end_value": last_value,
        "absolute_change": absolute_change,
        "percentage_change": percentage_change,
    }


def build_market_trend_chart(
    quarters: list[str] | None = None,
    values: list[float] | None = None,
) -> dict[str, Any]:
    """Build the responsive Plotly chart from synthetic quarterly values."""
    quarters = TREND_QUARTERS if quarters is None else quarters
    values = TREND_VALUES if values is None else values
    lowest_value = min(values)
    highest_value = max(values)
    value_padding = max((highest_value - lowest_value) * 0.15, 1.0)

    figure = go.Figure(
        go.Scatter(
            x=quarters,
            y=values,
            mode="lines+markers",
            name="Illustrative market size",
            line={"color": "#287d78", "width": 3, "shape": "spline"},
            marker={"size": 7, "color": "#287d78"},
            hoverinfo="skip",
        )
    )
    figure.update_layout(
        autosize=True,
        margin={"l": 12, "r": 12, "t": 12, "b": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#52606d"},
        xaxis={
            "type": "category",
            "tickmode": "array",
            "tickvals": quarters,
            "ticktext": quarters,
            "tickangle": -25,
            "automargin": True,
            "showgrid": False,
            "fixedrange": True,
            "linecolor": "#d9e2ec",
            "tickfont": {"size": 11},
        },
        yaxis={
            "title": {"text": "Illustrative market size (USD billions)", "font": {"size": 11}},
            "range": [
                lowest_value - value_padding,
                highest_value + value_padding,
            ],
            "gridcolor": "#edf1f5",
            "fixedrange": True,
            "tickprefix": "$",
            "ticksuffix": "B",
            "tickformat": ".1f",
            "tickfont": {"size": 11},
        },
    )
    return json.loads(figure.to_json())
