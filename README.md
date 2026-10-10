# Market Intelligence & Opportunity Dashboard

A portfolio project for exploring market segments, comparing competitors,
tracking industry trends, presenting explainable business opportunities, and
validating CSV market data. It uses FastAPI, Jinja2, Pandas, and Plotly.

## Data disclosure

Initial market data will be **synthetic demo data** created for demonstrating
the application. It is fictional and must not be interpreted as verified
real-world market research. Any future real-world data should be identified
with its source and collection date.

## Features

- Market overview with synthetic KPI cards
- Quarterly market trend analysis with range filters and derived summaries
- Searchable synthetic competitor comparisons
- Explainable synthetic opportunity scores, filters, and recommendations
- CSV upload, schema validation, row-level feedback, and a preview
- Downloadable CSV schema template
- Health and synthetic overview API endpoints
- Responsive dashboard and automated tests

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

The dashboard pages present synthetic KPI cards, a quarterly Plotly trend
chart, fictional competitor profiles, and transparently scored opportunity
themes. Plotly.js is loaded from its version-matched CDN, so interactive charts
need an internet connection.

## CSV Data Import

The Data Import page accepts UTF-8 `.csv` files up to 2 MB and 5,000 data rows.
The required columns are `segment`, `quarter`, `market_size_usd_billions`, and
`growth_percent`. Quarter values use a format such as `Q1 '25`; market size
must be positive, and numeric fields must contain finite numbers. Additional
columns are retained as text. Validation reports detected columns, row totals,
row-level errors, and a preview of valid rows. Download the template from the
page for a ready-made example.

Valid rows can be imported into the current browser tab's `sessionStorage`.
They are not persisted on the server, shared with another user, or connected
to the Overview, Market Trends, Competitors, or Opportunities pages. Reset
clears this tab's import. Do not upload sensitive data. Uploaded cell contents
are treated as untrusted text and are never executed.

## Creator

Built by Aditi Ranjan. See the LinkedIn and GitHub profile links in the
dashboard sidebar, or email <aditiranjan80@gmail.com>.

## Run tests

Run the automated endpoint tests with:

```powershell
python -m pytest
```

## Project status

This is a portfolio demonstration. Market statistics, competitor profiles,
and opportunities displayed outside the CSV workspace are synthetic and are
not verified real-world research. The application does not currently use
database persistence or external market data.
