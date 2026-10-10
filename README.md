# Market Intelligence & Opportunity Dashboard

A portfolio project for exploring market segments, comparing competitors,
tracking industry trends, and presenting explainable business opportunities.
The planned application will use FastAPI, Jinja2, Pandas, Plotly, and (if
persistence is needed) SQLite.

## Data disclosure

Initial market data will be **synthetic demo data** created for demonstrating
the application. It is fictional and must not be interpreted as verified
real-world market research. Any future real-world data should be identified
with its source and collection date.

## Planned features

- Market overview with KPI cards
- Market segment and trend analysis
- Competitor comparison
- Opportunity scoring with explainable inputs
- Interactive charts and filters
- CSV upload with validation and useful error messages
- Recommendations tied to displayed metrics
- API endpoints, automated tests, and a responsive dashboard

## Requirements

- Windows 11 with Python 3.13
- PowerShell
- Git

## Set up on Windows

Open PowerShell in the project folder. Create a virtual environment if one does
not already exist:

```powershell
py -3.13 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, you can use the virtual environment's
Python directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

With the environment activated, install the declared dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run locally

Start the local development server from the project folder with the virtual
environment activated:

```powershell
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/> for the landing page,
<http://127.0.0.1:8000/health> for the health check, and
<http://127.0.0.1:8000/api/v1/overview> for the illustrative synthetic
overview. FastAPI's interactive API documentation is at
<http://127.0.0.1:8000/docs>.

The dashboard page presents synthetic KPI cards, an interactive Plotly market
trend chart, fictional competitor profiles, and unranked opportunity themes.
Its search filters the displayed dashboard items. Data Import is marked as
planned and is not available in this phase. Plotly.js is loaded from its
version-matched CDN, so the interactive chart needs an internet connection.

## Run tests

Run the automated endpoint tests with:

```powershell
python -m pytest
```

## Project status

The dashboard interface, health check, and synthetic overview endpoint are
available. Database persistence, CSV uploads, and an opportunity-scoring
engine are planned for later, independently verifiable phases.
