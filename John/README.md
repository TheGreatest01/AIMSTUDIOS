# John — ICT Engine (TradingView indicator)

John is a Pine Script v6 indicator that detects ICT concepts from the 2016/2017 Core Content and the 2022 Mentorship. It is built one module at a time. Every rule follows the review doc **John — ICT Concept Detection Spec**; the part numbers below refer to it.

## Install

1. Open TradingView and go to **Pine Editor**.
2. Replace the editor contents with [`pine/John.pine`](pine/John.pine).
3. Click **Save**, then **Add to chart**.

## Development

`pine/John.pine` is generated: don't edit it by hand. The source is one file per module in `src/`, joined in the order listed in `src/manifest.txt`:

| File | Contains |
| --- | --- |
| `00_header` | Licence, description, `indicator()` declaration |
| `01_inputs` | All settings |
| `02_types` | `Pool`, `Span`, `Mark`, `TfTrack`, `Po3State` |
| `03_state` | Persistent arrays, maps and trackers |
| `04_helpers` | Formatting, colours, timeframe names |
| `05_structure_engine` | Swing / ITH / LTH / equal-high detection run on D, H4, H1, M15 |
| `06_requests` | `request.security` calls (structure, IPDA, M15 candles) |
| `07_liquidity` | Pools, raid/run checks, swept look |
| `08_structure_markers` | Swing markers on the chart |
| `09_killzones` | Spans, killzone tracking and boxes |
| `10_power_of_3` | Accumulation, manipulation, distribution |
| `11_per_bar` | Per-candle flags (new day, sessions) |
| `12_engine` | The once-per-closed-candle engine |
| `13_render` | Pool lines and labels at the last candle |
| `14_days` | Midnight separators and day names |
| `15_daily_bias` | Daily bias votes, score, DOL, invalidation and the bias table |
| `16_pd_arrays` | FVGs, order blocks and BOS/MSS from D, H4, H1, M15 |
| `17_setups` | 2022 model on M15: raid → MSS → FVG entry, stop, targets, paper stats |
| `18_data_window` | Data Window outputs |

After editing a module, run `python3 John/build.py` to regenerate `pine/John.pine`, then `python3 John/lint.py`. The linter catches Pine errors that are easy to miss: a function modifying a global, a function or global used before it is defined, and wrapped lines indented by a multiple of 4. `python3 John/build.py --check` fails if the generated file is stale or was hand-edited. Pine needs everything defined before it's used, so a new module goes in the manifest after whatever it depends on.

## Modules

| Module | Spec part | Status |
| --- | --- | --- |
| Market structure (top-down D · H4 · H1 · M15): ITH/ITL, LTH/LTL | 2.1–2.2 | Built |
| Liquidity map: BSL/SSL pools, equal highs/lows, raid vs run | 3.1–3.3 | Built |
| Time map: midnight separators, day names, killzone boxes | 1.2–1.3, 5.1 | Built |
| Power of 3 (AMD): accumulation, manipulation, distribution boxes | 5.3 | Built |
| Daily bias: six votes → score → Bullish / Bearish / Neutral table | 8 | Built |
| PD arrays: FVGs, order blocks, BOS/MSS (D · H4 · H1 · M15) | 2.3–2.4, 4 | Built |
| Setups: 2022 model with entry, stop-loss, TP1/TP2 and paper stats | 9 | Built |

## Top-down by design

John reads market structure **only from Daily, H4, H1 and M15 candles**, whatever timeframe the chart is on. A Daily ITL is the same Daily ITL on the H4, M15 or M1 chart.

- **What each chart shows:** its own timeframe's structure and every higher one.

| Chart | Structure shown |
| --- | --- |
| Daily | D |
| H4 | D, H4 |
| H1 | D, H4, H1 |
| M15, M5, M1 | D, H4, H1, M15 |

