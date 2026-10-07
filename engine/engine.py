"""The event loop. this is where the point-in-time discipline lives.

per bar, in this exact order:
  1. execute yesterday's pending orders at today's OPEN
  2. emit market events for today's bar -> strategy -> signals -> new pending orders
  3. mark the portfolio to market at today's CLOSE

so a signal computed from bar t's close can only ever trade at bar t+1's
open. there is no code path that fills at bar t's close. if you think you
found one, that's a bug — file an issue.

the leak flag exists for one reason: the demo. when True, the strategy is
handed bars shifted one step into the future, so it "knows" tomorrow's
close while still executing at tomorrow's open. everything else is
identical. the point is to show how much that inflates the numbers.
"""

from collections import deque

import pandas as pd

from .events import MarketEvent, OrderEvent
from .execution import ExecutionHandler
from .portfolio import Portfolio


class BacktestEngine:
    def __init__(self, bars: dict, strategy, portfolio: Portfolio,
                 execution: ExecutionHandler, leak: bool = False):
        """
        bars: dict symbol -> DataFrame with columns open/high/low/close/volume,
              indexed by date, aligned across symbols.
        strategy: object with on_bar(symbol, bars_up_to_now, date) -> target_shares | None
        """
        self.bars = bars
        self.symbols = list(bars.keys())
        self.strategy = strategy
        self.portfolio = portfolio
        self.execution = execution
        self.leak = leak
        self.dates = bars[self.symbols[0]].index

    def _asof_bars(self, symbol, i):
        # the ONLY place future data can enter. honest: bars[:i+1].
        # leak=True (demo only): bars[:i+2], i.e. strategy sees tomorrow's close.
        end = i + 2 if self.leak else i + 1
        return self.bars[symbol].iloc[:end]

    def run(self) -> pd.DataFrame:
        pending = deque()  # orders created today, executed at tomorrow's open
        n = len(self.dates)

        for i, date in enumerate(self.dates):
            # 1. fills at today's open for orders placed yesterday
            while pending:
                order = pending.popleft()
                order.execute_date = date.date() if hasattr(date, "date") else date
                open_price = float(self.bars[order.symbol]["open"].iloc[i])
                fill = self.execution.execute(order, open_price)
                self.portfolio.update_fill(fill)

            # 2. market events -> strategy -> signals -> orders (for tomorrow)
            for symbol in self.symbols:
                asof = self._asof_bars(symbol, i)
                target = self.strategy.on_bar(symbol, asof, date)
                if target is None:
                    continue
                from .events import SignalEvent
                signal = SignalEvent(date=date, symbol=symbol,
                                     target_shares=float(target))
                order = self.portfolio.update_signal(signal)
                if order is not None:
                    pending.append(order)

                # market event is mostly ceremonial here (the strategy pulls
                # asof bars directly), but the queue exists so nothing can
                # bypass the ordering above. kept for structure.
                _ = MarketEvent(date=date, symbol=symbol,
                                bar=self.bars[symbol].iloc[i].to_dict())

            # 3. mark to market at the close
            closes = {s: float(self.bars[s]["close"].iloc[i]) for s in self.symbols}
            self.portfolio.mark_to_market(date, closes)

        # any order left pending at the end never executes (no tomorrow).
        # this slightly understates the last signal; acceptable and documented.
        curve = pd.DataFrame(self.portfolio.equity_curve).set_index("date")
        curve["returns"] = curve["equity"].pct_change().fillna(0.0)
        return curve
