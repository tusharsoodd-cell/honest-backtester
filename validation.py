"""Validation: walk-forward splits and purged cross-validation.

in-sample sharpe is a story you tell yourself. these splitters exist so
you can tell the out-of-sample story instead.
"""

import numpy as np
import pandas as pd

from data import sharpe


def walk_forward(n: int, train: int, test: int, step: int = None):
    """Yield (train_idx, test_idx) as integer arrays.

    rolling windows: train on [i, i+train), test on [i+train, i+train+test),
    step forward by `step` (defaults to test length, i.e. non-overlapping
    test folds).
    """
    step = step or test
    i = 0
    while i + train + test <= n:
        yield np.arange(i, i + train), np.arange(i + train, i + train + test)
        i += step


def purged_cv(n: int, n_splits: int = 5, embargo: int = 5):
    """K-fold with purge + embargo (Lopez de Prado's recipe, simplified).

    each test fold drops `embargo` observations on BOTH sides of the fold
    from every training set, so labels computed over a horizon can't leak
    across the boundary. for daily bars with a 5-day label horizon, embargo=5.
    """
    idx = np.arange(n)
    folds = np.array_split(idx, n_splits)
    for k, test in enumerate(folds):
        lo, hi = test[0], test[-1]
        mask = (idx < lo - embargo) | (idx > hi + embargo)
        yield idx[mask], test


def oos_sharpe(returns, splits, periods_per_year=252):
    """Sharpe computed ONLY on concatenated out-of-sample (test) segments."""
    oos = np.concatenate([np.asarray(returns)[t] for _, t in splits])
    return sharpe(pd.Series(oos), periods_per_year)
