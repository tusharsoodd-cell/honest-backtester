"""portfolio accounting tests. if these fail, nothing else can be trusted."""

import pytest

from costs import CostModel
from engine import FillEvent, Portfolio
from engine.events import SignalEvent


def make_portfolio(**kw):
    cm = CostModel(kw.pop("commission_bps", 0.0), kw.pop("slippage_bps", 0.0))
    return Portfolio(100_000.0, cm)


def test_buy_reduces_cash_by_cost():
    p = make_portfolio()
    p.update_fill(FillEvent(date="2024-01-02", symbol="SPY", quantity=100,
                            fill_price=400.0, commission=4.0))
    assert p.position("SPY") == 100
    assert p.cash == pytest.approx(100_000 - 40_000 - 4.0)


def test_sell_adds_cash():
    p = make_portfolio()
    p.update_fill(FillEvent(date="2024-01-02", symbol="SPY", quantity=100,
                            fill_price=400.0, commission=0.0))
    p.update_fill(FillEvent(date="2024-01-03", symbol="SPY", quantity=-100,
                            fill_price=410.0, commission=0.0))
    assert p.position("SPY") == 0
    assert p.cash == pytest.approx(100_000 + 1_000.0)


def test_signal_to_order_delta():
    p = make_portfolio()
    p.update_fill(FillEvent(date="2024-01-02", symbol="SPY", quantity=50,
                            fill_price=400.0, commission=0.0))
    sig = SignalEvent(date="2024-01-03", symbol="SPY", target_shares=100.0)
    order = p.update_signal(sig)
    assert order.quantity == pytest.approx(50.0)  # only the delta


def test_no_order_when_position_unchanged():
    p = make_portfolio()
    p.update_fill(FillEvent(date="2024-01-02", symbol="SPY", quantity=50,
                            fill_price=400.0, commission=0.0))
    sig = SignalEvent(date="2024-01-03", symbol="SPY", target_shares=50.0)
    assert p.update_signal(sig) is None


def test_mark_to_market():
    p = make_portfolio()
    p.update_fill(FillEvent(date="2024-01-02", symbol="SPY", quantity=100,
                            fill_price=400.0, commission=0.0))
    equity = p.mark_to_market("2024-01-03", {"SPY": 405.0})
    # cash 60k + 100*405 = 100,500
    assert equity == pytest.approx(100_500.0)
    assert p.equity_curve[-1]["equity"] == pytest.approx(100_500.0)
