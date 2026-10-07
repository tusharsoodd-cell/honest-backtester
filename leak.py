"""The leak toggle.

leak=True hands the strategy bars shifted one step into the future:
at bar t it sees t+1's close, but still executes at t+1's open. so it
"knows" the open->close move of the execution bar. that is textbook
look-ahead bias, and it's here on purpose: run the same strategy twice
and watch what it does to the Sharpe.

this module is the whole reason the repo exists. if you take one thing
from it: any backtest result you can't reproduce with leak=False is a
story, not a strategy.
"""

from costs import CostModel
from data import fetch, max_drawdown, sharpe
from engine import BacktestEngine, ExecutionHandler, Portfolio


def run_once(symbols, strategy_fn, start, end, initial_capital=100_000.0,
             leak=False, commission_bps=1.0, slippage_bps=2.0, costs=True):
    bars = fetch(symbols, start, end)
    if not costs:
        # fantasy mode: supported, but flagged in the results dict so it
        # can't silently end up in a table.
        commission_bps, slippage_bps = 0.0, 0.0
    cost_model = CostModel(commission_bps, slippage_bps)
    portfolio = Portfolio(initial_capital, cost_model)
    execution = ExecutionHandler(cost_model)
    engine = BacktestEngine(bars, strategy_fn, portfolio, execution, leak=leak)
    curve = engine.run()
    rets = curve["returns"]
    return {
        "leak": leak,
        "costs_disabled": not costs,
        "n_bars": len(curve),
        "n_trades": len(portfolio.trades),
        "total_return": float(curve["equity"].iloc[-1] / initial_capital - 1),
        "sharpe": sharpe(rets),          # annualized, rf=0, 252 trading days
        "max_drawdown": max_drawdown(curve["equity"]),
        "curve": curve,
        "trades": portfolio.trades,
    }


def demo(symbols, strategy_fn, start, end, **kw):
    """run honest vs leaking side by side, print the comparison."""
    honest = run_once(symbols, strategy_fn, start, end, leak=False, **kw)
    leaking = run_once(symbols, strategy_fn, start, end, leak=True, **kw)

    def row(name, r):
        return (f"{name:<10} sharpe={r['sharpe']:6.2f}  "
                f"ret={r['total_return'] * 100:7.2f}%  "
                f"maxdd={r['max_drawdown'] * 100:6.2f}%  "
                f"trades={r['n_trades']:4d}")

    print(row("honest", honest))
    print(row("LEAKING", leaking))
    print(f"\nsharpe inflation from one bar of look-ahead: "
          f"{leaking['sharpe'] - honest['sharpe']:+.2f}")
    return honest, leaking


if __name__ == "__main__":
    # the signature demo: intraday continuation, honest vs one bar of peek.
    # same code, same costs — only the leak flag changes.
    from strategies.intraday import IntradayContinuation
    honest, leaking = demo(
        ["SPY", "QQQ", "IWM"], IntradayContinuation(),
        start="2021-01-01", end="2024-01-01",
    )
