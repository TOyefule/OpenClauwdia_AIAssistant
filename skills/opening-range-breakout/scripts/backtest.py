#!/usr/bin/env python3
"""
9:30 Opening Range Breakout — Backtester
==========================================
Replays every trading day in the CSV, simulates each trade to its outcome
(stop hit or target hit), and prints a full performance report.

Usage:
    python backtest.py --csv data.csv
    python backtest.py --csv data.csv --slippage 0.01
    python backtest.py --csv data.csv --commission 0.005 --slippage 0.01

CSV format (1-minute OHLCV, Eastern time):
    datetime,open,high,low,close,volume
    2024-01-15 09:30:00,450.10,451.20,449.80,450.90,123456
    ...
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from strategy import (
    Candle,
    SESSION_END_TIME,
    TradeSignal,
    analyze_day,
    group_by_date,
    load_candles,
)

# ---------------------------------------------------------------------------
# Trade result
# ---------------------------------------------------------------------------

@dataclass
class TradeResult:
    date: str
    signal: TradeSignal
    outcome: str        # "win", "loss", or "open" (session ended before resolution)
    exit_price: float
    exit_time: datetime
    pnl_r: float        # P&L in R-multiples (-1.0 for loss, +2.0 for win)
    pnl_points: float   # raw price move


def simulate_trade(
    signal: TradeSignal,
    date_str: str,
    post_signal_candles: list[Candle],
    slippage: float = 0.0,
    commission: float = 0.0,
) -> TradeResult:
    """
    Walk candle-by-candle after the signal and determine the exit.

    Priority per candle: check stop first (conservative), then target.
    Slippage and commission are applied symmetrically per side.
    """
    adj_entry = signal.entry
    if signal.direction == "long":
        adj_entry += slippage
        effective_stop = signal.stop_loss
        effective_tp = signal.take_profit + slippage  # target moves with entry
    else:
        adj_entry -= slippage
        effective_stop = signal.stop_loss
        effective_tp = signal.take_profit - slippage

    total_cost = commission * 2  # entry + exit

    for candle in post_signal_candles:
        if signal.direction == "long":
            # Stop touched if candle low reaches or goes below stop
            if candle.low <= effective_stop:
                exit_p = effective_stop - slippage
                pnl_pts = exit_p - adj_entry - total_cost
                return TradeResult(
                    date=date_str,
                    signal=signal,
                    outcome="loss",
                    exit_price=exit_p,
                    exit_time=candle.dt,
                    pnl_r=-1.0,
                    pnl_points=pnl_pts,
                )
            # Target touched
            if candle.high >= effective_tp:
                exit_p = effective_tp
                pnl_pts = exit_p - adj_entry - total_cost
                return TradeResult(
                    date=date_str,
                    signal=signal,
                    outcome="win",
                    exit_price=exit_p,
                    exit_time=candle.dt,
                    pnl_r=2.0,
                    pnl_points=pnl_pts,
                )
        else:  # short
            if candle.high >= effective_stop:
                exit_p = effective_stop + slippage
                pnl_pts = adj_entry - exit_p - total_cost
                return TradeResult(
                    date=date_str,
                    signal=signal,
                    outcome="loss",
                    exit_price=exit_p,
                    exit_time=candle.dt,
                    pnl_r=-1.0,
                    pnl_points=pnl_pts,
                )
            if candle.low <= effective_tp:
                exit_p = effective_tp
                pnl_pts = adj_entry - exit_p - total_cost
                return TradeResult(
                    date=date_str,
                    signal=signal,
                    outcome="win",
                    exit_price=exit_p,
                    exit_time=candle.dt,
                    pnl_r=2.0,
                    pnl_points=pnl_pts,
                )

    # Session ended without resolution — mark as open/flat at last candle close
    last = post_signal_candles[-1] if post_signal_candles else signal.signal_candle
    exit_p = last.close
    if signal.direction == "long":
        pnl_pts = exit_p - adj_entry - total_cost
    else:
        pnl_pts = adj_entry - exit_p - total_cost
    risk = signal.risk if signal.risk else 1
    pnl_r = pnl_pts / risk

    return TradeResult(
        date=date_str,
        signal=signal,
        outcome="open",
        exit_price=exit_p,
        exit_time=last.dt,
        pnl_r=pnl_r,
        pnl_points=pnl_pts,
    )


# ---------------------------------------------------------------------------
# Performance report
# ---------------------------------------------------------------------------

def print_report(results: list[TradeResult]) -> None:
    if not results:
        print("No trades to report.")
        return

    wins   = [r for r in results if r.outcome == "win"]
    losses = [r for r in results if r.outcome == "loss"]
    opens  = [r for r in results if r.outcome == "open"]
    closed = wins + losses

    total_r  = sum(r.pnl_r for r in results)
    win_rate = len(wins) / len(closed) * 100 if closed else 0.0
    avg_win  = sum(r.pnl_r for r in wins) / len(wins) if wins else 0.0
    avg_loss = sum(r.pnl_r for r in losses) / len(losses) if losses else 0.0
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

    # Max drawdown in R (peak-to-trough on cumulative R curve)
    cum_r = 0.0
    peak  = 0.0
    max_dd = 0.0
    for r in results:
        cum_r += r.pnl_r
        if cum_r > peak:
            peak = cum_r
        dd = peak - cum_r
        if dd > max_dd:
            max_dd = dd

    sep = "=" * 55
    print(f"\n{sep}")
    print("  9:30 Opening Range Breakout — Backtest Report")
    print(sep)
    print(f"  Total trading days analyzed : {len(results) + (0)}")
    print(f"  Signals generated           : {len(results)}")
    print(f"  Closed trades               : {len(closed)}")
    print(f"    Wins                      : {len(wins)}")
    print(f"    Losses                    : {len(losses)}")
    print(f"    Open (unresolved)         : {len(opens)}")
    print(f"  Win rate (closed)           : {win_rate:.1f}%")
    print(f"  Average win                 : {avg_win:+.2f}R")
    print(f"  Average loss                : {avg_loss:+.2f}R")
    print(f"  Expectancy per trade        : {expectancy:+.3f}R")
    print(f"  Total net P&L               : {total_r:+.2f}R")
    print(f"  Max drawdown                : -{max_dd:.2f}R")
    print(sep)
    print()

    # Trade-by-trade log
    print(f"{'Date':<12} {'Dir':<6} {'Entry':>8} {'SL':>8} {'TP':>8} "
          f"{'Exit':>8} {'Time':<7} {'R':>6}  Outcome")
    print("-" * 75)
    for r in results:
        s = r.signal
        print(
            f"{r.date:<12} "
            f"{s.direction.upper():<6} "
            f"{s.entry:>8.3f} "
            f"{s.stop_loss:>8.3f} "
            f"{s.take_profit:>8.3f} "
            f"{r.exit_price:>8.3f} "
            f"{r.exit_time.strftime('%H:%M'):<7} "
            f"{r.pnl_r:>+6.2f}  "
            f"{r.outcome.upper()}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="9:30 Opening Range Breakout — backtester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--csv", required=True, metavar="FILE",
                   help="Path to 1-minute OHLCV CSV file")
    p.add_argument("--slippage", type=float, default=0.0, metavar="POINTS",
                   help="One-way slippage per trade in price units (default: 0)")
    p.add_argument("--commission", type=float, default=0.0, metavar="POINTS",
                   help="One-way commission per trade in price units (default: 0)")
    return p


def main() -> None:
    args = build_parser().parse_args()

    all_candles = load_candles(args.csv)
    by_date     = group_by_date(all_candles)
    results: list[TradeResult] = []

    for date_str in sorted(by_date.keys()):
        day = by_date[date_str]
        signal = analyze_day(day)
        if signal is None:
            continue

        # Candles that come AFTER the signal candle, within the session
        post_signal = [
            c for c in day
            if c.dt > signal.signal_candle.dt and c.dt.time() < SESSION_END_TIME
        ]

        result = simulate_trade(
            signal=signal,
            date_str=date_str,
            post_signal_candles=post_signal,
            slippage=args.slippage,
            commission=args.commission,
        )
        results.append(result)

    print_report(results)


if __name__ == "__main__":
    main()
