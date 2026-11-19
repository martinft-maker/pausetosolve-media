#!/usr/bin/env python3
"""Lager pipeline/puzzles.jsonl for @pausetosolve: 100 gåter, alle svar regnes ut og kontrolleres i koden.
Bruk: gen_bank.py OUT.jsonl [START_ID] [ANTALL] [SEED]"""
import json, random, sys, math

R = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 2026)
THEMES = [list("🍎🍌🍇🍓🍒🍍🥝🍋🍉🍑"), ["🐶", "🐱", "🐸", "🐵", "🦊", "🐼", "🐷", "🐰"],
          ["🍔", "🍕", "🌮", "🍩", "🍪", "🧁", "🥨", "🍟"], ["⚽", "🏀", "🎾", "🎈", "🎁", "⭐", "🎲", "🧸"]]
HOOK = {"A": ["ONLY 3% GET THIS", "99% GET THIS WRONG", "QUICK MATH TEST", "GENIUS LEVEL"],
        "B": ["FIND IT IN 5 SECONDS", "EYE TEST", "SHARP EYES ONLY", "CAN YOU SPOT IT?"],
        "C": ["WHAT COMES NEXT?", "IQ TEST", "PATTERN TEST", "ONLY 5% SEE IT"],
        "D": ["RIDDLE TIME", "CAN YOU SOLVE THIS?", "THINK FAST", "TRICK QUESTION"],
        "E": ["YOUR EYES LIE", "ILLUSION TEST", "TRUST YOUR EYES?"],
        "F": ["MEMORY TEST", "3 SECONDS ONLY", "FOCUS TEST"]}
TAG = {"A": "#mathpuzzle", "B": "#findtheoddoneout", "C": "#iqtest", "D": "#riddle", "E": "#opticalillusion", "F": "#memorytest"}

def gen_A():
    th = R.choice(THEMES); x, y, z = R.sample(th, 3)
    while True:
        vx, vy, vz = R.randint(3, 15), R.randint(2, 12), R.randint(2, 9)
        if len({vx, vy, vz}) == 3: break
    rows = [[x, "+", x, "+", x, "=", str(3 * vx)],
            [y, "+", y, "+", x, "=", str(2 * vy + vx)],
            [z, "+", y, "+", z, "=", str(2 * vz + vy)]]
    trap = R.random() < 0.45
    if trap:
        q = [x, "+", y, "×", z, "=", "?"]; ans = vx + vy * vz; extra = " · × first!"
    else:
        q = [z, "+", x, "+", y, "=", "?"]; ans = vz + vx + vy; extra = ""
    # kontroll: løs radene på nytt
    assert int(rows[0][-1]) // 3 == vx and (int(rows[1][-1]) - vx) // 2 == vy and (int(rows[2][-1]) - vy) // 2 == vz
    return dict(series="A", rows=rows, q=q, answer=ans, prompt="Solve it before the timer ends",
                explain_top=f"{x} = {vx}  ·  {y} = {vy}  ·  {z} = {vz}{extra}", verdict=f"Answer: {ans}",
                cap_q="Can you solve the last line?" if not trap else "Careful with the last line…")

PAIRS = [("😀", "😃"), ("😃", "😄"), ("🙂", "🙃"), ("😐", "😑"), ("😺", "😸"), ("🕐", "🕑"), ("😗", "😙"), ("😴", "😪"),
         ("💛", "🧡"), ("📗", "📘"), ("🌕", "🌝"), ("😊", "🙂"), ("😁", "😆"), ("🐵", "🙈"), ("🥲", "😂"), ("🌲", "🌳"),
         ("🔵", "🫐"), ("🍏", "🍐"), ("🐻", "🐨"), ("⏰", "⏲️")]
