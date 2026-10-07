# Interview notes

Questions I'd expect on this repo, and the honest answers.

**How do you avoid look-ahead bias?**
Three layers. First, the engine hands the strategy an as-of slice (`bars.iloc[:i+1]`) — the strategy physically cannot see the future. Second, execution is always at the *next* bar's open; there's no fill-at-signal-close code path, which is where most hobbyist backtesters leak. Third, `tests/test_no_lookahead.py` proves it: corrupt everything after the as-of bar and assert the signals don't change. If a signal ever depends on future data, that test goes red.

**What's your Sharpe convention, and what's the sample size?**
Annualized, risk-free rate 0, 252 trading days, computed on daily equity returns. The demo is 753 daily bars (2021-01-04 → 2023-12-29), three symbols. I state this because a Sharpe without a sample size and convention is a red flag — it's the easiest number in finance to inflate by omission.

**Why event-driven instead of vectorized?**
Vectorized is faster and I'd use it for research iteration. But vectorized code makes look-ahead *easy* — one unshifted series and your signal trades on information from the close it's supposedly predicting. The event-driven loop makes the time ordering structural: market → signal → order → fill-at-next-open. You can't accidentally write the leak because there's nowhere to put it. Speed was never the constraint here; correctness was.

**The honest strategy loses money. Why show that?**
Because a backtester that flatters a toy strategy is lying about its own correctness. The honest run (Sharpe -0.48, costs on) is what a weak idea actually looks like. The leaking run (Sharpe 12.46, same code) is what the *same* idea looks like with one bar of peek. If I'd tuned the strategy until the honest number was positive, I'd be demonstrating overfitting, not engineering.

**What breaks with survivorship bias?**
The engine doesn't know or care what universe you feed it. Backtest a hand-picked list of stocks that survived to 2024 and you'll get a beautiful equity curve that means nothing. The demo uses ETFs (SPY/QQQ/IWM) specifically so this is moot, but it's a data problem, not an engine problem — no backtester can fix your universe.

**Why are costs on by default?**
Because every backtest I've seen with costs off is a fantasy. 1bp commission + 2bps slippage is conservative for the demo's size. You can turn them off (`costs=False`) but the results dict flags `costs_disabled=True`, so it can't quietly end up in a screenshot.

**What would you add next?**
Market impact model (even a simple square-root one), borrow cost modeling for shorts, corporate-action handling, and intraday bars to make the execution model meaningful at higher frequency. Roughly in that order.
