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
| `15_data_window` | Data Window outputs |

After editing a module, run `python3 John/build.py` to regenerate `pine/John.pine`. `python3 John/build.py --check` fails if the generated file is stale or was hand-edited. Pine needs everything defined before it's used, so a new module goes in the manifest after whatever it depends on.

## Modules

| Module | Spec part | Status |
| --- | --- | --- |
| Market structure (top-down D · H4 · H1 · M15): ITH/ITL, LTH/LTL | 2.1–2.2 | Built |
| Liquidity map: BSL/SSL pools, equal highs/lows, raid vs run | 3.1–3.3 | Built |
| Time map: midnight separators, day names, killzone boxes | 1.2–1.3, 5.1 | Built |
| Power of 3 (AMD): accumulation, manipulation, distribution boxes | 5.3 | Built |
| Daily Bias engine | 8 | Next |
| PD arrays, structure (BOS/MSS), setups | 4–7, 9 | Planned |

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
