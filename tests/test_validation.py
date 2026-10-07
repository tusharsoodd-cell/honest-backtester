"""validation splitter tests: folds must tile, test sets must not overlap,
embargo must actually embargo."""

import numpy as np

from validation import purged_cv, walk_forward


def test_walk_forward_tiles():
    splits = list(walk_forward(100, train=40, test=10))
    # (100-40-10)/10 + 1 = 6 folds
    assert len(splits) == 6
    for tr, te in splits:
        assert len(tr) == 40 and len(te) == 10
        assert tr[-1] + 1 == te[0]          # test starts right after train
    # test folds don't overlap
    all_test = np.concatenate([te for _, te in splits])
    assert len(np.unique(all_test)) == len(all_test)


def test_walk_forward_custom_step():
    splits = list(walk_forward(100, train=40, test=10, step=5))
    assert len(splits) == 11  # (100-50)//5 + 1
    # overlapping test folds allowed here, but train must precede test
    for tr, te in splits:
        assert tr[-1] < te[0]


def test_purged_cv_embargo():
    n, k, embargo = 100, 5, 5
    splits = list(purged_cv(n, n_splits=k, embargo=embargo))
    assert len(splits) == k
    for tr, te in splits:
        lo, hi = te[0], te[-1]
        # no training point within `embargo` of either side of the test fold
        assert not np.any((tr >= lo - embargo) & (tr <= hi + embargo))
        # every point is either train or test, never both
        assert len(np.intersect1d(tr, te)) == 0


def test_purged_cv_covers_all():
    splits = list(purged_cv(100, n_splits=4, embargo=3))
    all_test = np.concatenate([te for _, te in splits])
    assert sorted(all_test.tolist()) == list(range(100))
