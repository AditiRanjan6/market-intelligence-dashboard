"""FastAPI application entry point for the dashboard."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from plotly.offline import get_plotlyjs_version

from app.dashboard_data import (
    COMPETITORS,
    DEMO_OVERVIEW,
    OPPORTUNITIES,
    OPPORTUNITY_SCORE_WEIGHTS,
    TREND_QUARTERS,
    build_competitor_chart,
    calculate_market_trend_metrics,
    build_market_trend_chart,
    filter_competitors,
    filter_opportunities,
    select_market_trend_range,
)
from app.data_import import (
    MAX_DATA_ROWS,
    MAX_UPLOAD_BYTES,
    REQUIRED_COLUMNS,
    TEMPLATE_CSV,
    validate_csv_upload,
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


@app.get("/opportunities", response_class=HTMLResponse)
def opportunities_page(
    request: Request,
    q: str = "",
    category: str = "",
    minimum_score: int = Query(default=0, ge=0, le=100),
    sort_by: Literal["score_desc", "score_asc", "name_asc"] = "score_desc",
) -> HTMLResponse:
    """Render ranked synthetic opportunities with transparent score filters."""
    opportunities = filter_opportunities(q, category, minimum_score, sort_by)
    categories = sorted({item["category"] for item in OPPORTUNITIES})
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page": "opportunities",
            "overview": DEMO_OVERVIEW,
            "opportunities": opportunities,
            "opportunity_categories": categories,
            "opportunity_query": q,
            "opportunity_category": category,
            "minimum_score": minimum_score,
            "opportunity_sort_by": sort_by,
            "opportunity_score_weights": OPPORTUNITY_SCORE_WEIGHTS,
            "plotlyjs_version": get_plotlyjs_version(),
        },
    )


@app.get("/data-import", response_class=HTMLResponse)
def data_import_page(request: Request) -> HTMLResponse:
    """Render the tab-scoped CSV import workspace."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page": "data_import",
            "overview": DEMO_OVERVIEW,
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "max_upload_rows": MAX_DATA_ROWS,
            "required_columns": REQUIRED_COLUMNS,
            "plotlyjs_version": get_plotlyjs_version(),
        },
    )


@app.post("/data-import/validate")
async def validate_data_import(file: UploadFile = File(...)) -> Response:
    """Validate an uploaded CSV and return safe preview records and diagnostics."""
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        result = validate_csv_upload(file.filename or "", content)
    finally:
        await file.close()

    status_code = result.pop("status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@app.get("/data-import/template")
def download_data_import_template() -> Response:
    """Download a CSV containing the required import schema and example row."""
    return Response(
        content=TEMPLATE_CSV,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="market-data-template.csv"'
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
