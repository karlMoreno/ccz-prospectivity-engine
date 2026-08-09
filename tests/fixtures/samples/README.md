# tests/fixtures/samples/

Per-source-family sample files, shaped like what each real Phase-1 fetch
mechanism hands back — i.e. what `PangaeaAdapter` / `TabularFileAdapter` /
`RegionalGridAdapter` actually consume. **Origins are DECLARED in
[`data_origin.yaml`](data_origin.yaml) in this directory — that sidecar is
the authoritative side if this prose ever diverges again** (it did once: an
earlier version of this README claimed the whole directory held no real
data, which was false for the fourth file below — audit §5 #2, fixed
P2.0d-3).

Three files are hand-built (AUTHORED — invented values, plausible shapes,
enough rows to exercise the evidence-class fan-out):

- `pangaea_boxcore_sample.csv` — what `pangaeapy.PanDataSet(doi).data` would
  hand back for a source shaped like src_so268_boxcore [01]
  (MASS+COUNT+COVER from one box-core event).
- `dryad_chamber_sample.csv` — a Dryad-style chamber workbook, shaped like
  src_dryad_chamber [06] (MASS only; per-experiment chamber footprint).
- `regional_grid_sample.csv` — a compiled regional grid table, shaped like
  src_ts6_grid [18] (GRID only, prior/benchmark).

One file is REAL data (MEASURED — a verbatim excerpt, not a fabrication):

- `so268_nodules_sample.csv` — rows taken as-is from four named events of
  **PANGAEA.904962** (Schoening & Gazis 2019, "Sizes, weights and volumes of
  poly-metallic nodules from box cores taken during SONNE cruises SO268/1
  and SO268/2", GEOMAR; **CC BY-NC 4.0**;
  https://doi.org/10.1594/PANGAEA.904962). The row SELECTION is authored
  (the events are listed in the CSV's own header); the VALUES are measured.
  The parent file lives at `data/sources/SO268-bc-nodules-PANGAEA-904962.tab`
  with its hash recorded in `data/corpus/manifest.json` and the sidecar.
