# Backtest Quick Check Report

Date: 2026-03-29

## Environment
- Backend URL: http://127.0.0.1:8002
- Holding period: 15 days (default)

## Health Check
- GET /health -> {"status":"ok"}

## Backtest Results (Summary Table)

| Ticker | Pattern | Sample Count | Win Rate | Avg Gain % | Avg Loss % | RR | Median % | Note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| RELIANCE | breakout | 18 | 0.556 | 2.76 | -4.92 | 0.56 | 0.64 | Based on 18 historical occurrences over 5y |
| RELIANCE | macd_crossover | 43 | 0.488 | 4.65 | -4.80 | 0.97 | -0.92 | Based on 43 historical occurrences over 5y |
| RELIANCE | golden_cross | 3 | 0.667 | 8.62 | -2.14 | 4.02 | 3.40 | Based on 3 historical occurrences over 5y - low sample size, interpret cautiously |
| RELIANCE | double_top | 11 | 0.000 | null | -4.36 | null | -4.49 | Based on 11 historical occurrences over 5y |
| RELIANCE | head_shoulders | 1 | null | null | null | null | null | Insufficient historical data - fewer than 3 occurrences found |
| SBIN | head_shoulders | 0 | null | null | null | null | null | Insufficient historical data - fewer than 3 occurrences found |
| TCS | breakout | 13 | 0.462 | 1.97 | -3.00 | 0.66 | -0.48 | Based on 13 historical occurrences over 5y |
| TCS | macd_crossover | 40 | 0.500 | 3.40 | -5.04 | 0.68 | -0.33 | Based on 40 historical occurrences over 5y |
| INFY | golden_cross | 4 | 0.500 | 1.94 | -2.86 | 0.68 | 0.37 | Based on 4 historical occurrences over 5y - low sample size, interpret cautiously |
| HDFCBANK | breakout | 21 | 0.524 | 3.49 | -3.92 | 0.89 | 0.06 | Based on 21 historical occurrences over 5y |
| ICICIBANK | macd_crossover | 38 | 0.526 | 3.65 | -1.89 | 1.93 | 0.45 | Based on 38 historical occurrences over 5y |

## Raw JSON Outputs

### RELIANCE breakout
{"pattern_type":"breakout","ticker":"RELIANCE.NS","sample_count":18,"win_rate":0.556,"avg_gain_pct":2.76,"avg_loss_pct":-4.92,"rr_ratio":0.56,"median_return_pct":0.64,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 18 historical occurrences over 5y"}

### RELIANCE macd_crossover
{"pattern_type":"macd_crossover","ticker":"RELIANCE.NS","sample_count":43,"win_rate":0.488,"avg_gain_pct":4.65,"avg_loss_pct":-4.8,"rr_ratio":0.97,"median_return_pct":-0.92,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 43 historical occurrences over 5y"}

### RELIANCE golden_cross
{"pattern_type":"golden_cross","ticker":"RELIANCE.NS","sample_count":3,"win_rate":0.667,"avg_gain_pct":8.62,"avg_loss_pct":-2.14,"rr_ratio":4.02,"median_return_pct":3.4,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 3 historical occurrences over 5y - low sample size, interpret cautiously"}

### RELIANCE double_top
{"pattern_type":"double_top","ticker":"RELIANCE.NS","sample_count":11,"win_rate":0.0,"avg_gain_pct":null,"avg_loss_pct":-4.36,"rr_ratio":null,"median_return_pct":-4.49,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 11 historical occurrences over 5y"}

### RELIANCE head_shoulders
{"pattern_type":"head_shoulders","ticker":"RELIANCE.NS","sample_count":1,"win_rate":null,"avg_gain_pct":null,"avg_loss_pct":null,"rr_ratio":null,"median_return_pct":null,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Insufficient historical data - fewer than 3 occurrences found"}

### SBIN head_shoulders
{"pattern_type":"head_shoulders","ticker":"SBIN.NS","sample_count":0,"win_rate":null,"avg_gain_pct":null,"avg_loss_pct":null,"rr_ratio":null,"median_return_pct":null,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Insufficient historical data - fewer than 3 occurrences found"}

### TCS breakout
{"pattern_type":"breakout","ticker":"TCS.NS","sample_count":13,"win_rate":0.462,"avg_gain_pct":1.97,"avg_loss_pct":-3.0,"rr_ratio":0.66,"median_return_pct":-0.48,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 13 historical occurrences over 5y"}

### TCS macd_crossover
{"pattern_type":"macd_crossover","ticker":"TCS.NS","sample_count":40,"win_rate":0.5,"avg_gain_pct":3.4,"avg_loss_pct":-5.04,"rr_ratio":0.68,"median_return_pct":-0.33,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 40 historical occurrences over 5y"}

### INFY golden_cross
{"pattern_type":"golden_cross","ticker":"INFY.NS","sample_count":4,"win_rate":0.5,"avg_gain_pct":1.94,"avg_loss_pct":-2.86,"rr_ratio":0.68,"median_return_pct":0.37,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 4 historical occurrences over 5y - low sample size, interpret cautiously"}

### HDFCBANK breakout
{"pattern_type":"breakout","ticker":"HDFCBANK.NS","sample_count":21,"win_rate":0.524,"avg_gain_pct":3.49,"avg_loss_pct":-3.92,"rr_ratio":0.89,"median_return_pct":0.06,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 21 historical occurrences over 5y"}

### ICICIBANK macd_crossover
{"pattern_type":"macd_crossover","ticker":"ICICIBANK.NS","sample_count":38,"win_rate":0.526,"avg_gain_pct":3.65,"avg_loss_pct":-1.89,"rr_ratio":1.93,"median_return_pct":0.45,"holding_period_days":15,"entry_mode":"next_open","success_mode":"target_or_positive_return","note":"Based on 38 historical occurrences over 5y"}

## Interpretation Notes

- Health endpoint responded OK.
- Sample counts look plausible (golden cross low counts, MACD higher counts).
- Win rates stay in [0, 1] and losses are negative where expected.
- Low-sample warnings appear for sample_count < 5, as intended.
- Bearish patterns show negative median returns, indicating directional handling is working.
- Head-and-shoulders counts are now low, indicating stricter filtering.

## Debug Check (Bearish Direction)

Double top debug output confirms bearish handling: raw returns are positive while directional returns are negative, and success is 0.0 for those cases.

Example snippet:

{"signal_idx":286.0,"entry_idx":287.0,"exit_idx":302.0,"entry_price":1040.812257084253,"exit_price":1068.8638916015625,"return_pct":2.6951675795876833,"directional_return_pct":-2.6951675795876833,"success":0.0}

## Quick Verdict

- Status: PASS for Phase 3 sanity checks.
- Follow-ups: None required before Phase 4.
