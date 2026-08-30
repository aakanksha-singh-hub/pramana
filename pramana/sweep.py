"""Phase-study runner.

Cells are grouped by (lambda, seed) because that pair determines the cached
base ledger, which is the expensive object. Everything else - the declared
purposes under rho and the chosen adversary, the beneficiary noise under beta,
the taxonomy under K - is applied to a cached ledger in seconds. One worker
takes one group and walks its cells sequentially, so a 200-cell study loads
15 ledgers rather than 200.

Every cell writes its own JSON as soon as it finishes, so an interrupted run
resumes rather than restarting.
"""

from __future__ import annotations

import itertools
import json
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed, parallel_config

from .dataset import build_base
from .harness import run_cell

RAW_DIR = Path("results/raw")


def expand(grid: dict, label: str) -> list[dict]:
    keys = [k for k in ("rho", "lam", "K", "beta", "seed", "adversary") if k in grid]
    out = []
    for combo in itertools.product(*(grid[k] for k in keys)):
        cell = dict(zip(keys, combo))
        cell.setdefault("adversary", "uniform")
        cell["block"] = label
        out.append(cell)
    return out


def cell_id(cell: dict) -> str:
    return ("rho{rho}_lam{lam}_K{K}_beta{beta}_adv{adversary}_seed{seed}"
            .format(**cell).replace(".", "p"))


def _run_group(key: tuple[float, int], cells: list[dict], cfg: dict,
               n_boot: int, out_dir: Path) -> list[str]:
    lam, seed = key
    done: list[str] = []
    base = None
    for cell in cells:
        path = out_dir / f"{cell_id(cell)}.json"
        if path.exists():
            done.append(path.name)
            continue
        if base is None:
            base = build_base(cfg, lam, seed)
        t0 = time.time()
        try:
            res = run_cell(base, cfg, rho=cell["rho"], lam=lam, K=cell["K"],
                           beta=cell["beta"], seed=seed, n_boot=n_boot,
                           adversary=cell["adversary"])
            res["_meta"]["block"] = cell["block"]
            res["_meta"]["seconds"] = time.time() - t0
            path.write_text(json.dumps(res))
            done.append(path.name)
            print(f"  done {path.name} ({time.time()-t0:.0f}s)", flush=True)
        except Exception:
            print(f"  FAILED {path.name}\n{traceback.format_exc()}", flush=True)
    return done


def run_sweep(cfg: dict, cells: list[dict], n_jobs: int = 6,
              n_boot: int = 1000, out_dir: Path = RAW_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[tuple[float, int], list[dict]] = {}
    for c in cells:
        groups.setdefault((c["lam"], c["seed"]), []).append(c)

    pending = [c for c in cells if not (out_dir / f"{cell_id(c)}.json").exists()]
    print(f"{len(cells)} cells, {len(pending)} pending, "
          f"{len(groups)} (lambda, seed) groups, {n_jobs} workers", flush=True)

    # build every base ledger serially first: parallel workers would otherwise
    # race to write the same cache file
    for (lam, seed) in sorted(groups):
        if any(not (out_dir / f"{cell_id(c)}.json").exists() for c in groups[(lam, seed)]):
            t0 = time.time()
            build_base(cfg, lam, seed)
            print(f"base ledger lam={lam} seed={seed} ready ({time.time()-t0:.0f}s)", flush=True)

    # inner_max_num_threads=1 stops every worker's BLAS and OpenMP pools from
    # each trying to use the whole machine. Without it, n_jobs processes spawn
    # n_jobs x n_cores threads and the run collapses into contention and swap.
    with parallel_config(backend="loky", inner_max_num_threads=1):
        Parallel(n_jobs=n_jobs, verbose=0)(
            delayed(_run_group)(k, v, cfg, n_boot, out_dir)
            for k, v in sorted(groups.items()))


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

def collect(out_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Flatten every finished cell into one long-format table."""
    rows = []
    for p in sorted(out_dir.glob("*.json")):
        r = json.loads(p.read_text())
        meta = r["_meta"]
        for arm, d in r.get("delta", {}).items():
            for metric, e in d.items():
                rows.append({
                    **{k: meta[k] for k in ("rho", "lam", "K", "beta", "seed",
                                            "adversary", "block", "n_test",
                                            "n_test_fraud")},
                    "arm": arm, "metric": metric,
                    "delta": e["point"], "ci_lo": e["ci"][0], "ci_hi": e["ci"][1],
                    "significant": e["significant"],
                    "baseline": r["B1+B2+B3"]["recall_at_fpr"]["0.001"]
                    if metric == "recall@fpr=0.001" else np.nan,
                })
    return pd.DataFrame(rows)


def arm_table(out_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Per-arm point metrics for every cell."""
    rows = []
    for p in sorted(out_dir.glob("*.json")):
        r = json.loads(p.read_text())
        meta = r["_meta"]
        for arm in ("B1", "B1+B2", "B1+B2+B3", "B1+B2+B3+B4a", "B1+B2+B3+B4b"):
            if arm not in r:
                continue
            x = r[arm]
            row = {**{k: meta[k] for k in ("rho", "lam", "K", "beta", "seed",
                                           "adversary", "block")},
                   "arm": arm, "pr_auc": x["pr_auc"], "roc_auc": x["roc_auc"],
                   "n_features": x["n_features"]}
            for f, v in x["recall_at_fpr"].items():
                row[f"recall@fpr={f}"] = v
            for q, v in x["fpr_at_recall"].items():
                row[f"fpr@recall={q}"] = v
            for f, v in x["value_weighted_at_fpr"].items():
                row[f"vw@fpr={f}"] = v
            rows.append(row)
    return pd.DataFrame(rows)


def rho_star(df: pd.DataFrame, arm: str, metric: str, adversary: str = "uniform",
             K: int = 11, beta: float = 0.5) -> pd.DataFrame:
    """rho*, per lambda: the largest rho at which the incremental value of the
    arm is still significant on *every* seed.

    Reported as an interval, because rho is sampled on a grid: the value is
    known to lie between the last significant grid point and the first
    non-significant one. Anything finer would be an interpolation the design
    does not support.
    """
    sel = df[(df.arm == arm) & (df.metric == metric) & (df.adversary == adversary)
             & (df.K == K) & (df.beta == beta)]
    out = []
    for lam, g in sel.groupby("lam"):
        per_rho = g.groupby("rho")["ci_lo"].min()          # worst seed
        sig = per_rho[per_rho > 0]
        rhos = sorted(per_rho.index)
        if len(sig) == 0:
            out.append({"lam": lam, "rho_star_lo": np.nan, "rho_star_hi": 0.0,
                        "status": "never significant"})
            continue
        last = max(sig.index)
        after = [r for r in rhos if r > last]
        out.append({
            "lam": lam, "rho_star_lo": last,
            "rho_star_hi": min(after) if after else np.inf,
            "status": "significant throughout" if not after else "bracketed",
        })
    return pd.DataFrame(out).sort_values("lam")