def gen_B(i):
    base, odd = PAIRS[i % len(PAIRS)]
    if R.random() < 0.5: base, odd = odd, base
    cols, rows = R.choice([(7, 5), (8, 6), (7, 6), (8, 5)])
    pos = [R.randrange(rows), R.randrange(cols)]
    return dict(series="B", base=base, odd=odd, rows=rows, cols=cols, pos=pos, answer=f"Row {pos[0]+1}, column {pos[1]+1}",
                prompt="Find the odd one out", explain_top=f"Row {pos[0]+1}, column {pos[1]+1}", verdict="Found it?",
                cap_q=f"Find the {odd} hiding between the {base}")

def gen_C():
    kind = R.choice(["grow", "double", "square", "fib", "alt", "prime", "x2p1", "cube", "interleave", "shrink"])
    if kind == "grow":
        a, d, k = R.randint(1, 6), R.randint(1, 4), R.randint(1, 3)
        s = [a]; diffs = []
        for i in range(5): diffs.append(d + i * k); s.append(s[-1] + diffs[-1])
        exp = " ".join(f"+{v}" for v in diffs)
    elif kind == "double":
        a, m = R.randint(1, 5), R.choice([2, 3]); s = [a * m ** i for i in range(6)]; exp = f"×{m} each time"
    elif kind == "square":
        st = R.randint(1, 5); s = [(st + i) ** 2 for i in range(6)]; exp = f"{st}², {st+1}², {st+2}²…"
    elif kind == "fib":
        a, b = R.randint(1, 4), R.randint(2, 6); s = [a, b]
        while len(s) < 6: s.append(s[-1] + s[-2])
        exp = "Add the two before it"
    elif kind == "alt":
        a, d = R.randint(1, 5), R.randint(2, 5); s = [a]
        for i in range(5): s.append(s[-1] + d if i % 2 == 0 else s[-1] * 2)
        exp = f"+{d}, ×2, +{d}, ×2…"
    elif kind == "prime":
        P = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]; st = R.randint(0, 4); s = P[st:st + 6]; exp = "Prime numbers"
    elif kind == "x2p1":
        a = R.randint(1, 4); s = [a]
        for i in range(5): s.append(s[-1] * 2 + 1)
        exp = "×2, then +1"
    elif kind == "cube":
        st = R.randint(1, 3); s = [(st + i) ** 3 for i in range(5)]; s.append((st + 5) ** 3); exp = f"{st}³, {st+1}³, {st+2}³…"
    elif kind == "interleave":
        a, b, da, db = R.randint(1, 5), R.randint(20, 30), R.randint(2, 4), -R.randint(1, 3)
        s = [a, b, a + da, b + db, a + 2 * da, b + 2 * db]; exp = f"Two patterns: +{da} and {db}"
    else:
        a, d = R.randint(60, 99), R.randint(2, 4); s = [a]; diffs = []
        for i in range(5): diffs.append(d + i); s.append(s[-1] - diffs[-1])
        exp = " ".join(f"−{v}" for v in diffs)
    shown = s[:5] + ["?"] if kind != "cube" else s[:4] + ["?"]
    ans = s[5] if kind != "cube" else s[4]
    return dict(series="C", seq=shown, answer=ans, explain=exp, prompt="What number comes next?", explain_top=exp,
                verdict=f"Answer: {ans}", cap_q="What number comes next?")

RIDDLES = [("What has keys but can't open a single lock?", "A piano 🎹"), ("What gets wetter the more it dries?", "A towel"),
           ("What has hands but can't clap?", "A clock ⏰"), ("What can you catch but never throw?", "A cold 🤧"),
           ("What has a neck but no head?", "A bottle 🍾"), ("What goes up but never comes down?", "Your age"),
           ("The more you take, the more you leave behind. What are they?", "Footsteps 👣"),
           ("What has one eye but can't see?", "A needle 🪡"), ("What belongs to you, but other people use it more than you do?", "Your name"),
           ("I'm tall when I'm young and short when I'm old. What am I?", "A candle 🕯️"),
           ("What has lots of teeth but can't bite?", "A comb"), ("What can travel around the world while staying in a corner?", "A stamp 📮"),
           ("What has words but never speaks?", "A book 📖"),
           ("A rooster lays an egg on a roof. Which way does the egg roll?", "Roosters don't lay eggs 🐓"),
           ("A bat and a ball cost $1.10. The bat costs $1.00 more than the ball. How much is the ball?", "5 cents (not 10!)")]
