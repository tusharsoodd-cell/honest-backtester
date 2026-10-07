"""no-look-ahead tests. the most important tests in the repo.

idea: take real bars, compute the strategy's signal at bar t. then corrupt
everything AFTER bar t (reverse future returns) and recompute. if the
signal changes, the strategy peeked. it must not change.
"""

import numpy as np
import pandas as pd

from strategies.momentum import TimeSeriesMomentum


def fake_bars(n=400, seed=7):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0004, 0.01, n)
    close = 100 * np.exp(np.cumsum(rets))
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": close * 0.999, "high": close * 1.002,
                         "low": close * 0.998, "close": close,
                         "volume": 1_000_000}, index=idx)


def signals_over_time(bars, asof):
    strat = TimeSeriesMomentum()
    out = []
    for i in range(273, asof + 1):  # 252 + 21 warmup
        out.append(strat.on_bar("TST", bars.iloc[: i + 1], bars.index[i]))
    return out


def test_momentum_ignores_future():
    bars = fake_bars()
    asof = 350
    honest = signals_over_time(bars, asof)

    # corrupt the future: reverse all returns after the as-of bar
    corrupted = bars.copy()
    future_rets = corrupted["close"].iloc[asof + 1:].pct_change().fillna(0)
    base = corrupted["close"].iloc[asof]
    corrupted.loc[corrupted.index[asof + 1]:, "close"] = base * (1 + future_rets[::-1].values).cumprod()

    tampered = signals_over_time(corrupted, asof)
    assert honest == tampered


def test_engine_asof_slice_is_honest():
    """the engine must hand the strategy bars ending at (not after) bar t."""
    from costs import CostModel
    from engine import BacktestEngine, ExecutionHandler, Portfolio

    bars = {"TST": fake_bars(300)}
    seen_ends = []

    class Spy:
        def on_bar(self, symbol, asof_bars, date):
            seen_ends.append(asof_bars.index[-1])
            return None

    eng = BacktestEngine(bars, Spy(), Portfolio(10_000, CostModel(0, 0)),
                         ExecutionHandler(CostModel(0, 0)), leak=False)
    eng.run()
    # every asof window must end exactly on its bar's date
    for seen, actual in zip(seen_ends, bars["TST"].index):
        assert seen == actual


def test_leak_mode_sees_one_bar_ahead():
    from costs import CostModel
    from engine import BacktestEngine, ExecutionHandler, Portfolio

    bars = {"TST": fake_bars(300)}
    seen_ends = []

    class Spy:
        def on_bar(self, symbol, asof_bars, date):
            seen_ends.append(asof_bars.index[-1])
            return None

    eng = BacktestEngine(bars, Spy(), Portfolio(10_000, CostModel(0, 0)),
                         ExecutionHandler(CostModel(0, 0)), leak=True)
    eng.run()
    # leak=True: strategy sees one bar ahead (except the final bar, clamped)
    for seen, actual, nxt in zip(seen_ends, bars["TST"].index,
                                 list(bars["TST"].index[1:]) + [bars["TST"].index[-1]]):
        assert seen == nxt
