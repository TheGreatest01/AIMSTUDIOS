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
| Daily Bias engine | 8 | Next |
| Liquidity map, PD arrays, structure (BOS/MSS), sessions, setups | 3–7, 9 | Planned |

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
