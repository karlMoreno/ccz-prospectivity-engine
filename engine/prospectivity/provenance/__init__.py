"""Provenance artifacts (AR-D05, AR-P09) — see docs/contracts/PROVENANCE.md.

Three stage-level artifacts, deliberately NOT merged, all extending
ProvenanceArtifact (LAYER SUPERTYPE, artifact.py) so the chaining fields have
identical names everywhere:

    CorpusManifest        ingestion   data/corpus/manifest.json
    FeatureStackManifest  features    <stack dir>/provenance.json
    RunManifest           model run   (domain/results.py; Phase 2-4)

Deliberately no package-level re-exports: `domain/results.py` imports
`artifact` directly, and pulling `recorder` (which imports `domain`) in here
would make that a cycle. Import from the submodules.
"""
