"""Event types for the backtest engine.

everything that happens in a backtest is an event on a queue. this keeps
the data flow honest: strategies only ever see market events, the portfolio
only sees signals and fills. nothing can reach into the future because
there is no future in the queue, just the next event.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Event:
    type: str = field(default="EVENT", init=False)


@dataclass
class MarketEvent(Event):
    """a new bar has closed (or opened, for execution). the strategy's only input."""

    type: str = field(default="MARKET", init=False)
    date: date = None
    symbol: str = ""
    # dict with open/high/low/close/volume for this bar. the strategy gets
    # exactly this bar and nothing after it. that's the whole point.
    bar: dict = field(default_factory=dict)


@dataclass
class SignalEvent(Event):
    """strategy output: desired position in shares (signed). engine turns it into an order."""

    type: str = field(default="SIGNAL", init=False)
    date: date = None
    symbol: str = ""
    target_shares: float = 0.0
    # free-form, e.g. "momentum +1" or "ma cross down -> flat". useful in logs.
    reason: str = ""


@dataclass
class OrderEvent(Event):
    """a market-on-open order, filled at the NEXT bar's open. always."""

    type: str = field(default="ORDER", init=False)
    date: date = None          # date the order was created (bar t)
    symbol: str = ""
    quantity: float = 0.0      # signed shares; positive = buy
    # execution date is set by the engine, not the strategy
    execute_date: Any = None


@dataclass
class FillEvent(Event):
    """what actually happened: price after slippage, commission taken out."""

    type: str = field(default="FILL", init=False)
    date: date = None          # execution date (bar t+1)
    symbol: str = ""
    quantity: float = 0.0
    fill_price: float = 0.0
    commission: float = 0.0
