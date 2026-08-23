import numpy as np, sys
sys.path.insert(0, '/Users/karlmoreno/CCZ/ccz-prospectivity-engine')
mu = np.load('/tmp/_m5_mu.npy'); mean = float(np.load('/tmp/_m5_mean.npy'))
flat = mu[np.isfinite(mu)]
rng = np.random.RandomState(0); sample = flat[rng.choice(flat.size, 200, replace=False)]
varies = sample.std() > 1e-9
print(f'      uniform 200-cell sample: sd={sample.std():.6f} -> "surface varies" {varies}')
