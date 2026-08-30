"""Phase diagrams, rho*, and the web-ready surface export.

A cell is shown as significant only if the lower bound of the paired bootstrap
95% CI is above zero on *every* seed. Cells that fail that test are hatched,
not hidden: the regions where declared context does not pay are part of the
result.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

from pramana.sweep import arm_table, collect, rho_star

FIG = Path("results/figures")
ARM = "B1+B2+B3+B4b"
HEADLINE_METRICS = ["recall@fpr=0.001", "fpr@recall=0.7"]
PRETTY = {"recall@fpr=0.001": "Δ recall @ FPR 0.1%",
          "recall@fpr=0.005": "Δ recall @ FPR 0.5%",
          "recall@fpr=0.01": "Δ recall @ FPR 1%",
          "fpr@recall=0.5": "Δ FPR @ recall 50% (reduction)",
          "fpr@recall=0.7": "Δ FPR @ recall 70% (reduction)",
          "fpr@recall=0.9": "Δ FPR @ recall 90% (reduction)"}


def surface(df: pd.DataFrame, arm: str, metric: str, adversary: str,
            K: int = 11, beta: float = 0.5) -> pd.DataFrame:
    sel = df[(df.arm == arm) & (df.metric == metric) & (df.adversary == adversary)
             & (df.K == K) & (df.beta == beta)]
    g = sel.groupby(["lam", "rho"]).agg(
        delta=("delta", "mean"), delta_sd=("delta", "std"),
        ci_lo_min=("ci_lo", "min"), ci_hi_max=("ci_hi", "max"),
        n_seeds=("seed", "nunique"), n_test_fraud=("n_test_fraud", "mean"),
    ).reset_index()
    g["significant"] = g.ci_lo_min > 0
    return g


def heatmap(ax, g: pd.DataFrame, title: str, cbar_label: str):
    lams = sorted(g.lam.unique())
    rhos = sorted(g.rho.unique())
    M = np.full((len(lams), len(rhos)), np.nan)
    S = np.zeros_like(M, dtype=bool)
    for _, r in g.iterrows():
        i, j = lams.index(r.lam), rhos.index(r.rho)
        M[i, j] = r.delta
        S[i, j] = r.significant

    vmax = np.nanmax(np.abs(M)) or 1e-9
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    im = ax.imshow(M, cmap="RdBu_r", norm=norm, aspect="auto", origin="lower")
    for i in range(len(lams)):
        for j in range(len(rhos)):
            if np.isnan(M[i, j]):
                continue
            if not S[i, j]:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                           hatch="////", edgecolor="0.35", lw=0))
            ax.text(j, i, f"{M[i, j]:+.3f}", ha="center", va="center", fontsize=7.5,
                    color="0.1" if abs(M[i, j]) < vmax * .6 else "white")
    ax.set_xticks(range(len(rhos)), [f"{r:g}" for r in rhos])
    ax.set_yticks(range(len(lams)), [f"{l:g}" for l in lams])
    ax.set_xlabel(r"$\rho$  coaching effectiveness")
    ax.set_ylabel(r"$\lambda$  structural overlap")
    ax.set_title(title, fontsize=10.5)
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label(cbar_label, fontsize=8)
    return im


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    df = collect()
    if df.empty:
        raise SystemExit("no results in results/raw — run `make sweep` first")
    arms = arm_table()

    # ---- phase diagrams -------------------------------------------------
    for adversary in sorted(df.adversary.unique()):
        fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.6))
        for ax, metric in zip(axes, HEADLINE_METRICS):
            g = surface(df, ARM, metric, adversary)
            if g.empty:
                continue
            heatmap(ax, g, PRETTY[metric], PRETTY[metric])
        label = ("pre-registered adversary" if adversary == "uniform"
                 else "prevalence-matched adversary (secondary)")
        fig.suptitle(f"Incremental value of declared payment context — {label}\n"
                     f"hatched: paired bootstrap 95% CI includes zero on at "
                     f"least one seed", fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(FIG / f"phase_{adversary}.png", dpi=170)
        plt.close(fig)

    # ---- rho* ------------------------------------------------------------
    rs = {}
    for adversary in sorted(df.adversary.unique()):
        for metric in HEADLINE_METRICS:
            rs[f"{adversary}|{metric}"] = rho_star(df, ARM, metric, adversary).to_dict("records")

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for adversary, colour in (("uniform", "#1f4e79"), ("prevalence", "#c1121f")):
        key = f"{adversary}|recall@fpr=0.001"
        if key not in rs:
            continue
        recs = rs[key]
        x = [r["lam"] for r in recs]
        y = [1.15 if np.isinf(r["rho_star_hi"]) else r["rho_star_hi"] for r in recs]
        for r in recs:
            if r.get("non_monotonic"):
                print(f"  NOTE lam={r['lam']}: significance is non-monotonic in rho "
                      f"(grid {r['significant_grid']})")
        lo = [0.0 if np.isnan(r["rho_star_lo"]) else r["rho_star_lo"] for r in recs]
        ax.plot(x, y, "o-", color=colour, label=f"{adversary} adversary")
        ax.fill_between(x, lo, y, color=colour, alpha=0.18)
    ax.axhline(1.0, color="0.5", ls=":", lw=1)
    ax.text(0.001, 1.02, "no coaching level in range removes the signal",
            fontsize=7.5, color="0.35")
    ax.set_xlabel(r"$\lambda$  structural overlap rate")
    ax.set_ylabel(r"$\rho^*$  (bracketed by the sweep grid)")
    ax.set_title(r"$\rho^*$: coaching level at which incremental value stops "
                 "being significant\nrecall @ FPR 0.1%", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "rho_star.png", dpi=170)
    plt.close(fig)

    # ---- ablation --------------------------------------------------------
    base = arms[(arms.rho == 0.4) & (arms.lam == 0.10) & (arms.K == 11)
                & (arms.beta == 0.5) & (arms.adversary == "uniform")]
    if not base.empty:
        agg = base.groupby("arm")["recall@fpr=0.001"].agg(["mean", "std"])
        order = ["B1", "B1+B2", "B1+B2+B3", "B1+B2+B3+B4a", "B1+B2+B3+B4b"]
        agg = agg.reindex([a for a in order if a in agg.index])
        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        colours = ["#b0b7c3", "#8d97a8", "#1f4e79", "#2e7d32", "#1b5e20"]
        ax.bar(range(len(agg)), agg["mean"], yerr=agg["std"], capsize=4,
               color=colours[:len(agg)])
        for i, v in enumerate(agg["mean"]):
            ax.text(i, v + 0.015, f"{v:.3f}", ha="center", fontsize=8.5)
        ax.set_xticks(range(len(agg)), agg.index, fontsize=8.5)
        ax.set_ylim(0, 1.08)
        ax.set_ylabel("recall @ FPR 0.1%")
        ax.set_title(r"Ablation at $\rho$=0.4, $\lambda$=0.10 (3 seeds, "
                     "error bars = SD across seeds)", fontsize=10)
        fig.tight_layout()
        fig.savefig(FIG / "ablation.png", dpi=170)
        plt.close(fig)

    # ---- secondary 1-D sweeps -------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    for ax, (col, block, xlabel) in zip(axes, [
            ("K", "cardinality", "purpose cardinality K"),
            ("beta", "beneficiary_noise", r"$\beta$  beneficiary-feature noise")]):
        sel = df[(df.arm == ARM) & (df.metric == "recall@fpr=0.001")
                 & (df.adversary == "uniform") & (df.rho == 0.4) & (df.lam == 0.10)]
        g = sel.groupby(col).agg(delta=("delta", "mean"),
                                 lo=("ci_lo", "min"), hi=("ci_hi", "max")).reset_index()
        if g.empty:
            continue
        ax.errorbar(g[col], g.delta, yerr=[g.delta - g.lo, g.hi - g.delta],
                    fmt="o-", color="#1f4e79", capsize=4)
        ax.axhline(0, color="0.6", lw=1, ls="--")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(PRETTY["recall@fpr=0.001"])
    fig.suptitle(r"Secondary sweeps at $\rho$=0.4, $\lambda$=0.10", fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(FIG / "secondary_sweeps.png", dpi=170)
    plt.close(fig)

    # ---- web-ready export ------------------------------------------------
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "arm": ARM,
        "metrics": {},
        "rho_star": rs,
        "ablation": arms.to_dict("records"),
        "cells": df.to_dict("records"),
    }
    for adversary in sorted(df.adversary.unique()):
        for metric in df.metric.unique():
            g = surface(df, ARM, metric, adversary)
            if not g.empty:
                payload["metrics"][f"{adversary}|{metric}"] = g.to_dict("records")
    Path("results/phase_surface.json").write_text(json.dumps(payload, default=str))

    # ---- console summary --------------------------------------------------
    print(f"cells collected: {df[['rho','lam','K','beta','seed','adversary']].drop_duplicates().shape[0]}")
    for adversary in sorted(df.adversary.unique()):
        print(f"\n=== {adversary} adversary — rho* by lambda (recall @ FPR 0.1%) ===")
        rsx = rho_star(df, ARM, "recall@fpr=0.001", adversary)
        print(rsx.to_string(index=False) if len(rsx) else "  (no cells)")
        g = surface(df, ARM, "recall@fpr=0.001", adversary)
        if len(g):
            print(g.pivot(index="lam", columns="rho", values="delta").round(4).to_string())
            sg = surface(df, ARM, "recall@fpr=0.001", adversary)
            print("\nsignificant (CI lower bound > 0 on every seed):")
            print(sg.pivot(index="lam", columns="rho", values="significant").to_string())
    print(f"\nfigures -> {FIG}")


if __name__ == "__main__":
    main()
