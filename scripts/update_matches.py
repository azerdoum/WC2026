from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_COMPETITION = "WC"
DEFAULT_SEASON = "2026"
FINALIZATION_DATES = {
    "2026-06-28": "Round of 32 field finalized after group stage",
    "2026-07-04": "Round of 16 field finalized after Round of 32",
    "2026-07-08": "Quarterfinal field finalized after Round of 16",
    "2026-07-12": "Semifinal field finalized after quarterfinals",
    "2026-07-16": "Final and third-place matchups finalized after semifinals",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update matches.json from football-data.org.")
    parser.add_argument("--force", action="store_true", help="Update even when today is not a finalization date.")
    parser.add_argument("--out", default="matches.json", help="Output JSON file.")
    parser.add_argument("--csv-fallback", default="Schedule 2026(Schedule).csv", help="CSV used if API has no useful data.")
    parser.add_argument("--timezone", default=os.getenv("MATCH_DISPLAY_TZ", "America/New_York"))
    args = parser.parse_args()

    tz = ZoneInfo(args.timezone)
    today = datetime.now(tz).date().isoformat()

    if not args.force and today not in FINALIZATION_DATES:
        print(f"Skipping update: {today} is not a configured finalization date.")
        print("Configured dates:")
        for date, reason in FINALIZATION_DATES.items():
            print(f"- {date}: {reason}")
        return 0

    token = os.getenv("FOOTBALL_DATA_TOKEN")
    if not token:
        print("FOOTBALL_DATA_TOKEN is not set.", file=sys.stderr)
        return 1

    competition = os.getenv("FOOTBALL_DATA_COMPETITION", DEFAULT_COMPETITION)
    season = os.getenv("FOOTBALL_DATA_SEASON", DEFAULT_SEASON)
    payload = fetch_football_data(token, competition, season)
    matches = [normalize_api_match(match, tz) for match in payload.get("matches", [])]
    matches = [match for match in matches if match["home"] and match["away"]]

    if not matches:
        print("API returned no matches; using CSV fallback.")
        matches = read_csv_matches(Path(args.csv_fallback), tz)

    output = {
        "source": "football-data.org",
        "competition": payload.get("competition", {}).get("name", "FIFA World Cup"),
        "season": season,
        "updatedAt": datetime.now(tz).isoformat(timespec="seconds"),
        "timezone": args.timezone,
        "matches": sorted(matches, key=lambda match: match.get("utcDate", "")),
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(output['matches'])} matches to {out_path}")
    return 0


def fetch_football_data(token: str, competition: str, season: str) -> dict:
    url = f"https://api.football-data.org/v4/competitions/{competition}/matches?season={season}"
    request = urllib.request.Request(url, headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"football-data.org returned HTTP {error.code}: {body}") from error


def normalize_api_match(match: dict, tz: ZoneInfo) -> dict:
    utc_date = match.get("utcDate") or ""
    kickoff = datetime.fromisoformat(utc_date.replace("Z", "+00:00")).astimezone(tz) if utc_date else None
    home_team = match.get("homeTeam") or {}
    away_team = match.get("awayTeam") or {}
    score = match.get("score") or {}
    full_time = score.get("fullTime") or {}
    stage = humanize(match.get("stage") or "")
    group = humanize(match.get("group") or "")

    home = clean_team_name(home_team.get("shortName") or home_team.get("name") or "TBD")
    away = clean_team_name(away_team.get("shortName") or away_team.get("name") or "TBD")
    venue = match.get("venue") or {}
    stadium = venue.get("name") if isinstance(venue, dict) else ""
    city = venue.get("city") if isinstance(venue, dict) else ""

    date_text = format_date(kickoff) if kickoff else ""
    time_text = format_time(kickoff) if kickoff else ""

    return {
        "id": match.get("id"),
        "key": f"{match.get('id') or ''}|{utc_date}|{home}|{away}",
        "date": date_text,
        "time": time_text,
        "utcDate": utc_date,
        "home": home,
        "away": away,
        "stage": stage,
        "group": group,
        "stadium": stadium or "",
        "city": city or "",
        "status": match.get("status") or "SCHEDULED",
        "homeScore": full_time.get("home"),
        "awayScore": full_time.get("away"),
    }


def read_csv_matches(path: Path, tz: ZoneInfo) -> list[dict]:
    if not path.exists():
        return []

    matches = []
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        for index, row in enumerate(csv.DictReader(csv_file)):
            if not row.get("Date") or not row.get("Team (Home)") or not row.get("Team (Away)"):
                continue
            matches.append({
                "id": index,
                "key": "|".join([
                    row.get("Date", ""),
                    row.get("Time", ""),
                    row.get("Team (Home)", ""),
                    row.get("Team (Away)", ""),
                    row.get("Stadium", ""),
                ]),
                "date": row.get("Date", ""),
                "time": row.get("Time", ""),
                "utcDate": "",
                "home": row.get("Team (Home)", ""),
                "away": row.get("Team (Away)", ""),
                "stage": row.get("Stage", ""),
                "group": row.get("Group", ""),
                "stadium": row.get("Stadium", ""),
                "city": row.get("City", ""),
                "status": "SCHEDULED",
                "homeScore": None,
                "awayScore": None,
            })
    return matches


def clean_team_name(name: str) -> str:
    replacements = {
        "Korea Republic": "Korea Republic",
        "Türkiye": "Turkiye",
        "Iran": "IR Iran",
        "USA": "USA",
    }
    return replacements.get(name, name)


def humanize(value: str) -> str:
    if not value:
        return ""
    return value.replace("_", " ").title()


def format_date(value: datetime) -> str:
    return f"{value:%A} {value.day} {value:%B %Y}"


def format_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


if __name__ == "__main__":
    raise SystemExit(main())
