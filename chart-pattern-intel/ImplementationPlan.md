Best implementation plan in the correct order

Here’s the order I’d strongly recommend.

Phase 1 — Lock the backend foundation

You already started here. Finish it first before touching polish.

Step 1: Stabilize data fetcher

Goal:

consistent NSE symbol normalization
clean OHLCV data
missing-value handling
caching
sensible error messages

Checklist:

ensure .NS suffix logic works
validate empty DataFrame cases
handle weekends/holidays gracefully
cache repeated fetches for a few minutes
expose same schema always
Step 2: Standardize indicator preparation

Make one preprocessing function that always returns:

OHLCV
RSI
MACD
SMAs
Bollinger Bands
volume SMA

All detectors should use this same prepared DataFrame.

Step 3: Improve detector output consistency

Every detector should return the same structure:

pattern_type
name
detected_on
confidence
description
plain_english
key_levels
entry/stop/target

This makes frontend integration easy.

Phase 2 — Make the pattern engine convincing

This matters more than adding lots of patterns.

Step 4: Finalize support/resistance

This is foundational because breakout/bounce logic depends on it.

Improve:

merge nearby levels
rank by touches
ignore weak/noisy levels
maybe only keep top 5–8 levels
Step 5: Finalize breakout detector

This should be your hero detector.

Conditions:

close above resistance
breakout happened recently
volume confirmation
not too extended from breakout zone

This pattern demos well because it’s intuitive.

Step 6: Finalize momentum detector

Keep only the ones that are easiest to explain:

RSI bullish divergence
MACD bullish crossover
golden cross

Don’t overcomplicate divergence detection. Even a simple local-swing method is fine for a hackathon.

Step 7: Finalize reversal detector

Pick 1–2 reliable ones only:

double bottom
maybe double top or head-and-shoulders if already working well

Do not include weak detections just to increase count.

Step 8: Finalize candlestick detector

Use only as secondary signals:

hammer
bullish engulfing

These should not dominate ranking unless they occur near support or after a fall.

Phase 3 — Make backtesting the star

This is the unique value prop.

Step 9: Define pattern occurrence rules historically

For each pattern type, define a historical detection rule.

Important:
the historical rule must be the same as live detection logic, or at least close enough.

Examples:

breakout occurrence = close above prior resistance + volume spike
MACD occurrence = bullish crossover on day X
hammer occurrence = candle shape qualifies
Step 10: Define evaluation logic

For each occurrence:

entry = close on signal day or next open
horizon = maybe 10 or 15 trading days
success = positive return, or target hit before stop

For a hackathon, keep it simple and consistent.

Step 11: Compute core stats

Per stock + pattern:

sample count
win rate
avg gain
avg loss
RR ratio
maybe median return
Step 12: Add “insufficient data” logic

Very important.

If occurrences < 3 or < 5:

don’t pretend it is reliable
show “low sample size”

This honesty actually improves credibility.

Phase 4 — Replace LLM dependency with free explanation logic

This is the cleanest no-paid-resources move.

Step 13: Build rule-based explainer

Instead of external LLM, create generate_explanation(pattern, backtest).

Example output structure:

paragraph 1: what pattern means
paragraph 2: stock-specific historical result
paragraph 3: what invalidates the setup

This is enough.

Example:

RELIANCE has moved above a price zone where sellers repeatedly appeared earlier. The higher-than-normal volume suggests stronger buying interest than usual.

Over the past 5 years, similar breakouts on RELIANCE produced positive returns 71% of the time across 17 cases.

This setup weakens if price falls back below the breakout level or if volume dries up over the next few sessions.

That is basically what the judges want.

Phase 5 — Build the frontend experience

Do this after backend is stable.

Step 14: Build ticker search

Needs:

searchable ticker list
debounce
company name + symbol display
fallback manual entry
Step 15: Build candlestick chart

Show:

OHLC candles
horizontal support/resistance lines
maybe entry/stop/target lines for selected pattern
Step 16: Build pattern cards

Each card should show:

pattern name
confidence
one-line meaning
entry / stop / target
detected date
CTA-like label: bullish / bearish / neutral
Step 17: Build backtest stats component

Show:

win rate bar
sample count
avg gain
avg loss
RR ratio

This is one of the strongest UI elements.

Step 18: Build explanation panel

When a pattern card is selected:

show the plain-English explanation
highlight the levels on chart
Step 19: Add empty/loading/error states

Examples:

“No strong patterns detected”
“Ticker not found”
“Fetching latest data”
“Historical sample too small for reliable stats”

These make the product feel real.

Phase 6 — Add hackathon polish

This is where demos are won.

Step 20: Rank and filter patterns

Sort by:

confidence
recency
backtest win rate
sample size

Also add:

high-confidence only toggle
Step 21: Add tags like
“High confidence”
“Backed by 14 historical cases”
“Low sample size”
“Bullish”
Step 22: Make the UI opinionated

Don’t just dump raw numbers. Summarize:

“Strong bullish breakout”
“Momentum improving”
“Near major support”
“Signal unreliable: low historical sample”
Step 23: Prepare a safe demo ticker list

Pre-check these stocks before final demo so you know what appears.

Step 24: Write a crisp story

Your product story is:

retail investors don’t understand charts
pattern tools are generic
we personalize technical analysis to each stock
we explain it simply
we back it with history

That story matters as much as code.