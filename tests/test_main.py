import json
import re

import pytest
from fastapi.testclient import TestClient

from app.dashboard_data import (
    COMPETITORS,
    OPPORTUNITIES,
    OPPORTUNITY_SCORE_WEIGHTS,
    TREND_QUARTERS,
    TREND_VALUES,
    build_competitor_chart,
    build_market_trend_chart,
    calculate_market_trend_metrics,
    filter_competitors,
    filter_opportunities,
    score_opportunity,
    select_market_trend_range,
)
from app.data_import import MAX_DATA_ROWS, MAX_UPLOAD_BYTES, REQUIRED_COLUMNS, TEMPLATE_CSV
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


def test_opportunity_score_uses_all_documented_weights() -> None:
    scored = score_opportunity(OPPORTUNITIES[0])
    evidence = OPPORTUNITIES[0]["evidence"]
    expected_contributions = {
        factor: evidence[factor] * weight / 100
        for factor, weight in OPPORTUNITY_SCORE_WEIGHTS.items()
    }

    assert sum(OPPORTUNITY_SCORE_WEIGHTS.values()) == 100
    assert scored["contributions"] == expected_contributions
    assert scored["score"] == round(sum(expected_contributions.values())) == 79
    assert scored["strongest_factor"] == "demand_momentum"
    assert "Demand momentum contributes most" in scored["ranking_explanation"]


def test_opportunities_rank_and_sort_deterministically() -> None:
    ranked = filter_opportunities()

    assert [item["name"] for item in ranked] == [
        "Mid-market automation",
        "Regional insight tools",
        "Sustainability reporting",
    ]
    assert [item["score"] for item in ranked] == [79, 77, 72]
    assert [item["name"] for item in filter_opportunities(sort_by="score_asc")] == [
        "Sustainability reporting",
        "Regional insight tools",
        "Mid-market automation",
    ]
    assert [item["name"] for item in filter_opportunities(sort_by="name_asc")] == sorted(
        item["name"] for item in OPPORTUNITIES
    )


def test_opportunity_filters_match_search_category_and_score() -> None:
    result = filter_opportunities(
        query="regional",
        category="Market intelligence",
        minimum_score=75,
    )
    assert [item["name"] for item in result] == ["Regional insight tools"]
    assert filter_opportunities(minimum_score=80) == []


def test_opportunities_page_renders_scoring_factors_and_recommendations() -> None:
    response = client.get("/opportunities")

    assert response.status_code == 200
    assert "Opportunity Priorities" in response.text
    assert 'href="/opportunities" aria-current="page"' in response.text
    assert "not verified market research" in response.text
    assert "EXPLAINABLE MODEL" in response.text
    assert "Score = Σ" in response.text
    assert all(f"{weight}%" in response.text for weight in OPPORTUNITY_SCORE_WEIGHTS.values())
    assert all(item["name"] in response.text for item in OPPORTUNITIES)
    assert all(item["recommendation"] in response.text for item in OPPORTUNITIES)
    assert 'name="category"' in response.text
    assert 'name="minimum_score"' in response.text
    assert 'name="sort_by"' in response.text


def test_opportunities_route_applies_filters_and_sort_order() -> None:
    response = client.get(
        "/opportunities",
        params={"category": "Market intelligence", "minimum_score": 75, "sort_by": "score_asc"},
    )

    assert response.status_code == 200
    assert "Regional insight tools" in response.text
    assert "Mid-market automation" not in response.text
    assert "Sustainability reporting" not in response.text
    assert "77/100" in response.text


def test_opportunities_route_validates_filter_parameters() -> None:
    response = client.get("/opportunities", params={"minimum_score": 101})
    assert response.status_code == 422

    response = client.get("/opportunities", params={"sort_by": "unsupported"})
    assert response.status_code == 422


