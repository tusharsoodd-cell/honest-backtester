"""leak toggle tests: with leak=True the strategy must see the future,
and on random data that must show up as inflated performance."""

import numpy as np
import pandas as pd

from costs import CostModel
from data import sharpe
from engine import BacktestEngine, ExecutionHandler, Portfolio


def rand_bars(n=500, seed=11):
    rng = np.random.default_rng(seed)
    overnight = rng.normal(0.0, 0.006, n)
    intraday = rng.normal(0.0, 0.008, n)
    close = np.empty(n)
    opn = np.empty(n)
    c = 100.0
    for i in range(n):
        opn[i] = c * (1 + overnight[i])
        c = opn[i] * (1 + intraday[i])
        close[i] = c
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": opn, "high": np.maximum(opn, close) * 1.001,
                         "low": np.minimum(opn, close) * 0.999, "close": close,
                         "volume": 1e6}, index=idx)


class Peekaboo:
    """long if the last visible close rose, short if it fell.

    in honest mode this is noise trading on yesterday's move (roughly
    zero expectancy). in leak mode the "last visible close" is TOMORROW's
    close while execution is at tomorrow's open — so it knows the
    open->close move it's about to trade. expectancy goes strongly positive.
    """

    def on_bar(self, symbol, bars, date):
        if len(bars) < 2:
            return None
        c = bars["close"]
        return 100.0 if c.iloc[-1] > c.iloc[-2] else -100.0


def run(bars, leak):
    cm = CostModel(0.0, 0.0)  # isolate the leak effect from costs
    eng = BacktestEngine({"TST": bars}, Peekaboo(), Portfolio(100_000, cm),
                         ExecutionHandler(cm), leak=leak)
    curve = eng.run()
    return curve


def test_leak_changes_results():
    bars = rand_bars()
    honest = run(bars, leak=False)
    leaking = run(bars, leak=True)
    assert not honest["equity"].equals(leaking["equity"])


def test_leak_inflates_sharpe_on_noise():
    # on pure noise, honest peekaboo should be ~flat and leaking strongly positive
    bars = rand_bars()
    s_honest = sharpe(run(bars, leak=False)["returns"])
    s_leak = sharpe(run(bars, leak=True)["returns"])
    assert s_leak > s_honest + 1.0, (s_honest, s_leak)
    assert s_leak > 2.0  # knowing tomorrow's direction is a big edge
