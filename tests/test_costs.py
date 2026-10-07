"""cost model tests: slippage is adverse, commission scales with size."""

import pytest

from costs import CostModel
from engine import ExecutionHandler
from engine.events import OrderEvent


def test_buy_pays_more_than_mid():
    cm = CostModel(commission_bps=0.0, slippage_bps=10.0)
    assert cm.apply_slippage(100.0, 10.0) == pytest.approx(100.10)


def test_sell_gets_less_than_mid():
    cm = CostModel(commission_bps=0.0, slippage_bps=10.0)
    assert cm.apply_slippage(100.0, -10.0) == pytest.approx(99.90)


def test_commission_proportional():
    cm = CostModel(commission_bps=1.0, slippage_bps=0.0)
    assert cm.commission(100.0, 400.0) == pytest.approx(4.0)
    assert cm.commission(-100.0, 400.0) == pytest.approx(4.0)  # abs quantity


def test_execution_applies_both():
    cm = CostModel(commission_bps=1.0, slippage_bps=10.0)
    ex = ExecutionHandler(cm)
    order = OrderEvent(date="2024-01-02", symbol="SPY", quantity=100.0)
    order.execute_date = "2024-01-03"
    fill = ex.execute(order, 400.0)
    assert fill.fill_price == pytest.approx(400.40)
    assert fill.commission == pytest.approx(100 * 400.40 * 1e-4)
    assert fill.date == "2024-01-03"
