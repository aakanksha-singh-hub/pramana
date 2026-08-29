"""Guards on the two things that would invalidate the whole experiment:
a feature appearing in two buckets, and the consistency model seeing a label
or a test row it must not see."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pramana.features import (B1_COLS, B2_COLS, B3_COLS, B4A_COLS, B4B_COLS,
                              FORBIDDEN_AS_INPUT, columns_for, validate)
from pramana.features.b4_context import ConsistencyModel


def test_one_bucket_invariant():
    validate()


def test_groups_are_pairwise_disjoint():
    for a, b in ((B1_COLS, B2_COLS), (B1_COLS, B3_COLS), (B2_COLS, B3_COLS)):
        assert not set(a) & set(b)


def test_b4_does_not_reintroduce_b3():
    b3 = set(B3_COLS)
    assert not b3 & set(B4A_COLS)
    assert not b3 & set(B4B_COLS)


def test_no_arm_contains_a_forbidden_column():
    for arm in (["b1"], ["b1", "b2"], ["b1", "b2", "b3"],
                ["b1", "b2", "b3", "b4a"], ["b1", "b2", "b3", "b4b"]):
        assert not set(columns_for(arm)) & FORBIDDEN_AS_INPUT


def _toy(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({c: rng.normal(size=n) for c in B3_COLS})
    df["purpose_code"] = rng.choice(["rent", "friend_transfer", "other"], n)
    df["is_fraud"] = (rng.random(n) < 0.05).astype(int)
    return df


def test_consistency_model_is_invariant_to_the_labels_it_is_not_given():
    """Permuting the labels of rows the model never uses (the fraud rows it
    excludes stay excluded) must not change a single residual."""
    tr = _toy()
    a = ConsistencyModel().fit(tr).transform(tr)
    tr2 = tr.copy()
    # shuffle values *within* the fraud subset: the excluded set is identical,
    # so a model that only uses the label to exclude must be unchanged
    idx = tr2.index[tr2.is_fraud == 1]
    perm = np.random.default_rng(1).permutation(idx)
    tr2.loc[idx, B3_COLS] = tr2.loc[perm, B3_COLS].to_numpy()
    b = ConsistencyModel().fit(tr2).transform(tr)
    num = [c for c in a.columns if c != "purpose_code"]
    assert np.allclose(a[num].to_numpy(), b[num].to_numpy(), atol=1e-10)


def test_consistency_model_never_fits_on_test_rows():
    tr, te = _toy(seed=0), _toy(seed=1)
    cm = ConsistencyModel().fit(tr)
    before = cm.reference("rent")
    cm.transform(te)
    after = cm.reference("rent")
    assert before == after


def test_transform_before_fit_raises():
    with pytest.raises(RuntimeError):
        ConsistencyModel().transform(_toy())
