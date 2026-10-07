"""Execution: turns orders into fills at the next bar's open.

the only execution model here is market-on-open at t+1. no "fill at the
close of the signal bar" — that's the most common accidental look-ahead in
hobbyist backtesters and i refuse to support it.
"""

from .events import FillEvent, OrderEvent


class ExecutionHandler:
    def __init__(self, cost_model):
        self.cost_model = cost_model

    def execute(self, order: OrderEvent, open_price: float) -> FillEvent:
        fill_price = self.cost_model.apply_slippage(open_price, order.quantity)
        commission = self.cost_model.commission(order.quantity, fill_price)
        return FillEvent(
            date=order.execute_date,
            symbol=order.symbol,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
        )
