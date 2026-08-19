"""Spatial cross-validation (AR-P05) — E2.4: `splitter` (FoldSplitter Strategy +
fold assignment provenance + the spatial-leakage assertion) and `metrics`
(the metric set with its sd=0 policy). E2.4 §2 adds the runner; E2.5 adds
the refuse-to-validate guard. Originally reserved as:
spatially-blocked CV + the mean-baseline comparison + the "refuse to validate
if spatial CV didn't run" guard.
"""
