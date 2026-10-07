# honest-backtester

An event-driven backtesting engine where **rigor is the feature**. It exists to catch the three mistakes that kill quant candidates in interviews: look-ahead bias, missing costs, and in-sample-only results.

The signature demo: a deliberate `leak` toggle. Run the same strategy twice — once honest, once allowed to peek one bar ahead — and watch what it does to the Sharpe.

## The demo (real numbers, run on this machine)

Strategy: intraday continuation (long if the last bar closed up, short if down, 1-day hold). Universe: SPY, QQQ, IWM. Daily bars, 2021-01-04 → 2023-12-29 (753 bars). Costs: 1bp commission + 2bps slippage, on in both runs. Sharpe: annualized, rf=0, 252 trading days.

| run | Sharpe | total return | max drawdown | trades |
|---|---|---|---|---|
| honest | **-0.48** | -26.65% | -46.58% | 2,251 |
| leaking (1 bar of peek) | **12.46** | +562.02% | -0.75% | 2,254 |

Same code. Same costs. The only difference is `leak=True`, which lets the strategy see tomorrow's close while executing at tomorrow's open. One bar of look-ahead turns a money-loser into a 12-Sharpe money printer.

That's the entire point of this repo: **any backtest result you can't reproduce with `leak=False` is a story, not a strategy.**

(And yes, the honest strategy loses money. There is no alpha here — the engine is the product, not the strategy. A backtester that makes a toy strategy look good is lying to you.)

## Architecture

```
┌──────────┐   MarketEvent    ┌──────────┐   SignalEvent    ┌───────────┐
│   Data   │ ──────────────▶ │ Strategy │ ──────────────▶ │ Portfolio │ ──▶ OrderEvent (pending)
└──────────┘                 └──────────┘                  └───────────┘
                                                                    │
                                                                    ▼
┌──────────┐   FillEvent     ┌────────────┐                  ┌──────────────┐
│ Portfolio│ ◀────────────── │ Execution  │ ◀── fills at ── │ next bar's   │
│ (cash +  │                 │ (slippage) │     tomorrow's     │ OPEN only    │
│  shares) │                 └────────────┘     open           └──────────────┘
```

Per bar, in this exact order:
1. **Execute** yesterday's pending orders at today's open (with slippage + commission)
2. **Signal**: strategy sees bars `[:t+1]` only → emits target positions → orders queued for tomorrow
3. **Mark to market** at today's close

There is no code path that fills at the signal bar's close. That's the most common accidental look-ahead in hobbyist backtesters and this engine refuses to support it.

## Point-in-time discipline

- Strategies receive `bars.iloc[:i+1]` — the as-of slice. The engine enforces this; the strategy can't reach further even if it tries.
- Signals computed on bar *t*'s close trade at bar *t+1*'s open. Always.
- No forward-fill across the as-of boundary. Symbols are aligned on the intersection of trading days instead.

## Costs (on by default)

- Commission: 1bp per trade, Slippage: 2bps adverse (buys pay up, sells get hit)
- Disable with `costs=False` — but then results are flagged `costs_disabled=True` so it can't silently end up in a table

## Validation

- `validation.walk_forward(n, train, test, step)` — rolling train/test windows
- `validation.purged_cv(n, n_splits, embargo)` — purged K-fold with embargo on both sides of each test fold (for ML-style signals with label horizons)
- `validation.oos_sharpe(...)` — Sharpe on concatenated out-of-sample segments only

## Setup

```bash
pip install -r requirements.txt
pytest                    # 18 tests, incl. no-look-ahead proofs
python leak.py            # the demo: honest vs leaking, side by side
```

## What this doesn't model (limitations)

- **Market impact** — fills don't move the price. At 30k notional on SPY that's fine; at real size it isn't.
- **Borrow costs / hard-to-borrow** — shorts pay no borrow fee here.
- **Corporate actions** — yfinance `auto_adjust=False` + no split/dividend handling. Don't run single-name strategies through a split and wonder what happened.
- **Survivorship bias** — the demo universe (SPY/QQQ/IWM) is ETFs, so it's moot here, but the engine won't stop you from backtesting a hand-picked list of today's winners.
- **Intraday granularity** — daily bars. The open-to-open execution model is honest at this resolution and dishonest if you pretend it's HFT.

## What I learned

Building the leak toggle taught me more than any of the strategies: the honest version of a plausible-sounding idea usually loses money, and the distance between "loses money" and "12 Sharpe" can be a single off-by-one in an array slice. That's a terrifying sentence to write about other people's backtesters, but it's true of most of them.
