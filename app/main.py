"""FastAPI application entry point for the dashboard."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from plotly.offline import get_plotlyjs_version

from app.dashboard_data import (
    COMPETITORS,
    DEMO_OVERVIEW,
    OPPORTUNITIES,
    TREND_QUARTERS,
    TREND_VALUES,
    build_competitor_chart,
    calculate_market_trend_metrics,
    build_market_trend_chart,
    filter_competitors,
    select_market_trend_range,
)

APP_DIRECTORY = Path(__file__).resolve().parent

app = FastAPI(
    title="Market Intelligence & Opportunity Dashboard",
    description="A portfolio project for exploring market insights and opportunities.",
    version="0.1.0",
)
app.mount(
    "/static",
    StaticFiles(directory=APP_DIRECTORY / "static"),
    name="static",
)
templates = Jinja2Templates(directory=APP_DIRECTORY / "templates")


class HealthResponse(BaseModel):
    status: Literal["healthy"]


class MarketOverview(BaseModel):
    data_type: Literal["synthetic_demo_data"]
    market_size_usd_billions: float
    year_over_year_growth_percent: float
    segments_tracked: int
    competitors_tracked: int
    disclosure: str


@app.get("/")
def home(request: Request) -> HTMLResponse:
    """Render the dashboard interface using the labelled demo content."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page": "overview",
            "overview": DEMO_OVERVIEW,
            "competitors": COMPETITORS,
            "opportunities": OPPORTUNITIES,
            "trend_chart": build_market_trend_chart(),
            "plotlyjs_version": get_plotlyjs_version(),
        },
    )


@app.get("/market-trends", response_class=HTMLResponse)
def market_trends(
    request: Request,
    start_quarter: str = TREND_QUARTERS[0],
    end_quarter: str = TREND_QUARTERS[-1],
) -> HTMLResponse:
    """Render the interactive synthetic market-trends analysis page."""
    try:
        quarters, values = select_market_trend_range(start_quarter, end_quarter)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page": "trends",
            "overview": DEMO_OVERVIEW,
            "trend_chart": build_market_trend_chart(quarters, values),
            "trend_metrics": calculate_market_trend_metrics(quarters, values),
            "trend_quarters": TREND_QUARTERS,
            "start_quarter": quarters[0],
            "end_quarter": quarters[-1],
            "plotlyjs_version": get_plotlyjs_version(),
        },
    )


@app.get("/competitors", response_class=HTMLResponse)
def competitors_page(request: Request, q: str = "") -> HTMLResponse:
    """Render and filter the synthetic competitor comparison page."""
    competitors = filter_competitors(q)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page": "competitors",
            "overview": DEMO_OVERVIEW,
            "competitors": competitors,
            "competitor_chart": build_competitor_chart(competitors),
            "competitor_query": q,
            "plotlyjs_version": get_plotlyjs_version(),
        },
    )


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report that the application process is responding."""
    return HealthResponse(status="healthy")


@app.get("/api/v1/overview", response_model=MarketOverview)
def get_market_overview() -> MarketOverview:
    """Return illustrative figures to demonstrate the overview API shape."""
    return MarketOverview(
        data_type="synthetic_demo_data",
        market_size_usd_billions=42.5,
        year_over_year_growth_percent=8.2,
        segments_tracked=4,
        competitors_tracked=6,
        disclosure=(
            "Illustrative synthetic demo data only; these figures are not "
            "verified real-world market data."
        ),
    )