- **M1 and M5 candles never decide structure.** On those charts they are used only to place each swing's marker on the exact candle that made the high or low.
- **Raids and runs are always judged on M15 candles,** so the verdict doesn't change when you switch timeframes.

## Market structure

On each of D, H4, H1 and M15, using that timeframe's own candles:

- **Short-term high (STH):** a candle whose high is strictly above the high of the candle before it and at least equal to the high of the candle after it. The number of candles on each side is the *Short-term swing length* input (default 1, the classic 3-candle swing).
- **Intermediate-term high (ITH):** a short-term high with a lower short-term high on each side.
- **Long-term high (LTH):** an intermediate-term high with a lower intermediate-term high on each side.
- Lows mirror this.

**Markers:** black triangles, pointing down above the candle for highs and up below the candle for lows.
- **Size** follows the timeframe: D large, H4 normal, H1 small, M15 tiny.
- **Tags** name the timeframe and tier, e.g. "H4 LTL".
- **Shared candles:** when one candle is a swing on several timeframes, they share one marker, e.g. "D LTL · H4 LTL · H1 ITL".
- **Settings:** each timeframe, each tier, the tags, sizes and colour can be switched or changed.
- **Tooltip:** hover a marker for its price and New York time.

**Timing:** a marker appears once that timeframe's candle confirming it has closed, and is never removed afterwards.
- An ITH is confirmed when that timeframe's *next* short-term high forms.
- An LTH is confirmed when the next ITH forms, and its marker updates in place.
- On a dark chart theme, change *Marker colour* to a light colour; black is the default.

## Liquidity map

John tracks every level where stops are likely to rest: **buyside liquidity** (BSL, blue) above old highs and **sellside liquidity** (SSL, red) below old lows.

| Pool | Line | Removed when untaken |
| --- | --- | --- |
| PDH / PDL (previous day) | Solid | The day rolls |
| PWH / PWL (previous week) | Solid, thick | The week rolls |
| Asia / LDN / NY AM / NY PM killzone high and low (charts of 1 hour or lower) | Dashed | 24 hours after the killzone ends |
| Untaken ITH/ITL and LTH/LTL from D, H4, H1 (M15 optional), e.g. "H4 ITH" | Dotted (thick for LTH/LTL) | Over the cap: newest 3 per side, tier and timeframe |
| EQH / EQL from H4, H1, M15 (D optional): two untaken short-term swings on that timeframe ≥ 3 of its candles apart, within 0.1 × its ATR | Solid | Over the cap: newest 3 per side and timeframe |
| IPDA20/40/60 H and L: highs and lows of the last 20, 40, 60 completed days | Dashed | The level rolls to a new value |

**Untaken pools** run to just right of price, each with a label. Labels for pools at nearly the same price on the same side merge into one, e.g. "PDH · H4 ITH".

**Taken pools** are judged on **M15 candles** on every chart:
- **Raid:** the M15 candle that trades through closes back inside, or one does within the next 2 M15 candles. The line stops at that candle and fades, the label reads "PDH raid", and an ✕ marks the wick.
- **Deep raid:** a raid deeper than 1 H1 ATR is tagged "(deep)".
- **Run:** price stays beyond for 2 more M15 closes. The faded line ends in an arrowhead.
- When one candle takes several pools at the same level, they share one label.
- TradingView only supplies M15 data for recent history. Further back (e.g. older candles on a Daily chart), the chart's own candle judges the raid/run, so old pools still end where price actually took them. The tooltip says which candles judged it.
- Equal highs/lows start at the swing that sits at the pool's price, so the line begins on that wick.

**Tooltips:** hover any label for the price, when the pool formed, how and when it was taken, and the depth in pips and H1 ATR.

**Alerts:** create an alert on John with the condition *Any alert() function call* to be told about every raid and run.

**Data Window:** shows the nearest untaken BSL and SSL.

**Limitation:** swing and equal-high pools only come from swings confirmed inside the chart's loaded history. On an M1 chart, which holds only a week or two, older Daily/H4 swing pools won't appear. PDH/PDL, PWH/PWL and the IPDA levels still cover the major higher-timeframe liquidity there.

