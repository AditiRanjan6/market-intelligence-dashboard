import json
import re

import pytest
from fastapi.testclient import TestClient

from app.dashboard_data import (
    COMPETITORS,
    TREND_QUARTERS,
    TREND_VALUES,
    build_competitor_chart,
    build_market_trend_chart,
    calculate_market_trend_metrics,
    filter_competitors,
    select_market_trend_range,
)
from app.main import app

client = TestClient(app)


def test_home_returns_professional_landing_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Market Intelligence" in response.text
    assert "Market Trends" in response.text
    assert "Competitor Overview" in response.text
    assert "Top Opportunities" in response.text
    assert "Total Market Size" in response.text
    assert "Market Growth" in response.text
    assert "Competitors Tracked" in response.text
    assert "Opportunities Identified" in response.text
    assert "Data Import" in response.text
    assert "synthetic demo data" in response.text
    assert "not verified real-world market data" in response.text
    assert 'id="market-trend-chart"' in response.text
    assert "DEMO DATA" in response.text


def test_dashboard_static_assets_are_served() -> None:
    css_response = client.get("/static/css/dashboard.css")
    js_response = client.get("/static/js/dashboard.js")

    assert css_response.status_code == 200
    assert "prefers-reduced-motion" in css_response.text
    assert re.search(r"(?m)^svg\s*\{", css_response.text) is None
    assert ".brand-mark svg, .nav-link svg" in css_response.text
    assert js_response.status_code == 200
    assert ".newPlot(" in js_response.text
    assert "could not load" in js_response.text
    assert "could not be rendered" in js_response.text
    assert "ResizeObserver" in js_response.text
    assert "dashboard-search" in js_response.text


def test_market_trend_chart_has_visible_quarterly_line_configuration() -> None:
    figure = build_market_trend_chart()
    trace = figure["data"][0]
    x_axis = figure["layout"]["xaxis"]
    y_axis = figure["layout"]["yaxis"]

    assert trace["type"] == "scatter"
    assert trace["mode"] == "lines+markers"
    assert trace["x"] == TREND_QUARTERS
    assert trace["y"] == TREND_VALUES
    assert len(trace["x"]) == len(trace["y"])
    assert x_axis["tickmode"] == "array"
    assert x_axis["tickvals"] == TREND_QUARTERS
    assert x_axis["ticktext"] == TREND_QUARTERS
    assert y_axis["range"][0] < min(TREND_VALUES)
    assert y_axis["range"][1] > max(TREND_VALUES)
    assert y_axis["tickprefix"] == "$"
    assert y_axis["ticksuffix"] == "B"
    assert trace["hoverinfo"] == "skip"


def test_dashboard_serializes_market_trend_data_for_plotly() -> None:
    response = client.get("/")
    chart_data = re.search(
        r'<script id="trend-chart-data" type="application/json">(.*?)</script>',
        response.text,
        re.DOTALL,
    )

    assert chart_data is not None
    figure = json.loads(chart_data.group(1))
    assert figure["data"][0]["x"] == TREND_QUARTERS
    assert figure["data"][0]["y"] == TREND_VALUES
    assert figure["data"][0]["mode"] == "lines+markers"


def test_market_trends_page_renders_synthetic_series_and_summary() -> None:
    response = client.get("/market-trends")

    assert response.status_code == 200
    assert "Market Trends" in response.text
    assert "Demo data disclosure" in response.text
    assert "synthetic demo data only" in response.text
    assert "not verified real-world market data" in response.text
    assert 'action="/market-trends"' in response.text
    assert 'name="start_quarter"' in response.text
    assert 'name="end_quarter"' in response.text
    assert "+$8.3B" in response.text
    assert "+24.3%" in response.text
    assert "hoverinfo" in response.text


def test_market_trend_range_filter_updates_chart_and_metrics() -> None:
    response = client.get(
        "/market-trends",
        params={"start_quarter": "Q2 '24", "end_quarter": "Q4 '24"},
    )

    assert response.status_code == 200
    chart_data = re.search(
        r'<script id="trend-chart-data" type="application/json">(.*?)</script>',
        response.text,
        re.DOTALL,
    )
    assert chart_data is not None
    figure = json.loads(chart_data.group(1))
    assert figure["data"][0]["x"] == TREND_QUARTERS[1:4]
    assert figure["data"][0]["y"] == TREND_VALUES[1:4]
    assert "+$2.1B" in response.text
    assert "+6.0%" in response.text


