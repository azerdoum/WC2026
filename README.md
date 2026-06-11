# World Cup 2026 Family Schedule

A simple World Cup 2026 schedule site for checking match dates, teams, groups, host cities, and stadiums.

The site supports search, filters, table/card views, team color accents, and saved favorite matches in each visitor's browser.

## Preview Locally

Serve the folder from the repo root:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Data

The page reads generated match data when available and falls back to `Schedule 2026(Schedule).csv`.

Times are shown as listed in the schedule data.
