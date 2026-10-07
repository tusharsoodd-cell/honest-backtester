"""Portfolio: cash + positions, mark-to-market accounting.

boring on purpose. every fill updates cash and shares, every bar close
recomputes equity. if this is wrong nothing else matters, so it's the most
tested module in the repo.
"""

from collections import defaultdict

from .events import FillEvent, OrderEvent, SignalEvent


class Portfolio:
    def __init__(self, initial_capital: float, cost_model):
        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.positions = defaultdict(float)  # symbol -> shares
        self.cost_model = cost_model
        self.equity_curve = []   # list of dicts, one per bar
        self.trades = []         # list of FillEvents

    def update_signal(self, signal: SignalEvent):
        """turn a target position into an order for the delta. None if no change."""
        current = self.positions[signal.symbol]
        delta = signal.target_shares - current
        if abs(delta) < 1e-8:
            return None
        return OrderEvent(
            date=signal.date,
            symbol=signal.symbol,
            quantity=delta,
        )

    def update_fill(self, fill: FillEvent):
        # cash moves by signed quantity * price, commission always reduces cash.
        # (selling: quantity negative, so -qty*price is a cash inflow. took me
        # an embarrassingly long time to get the sign right the first time.)
        self.cash -= fill.quantity * fill.fill_price
        self.cash -= fill.commission
        self.positions[fill.symbol] += fill.quantity
        self.trades.append(fill)

    def mark_to_market(self, date, closes: dict):
        position_value = sum(
            self.positions[sym] * closes.get(sym, 0.0) for sym in self.positions
        )
        equity = self.cash + position_value
        self.equity_curve.append(
            {"date": date, "equity": equity, "cash": self.cash,
             "positions": position_value}
        )
        return equity

    def position(self, symbol: str) -> float:
        return self.positions[symbol]
