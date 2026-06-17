#!/usr/bin/env python3
"""
9:30 Opening Range Breakout Strategy
=====================================
Source: YouTube Shorts "9:30 Candle Strategy"

Rules:
  1. Mark the high/low of the 5-min candle that spans 9:30–9:35 AM.
  2. Switch to the 1-min chart and watch for price to break above/below that range.
  3. A valid break requires a Fair Value Gap (FVG) — not just a candle close.
  4. Enter on the FVG signal candle's close.
  5. Stop loss: low (long) or high (short) of the first 1-min candle that closed outside the range.
  6. Take profit: 2:1 reward-to-risk from entry.

Usage:
    python strategy.py --csv data.csv
    python strategy.py --csv data.csv --date 2024-01-15
    python strategy.py --csv data.csv --list-dates

CSV format expected (1-minute OHLCV):
    datetime,open,high,low,close,volume
    2024-01-15 09:30:00,450.10,451.20,449.80,450.90,123456
    ...
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPEN_TIME = time(9, 30)        # Market open
RANGE_END_TIME = time(9, 35)   # End of the initial 5-min range candle
SESSION_END_TIME = time(16, 0)  # Market close — no new entries after this
REWARD_RATIO = 2.0              # Fixed 2:1 R:R
SESSION_TZ = "US/Eastern"      # Informational only; data must already be in ET

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Candle:
    dt: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class FairValueGap:
    """Three-candle FVG pattern (candles i-2, i-1, i)."""
    direction: str          # "bullish" or "bearish"
    gap_top: float          # upper boundary of the gap
    gap_bottom: float       # lower boundary of the gap
    signal_candle: Candle   # the third candle that completes the pattern


@dataclass
class TradeSignal:
    direction: str          # "long" or "short"
    entry: float
    stop_loss: float
    take_profit: float
    risk: float             # |entry - stop_loss|
    fvg: FairValueGap
    breakout_candle: Candle
    signal_candle: Candle   # same as fvg.signal_candle
    range_high: float
    range_low: float

    @property
    def reward(self) -> float:
        return self.risk * REWARD_RATIO

    def summary(self) -> str:
        arrow = "LONG  ^" if self.direction == "long" else "SHORT v"
        return (
            f"{arrow} | "
            f"Entry {self.entry:.4f}  "
            f"SL {self.stop_loss:.4f}  "
            f"TP {self.take_profit:.4f}  "
            f"Risk {self.risk:.4f}  "
            f"R:R 1:{REWARD_RATIO:.1f}  "
            f"Signal @ {self.signal_candle.dt.strftime('%H:%M')}"
        )


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_candles(path: str) -> list[Candle]:
    """Load 1-minute OHLCV CSV into a list of Candle objects.

    Accepts two common datetime formats:
      - "2024-01-15 09:30:00"
      - "2024-01-15T09:30:00"
    """
    candles: list[Candle] = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            raw_dt = row.get("datetime") or row.get("time") or row.get("timestamp") or ""
            raw_dt = raw_dt.replace("T", " ").strip()
            try:
                dt = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M")
            candles.append(
                Candle(
                    dt=dt,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0)),
                )
            )
    candles.sort(key=lambda c: c.dt)
    return candles


def group_by_date(candles: list[Candle]) -> dict[str, list[Candle]]:
    groups: dict[str, list[Candle]] = {}
    for c in candles:
        key = c.dt.strftime("%Y-%m-%d")
        groups.setdefault(key, []).append(c)
    return groups


# ---------------------------------------------------------------------------
# Fair Value Gap detection
# ---------------------------------------------------------------------------

def detect_fvg(c0: Candle, c1: Candle, c2: Candle) -> Optional[FairValueGap]:
    """
    Identify a Fair Value Gap in a 3-candle window.

    Bullish FVG: c2.low > c0.high  — an upward gap; buyers dominating.
    Bearish FVG: c2.high < c0.low  — a downward gap; sellers dominating.
    """
    if c2.low > c0.high:
        return FairValueGap(
            direction="bullish",
            gap_bottom=c0.high,
            gap_top=c2.low,
            signal_candle=c2,
        )
    if c2.high < c0.low:
        return FairValueGap(
            direction="bearish",
            gap_bottom=c2.high,
            gap_top=c0.low,
            signal_candle=c2,
        )
    return None


# ---------------------------------------------------------------------------
# Core strategy for a single trading day
# ---------------------------------------------------------------------------

def analyze_day(day_candles: list[Candle]) -> Optional[TradeSignal]:
    """
    Run the 9:30 Opening Range Breakout strategy for one trading day.

    Returns the first valid TradeSignal, or None if no setup forms.

    Step-by-step:
      1. Isolate the 9:30–9:35 5-minute range from the 1-min candles.
      2. Find the first 1-min candle that CLOSES outside that range.
      3. After the breakout, scan subsequent 1-min candles for an FVG
         in the breakout direction.
      4. Build a TradeSignal with correct stop and 2:1 target.
    """

    # Step 1 — Build the initial 5-min range from the 9:30–9:34 1-min candles
    range_candles = [
        c for c in day_candles
        if c.dt.time() >= OPEN_TIME and c.dt.time() < RANGE_END_TIME
    ]
    if not range_candles:
        return None

    range_high = max(c.high for c in range_candles)
    range_low = min(c.low for c in range_candles)

    # Step 2 — Post-range candles (9:35 onward, within session)
    post_range = [
        c for c in day_candles
        if c.dt.time() >= RANGE_END_TIME and c.dt.time() < SESSION_END_TIME
    ]
    if len(post_range) < 3:
        return None

    # Find the first candle that closes OUTSIDE the range (the breakout candle)
    breakout_candle: Optional[Candle] = None
    breakout_dir: Optional[str] = None
    breakout_idx: int = -1

    for idx, c in enumerate(post_range):
        if c.close > range_high:
            breakout_candle = c
            breakout_dir = "long"
            breakout_idx = idx
            break
        if c.close < range_low:
            breakout_candle = c
            breakout_dir = "short"
            breakout_idx = idx
            break

    if breakout_candle is None:
        return None  # Price never escaped the opening range today

    # Stop loss anchor: low (long) or high (short) of the breakout candle
    # This is the level that proves the breakout was false if hit
    stop_anchor = breakout_candle.low if breakout_dir == "long" else breakout_candle.high

    # Step 3 — Scan for the first FVG that aligns with the breakout direction
    # We need at least 2 candles after the breakout candle for a 3-candle FVG
    post_breakout = post_range[breakout_idx:]  # includes breakout candle at [0]

    fvg: Optional[FairValueGap] = None
    for i in range(2, len(post_breakout)):
        c0, c1, c2 = post_breakout[i - 2], post_breakout[i - 1], post_breakout[i]
        candidate = detect_fvg(c0, c1, c2)
        if candidate is None:
            continue
        # FVG must align with breakout direction
        if breakout_dir == "long" and candidate.direction == "bullish":
            fvg = candidate
            break
        if breakout_dir == "short" and candidate.direction == "bearish":
            fvg = candidate
            break

    if fvg is None:
        return None  # Breakout was not confirmed by an FVG

    # Step 4 — Calculate trade parameters
    entry = fvg.signal_candle.close
    stop_loss = stop_anchor
    risk = abs(entry - stop_loss)

    if risk == 0:
        return None  # Degenerate case; skip

    if breakout_dir == "long":
        take_profit = entry + REWARD_RATIO * risk
    else:
        take_profit = entry - REWARD_RATIO * risk

    return TradeSignal(
        direction=breakout_dir,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk=risk,
        fvg=fvg,
        breakout_candle=breakout_candle,
        signal_candle=fvg.signal_candle,
        range_high=range_high,
        range_low=range_low,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="9:30 Opening Range Breakout — signal generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--csv", required=True, metavar="FILE",
                   help="Path to 1-minute OHLCV CSV file")
    p.add_argument("--date", metavar="YYYY-MM-DD",
                   help="Analyze a specific date (default: all dates in CSV)")
    p.add_argument("--list-dates", action="store_true",
                   help="List all available trading dates in the CSV and exit")
    return p


def main() -> None:
    args = build_parser().parse_args()

    candles = load_candles(args.csv)
    by_date = group_by_date(candles)

    if args.list_dates:
        print("Available dates:")
        for d in sorted(by_date.keys()):
            print(f"  {d}  ({len(by_date[d])} candles)")
        return

    dates = sorted(by_date.keys())
    if args.date:
        if args.date not in by_date:
            print(f"ERROR: date {args.date} not found in CSV.", file=sys.stderr)
            sys.exit(1)
        dates = [args.date]

    signals_found = 0
    for date_str in dates:
        signal = analyze_day(by_date[date_str])
        if signal:
            signals_found += 1
            print(f"\n=== {date_str} ===")
            print(f"  Opening range : {signal.range_low:.4f} – {signal.range_high:.4f}")
            print(f"  Breakout      : {signal.breakout_candle.dt.strftime('%H:%M')}  "
                  f"close={signal.breakout_candle.close:.4f}")
            print(f"  FVG           : {signal.fvg.direction}  "
                  f"gap={signal.fvg.gap_bottom:.4f}–{signal.fvg.gap_top:.4f}")
            print(f"  Signal        : {signal.summary()}")

    if signals_found == 0:
        print("No valid setups found for the given date(s).")
    else:
        print(f"\n{signals_found} signal(s) across {len(dates)} day(s).")


if __name__ == "__main__":
    main()
