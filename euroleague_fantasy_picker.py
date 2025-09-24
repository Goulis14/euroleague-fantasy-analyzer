#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import math
import pandas as pd

RAW_FILE = "players_raw.csv"
OUT_DIR  = "out"

# --- Ρυθμίσεις επιλογών ---
TOP_N_PER_POS          = 10   # πόσους να εμφανίζω ανά θέση στους πίνακες
CHEAP_MAX_CREDITS      = 8.0  # όριο για "φθηνά διαμαντάκια"
PREMIUM_MIN_CREDITS    = 15.0 # όριο για "πρωτοκλασάτους"
TEAM_SHAPE             = {"G": 4, "F": 4, "C": 4}  # προτεινόμενη 12άδα

def to_float(x, default=0.0):
    try:
        s = str(x).strip().replace(",", ".")
        return float(s) if s not in ("", "None", "nan") else default
    except Exception:
        return default

def norm_pos(p: str) -> str:
    p = (p or "").upper()
    if "C" in p: return "C"
    if "F" in p: return "F"
    return "G"

def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Ασφαλής μετατροπή βασικών πεδίων
    df["credits"] = df.get("cr", 0).map(lambda x: to_float(x, 0.0))
    df["pdk"]     = df.get("pdk", 0).map(lambda x: to_float(x, 0.0))
    df["gp"]      = df.get("gp", 0).map(lambda x: to_float(x, 0.0))
    df["min"]     = df.get("min", 0).map(lambda x: to_float(x, 0.0))
    # Όνομα/ομάδα/θέση
    first = df.get("first_name", "").astype(str).str.strip()
    last  = df.get("last_name", "").astype(str).str.strip()
    df["name"] = (first + " " + last).str.strip()
    df["team_code"] = df.get("team_code", df.get("team_name", "")).astype(str)
    df["team_name"] = df.get("team_name", "").astype(str)
    df["pos"] = df.get("position", "").astype(str).map(norm_pos)
    # Χρήσιμα rates
    df["eff_per_credit"] = df.apply(lambda r: (r["pdk"] / r["credits"]) if r["credits"] > 0 else 0.0, axis=1)
    df["eff_per_game"]   = df.apply(lambda r: (r["pdk"] / r["gp"]) if r["gp"] > 0 else 0.0, axis=1)
    df["min_per_game"]   = df.apply(lambda r: (r["min"] / r["gp"]) if r["gp"] > 0 else 0.0, axis=1)
    # core stats (αν υπάρχουν)
    for col in ["pts","reb","ast","stl","blk","tov"]:
        if col in df.columns:
            df[col] = df[col].map(lambda x: to_float(x, 0.0))
        else:
            df[col] = 0.0
    # καθάρισμα κενών
    df = df[(df["name"] != "") & (df["team_code"] != "")]
    df = df.drop_duplicates(subset=["name","team_code"], keep="first")
    return df

def top_by_position(df: pd.DataFrame, metric: str, top_n: int) -> dict:
    out = {}
    for pos in ["G","F","C"]:
        sub = df[df["pos"] == pos].sort_values(metric, ascending=False).head(top_n)
        out[pos] = sub
    return out

def save_table(df: pd.DataFrame, name: str):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8")
    return path

def print_table(title: str, df: pd.DataFrame, cols: list[str], max_rows: int = 20):
    print(f"\n=== {title} ===")
    print(df[cols].head(max_rows).to_string(index=False))

def build_recap_cols(include_eff=True):
    cols = ["name","pos","team_code","credits","pdk","gp","min_per_game"]
    if include_eff:
        cols.insert(5, "eff_per_credit")
        cols.insert(6, "eff_per_game")
    return cols

