"""Data: fetch OHLCV bars and keep them honest.

two rules enforced here:
  1. no forward-fill across the as-of boundary. missing bars stay missing;
     the engine simply has no bar for that date (we align symbols on the
     intersection of trading days instead).
  2. signals are always computed on CLOSED bars. the engine slices bars
     [:i+1] before the strategy ever sees them — see engine.py.
"""

import pandas as pd
import yfinance as yf


def fetch(symbols, start: str, end: str) -> dict:
    """download daily OHLCV for each symbol, aligned on common trading days."""
    bars = {}
    for sym in symbols:
        df = yf.download(sym, start=start, end=end, progress=False,
                         auto_adjust=False)
        # yfinance sometimes returns multiindex columns; flatten.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df = df.dropna()
        # no ffill/bfill: a missing bar is a missing bar. if a symbol didn't
        # trade that day we don't invent a price for it.
        bars[sym] = df

    # align on intersection so every symbol has a bar for every engine date.
    # (avoids the "what price do we mark symbol X at on its holiday" problem
    # entirely — it just isn't a trading date.)
    common = None
    for df in bars.values():
        common = df.index if common is None else common.intersection(df.index)
    common = common.sort_values()
    return {s: df.loc[common] for s, df in bars.items()}


def daily_returns(equity: pd.Series) -> pd.Series:
    return equity.pct_change().fillna(0.0)


def sharpe(returns: pd.Series, periods_per_year: int = 252, rf: float = 0.0) -> float:
    """annualized Sharpe, rf=0 unless you say otherwise. sample size = len(returns)."""
    excess = returns - rf / periods_per_year
    std = excess.std(ddof=1)
    if std == 0 or len(excess) < 2:
        return 0.0
    return (excess.mean() / std) * (periods_per_year ** 0.5)


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())
