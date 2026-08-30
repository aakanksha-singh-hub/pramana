import yaml, time
from pramana.dataset import build_base
from pramana.harness import run_cell
cfg = yaml.safe_load(open('config/base.yaml'))
base = build_base(cfg, 0.10, 0)
for adv in ('matched',):
    for rho in (1.0, 0.4, 0.0):
        t = time.time()
        r = run_cell(base, cfg, rho=rho, lam=0.10, K=11, beta=0.5, seed=0,
                     n_boot=500, adversary=adv)
        da = r['delta']['B1+B2+B3+B4a']['recall@fpr=0.001']
        db = r['delta']['B1+B2+B3+B4b']['recall@fpr=0.001']
        print("%s rho=%.1f (%.0fs, rerouted %d)" % (adv, rho, time.time()-t, r['_meta']['n_rerouted']), flush=True)
        print("   baseline R@.1%%=%.4f  +B4a=%.4f  +B4b=%.4f" % (
            r['B1+B2+B3']['recall_at_fpr']['0.001'],
            r['B1+B2+B3+B4a']['recall_at_fpr']['0.001'],
            r['B1+B2+B3+B4b']['recall_at_fpr']['0.001']), flush=True)
        print("   delta B4a %+.5f CI[%+.5f,%+.5f] %s" % (da['point'], da['ci'][0], da['ci'][1], 'SIG' if da['significant'] else 'NOT SIG'), flush=True)
        print("   delta B4b %+.5f CI[%+.5f,%+.5f] %s" % (db['point'], db['ci'][0], db['ci'][1], 'SIG' if db['significant'] else 'NOT SIG'), flush=True)
