"""Example strategies. both are deliberately simple — the engine is the
product here, not the alpha (there is no alpha).
"""

import pandas as pd


class TimeSeriesMomentum:
    """classic trend: sign of trailing 12m return (skipping the last month),
    rebalanced monthly, equal notional per name.

    the 21-day skip is the standard convention — short-term reversal
    contaminates the 1-month formation window. rebalance monthly because
    daily rebalancing a 12m signal just burns commission.
    """

    def __init__(self, lookback=252, skip=21, notional=100_000.0):
        self.lookback = lookback
        self.skip = skip
        self.notional = notional
        self._last_month = {}

    def on_bar(self, symbol, bars, date):
        if len(bars) < self.lookback + self.skip:
            return None
        # monthly rebalance only
        month = (date.year, date.month) if hasattr(date, "year") else str(date)[:7]
        if self._last_month.get(symbol) == month:
            return None
        self._last_month[symbol] = month

        closes = bars["close"]
        # formation window ends `skip` days before the as-of bar
        past = closes.iloc[-(self.lookback + self.skip):-self.skip]
        # ^ this slice is the one people get wrong. iloc[-273:-21] on a
        # 252+21 window: formation return excludes the most recent month.
        # double-checked against a manual loop on 2023 SPY data. it matches.
        mom = past.iloc[-1] / past.iloc[0] - 1
        sign = 1.0 if mom > 0 else -1.0
        price = closes.iloc[-1]
        return sign * self.notional / price
