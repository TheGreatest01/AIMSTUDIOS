# John — ICT Engine (TradingView indicator)

John is a Pine Script v6 indicator that detects ICT concepts from the 2016/2017 Core Content and the 2022 Mentorship. It is built one module at a time. Every rule follows the review doc **John — ICT Concept Detection Spec**; the part numbers below refer to it.

## Install

1. Open TradingView and go to **Pine Editor**.
2. Replace the editor contents with [`pine/John.pine`](pine/John.pine).
3. Click **Save**, then **Add to chart**.

## Modules

| Module | Spec part | Status |
| --- | --- | --- |
| Swing tiers: STH/STL, ITH/ITL, LTH/LTL | 2.1–2.2 | Built |
| Liquidity map: BSL/SSL pools, equal highs/lows, raid vs run | 3.1–3.3 | Built |
| Daily Bias engine | 8 | Next |
| PD arrays, structure (BOS/MSS), sessions, setups | 4–7, 9 | Planned |

## Swing tiers

- **Short-term high (STH):** a candle whose high is strictly above the high of the candle before it and at least equal to the high of the candle after it. The number of candles on each side is the *Short-term swing length* input (default 1, the classic 3-candle swing).
- **Intermediate-term high (ITH):** a short-term high with a lower short-term high on each side.
- **Long-term high (LTH):** an intermediate-term high with a lower intermediate-term high on each side.
- Lows mirror this. All tiers are computed on the chart's own timeframe.

**Markers:**
- Highs get a downward triangle above the candle; lows get an upward triangle below it.
- ITH/ITL and LTH/LTL markers are black, and long-term markers are drawn larger.
- Short-term markers are optional and shown in grey.
- Hover over any marker to see its tier, price and New York time.

**Timing:** a marker is drawn only once its swing is confirmed, and is never removed afterwards.
- A short-term swing is confirmed when the candles on its right have closed.
- An ITH is confirmed when the *next* short-term high forms, which can be many candles later.
- An LTH is confirmed when the next ITH forms.
- When an ITH is promoted to an LTH, its existing triangle grows in place.

On a dark chart theme, change *Marker colour* to a light colour; black is the default.

## Liquidity map

John tracks every level where stops are likely to rest: **buyside liquidity** (BSL, blue) above old highs and **sellside liquidity** (SSL, red) below old lows.

| Pool | Line | Removed when untaken |
| --- | --- | --- |
| PDH / PDL (previous day) | Solid | The day rolls |
| PWH / PWL (previous week) | Solid, thick | The week rolls |
| Asia / LDN / NY session high and low (New York time; charts of 1 hour or lower) | Dashed | 24 hours after the session ends |
| Untaken ITH / ITL and LTH / LTL (from the swing tiers) | Dotted (thick for LTH/LTL) | Over the per-side cap (default 4) |
| EQH / EQL: two untaken short-term swings ≥ 3 candles apart, within 0.1 × ATR | Solid | Over the per-side cap (4) |
| IPDA20/40/60 H and L: highs and lows of the last 20, 40, 60 completed days | Dashed | The level rolls to a new value |

**Untaken pools** run to just right of price, each with a label. Labels for pools at nearly the same price on the same side merge into one, e.g. "PDH · ITH".

**Taken pools.** A pool is taken when a closed candle trades beyond it:
- **Raid:** the candle closes back inside, or a later one does within 2 candles. The line stops at that candle and fades, the label reads "PDH raid", and an ✕ marks the wick. A raid deeper than 1 ATR is tagged "(deep)".
- **Run:** price stays beyond for 2 more closes. The faded line ends in an arrowhead.
- When one candle takes several pools at the same level, they share one label.

**Tooltips:** hover any label for the price, when the pool formed, how and when it was taken, and the depth in pips and ATR.

**Alerts:** create an alert on John with the condition *Any alert() function call* to be told about every raid and run.

**Data Window:** shows the nearest untaken BSL and SSL.
