"""Costs: commissions + slippage. ON by default.

the default here is opinionated: 1bp commission, 2bps slippage, applied to
every fill. a backtest with no costs is a fantasy, so you have to opt OUT
explicitly (costs=None) and then it shows up in the results dict as
costs_disabled=True. no silent free lunches.
"""

COMMISSION_BPS = 1.0
SLIPPAGE_BPS = 2.0


class CostModel:
    def __init__(self, commission_bps: float = COMMISSION_BPS,
                 slippage_bps: float = SLIPPAGE_BPS):
        self.commission_bps = commission_bps
        self.slippage_bps = slippage_bps

    def apply_slippage(self, price: float, quantity: float) -> float:
        # buys pay the offer, sells hit the bid. slippage is adverse by construction.
        slip = price * self.slippage_bps / 1e4
        return price + slip if quantity > 0 else price - slip

    def commission(self, quantity: float, price: float) -> float:
        return abs(quantity) * price * self.commission_bps / 1e4

    def describe(self) -> dict:
        return {"commission_bps": self.commission_bps,
                "slippage_bps": self.slippage_bps}
