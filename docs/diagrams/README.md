# docs/diagrams — Phase 1 explained in five pictures

Mermaid source (`.mmd`). Each file ends with a `%%` comment block containing a
plain-English caption, the date, and the manifest `content_hash` it was drawn
from — so a diagram that has drifted from the corpus is detectable rather than
quietly wrong.

**Read in this order.** The first three are for Isaac; the last two are an
appendix for code reviewers.

| # | File | One line |
|---|---|---|
| 1 | [`evidence_classes.mmd`](evidence_classes.mmd) | The five kinds of evidence and what each is allowed to become — the project's scientific discipline, and the one to lead with. |
| 2 | [`two_track_build.mmd`](two_track_build.mmd) | Who owns what: Track E builds on fixtures, Track G supplies real data, the seven contracts are the only coupling — and what is still outstanding. |
| 3 | [`data_flow.mmd`](data_flow.mmd) | Source → corpus → covariates → model, annotated with today's real row counts and which sources are wired, unwired, or not yet. |
| 4 | [`architecture_uml_ingestion.mmd`](architecture_uml_ingestion.mmd) | Appendix: the ingestion classes and the design pattern each cluster implements. |
| 5 | [`architecture_uml_features_provenance.mmd`](architecture_uml_features_provenance.mmd) | Appendix: terrain features and the three chained provenance artifacts. |

Diagrams 4 and 5 are the two halves of what the brief called
`architecture_uml.mmd`. Around thirty classes in one picture is unreadable, and
the brief prefers two legible diagrams to one dense one.

## Provenance of the numbers

Every figure is read from the repo, not from memory:

- row counts, source dispositions, training-eligible count, licences —
  `data/corpus/manifest.json`
- evidence-class rules and screening bounds — `data/config/normalization.yaml`
- covariate list and versions — `docs/contracts/covariates.yaml`
- wired vs unwired sources — `engine/prospectivity/ingestion/corpus_builder.py`
- contract delivery status — the seven contract files themselves

Drawn from manifest `generated_at` **2026-07-31T03:45:25Z**,
`content_hash` **sha256:372be3bb381385fbbeacdcfb5bd407807e60ddedcd522737c7f9d350dbbbf32f**.

Pin updated 2026-08-08 (P2.0c) to
**sha256:0227d6df608ee23476c7f5915bede82f1ffb360c542e33152386257a2fd07fd9**:
that rebuild was METADATA-ONLY (origin markers + contract-version bumps — see
`docs/walkthroughs/P2.0.md` §c). The corpus CSV is byte-identical and every
count these diagrams show is unchanged, so they remain accurate against the
new hash.

If `data/corpus/manifest.json`'s `content_hash` no longer matches the newest
pin above, these diagrams predate the current corpus and their numbers should
be re-checked.

## Rendering

Paste a file into <https://mermaid.live>, or view on GitHub (which renders
```mermaid fences — wrap the file contents in one), or run
`npx @mermaid-js/mermaid-cli -i evidence_classes.mmd -o evidence_classes.svg`.

All five were verified by parsing **and** rendering to SVG with mermaid v11
(see the task report for the method and its one caveat).
