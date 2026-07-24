# tests/fixtures/samples/

Small, hand-built samples standing in for what each real Phase-1 source
family looks like *after* its own fetch mechanism has run — i.e. the shape
`PangaeaAdapter`/`TabularFileAdapter`/`RegionalGridAdapter` actually consume.
Not real downloaded data (no real coordinates/values); enough rows to
exercise the evidence-class fan-out (a barren row, a row missing an optional
column, etc.).

- `pangaea_boxcore_sample.csv` — what `pangaeapy.PanDataSet(doi).data` would
  hand back for a source shaped like src_so268_boxcore [01] (MASS+COUNT+COVER
  from one box-core event).
- `dryad_chamber_sample.csv` — a Dryad-style chamber workbook, shaped like
  src_dryad_chamber [06] (MASS only; per-experiment chamber footprint).
- `regional_grid_sample.csv` — a compiled regional grid table, shaped like
  src_ts6_grid [18] (GRID only, prior/benchmark).
