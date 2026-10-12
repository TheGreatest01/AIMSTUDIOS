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
| `06_requests` | `request.security` calls (structure, M15 candles) |
| `07_liquidity` | Pools, raid/run checks, swept look |
| `08_structure_markers` | Swing markers on the chart |
| `09_killzones` | Spans, killzone tracking and boxes |
| `10_power_of_3` | Accumulation, manipulation, distribution |
| `11_per_bar` | Per-candle flags (new day, sessions) |
| `12_engine` | The once-per-closed-candle engine |
| `13_render` | Pool lines and labels at the last candle |
| `14_days` | Midnight separators and day names |
| `16_pd_arrays` | FVGs, order blocks and BOS/MSS from D, H4, H1, M15 |
| `17_setups` | Raid → MSS on M1/M3/M5 → FVG/OB entry, stop, target, paper stats |
| `18_data_window` | Data Window outputs |

`src/disabled/` holds modules that are switched off and left out of the build: `15_daily_bias` (the bias engine and table), `12b_ipda` (IPDA 20/40/60 levels) and `17_setups_bias_2022` (the earlier bias-gated setups). To switch one back on, move it into `src/` and list it in the manifest (each file's header says where).

After editing a module, run `python3 John/build.py` to regenerate `pine/John.pine`, then `python3 John/lint.py`. The linter catches Pine errors that are easy to miss: a function modifying a global, a function or global used before it is defined, and wrapped lines indented by a multiple of 4. `python3 John/build.py --check` fails if the generated file is stale or was hand-edited. Pine needs everything defined before it's used, so a new module goes in the manifest after whatever it depends on.

## Modules

| Module | Spec part | Status |
| --- | --- | --- |
| Market structure (top-down D · H4 · H1 · M15): ITH/ITL, LTH/LTL | 2.1–2.2 | Built |
| Liquidity map: BSL/SSL pools, equal highs/lows, raid vs run | 3.1–3.3 | Built |
| Time map: midnight separators, day names, killzone boxes | 1.2–1.3, 5.1 | Built |
| Power of 3 (AMD): accumulation, manipulation, distribution boxes | 5.3 | Built |
| Daily bias: six votes → score → Bullish / Bearish / Neutral table | 8 | Off for now (`src/disabled/`) |
| IPDA 20/40/60-day levels | 3 | Off for now (`src/disabled/`) |
| PD arrays on structure timeframes (D · H4 · H1 · M15): draws on liquidity | 2.3–2.4, 4 | Built |
| Setups: raid → MSS (M1/M3/M5) → FVG/OB entry, stop, target, paper stats | 9 | Built |

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
| Untaken ITH/ITL and LTH/LTL from D, H4, H1, M15, e.g. "M15 ITH" | Dotted (thick for LTH/LTL) | Over the cap: newest 3 per side, tier and timeframe |
| EQH / EQL from H4, H1, M15 (D optional): two untaken short-term swings on that timeframe ≥ 3 of its candles apart, within 0.1 × its ATR | Solid | Over the cap: newest 3 per side and timeframe |

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

**Limitation:** swing and equal-high pools only come from swings confirmed inside the chart's loaded history. On an M1 chart, which holds only a week or two, older Daily/H4 swing pools won't appear. PDH/PDL and PWH/PWL still cover the major higher-timeframe liquidity there.

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

## Switched off for now

The **Daily bias** engine (votes, draw on liquidity, invalidation, the Bias table) and the **IPDA 20/40/60** levels are kept in `src/disabled/` but not built into `John.pine`. Setups run without a bias filter until bias and top-down analysis are revisited.

## PD arrays and structure breaks

From D, H4, H1 and M15 candles (a chart shows its own timeframe and every higher one), each switchable per timeframe. These are **draws on liquidity**: places price is likely to reach for. They are never entries. Entry FVGs and order blocks come only from M1, M3 and M5 (see Setups).

| Array | Rule | Default timeframes |
| --- | --- | --- |
| FVG | Candle 3's low above candle 1's high (bullish) or its high below candle 1's low (bearish), ≥ 0.1 × that timeframe's ATR | H4, H1 |
| Order block | The last opposite-colour candle before a displacement that closes through a swing | H4, H1 |
| BOS / MSS | A displaced close through the last swing high/low; MSS when it turns the previous break's direction, BOS when it continues it | Off (the setups mark their own MSS) |

- **Zones** are boxes with a dashed midpoint (the FVG's consequent encroachment, the OB's mean threshold). They run right until an M15 candle closes through the far edge, then stop there and fade.
- **Midpoint hit:** a zone whose midpoint has been reached is labelled "CE hit" or "MT hit".

## Setups · raid → MSS → FVG

Structure and liquidity come from H4, H1 and M15 (mainly M15). Entries come from M5, M3 and M1. There is no time filter and no bias filter. A short setup (longs mirror it):

1. **Raid:** price trades above a buyside pool: mainly an M15 ITH, or PDH/PWH, a killzone high or equal highs. Everything above the level is the manipulation, and its highest point is the **peak**. The turn can take several M15 candles, so the peak keeps moving up until the shift. Leg 1 runs up into the peak; leg 2 runs down out of it.
2. **Market structure shift:** in leg 2, the first close below the most recent short-term low (a low with a higher low on each side) on M1, M3 or M5, whichever happens first. By default the close must also be back below the raided level. A line marks the broken low, labelled "MSS (M3)" and so on. If no shift comes within 8 M15 candles of the peak, the raid is ignored.
3. **Entry:** the fair value gap leg 2 leaves on the timeframe of the shift, formed from the peak onwards. A sell limit sits at its bottom edge, the first price a retrace re-enters. If no FVG forms within 3 candles of the shift, the order block is used instead: the last up-close candle between the peak and the shift.
4. **Stop:** 1 pip above the peak.
5. **Target:** the most recent untaken M15 swing low (ITL/LTL) below the entry. If there is none, the nearest untaken sellside pool, otherwise 2R. The setup is skipped if reward:risk is below 1.

**On the chart:** the entry FVG/OB box, a green target box and a red risk box from the signal, and a label with the raided level, the MSS timeframe, entry, stop, target and R:R.

**Order and trade handling** (on M1 candles):
- The order goes live on the candle after the signal. It's dropped if price reaches the target first, if it isn't filled within 8 M15 candles, or if the peak breaks before an entry zone forms.
- Once filled, the trade runs to the stop or the target. When the fill and the stop fall in the same M1 candle, the stop is assumed hit.
- The result is printed in R ("+2.3R TP", "−1.0R SL").
- One setup per direction at a time.

**Stats and alerts:**
- The stats table (bottom right) shows setups, fills, win rate, and average and total R on the loaded history.
- Alerts fire on each new setup, fill and exit.

**Where setups appear:** M1, M3, M5 and M15 charts. They are built from M1 candles, so the same setups show on each. TradingView only supplies M1 data inside an M3–M15 chart for recent history, so setups and stats cover that period; an M1 chart covers its whole loaded history.

These are paper results from historical candles, not advice.