## Time map

- **Midnight separators:** a thin dotted vertical line at every calendar midnight, New York by default (London or UTC optional). This marks calendar days, not trading days. A matching line at the coming midnight closes off today. Over the weekend gap, the line is drawn on the first candle of the new day.
- **Day names:** Monday, Tuesday, … printed at the top of the chart (or the bottom), centred on each day at the first candle from noon.
- **Killzone boxes:** one rectangle per killzone (New York time; every time is adjustable).

| Killzone | Default time |
| --- | --- |
| Asian range | 20:00–00:00 |
| London killzone | 02:00–05:00 |
| New York AM session | 08:30–11:00 |
| New York PM session | 13:30–16:30 |

- From its first candle, each box spans the killzone's full time window and grows to its high and low as they form.
- Each label shows the name and the range, e.g. "Asia  23.4 pips".
- Each killzone has its own on/off switch, label text and colour. Fill, label position and size are shared settings.
- Drawn on charts of 1 hour or lower.
- The last 30 days of separators and boxes are kept (adjustable).

## Power of 3 (AMD)

ICT reads every day as **open → accumulation → manipulation → distribution → close**. On a bullish day, price ranges near the open, makes a false move below it (the Judas swing, which forms the low of the day), then expands to the high and closes near it. A bearish day is the mirror image.

John draws one dashed box per phase (charts of 1 hour or lower, on/off with *Show Power of 3*):

| Box | What it covers |
| --- | --- |
| **A · Accumulation** | The accumulation window's high-to-low range (default the Asian range, 20:00–00:00 New York). When it matches the Asian range killzone, the A box replaces the Asia box. |
| **M · Manipulation** | From the true day open (midnight New York) to whichever of the day's two extremes forms first: the Judas swing. A low first means a bullish day (M ↓); a high first means a bearish one (M ↑). |
| **D · Distribution** | From that extreme to the opposite extreme, running to the end of the true day (default 17:00). |

- **Labels:** sizes in pips, and what the Judas swing took, e.g. "M · Manipulation ↓ Judas 18.2 pips · took A low · took PDL".
- **True day open line:** a dotted line marks the midnight open across the day.
- **Live behaviour:** while the day is running, M and D are marked "(developing)" and follow price. If price later breaks the first extreme, the day's reading can flip.
- **Settings:** every box has its own on/off switch, label and colour. The two windows, fill and labels are adjustable.

## Daily bias

A small table at the top right of the chart (or bottom right) shows **Bias | Bullish / Bearish / Neutral**:
- Dark green or red: strong. Lighter: moderate. Grey: Neutral, a no-trade day.
- Hover the cell for the score.

The bias for a day uses only daily and weekly candles that closed before the day opened, so it is locked for the whole day and reads the same on every chart timeframe. Six votes, each from −1 to +1:

| Vote | Weight | Rule (yesterday = D-1) |
| --- | --- | --- |
| Daily order flow | 1.5 | Last daily close through a 5-candle swing high (+) or low (−); full weight with displacement, 0.6 without; 0 if older than 60 days |
| Previous day | 1.25 | D-1 vs D-2: close above its high +1 · below its low −1 · took its high and closed back inside −1 · took its low and closed back inside +1 · outside day ±0.5 · inside day 0 |
| Liquidity cycle | 1.25 | D-1 raided external liquidity (swing or 20-day high/low, closed back inside) → toward the other side; or held a daily FVG above (+) / below (−) its midpoint |
| IPDA break | 1.0 | Most recent close beyond the 20/40/60-day high (+) or low (−) within 10 days, weighted 0.5 / 0.75 / 1.0 |
| Weekly order flow | 1.0 | Weekly structure averaged with last week against the week before |
| SMT (optional) | 0.75 | Set an SMT pair: D-1 took the day before's low but the pair didn't (+), or the high (−) |

