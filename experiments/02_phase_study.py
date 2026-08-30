"""The phase study.

Primary surface: rho x lambda under the pre-registered adversary.
Secondary surface: the same grid under a prevalence-matched adversary, whose
declared code carries no marginal information at rho = 1.
Secondary 1-D sweeps: purpose cardinality K, beneficiary noise beta.
"""

from __future__ import annotations

import os
import sys

import yaml

from pramana.sweep import expand, run_sweep

GRIDS = {
    "primary": dict(rho=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    lam=[0.0, 0.05, 0.10, 0.20, 0.35],
                    K=[11], beta=[0.5], seed=[0, 1, 2], adversary=["uniform"]),
    "prevalence": dict(rho=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                       lam=[0.0, 0.05, 0.10, 0.20, 0.35],
                       K=[11], beta=[0.5], seed=[0, 1, 2], adversary=["prevalence"]),
    "cardinality": dict(rho=[0.4], lam=[0.10], K=[3, 6], beta=[0.5],
                        seed=[0, 1, 2], adversary=["uniform"]),
    "beneficiary_noise": dict(rho=[0.4], lam=[0.10], K=[11], beta=[0.0, 1.0],
                              seed=[0, 1, 2], adversary=["uniform"]),
}


def main() -> None:
    cfg = yaml.safe_load(open("config/base.yaml"))
    # Block order matters: the pre-registered primary surface and its two
    # pre-registered secondary sweeps run first, so the frozen analysis is
    # complete before the added prevalence-matched surface starts.
    blocks = sys.argv[1:] or list(GRIDS)
    cells = [c for b in blocks for c in expand(GRIDS[b], b)]
    run_sweep(cfg, cells, n_jobs=int(os.environ.get("PRAMANA_JOBS", 7)),
              n_boot=cfg["evaluation"]["bootstrap_n"])


if __name__ == "__main__":
    main()