def test_market_trend_metrics_are_derived_from_selected_data() -> None:
    quarters, values = select_market_trend_range("Q2 '24", "Q4 '24")

    assert quarters == TREND_QUARTERS[1:4]
    assert values == TREND_VALUES[1:4]
    assert calculate_market_trend_metrics(quarters, values) == {
        "start_quarter": "Q2 '24",
        "end_quarter": "Q4 '24",
        "start_value": 35.1,
        "end_value": 37.2,
        "absolute_change": pytest.approx(2.1),
        "percentage_change": pytest.approx(2.1 / 35.1 * 100),
    }


def test_market_trend_filter_rejects_reversed_quarter_range() -> None:
    response = client.get(
        "/market-trends",
        params={"start_quarter": "Q3 '25", "end_quarter": "Q1 '25"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The start quarter must not be later than the end quarter."


def test_competitors_page_renders_synthetic_profiles_and_comparison_chart() -> None:
    response = client.get("/competitors")

    assert response.status_code == 200
    assert "Competitor Comparison" in response.text
    assert "six fictional profiles" in response.text
    assert "not verified real-world research" in response.text
    assert 'href="/competitors" aria-current="page"' in response.text
    assert 'id="competitor-share-chart"' in response.text
    assert all(competitor["name"] in response.text for competitor in COMPETITORS)
    assert all(f'{competitor["share"]}%' in response.text for competitor in COMPETITORS)


def test_competitor_profiles_and_chart_use_all_synthetic_records() -> None:
    assert len(COMPETITORS) == 6
    figure = build_competitor_chart(COMPETITORS)
    trace = figure["data"][0]

    assert trace["type"] == "bar"
    assert trace["orientation"] == "h"
    assert trace["y"] == [competitor["name"] for competitor in COMPETITORS]
    assert trace["x"] == [competitor["share"] for competitor in COMPETITORS]
    assert trace["customdata"] == [competitor["category"] for competitor in COMPETITORS]
    assert "Illustrative market share: %{x:.0f}%" in trace["hovertemplate"]


def test_competitor_search_filters_profiles_and_chart() -> None:
    response = client.get("/competitors", params={"q": "Northstar Analytics"})

    assert response.status_code == 200
    assert "Northstar Analytics" in response.text
    assert "BluePeak Intelligence" not in response.text
    chart_data = re.search(
        r'<script id="competitor-chart-data" type="application/json">(.*?)</script>',
        response.text,
        re.DOTALL,
    )
    assert chart_data is not None
    figure = json.loads(chart_data.group(1))
    assert figure["data"][0]["y"] == ["Northstar Analytics"]
    assert figure["data"][0]["x"] == [24]


def test_competitor_search_can_match_category_or_return_no_results() -> None:
    assert [entry["name"] for entry in filter_competitors("market research")] == [
        "BluePeak Intelligence"
    ]
    response = client.get("/competitors", params={"q": "no such company"})

    assert response.status_code == 200
    assert "No synthetic competitor profiles match" in response.text
    chart_data = re.search(
        r'<script id="competitor-chart-data" type="application/json">(.*?)</script>',
        response.text,
        re.DOTALL,
    )
    assert chart_data is not None
    assert json.loads(chart_data.group(1))["data"][0]["x"] == []


def test_health_returns_healthy_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_overview_returns_labelled_synthetic_demo_data() -> None:
    response = client.get("/api/v1/overview")

    assert response.status_code == 200
    overview = response.json()
    assert overview["data_type"] == "synthetic_demo_data"
    assert overview["market_size_usd_billions"] > 0
    assert overview["year_over_year_growth_percent"] > 0
    assert overview["segments_tracked"] > 0
    assert overview["competitors_tracked"] > 0
    assert "synthetic demo data" in overview["disclosure"]
    assert "not verified real-world market data" in overview["disclosure"]