def gen_D(i):
    q, a = RIDDLES[i]
    return dict(series="D", question=q, answer=a, prompt="Can you answer this riddle?", explain_top="The answer is…", verdict="Did you get it?",
                cap_q=q)

ILL = [dict(kind="muller", flip=False, prompt="Which line is longer: A or B?", answer="Same length!"),
       dict(kind="ebbinghaus", color=[255, 140, 40], prompt="Which orange dot is bigger: A or B?", answer="Same size!"),
       dict(kind="contrast", flip=False, gray=128, prompt="Which square is darker: A or B?", answer="Same color!"),
       dict(kind="ponzo", color=[255, 120, 60], prompt="Which bar is longer: A or B?", answer="Same length!"),
       dict(kind="muller", flip=True, prompt="Which line is longer: A or B?", answer="Same length!"),
       dict(kind="ebbinghaus", color=[255, 90, 140], prompt="Which pink dot is bigger: A or B?", answer="Same size!"),
       dict(kind="contrast", flip=True, gray=140, prompt="Which square is lighter: A or B?", answer="Same color!"),
       dict(kind="ponzo", color=[60, 220, 200], prompt="Which bar is longer: A or B?", answer="Same length!")]
def gen_E(i):
    e = dict(ILL[i]); e.update(series="E", explain_top="Your brain just got tricked 🤯", verdict=e["answer"], cap_q=e["prompt"])
    return e

def gen_F():
    th = R.choice(THEMES); kinds = R.sample(th, 4); target = kinds[0]; n = R.randint(2, 5)
    grid = [target] * n + [R.choice(kinds[1:]) for _ in range(12 - n)]; R.shuffle(grid)
    assert grid.count(target) == n
    return dict(series="F", grid=grid, cols=4, target=target, answer=n, prompt=f"How many {target} did you see?",
                explain_top=f"There were {n} {target}", verdict=f"Answer: {n}", cap_q=f"How many {target} were in the grid?")

def build(start=1, count=100):
    plan = ["A"] * 25 + ["B"] * 20 + ["C"] * 20 + ["D"] * 15 + ["E"] * 8 + ["F"] * 12
    # flett: aldri samme serie to ganger på rad
    order, pool = [], plan[:]
    while pool:
        opts = [s for s in sorted(set(pool)) if not order or s != order[-1]] or list(set(pool))
        weights = [pool.count(s) for s in opts]; s = R.choices(opts, weights)[0]; order.append(s); pool.remove(s)
    cnt = {k: 0 for k in "ABCDEF"}; out = []
    for n, s in enumerate(order[:count]):
        i = cnt[s]; cnt[s] += 1
        p = {"A": gen_A, "C": gen_C, "F": gen_F}[s]() if s in "ACF" else {"B": gen_B, "D": gen_D, "E": gen_E}[s](i)
        p["id"] = f"{start + n:03d}"; p["hook"] = HOOK[s][i % len(HOOK[s])]
        p["caption"] = (f"{p.pop('cap_q')} 🧠\n\nComment your answer before the timer runs out 👇\n"
                        f"New puzzle every day – follow @pausetosolve\n\n#brainteaser #puzzle {TAG[s]} #pausetosolve")
        p["title"] = f"{p['hook'].capitalize()} 🧠"
        out.append(p)
    return out

if __name__ == "__main__":
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1; count = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    ps = build(start, count)
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        for p in ps: f.write(json.dumps(p, ensure_ascii=False) + "\n")
    from collections import Counter; print(len(ps), Counter(p["series"] for p in ps))