def test_data_import_page_renders_schema_workflow_and_creator_attribution() -> None:
    response = client.get("/data-import")

    assert response.status_code == 200
    assert "Upload market data" in response.text
    assert 'href="/data-import" aria-current="page"' in response.text
    assert 'id="dashboard-search"' not in response.text
    assert "not saved to the server" in response.text
    assert "are not shared with other dashboard pages" in response.text
    assert all(column in response.text for column in REQUIRED_COLUMNS)
    assert 'href="/data-import/template"' in response.text
    assert 'id="import-csv"' in response.text
    assert 'id="reset-import"' in response.text
    assert "Built by" in response.text
    assert "Aditi Ranjan" in response.text
    assert 'href="mailto:aditiranjan80@gmail.com"' in response.text
    assert 'href="https://github.com/AditiRanjan6" target="_blank" rel="noopener noreferrer"' in response.text
    assert 'href="https://www.linkedin.com/in/aditi-ranjan-51780b255/" target="_blank" rel="noopener noreferrer"' in response.text


def test_data_import_javascript_uses_safe_tab_scoped_import_and_reset() -> None:
    response = client.get("/static/js/dashboard.js")

    assert response.status_code == 200
    assert 'sessionStorage.setItem(storageKey' in response.text
    assert 'sessionStorage.removeItem(storageKey)' in response.text
    assert "cell.textContent = String(record[column] ?? \"\")" in response.text
    assert "Other dashboard pages continue to use synthetic demo data." in response.text


def test_data_import_validates_and_previews_csv_rows() -> None:
    response = client.post(
        "/data-import/validate",
        files={"file": ("segments.csv", TEMPLATE_CSV.encode(), "text/csv")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True
    assert result["columns"] == list(REQUIRED_COLUMNS)
    assert result["total_rows"] == 1
    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 0
    assert result["preview"] == [
        {
            "segment": "Example segment",
            "quarter": "Q1 '25",
            "market_size_usd_billions": 12.5,
            "growth_percent": 4.2,
        }
    ]


def test_data_import_reports_invalid_values_and_keeps_valid_rows() -> None:
    csv_content = (
        "segment,quarter,market_size_usd_billions,growth_percent\n"
        "Valid,Q1 '25,10.2,3.1\n"
        ",Q2 '25,not-a-number,NaN\n"
    )
    response = client.post(
        "/data-import/validate",
        files={"file": ("mixed.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total_rows"] == 2
    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 1
    assert result["preview"][0]["segment"] == "Valid"
    assert "Row 3" in result["errors"][0]
    assert "segment is required" in result["errors"][0]
    assert "market_size_usd_billions must be a number" in result["errors"][0]
    assert "growth_percent must be a number" in result["errors"][0]


@pytest.mark.parametrize(
    ("filename", "content", "expected_status", "message"),
    [
        ("segments.txt", b"not a CSV", 415, ".csv extension"),
        ("empty.csv", b"", 422, "file is empty"),
        (
            "missing-columns.csv",
            b"segment,quarter\nExample,Q1 '25\n",
            422,
            "Missing required columns",
        ),
        (
            "malformed.csv",
            b'segment,quarter,market_size_usd_billions,growth_percent\n"unterminated',
            422,
            "could not be parsed",
        ),
    ],
)
def test_data_import_rejects_unsupported_empty_missing_or_malformed_csv(
    filename: str,
    content: bytes,
    expected_status: int,
    message: str,
) -> None:
    response = client.post(
        "/data-import/validate",
        files={"file": (filename, content, "text/csv")},
    )

    assert response.status_code == expected_status
    assert message.lower() in response.json()["message"].lower()


def test_data_import_enforces_upload_size_limit() -> None:
    response = client.post(
        "/data-import/validate",
        files={"file": ("large.csv", b"x" * (MAX_UPLOAD_BYTES + 1), "text/csv")},
    )

    assert response.status_code == 413
    assert "upload limit" in response.json()["message"]


def test_data_import_enforces_row_limit() -> None:
    content = (
        "segment,quarter,market_size_usd_billions,growth_percent\n"
        + "Example,Q1 '25,10,2\n" * (MAX_DATA_ROWS + 1)
    ).encode()
    response = client.post(
        "/data-import/validate",
        files={"file": ("too-many-rows.csv", content, "text/csv")},
    )

    assert response.status_code == 422
    assert "5,000-row limit" in response.json()["message"]


def test_data_import_template_download_has_expected_schema() -> None:
    response = client.get("/data-import/template")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.text.startswith(",".join(REQUIRED_COLUMNS))


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