- **Score:** the weighted average of the votes.
- **Location:** ×1.15 on the cheap side of the 20-day range for the bias; ×0.70 beside its far extreme.
- **Consolidation:** an inside day inside a tight 5-day range caps the score at ±0.30.
- **Classification:** |score| ≥ 0.30 is Bullish/Bearish, and ≥ 0.55 is strong.
- **Settings:** *Show the score and the six votes* expands the table. Every weight and threshold can be changed.
- **Alerts and Data Window:** an alert fires with each new day's bias, and the Data Window shows the score.

**Draw on liquidity and invalidation** (fixed when the day opens):
- **DOL:** the nearest untaken pool in the bias direction at least 0.3 × the average daily range away. It's drawn as a thick dashed line labelled "DOL · …" and shown in the table, with "✓ hit" once reached.
- **Invalidation:** the level the bias rests on (the raid extreme or FVG edge behind it), otherwise yesterday's low (bullish) or high (bearish).
- **Invalidated:** an M15 close beyond the invalidation level turns the table cell grey ("· invalidated"). Setups stop for that direction for the rest of the day.

## PD arrays and structure breaks

From D, H4, H1 and M15 candles (a chart shows its own timeframe and every higher one), each switchable per timeframe:

| Array | Rule | Default timeframes |
| --- | --- | --- |
| FVG | Candle 3's low above candle 1's high (bullish) or its high below candle 1's low (bearish), ≥ 0.1 × that timeframe's ATR | H4, H1 |
| Order block | The last opposite-colour candle before a displacement that closes through a swing | H4, H1 |
| BOS / MSS | A displaced close through the last swing high/low; MSS when it turns the previous break's direction, BOS when it continues it | H4, H1, M15 |

- **Zones** are boxes with a dashed midpoint (the FVG's consequent encroachment, the OB's mean threshold). They run right until an M15 candle closes through the far edge, then stop there and fade.
- **Midpoint hit:** a zone whose midpoint has been reached is labelled "CE hit" or "MT hit".

## Setups · ICT 2022 model

Signals come from **M15 candles** on every chart up to H4, inside the enabled killzones (London KZ, NY AM, NY PM) and in the direction of the daily bias. Long setup (shorts mirror it):

1. **Raid:** a sellside pool (PDL, a killzone low, a swing low, equal lows, an IPDA low…) is traded through.
2. **MSS:** within 10 M15 candles, a close above the swing high that began the drop into the raid, with displacement (bodies ≥ 1.2 × M15 ATR, each ≥ 60% of its candle).
3. **Entry:** the first FVG of that displacement leg: its edge (default), its midpoint, or the OTE 70.5% of the leg.
4. **Stop:** 1 pip below the raid low. **TP1:** the displacement high. **TP2:** the day's DOL if beyond TP1, otherwise the next untaken buyside pool, otherwise 2R.
5. **Filter:** the setup is only taken if reward:risk to TP2 is at least 2.

**On the chart:**
- A green target box (entry → TP2) and a red risk box (entry → stop), with TP1 dotted.
- A label with entry, stop, TP1, TP2 and R:R.
- A London setup whose raid took the Asian range is tagged "Judas".

**Order and trade handling:**
- The order waits until the killzone ends. It's dropped if price reaches TP1 first or closes through the FVG.
- Once filled: 50% closes at TP1 and the stop moves to entry. The rest runs to TP2, the stop, or 16:00 New York.
- The result is printed in R ("+2.6R TP2", "−1.0R SL", "+0.5R stop at entry").

**Stats and alerts:**
- The stats table (bottom right) shows setups, fills, win rate, and average and total R on the loaded history.
- Alerts fire on each new setup, fill and exit.

These are paper results from historical candles, not advice: fills assume price traded through the entry, and when the stop and entry fall in the same M15 candle the stop is assumed hit. TradingView only provides M15 data for recent history, so setups and stats cover that period.
