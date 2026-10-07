"""Moving-average crossover. the "hello world" of trend systems, included
because everyone has run one and nobody believes the in-sample chart.
"""


class MovingAverageCrossover:
    """50/200 SMA cross. long when fast > slow, flat otherwise.

    no shorting here — partly because borrow costs aren't modeled (see
    README limitations), partly because 200d cross systems spend most of
    their time whipsawing and i didn't want the demo to look even worse.
    """

    def __init__(self, fast=50, slow=200, notional=100_000.0):
        self.fast = fast
        self.slow = slow
        self.notional = notional

    def on_bar(self, symbol, bars, date):
        if len(bars) < self.slow + 1:
            return None
        closes = bars["close"]
        fast_ma = closes.rolling(self.fast).mean()
        slow_ma = closes.rolling(self.slow).mean()
        long_now = fast_ma.iloc[-1] > slow_ma.iloc[-1]
        long_prev = fast_ma.iloc[-2] > slow_ma.iloc[-2]
        if long_now == long_prev:
            return None  # no cross, no trade
        if long_now:
            return self.notional / closes.iloc[-1]
        return 0.0
