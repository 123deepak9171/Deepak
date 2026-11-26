#!/usr/bin/env python3
"""
BTC Scalping Agent (Binance BTCUSDT, 1-minute candles) -- PAPER TRADING ONLY.

Modes:
  python scalper.py backtest --days 7        # download real Binance history and test
  python scalper.py backtest --synthetic     # offline test on fake data
  python scalper.py live                     # live market data, fake money, runs 24/7

No API key is needed. No real order is ever placed by this script.
"""
import argparse
import csv
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

BASE_URLS = ["https://api.binance.com", "https://data-api.binance.vision"]


# --------------------------------------------------------------------------- #
# Settings (change these to tune the agent)
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    symbol: str = "BTCUSDT"
    start_balance: float = 100.0
    fee_rate: float = 0.0005          # 0.05% per side (Binance futures taker)
    leverage_cap: float = 3.0         # position value max = 3x balance
    risk_per_trade: float = 0.01      # lose max 1% of balance per trade
    ema_fast: int = 9
    ema_slow: int = 21
    rsi_len: int = 7
    atr_len: int = 14
    sl_atr: float = 1.0               # stop-loss = 1.0 x ATR
    tp_atr: float = 1.8               # take-profit = 1.8 x ATR
    max_hold_bars: int = 15           # close trade after 15 minutes anyway
    min_tp_vs_fees: float = 1.5       # TP move must be >= 1.5x round-trip fees
    daily_loss_limit: float = 0.05    # stop for the day after -5%
    max_consec_losses: int = 4        # then pause...
    cooldown_bars: int = 30           # ...for 30 minutes
    trade_log: str = "trades.csv"


# --------------------------------------------------------------------------- #
# Market data
# --------------------------------------------------------------------------- #
def _get(path, params):
    last_err = None
    for base in BASE_URLS:
        try:
            r = requests.get(base + path, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # try next mirror
            last_err = e
    raise RuntimeError(f"Binance se data nahi mila: {last_err}")


def klines_to_df(rows):
    df = pd.DataFrame(rows, columns=[
        "open_time", "open", "high", "low", "close", "volume", "close_time",
        "qv", "trades", "tb", "tq", "ignore"])
    df = df[["open_time", "open", "high", "low", "close", "volume", "close_time"]]
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = df[c].astype(float)
    return df.reset_index(drop=True)


def fetch_recent(symbol, limit=200):
    return klines_to_df(_get("/api/v3/klines",
                             {"symbol": symbol, "interval": "1m", "limit": limit}))


def fetch_history(symbol, days):
    end = int(time.time() * 1000)
    start = end - days * 24 * 60 * 60 * 1000
    rows = []
    while start < end:
        batch = _get("/api/v3/klines", {"symbol": symbol, "interval": "1m",
                                        "startTime": start, "limit": 1000})
        if not batch:
            break
        rows.extend(batch)
        start = batch[-1][0] + 60_000
        print(f"\r  downloaded {len(rows)} candles...", end="", flush=True)
        time.sleep(0.2)
    print()
    return klines_to_df(rows)


def synthetic_history(n=10_000, seed=7, start_price=95_000.0):
    """Random-walk BTC-like data with changing volatility (offline testing)."""
    rng = np.random.default_rng(seed)
    vol = 0.0008 * np.exp(np.cumsum(rng.normal(0, 0.02, n)).clip(-1, 1))
    rets = rng.normal(0, vol)
    close = start_price * np.exp(np.cumsum(rets))
    open_ = np.r_[start_price, close[:-1]]
    spread = np.abs(rng.normal(0, vol)) * close
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    t0 = 1_700_000_000_000
    ot = t0 + np.arange(n) * 60_000
    return pd.DataFrame({"open_time": ot, "open": open_, "high": high, "low": low,
                         "close": close, "volume": rng.uniform(5, 50, n),
                         "close_time": ot + 59_999})


# --------------------------------------------------------------------------- #
# Indicators + signal
# --------------------------------------------------------------------------- #
def add_indicators(df, cfg):
    df = df.copy()
    df["ema_f"] = df["close"].ewm(span=cfg.ema_fast, adjust=False).mean()
    df["ema_s"] = df["close"].ewm(span=cfg.ema_slow, adjust=False).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / cfg.rsi_len, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / cfg.rsi_len, adjust=False).mean()
    df["rsi"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    prev_c = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev_c).abs(),
                    (df["low"] - prev_c).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(alpha=1 / cfg.atr_len, adjust=False).mean()
    return df


def signal(df, i, cfg):
    """Return 'LONG', 'SHORT' or None using the CLOSED candle at index i."""
    if i < cfg.ema_slow + 5:
        return None
    r = df.iloc[i]
    p = df.iloc[i - 1]
    if any(math.isnan(x) for x in (r.rsi, p.rsi, r.atr)):
        return None
    # Only trade if expected move clearly beats the fees
    tp_pct = cfg.tp_atr * r.atr / r.close
    if tp_pct < cfg.min_tp_vs_fees * 2 * cfg.fee_rate:
        return None
    up = r.ema_f > r.ema_s and r.close > r.ema_s
    down = r.ema_f < r.ema_s and r.close < r.ema_s
    # Pullback in trend, then momentum turns back with the trend
    if up and p.rsi < 40 <= r.rsi:
        return "LONG"
    if down and p.rsi > 60 >= r.rsi:
        return "SHORT"
    return None


