#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import requests
import pandas as pd

REQUEST_URL = (
    "https://www.dunkest.com/api/stats/table?season_id=17&mode=nba&stats_type=tot"
    "&weeks%5B%5D=43&rounds%5B%5D=1"
    "&teams%5B%5D=31&teams%5B%5D=32&teams%5B%5D=33&teams%5B%5D=34&teams%5B%5D=35"
    "&teams%5B%5D=36&teams%5B%5D=37&teams%5B%5D=38&teams%5B%5D=39&teams%5B%5D=40"
    "&teams%5B%5D=41&teams%5B%5D=42&teams%5B%5D=43&teams%5B%5D=44&teams%5B%5D=45"
    "&teams%5B%5D=47&teams%5B%5D=48&teams%5B%5D=60"
    "&positions%5B%5D=1&positions%5B%5D=2&positions%5B%5D=3"
    "&player_search=&min_cr=4&max_cr=35&sort_by=pdk&sort_order=desc&iframe=yes"
    "&date_from=2024-10-03&date_to=2025-05-31"
)

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
}

RAW_OUT = "players_raw.csv"
PRETTY_OUT = "players_pretty.csv"


def fetch_rows(url: str) -> list[dict]:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    if isinstance(data, list):
        return data
    return []


def to_float(x) -> float:
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return 0.0


def norm_pos(p: str) -> str:
    p = (p or "").upper()
    if "C" in p: return "C"
    if "F" in p: return "F"
    return "G"


def make_pretty_csv(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Ασφαλείς προσβάσεις
    first = df.get("first_name", "").astype(str).str.strip()
    last  = df.get("last_name", "").astype(str).str.strip()
    team_code = df.get("team_code", "").astype(str)
    team_name = df.get("team_name", "").astype(str)
    pos  = df.get("position", "").astype(str)

    out = pd.DataFrame()
    out["name"] = (first + " " + last).str.strip()
    out["team_code"] = team_code
    out["team_name"] = team_name
    out["pos"] = pos.map(norm_pos)

    # credits = cr ως float (στο mode=nba συνήθως 0.0 — το κρατάμε όπως είναι)
    out["credits"] = df.get("cr", 0).map(to_float)

    # min_proj = συνολικά λεπτά / αγώνες
    gp = df.get("gp", 0).map(to_float).replace(0, pd.NA)
    minutes_total = df.get("min", 0).map(to_float)
    out["min_proj"] = (minutes_total / gp).fillna(0).round(2)

    # Μερικά core stats (όπως είναι στο feed)
    for col in ["pts", "reb", "ast", "stl", "blk", "tov", "pdk"]:
        out[col] = df.get(col, 0).map(to_float)

    # Προαιρετικά κράτα και raw gp/min για αναφορά
    out["gp"] = df.get("gp", 0).map(to_float)
    out["min_total"] = minutes_total

    # Φιλτράρουμε άδειες εγγραφές
    out = out[(out["name"] != "") & (out["team_code"] != "")]
    out = out.drop_duplicates(subset=["name", "team_code"], keep="first")

    # Σειρά στηλών
    cols = [
        "name", "team_code", "team_name", "pos",
        "credits", "min_proj",
        "pts", "reb", "ast", "stl", "blk", "tov",
        "pdk", "gp", "min_total"
    ]
    return out[cols]


def main() -> int:
    rows = fetch_rows(REQUEST_URL)

    # 1) RAW 1:1
    pd.DataFrame(rows).to_csv(RAW_OUT, index=False, encoding="utf-8")
    print(f"✅ Saved {RAW_OUT} with {len(rows)} rows (ALL FIELDS as returned).")

    # 2) PRETTY (προαιρετικό, για πιο καθαρή κατανάλωση)
    pretty_df = make_pretty_csv(rows)
    pretty_df.to_csv(PRETTY_OUT, index=False, encoding="utf-8")
    print(f"✅ Saved {PRETTY_OUT} with {len(pretty_df)} rows (tidy, includes credits/min_proj).")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
