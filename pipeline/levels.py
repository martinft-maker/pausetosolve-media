#!/usr/bin/env python3
"""Nivå-serien for @pausetosolve (Martin 25. nov): hver video er «Level N», og svaret på forrige nivå
vises øverst i neste video («✅ Level N-1 answer: …») og i bildeteksten. Svaret på sitt eget nivå vises aldri.

pipeline/levels.jsonl = postrekkefølgen: én linje per publisert/planlagt video {"level": N, "id": "NNN"}.

Bruk:
  levels.py assign BANK ANTALL      -> tar de neste ubrukte B/E/F-id-ene, gir dem neste nivåer,
                                       skriver levels.jsonl + used_ids.txt, skriver id-ene ut
  levels.py meta BANK NIVÅ [NIVÅ …]  -> JSON per nivå: id, caption, tiktok_title, youtube_title, url
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = os.path.join(HERE, "levels.jsonl")
USED = os.path.join(HERE, "used_ids.txt")
URL = "https://raw.githubusercontent.com/martinft-maker/pausetosolve-media/media/reels/pausetosolve_{id}.mp4"
SERIES_OK = set("BEF")          # kun formatene som funker (Martin 25. nov)
TAG = {"A": "#mathpuzzle", "B": "#findtheoddoneout", "C": "#iqtest", "D": "#riddle", "E": "#opticalillusion", "F": "#memorytest"}

def load_bank(bank):
    return {json.loads(l)["id"]: json.loads(l) for l in open(bank, encoding="utf-8") if l.strip()}

def load_levels():
    if not os.path.exists(LEVELS): return []
    return [json.loads(l) for l in open(LEVELS, encoding="utf-8") if l.strip()]

def answer_text(p):
    a = p["answer"]
    if p["series"] == "F": return f"{a} {p['target']}"
    return str(a)

def cap_q(p):
    return p["caption"].split("\n")[0].replace(" 🧠", "").strip()

def annotate(bank_dict):
    """Legger level + prev_answer inn i gåtene som har et nivå (brukes av pts_reel.py)."""
    lv = load_levels(); by_level = {e["level"]: e["id"] for e in lv}
    for e in lv:
        p = bank_dict.get(e["id"])
        if not p: continue
        p["level"] = e["level"]
        prev = by_level.get(e["level"] - 1)
        if prev and prev in bank_dict:
            p["prev_answer"] = f"Level {e['level'] - 1} answer: {answer_text(bank_dict[prev])}"
    return bank_dict

def meta(bank_dict, level):
    lv = {e["level"]: e["id"] for e in load_levels()}
    pid = lv[level]; p = bank_dict[pid]; prev = lv.get(level - 1)
    hook = p["hook"].capitalize().replace("Iq ", "IQ ")
    lines = [f"Level {level}: {cap_q(p)} 🧠", "",
             "Comment your answer 👇 The answer drops in my next video 👀",
             "Follow @pausetosolve so you don't miss it"]
    if prev and prev in bank_dict:
        lines += ["", f"✅ Level {level - 1} answer: {answer_text(bank_dict[prev])}"]
    lines += ["", f"#brainteaser #puzzle {TAG[p['series']]} #pausetosolve"]
    return dict(level=level, id=pid, series=p["series"], caption="\n".join(lines),
                tiktok_title=f"Level {level} 🧠 {hook}", youtube_title=f"Level {level}: {hook} 🧠 #shorts",
                url=URL.format(id=pid))

if __name__ == "__main__":
    cmd, bank = sys.argv[1], sys.argv[2]; B = load_bank(bank)
    if cmd == "assign":
        n = int(sys.argv[3])
        used = {l.strip() for l in open(USED) if l.strip()}
        lv = load_levels(); nxt = (lv[-1]["level"] + 1) if lv else 1
        free = [pid for pid in sorted(B) if pid not in used and B[pid]["series"] in SERIES_OK]
        # unngå samme serie to ganger på rad der det går
        pick, last = [], B[lv[-1]["id"]]["series"] if lv else None
        while len(pick) < n and free:
            j = next((k for k, pid in enumerate(free) if B[pid]["series"] != last), 0)
            pid = free.pop(j); pick.append(pid); last = B[pid]["series"]
        if len(pick) < n: print(f"ADVARSEL: bare {len(pick)} ledige B/E/F-gåter – kjør gen_bank.py --append først", file=sys.stderr)
        with open(LEVELS, "a", encoding="utf-8") as f:
            for k, pid in enumerate(pick): f.write(json.dumps({"level": nxt + k, "id": pid}) + "\n")
        with open(USED, "a") as f:
            for pid in pick: f.write(pid + "\n")
        print(" ".join(pick))
    elif cmd == "meta":
        print(json.dumps([meta(B, int(x)) for x in sys.argv[3:]], ensure_ascii=False, indent=1))
