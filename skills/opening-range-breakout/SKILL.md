# 9:30 Opening Range Breakout Strategy

A codified day-trading strategy based on the opening 5-minute range and
Fair Value Gap confirmation, targeting a fixed 2:1 reward-to-risk on every trade.

## Strategy Rules (exact, from source)

| Step | Rule |
|------|------|
| 1 | Mark the **high and low** of the 5-minute candle that forms at **9:30–9:35 AM ET** |
| 2 | Drop to the **1-minute chart** and watch for price to break above or below that range |
| 3 | A valid break requires a **Fair Value Gap (FVG)** — not a plain candle close or wick |
| 4 | **Enter** at the close of the FVG signal candle |
| 5 | **Stop loss** at the low (long) or high (short) of the first 1-min candle that closed outside the range |
| 6 | **Take profit** at a fixed **2:1 reward-to-risk** from entry |

## Fair Value Gap Definition

A Fair Value Gap is a 3-candle pattern indicating institutional momentum:

- **Bullish FVG**: `candle[i].low > candle[i-2].high` — upward price gap; buyers in control
- **Bearish FVG**: `candle[i].high < candle[i-2].low` — downward price gap; sellers in control

The FVG must align with the breakout direction to be valid.

## Files

```
scripts/
  strategy.py   — Signal generator: loads CSV, finds range, detects FVG, outputs trade setup
  backtest.py   — Backtester: replays all days, simulates outcomes, prints performance report
```

## CSV Format

1-minute OHLCV data, Eastern time zone, one row per bar:

```
datetime,open,high,low,close,volume
2024-01-15 09:30:00,450.10,451.20,449.80,450.90,123456
2024-01-15 09:31:00,450.90,452.00,450.50,451.75,98000
...
```

## Usage

### Generate a signal for a specific date
```bash
python scripts/strategy.py --csv data.csv --date 2024-01-15
```

### Generate signals for all dates in the CSV
```bash
python scripts/strategy.py --csv data.csv
```

### List all available dates
```bash
python scripts/strategy.py --csv data.csv --list-dates
```

### Run a full backtest
```bash
python scripts/backtest.py --csv data.csv
```

### Backtest with slippage and commission (per-side, in price units)
```bash
python scripts/backtest.py --csv data.csv --slippage 0.01 --commission 0.005
```

## Sample Output

### Signal generator
```
=== 2024-01-15 ===
  Opening range : 449.8000 – 451.2000
  Breakout      : 09:38  close=451.5500
  FVG           : bullish  gap=451.2000–451.6000
  LONG  ^ | Entry 451.5500  SL 451.1000  TP 452.4500  Risk 0.4500  R:R 1:2.0  Signal @ 09:40
```

### Backtest report
```
=======================================================
  9:30 Opening Range Breakout — Backtest Report
=======================================================
  Signals generated           : 42
  Closed trades               : 40
    Wins                      : 26
    Losses                    : 14
    Open (unresolved)         : 2
  Win rate (closed)           : 65.0%
  Average win                 : +2.00R
  Average loss                : -1.00R
  Expectancy per trade        : +0.650R
  Total net P&L               : +38.00R
  Max drawdown                : -4.00R
=======================================================
```

## Key Design Decisions

- **One trade per day** — the strategy fires on the first valid FVG after the first breakout.
- **Stop anchor** — placed at the breakout candle's low/high, not the range boundary, to account for the momentum of the break itself.
- **No re-entries** — if the first FVG setup is stopped out, no additional trades are taken that day.
- **Session limit** — no new entries after 4:00 PM ET; open trades are closed at session end.
- **No indicator dependencies** — pure price action: range levels + FVG pattern only.