# --------------------------------------------------------------------------- #
# Paper trading account with risk rules
# --------------------------------------------------------------------------- #
@dataclass
class Position:
    side: str
    entry: float
    qty: float
    sl: float
    tp: float
    opened_bar: int
    opened_at: str


@dataclass
class PaperAccount:
    cfg: Config
    balance: float = 0.0
    pos: Position = None
    trades: list = field(default_factory=list)
    consec_losses: int = 0
    pause_until_bar: int = -1
    day: str = ""
    day_start_balance: float = 0.0
    stopped_for_day: bool = False

    def __post_init__(self):
        self.balance = self.cfg.start_balance
        self.day_start_balance = self.balance

    # ---- risk gate ----
    def new_day_check(self, day):
        if day != self.day:
            self.day = day
            self.day_start_balance = self.balance
            self.stopped_for_day = False

    def can_trade(self, bar):
        if self.pos or self.stopped_for_day or bar < self.pause_until_bar:
            return False
        return self.balance > 1.0

    # ---- open / close ----
    def open(self, side, price, atr, bar, ts):
        sl_dist = self.cfg.sl_atr * atr
        risk_usd = self.balance * self.cfg.risk_per_trade
        qty = risk_usd / sl_dist
        qty = min(qty, self.balance * self.cfg.leverage_cap / price)
        if qty * price < 5:            # Binance minimum notional ~ $5
            return None
        sl = price - sl_dist if side == "LONG" else price + sl_dist
        tp_dist = self.cfg.tp_atr * atr
        tp = price + tp_dist if side == "LONG" else price - tp_dist
        self.balance -= qty * price * self.cfg.fee_rate
        self.pos = Position(side, price, qty, sl, tp, bar, ts)
        return self.pos

    def check_exit(self, high, low, close, bar, ts):
        """Exit on SL / TP / time. If SL and TP both touched, assume SL (worst case)."""
        p = self.pos
        if not p:
            return None
        exit_px, reason = None, None
        if p.side == "LONG":
            if low <= p.sl:
                exit_px, reason = p.sl, "STOP"
            elif high >= p.tp:
                exit_px, reason = p.tp, "TARGET"
        else:
            if high >= p.sl:
                exit_px, reason = p.sl, "STOP"
            elif low <= p.tp:
                exit_px, reason = p.tp, "TARGET"
        if exit_px is None and bar - p.opened_bar >= self.cfg.max_hold_bars:
            exit_px, reason = close, "TIME"
        if exit_px is None:
            return None
        return self._close(exit_px, reason, bar, ts)

    def _close(self, px, reason, bar, ts):
        p = self.pos
        gross = (px - p.entry) * p.qty * (1 if p.side == "LONG" else -1)
        fee_out = p.qty * px * self.cfg.fee_rate
        fee_in = p.qty * p.entry * self.cfg.fee_rate
        self.balance += gross - fee_out
        net = gross - fee_in - fee_out
        t = dict(opened=p.opened_at, closed=ts, side=p.side, entry=round(p.entry, 2),
                 exit=round(px, 2), qty=round(p.qty, 6), reason=reason,
                 pnl=round(net, 4), balance=round(self.balance, 4))
        self.trades.append(t)
        self.pos = None
        # risk rules
        self.consec_losses = self.consec_losses + 1 if net < 0 else 0
        if self.consec_losses >= self.cfg.max_consec_losses:
            self.pause_until_bar = bar + self.cfg.cooldown_bars
            self.consec_losses = 0
        if self.balance <= self.day_start_balance * (1 - self.cfg.daily_loss_limit):
            self.stopped_for_day = True
        return t

    def log_trade(self, t):
        new = not os.path.exists(self.cfg.trade_log)
        with open(self.cfg.trade_log, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(t.keys()))
            if new:
                w.writeheader()
            w.writerow(t)


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def ts_str(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def report(acct, cfg, title):
    tr = acct.trades
    wins = [t for t in tr if t["pnl"] > 0]
    pnl = acct.balance - cfg.start_balance
    bal_curve = [cfg.start_balance] + [t["balance"] for t in tr]
    peak, max_dd = bal_curve[0], 0.0
    for b in bal_curve:
        peak = max(peak, b)
        max_dd = max(max_dd, (peak - b) / peak)
    fees = sum(t["qty"] * (t["entry"] + t["exit"]) * cfg.fee_rate for t in tr)
    print("\n" + "=" * 52)
    print(f" {title}")
    print("=" * 52)
    print(f" Shuruaati balance : ${cfg.start_balance:,.2f}")
    print(f" Aakhri balance    : ${acct.balance:,.2f}  ({pnl / cfg.start_balance:+.2%})")
    print(f" Kul trades        : {len(tr)}")
    if tr:
        print(f" Jeet ka %         : {len(wins) / len(tr):.1%}")
        print(f" Sabse bada girav  : {max_dd:.2%}  (max drawdown)")
        print(f" Fees di           : ${fees:,.2f}")
        by = {}
        for t in tr:
            by[t["reason"]] = by.get(t["reason"], 0) + 1
        print(f" Exit reasons      : {by}")
    print("=" * 52)


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #
def run_backtest(df, cfg):
    df = add_indicators(df, cfg)
    acct = PaperAccount(cfg)
    pending = None
    for i in range(len(df)):
        r = df.iloc[i]
        ts = ts_str(r.open_time)
        acct.new_day_check(ts[:10])
        if pending and acct.can_trade(i):      # enter at this candle's open
            acct.open(pending[0], r.open, pending[1], i, ts)
        pending = None
        if acct.pos:
            acct.check_exit(r.high, r.low, r.close, i, ts)
        if not acct.pos and acct.can_trade(i + 1):
            s = signal(df, i, cfg)
            if s:
                pending = (s, r.atr)
    if acct.pos:
        acct._close(df.iloc[-1].close, "END", len(df), ts_str(df.iloc[-1].open_time))
    pd.DataFrame(acct.trades).to_csv("backtest_trades.csv", index=False)
    report(acct, cfg, f"BACKTEST  ({len(df)} candles = {len(df) / 1440:.1f} din)")
    print(" Har trade ki detail: backtest_trades.csv\n")
    return acct


def run_live(cfg, poll_sec=5):
    print(f"LIVE PAPER TRADING shuru: {cfg.symbol}, balance ${cfg.start_balance}")
    print("Asli paisa nahi lagega. Band karne ke liye Ctrl+C dabayein.\n")
    acct = PaperAccount(cfg)
    last_closed = None
    bar = 0
    try:
        while True:
            try:
                df = fetch_recent(cfg.symbol, 200)
            except Exception as e:
                print(f"[network] {e} -- 10 sec me dobara...")
                time.sleep(10)
                continue
            now_ms = int(time.time() * 1000)
            live = df.iloc[-1]
            price = live.close
            ts = ts_str(now_ms)
            acct.new_day_check(ts[:10])

            if acct.pos:
                t = acct.check_exit(price, price, price, bar, ts)
                if t:
                    acct.log_trade(t)
                    print(f"  << CLOSE {t['side']} @ {t['exit']}  {t['reason']}  "
                          f"PnL ${t['pnl']:+.4f}  balance ${t['balance']:.2f}")

            closed = df[df.close_time < now_ms]
            if len(closed) and closed.iloc[-1].open_time != last_closed:
                last_closed = closed.iloc[-1].open_time
                bar += 1
                ind = add_indicators(closed.reset_index(drop=True), cfg)
                r = ind.iloc[-1]
                s = signal(ind, len(ind) - 1, cfg) if acct.can_trade(bar) else None
                if s:
                    p = acct.open(s, price, r.atr, bar, ts)
                    if p:
                        print(f"  >> OPEN {s} @ {price:,.2f}  SL {p.sl:,.2f}  "
                              f"TP {p.tp:,.2f}  qty {p.qty:.6f}")
                state = ("PAUSED (aaj ka loss limit)" if acct.stopped_for_day else
                         f"OPEN {acct.pos.side}" if acct.pos else "waiting")
                n = len(acct.trades)
                w = sum(1 for t in acct.trades if t["pnl"] > 0)
                print(f"[{ts}] BTC ${price:,.2f}  RSI {r.rsi:5.1f}  "
                      f"balance ${acct.balance:.2f}  trades {n} (jeet {w})  {state}")
            time.sleep(poll_sec)
    except KeyboardInterrupt:
        report(acct, cfg, "LIVE PAPER SESSION")


def main():
    ap = argparse.ArgumentParser(description="BTC scalping agent (paper trading)")
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("backtest")
    b.add_argument("--days", type=int, default=7)
    b.add_argument("--synthetic", action="store_true")
    b.add_argument("--csv", help="pehle se save kiya hua candles CSV")
    sub.add_parser("live")
    ap.add_argument("--balance", type=float, default=100.0)
    ap.add_argument("--fee", type=float, default=0.0005,
                    help="fee per side, 0.0005 = 0.05%%")
    ap.add_argument("--min-edge", type=float, default=1.5,
                    help="TP move must be >= this x round-trip fees")
    args = ap.parse_args()

    cfg = Config(start_balance=args.balance, fee_rate=args.fee,
                 min_tp_vs_fees=args.min_edge)
    if args.mode == "backtest":
        if args.synthetic:
            df = synthetic_history()
        elif args.csv:
            df = pd.read_csv(args.csv)
        else:
            print(f"Binance se {args.days} din ka 1-minute data download ho raha hai...")
            df = fetch_history(cfg.symbol, args.days)
            df.to_csv("btc_1m.csv", index=False)
        run_backtest(df, cfg)
    else:
        run_live(cfg)


if __name__ == "__main__":
    sys.exit(main())
