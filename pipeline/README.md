# @pausetosolve – pipeline

- `puzzles.jsonl` – gåtebanken (fasit). Én linje per gåte, `id` = NNN. Serier: A emoji-likning, B finn den som skiller seg ut, C tallrekke, D gåte i tekst, E synsbedrag, F hukommelse.
- `gen_bank.py OUT.jsonl START ANTALL SEED` – lager nye gåter med svar regnet ut i koden. Nye gåter legges til på slutten av puzzles.jsonl med neste ledige id. Serie D (tekstgåter) og E (synsbedrag) har faste lister i skriptet – utvid listene før de brukes opp.
- `pts_reel.py puzzles.jsonl ID [ID…] reels/` – lager `reels/pausetosolve_NNN.mp4` (1080×1920, 30 fps, 12–14 s, original musikk + tikk, buzzer og ding).
- `pts_reel.py --still puzzles.jsonl ID ut.png T` – ett bilde ved tid T for kontroll (T=3 gåte, T=11 svar).
- `used_ids.txt` – id-er som er planlagt i Metricool. Aldri bruk en id to ganger.

Design A «Arcade»: marine bakgrunn med rutenett, neongul krok, kort med gåten, nedtellingsring, grønt svar.