def main():
    df = load_raw(RAW_FILE)
    recap_cols = build_recap_cols()

    # 1) Καλύτεροι σε κάθε θέση (με βάση το pdk)
    best_pos = top_by_position(df, metric="pdk", top_n=TOP_N_PER_POS)
    frames = []
    for pos, sub in best_pos.items():
        fname = save_table(sub[recap_cols], f"best_{pos}.csv")
        print_table(f"Καλύτεροι {pos} (pdk)", sub, recap_cols)
        frames.append(sub.assign(category=f"Best {pos} by pdk"))
    save_table(pd.concat(frames, ignore_index=True)[recap_cols + ["category"]], "best_by_pos_all.csv")

    # 2) Καλύτεροι value (pdk/credits) ανά θέση — αγνοούμε credits<=0
    df_value = df[df["credits"] > 0]
    best_value_pos = top_by_position(df_value, metric="eff_per_credit", top_n=TOP_N_PER_POS)
    frames = []
    for pos, sub in best_value_pos.items():
        fname = save_table(sub[recap_cols], f"value_{pos}.csv")
        print_table(f"Value {pos} (pdk/credits)", sub, recap_cols)
        frames.append(sub.assign(category=f"Value {pos}"))
    save_table(pd.concat(frames, ignore_index=True)[recap_cols + ["category"]], "value_by_pos_all.csv")

    # 3) Φθηνά διαμαντάκια (credits <= CHEAP_MAX_CREDITS) — συνολικά & ανά θέση
    gems_all = df_value[df_value["credits"] <= CHEAP_MAX_CREDITS].sort_values(["pdk","eff_per_credit"], ascending=False).head(50)
    save_table(gems_all[recap_cols], "gems_overall.csv")
    print_table(f"Φθηνά διαμαντάκια (credits ≤ {CHEAP_MAX_CREDITS})", gems_all, recap_cols, max_rows=20)

    frames = []
    for pos in ["G","F","C"]:
        gems_pos = (df_value[(df_value["pos"] == pos) & (df_value["credits"] <= CHEAP_MAX_CREDITS)]
                    .sort_values(["pdk","eff_per_credit"], ascending=False)
                    .head(TOP_N_PER_POS))
        save_table(gems_pos[recap_cols], f"gems_{pos}.csv")
        print_table(f"Φθηνά διαμαντάκια {pos}", gems_pos, recap_cols)
        frames.append(gems_pos.assign(category=f"Gems {pos}"))
    save_table(pd.concat(frames, ignore_index=True)[recap_cols + ["category"]], "gems_by_pos_all.csv")

    # 4) Πρωτοκλασάτοι (credits ≥ PREMIUM_MIN_CREDITS)
    premium = df_value[df_value["credits"] >= PREMIUM_MIN_CREDITS].sort_values("pdk", ascending=False).head(50)
    save_table(premium[recap_cols], "premium_stars.csv")
    print_table(f"Πρωτοκλασάτοι (credits ≥ {PREMIUM_MIN_CREDITS})", premium, recap_cols, max_rows=20)

    # 5) Προτεινόμενη 12άδα: 4G, 4F, 4C βάσει value (eff_per_credit),
    #    με μικρό tie-break στο pdk και min_per_game για ρεαλισμό
    team_rows = []
    for pos, count in TEAM_SHAPE.items():
        pool = df_value[df_value["pos"] == pos].copy()
        pool = pool.sort_values(["eff_per_credit","pdk","min_per_game"], ascending=False).head(max(count*5, count))
        pick = pool.head(count)
        team_rows.append(pick)
    team = pd.concat(team_rows, ignore_index=True)

    team_cols = build_recap_cols(include_eff=True)
    team_path = save_table(team[team_cols], "proposed_team_12.csv")
    total_credits = team["credits"].sum()
    total_pdk     = team["pdk"].sum()

    print_table("🏆 Προτεινόμενη 12άδα (4G/4F/4C) βάσει value", team, team_cols)
    print(f"\nΣύνολο credits: {total_credits:.1f} | Σύνολο pdk: {total_pdk:.1f}")
    print(f"\n📁 CSV αρχεία γράφτηκαν στον φάκελο: {os.path.abspath(OUT_DIR)}")

if __name__ == "__main__":
    main()
