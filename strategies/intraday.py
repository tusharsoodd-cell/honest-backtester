"""Intraday continuation: hold today's direction for tomorrow.

long if the last visible bar closed up (close > open), short if it closed
down. one-day holding period, re-evaluated every bar.

in honest mode this is basically noise — intraday continuation at the daily
level is weak and costs eat it. in leak mode the "last visible bar" is the
bar you're about to trade, so you know its intraday direction in advance.
that's the whole demo: same code, same costs, wildly different Sharpe.
"""


class IntradayContinuation:
    def __init__(self, notional=30_000.0):
        self.notional = notional

    def on_bar(self, symbol, bars, date):
        if len(bars) < 2:
            return None
        last = bars.iloc[-1]
        # up day -> long, down day -> short. flat days keep existing position
        # (return None = no change) to avoid churning on dojis.
        if last["close"] > last["open"]:
            sign = 1.0
        elif last["close"] < last["open"]:
            sign = -1.0
        else:
            return None
        return sign * self.notional / last["close"]
