# TAX.1 — SYNTHETIC's evidence rule, widened; the written rasters, classified

Specification: the TAX.1 task prompt (2026-08-21). Reading order:
`CLAUDE.md`'s evidence table → `tests/test_data_origin_audit.py`
(`MIN_DETERMINISM_BASIS_CHARS`, the resolver's SYNTHETIC branch) →
`engine/prospectivity/surfaces/writer.py`.

**Two commits, and why.** `5d97735` is the rule alone; `c6938a0` is the
rasters. A taxonomy rule is the thing every other check defers to, so
reviewing it together with its first consumer would mean judging the rule and
the artifact that motivated it in one diff. Split, commit 1 is checkable
against the declarations that already existed — and it is: the suite did not
move (502 → 502), meaning every existing SYNTHETIC declaration still passes
and none that previously failed now passes.

| commit | what | suite |
|---|---|---|
| `5d97735` | the widened rule + its negation fixture | 502 → **502** |
| `c6938a0` | the rasters' classification | 502 → **505** |

---

## §0 — The rule was unsatisfiable, and the artifact proved it

All three premises were verified against primary sources before anything was
edited:

| premise | verified |
|---|---|
| the surface sidecar declares SYNTHETIC without a seed | **yes** — `data_origin: SYNTHETIC`, `generator: engine.prospectivity.surfaces.builder.build_surfaces`, `seed: None` |
| ordinary kriging has no seed | **yes** — `"seed"` is absent from its `provenance()` entirely |
| the audit refuses the seedless declaration | **yes** — `SYNTHETIC without a recorded seed`, by name |

So an artifact that **is** synthetic, declared **honestly**, could not satisfy
the rule — while a **fabricated** seed would have passed. That asymmetry is
the argument: **a rule only the dishonest path can satisfy is not strict, it
is unenforceable.** E3.1+2's writer returning `None` rather than a `0` was
correct, and it is what made the gap visible instead of papering over it.

---

## §1 — The rule, before and after

```text
BEFORE:  a generator import path  AND   seed(s)
AFTER:   a generator import path  AND  (a seed OR a determinism basis)
```

**Not a loosening**, and the reason is recorded in the rule's own text rather
than only here: it replaces an unsatisfiable requirement with a satisfiable
one carrying **the same information** — what produced this artifact, and what
makes it reproducible. A seed and a determinism basis are two answers to one
question; the old rule admitted only one of them.

### The loophole, closed where the rule is written

A bare basis — `"deterministic"`, `"n/a"`, `"none"` — satisfies the letter and
carries nothing. The check is **`MIN_DETERMINISM_BASIS_CHARS = 40`**.

| | |
|---|---|
| **the trade-off** | a minimum length is **crude but mechanically observable**. "Must reference the generator's mechanism" is better in principle and not checkable without reading English. |
| **why 40** | above every bare token that would actually be reached for — `"deterministic"` 13, `"no seed"` 7, `"n/a"` 3, `"fixed"` 5 — and below one clause naming a mechanism. |
| **what it does NOT catch** | a long sentence that names nothing. *"this artifact is deterministic and always reproducible"* is 54 characters and vacuous. **The check verifies EFFORT, not MEANING**, and no mechanical check can verify meaning. Review is the observer for vacuity; this is the observer for absence. |

One check, not two: a reject-list of bare tokens alongside the length test
would be **unreachable** given the threshold — the defect this project just
recorded at coverage-that-isn't ×6.

### Sites — found, not assumed

`CLAUDE.md`'s evidence table (**requirement and enforcement-site column**);
`origin.py`'s prose in two places; the `Declaration` dataclass **and all three
of its builders** (in-file, module constant, sidecar); and the resolver check.

---

## §2 — The rasters

**Facts established first, and one corrects the prompt's paraphrase.** No
surface rasters are tracked today. The audit's walk is
`git ls-files -- data tests/fixtures`, so **outputs under `data/` are INSIDE
the boundary, not outside it** — E3.1+2 measured that directly, and the
"outputs directory may sit outside the walk" hedge does not apply.

**The association is one the audit resolves.** `data_origin.yaml` with a
`files:` mapping keyed by filename, read by `_sidecar_declaration` — the same
form `tests/fixtures/samples/` and `data/corpus/` already use. Not a naming
convention a human infers from adjacent filenames. A GeoTIFF cannot carry an
in-file declaration without changing the bytes it is pinned by (the P2.0c
marker-form rule), so the sidecar is the marker of record.

**Seed or basis, and never both** (§3's rule): the estimator declares which.
RF has a seed and records a seed; kriging and the mean baseline are seedless
and declare a basis. A surface whose estimator can evidence **neither** is
refused by name rather than written unevidenced.

### Two gaps the end-to-end probe found

1. The `.json` sidecar declared **itself** SYNTHETIC without carrying its own
   evidence — the audit refused it. It now carries the same generator and
   seed-or-basis.
2. `data_origin.yaml` came back **UNCLASSIFIED**. Existing sidecars are
   excluded by three *per-path* `EXCLUSIONS` entries all giving the same
   reason, so every new output directory would need a hand-added entry or its
   sidecar surfaces as unclassified. **Made generic** — the resolver already
   encodes that a sidecar is the mechanism, not a subject — and the three
   redundant entries removed. *A scope judgement, reported rather than made
   silently.*

### The probe, both directions

| direction | result |
|---|---|
| with declarations | 6 subjects enumerated; **zero unclassified, zero invalid** |
| basis replaced by `"deterministic"` | **both rasters refused BY NAME** with the length message |

---

## §3 — The basis at its first real use, verbatim

> `ordinary kriging solves a closed-form linear system (the OK system matrix
> plus a Lagrange multiplier) over a variogram fitted by weighted least
> squares on a FIXED candidate range grid; there is no sampling, no shuffling
> and no RNG at fit or predict time, so the output is a function of the
> inputs alone`

302 characters. **Does it read like boilerplate?** No — and the test is
whether it says anything a reader could check. It names the solve (closed-form
linear system, Lagrange multiplier), the fitting method (WLS on a fixed
candidate grid), and the specific absences that make determinism true here
(no sampling, no shuffling, no RNG at either phase). Each is falsifiable
against `kriging.py`. The mean baseline's is shorter (188 chars) and equally
specific: closed-form reductions over every training row.

**The honest caveat:** the length check would have admitted a vacuous
sentence of the same size. That these two are not vacuous is a fact about the
authoring, not about the check — which is exactly what the trade-off table
above says.

---

## §4 — Mutations

**Commit 1 — 4/4, each caught by EXACTLY ONE test across the full suite**,
which re-confirms the sole-observer docstring for all three branches:

| # | mutation | caught by |
|---|---|---|
| M1 | the loophole check removed (bare basis admitted) | the SYNTHETIC evidence test |
| M2 | the seed-or-basis check removed | " |
| M3 | the generator check removed | " |
| M4 | threshold lowered to admit `"deterministic"` | " |

**Commit 2 — 5/5:**

| # | mutation | caught by |
|---|---|---|
| R1 | raster origin hard-declared MEASURED (laundering) | `..._classified_by_the_audits_own_sidecar_mechanism` |
| R2 | sidecar overwritten instead of merged | `..._do_not_un_classify_the_first` |
| R3 | the seed-or-basis refusal removed | `..._can_evidence_neither_is_refused_by_name` |
| R4 | a seed recorded alongside a basis | `..._do_not_un_classify_the_first` |
| R5 | the generic sidecar exclusion removed | 2 audit tests |

## What this task did NOT do

No other member's evidence requirement was touched — **LITERATURE's
zero-observer gap remains its own BACKLOG item with its own live trigger**
(before Track G supplies any cited value). Admissibility is unchanged: this
is an evidence rule, not an admissibility rule, and the production guard's
declaration-plus-proof check is untouched.

## §5 — The TS-6 origin class, decided at the approval (2026-08-21)

Recorded here because E3.0 §6 made it a **prerequisite** for E3.3, and TAX.1's
approval is where it was answered.

**Karl's decision: `ts6_abundance.tif` is DERIVED**, declared in Contract 6
(`raster_data_origin`, `reference_version` 2 → 3, additive).

**WHAT THE ARTIFACT IS decides its class, not what it DEPICTS.** The file is
not TS-6's surface; it is a raster computed by us from a published figure by a
recorded procedure, so its values are a function of that figure and that
procedure — DERIVED's definition. The TS-6 publication is DERIVED's *input*,
cited as such, the same relation the corpus has to its sources.

| class | verdict |
|---|---|
| MEASURED | **refused** — we did not measure it, and hashing this file would hash OUR OWN OUTPUT, not a published one |
| LITERATURE | **refused** — the numbers are our *reading* of a printed surface, carrying digitization error we introduce |
| DERIVED | **the artifact's actual relation to its input** |

**The consequence is not the motive, and the record says so.** DERIVED has an
audit observer; LITERATURE does not. That is a **relief, not a reason** — had
the correct answer been LITERATURE, the answer would still be LITERATURE and
the observer gap would have become urgent instead. A classification chosen for
the convenience of its check is the failure the taxonomy exists to prevent.

**Two consequences carried to the BACKLOG rather than built here:** E3.3 must
propagate the digitization error (a comparison treating the benchmark as exact
overstates its own precision), and `digitization_method` is now DERIVED's
evidence — which a one-word answer cannot satisfy, exactly as a bare
"deterministic" cannot satisfy SYNTHETIC's basis.

**Two things unchanged, verified against the file rather than assumed:**
`role_note` remains `null` and `[GEOLOGY — ISAAC]`, with `benchmark_only`
marked *(PREFERRED)* in its comment — it is **not** a declared default, and
origin class and circularity are different axes. And **LITERATURE's
zero-observer gap stays OPEN** with its trigger live: this decision removes
one arrival from that class, but the AOI is still potentially LITERATURE and
the gap is unresolved either way.

## What the next task adds

E3.3 — its prerequisite is now answered.
