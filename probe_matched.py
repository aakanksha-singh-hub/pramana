import copy, yaml, time
from pramana.dataset import build_base
from pramana.harness import run_cell
base_cfg = yaml.safe_load(open('config/base.yaml'))
base = build_base(base_cfg, 0.10, 0)
for T in (1.0, 0.5):
    cfg = copy.deepcopy(base_cfg); cfg['fraud']['matcher_temperature'] = T
    for rho in (1.0, 0.4):
        t = time.time()
        r = run_cell(base, cfg, rho=rho, lam=0.10, K=11, beta=0.5, seed=0,
                     n_boot=500, adversary='matched')
        db = r['delta']['B1+B2+B3+B4b']['recall@fpr=0.001']
        da = r['delta']['B1+B2+B3+B4a']['recall@fpr=0.001']
        print("T=%.1f rho=%.1f (%.0fs) base=%.4f B4a=%.4f B4b=%.4f | dB4a %+.5f [%+.5f,%+.5f] %s | dB4b %+.5f [%+.5f,%+.5f] %s" % (
            T, rho, time.time()-t,
            r['B1+B2+B3']['recall_at_fpr']['0.001'],
            r['B1+B2+B3+B4a']['recall_at_fpr']['0.001'],
            r['B1+B2+B3+B4b']['recall_at_fpr']['0.001'],
            da['point'], da['ci'][0], da['ci'][1], 'SIG' if da['significant'] else 'NS',
            db['point'], db['ci'][0], db['ci'][1], 'SIG' if db['significant'] else 'NS'), flush=True)
