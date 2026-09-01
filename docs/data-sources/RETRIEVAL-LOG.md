# Retrieval log — attempts to obtain named closing evidence

Standing record of attempts to acquire documents that BACKLOG entries name as the
evidence that would close them. One section per target, appended as attempts happen.

**The distinction this file exists to keep.** A question can leave the "open" state
two ways, and they are not the same:

- **RESOLVED BY EVIDENCE** — a document was obtained (or an authoritative record
  read) and it answers the question.
- **RESOLVED BY DEFAULT AFTER A DOCUMENTED ATTEMPT** — the document could not be
  obtained, the attempt is written down, and the question is settled by falling
  back to what is already held. This is weaker and must never be recorded as if it
  were the first.
- **STILL OPEN** — attempted, not obtained, and nothing was settled by default
  either. The entry stays open with the attempt logged so it is not repeated blind.

---

## 1. Sorem, Reinhart, Fewkes & McFarland (1979a) — the DOMES chapter, pp. 475–527

**Why it matters.** [04] Table 1 is footnoted "From Sorem et al. 1979a"; the chapter
is named closing evidence for the **Contract 1 wet/dry gap** and is the only
plausible discriminator for **WET.2's 24 unresolved Moana Wave rows**. It is the
companion chapter to [03] in the same Plenum volume, so obtaining the volume would
also yield a clean copy of Table 8.

**Attempts, 2026-09-01:**

| # | route | outcome |
|---|---|---|
| 1 | SpringerLink chapter page (`10.1007/978-1-4684-3518-4_14`) | **303 redirect to `idp.springer.com` auth** — paywalled, no full text |
| 2 | Crossref API for the same DOI | **SUCCEEDED — metadata only** (see below) |
| 3 | HathiTrust full-text search for the volume | **HTTP 403** — blocks automated fetch |
| 4 | Open-web search for a full-view / open copy of the volume | none found; print-on-demand and paywalled listings only |

**RESOLVED BY EVIDENCE (a different question than the one we were chasing).**
Crossref — the publisher's own canonical record for its own book — gives:

> **Title:** "Occurrence and Character of Manganese Nodules in DOMES Sites A, B,
> and C, East Equatorial Pacific Ocean"
> **Authors, in order:** R. K. Sorem · W. R. Reinhart · R. H. Fewkes · W. D. McFarland
> **Pages:** 475–527 · **Book:** *Marine Geology and Oceanography of the Pacific
> Manganese Nodule Province* · **Publisher:** Springer US · **Year:** 1979

This **settles WET.3's citation discrepancy**. The canonical author list is the
**four-author** form, in **exactly Piper 1979's order** — so Piper's reference list
(p. 473) is right and **Sorem 1989's own reference list (p. 200) omits W. R.
Reinhart** from a chapter Sorem himself co-authored. The page range 475–527 matches
both. Crossref also supplies the initials Piper's entry lacked (**W. D.** McFarland).
See WET.3 §23 for how the records were updated.

**STILL OPEN — the thing actually wanted.** No full text was obtained, so the
**wet/dry gap stays open** and the **M.W. rows stay UNRESOLVED**. Nothing was
resolved by default; the fallback would have been to guess a drying protocol, which
is exactly what those entries refuse to do.

**Not attempted, and why.** CU Boulder ILL requires signing in to the user's
institutional account. That is an account action on the user's behalf and is left
to Karl — it remains the highest-value route, since the volume yields both this
chapter and a clean Table 8.

---

## 2. Fewkes, McFarland, Reinhart & Sorem (1980) — USBM OFR 108-80, NTIS PB80-228992

**Why it matters.** [02]'s parent report. Wanted for [02]'s own methods and as a
cross-check on the DOMES-family author record.

**Attempts, 2026-09-01:**

| # | route | outcome |
|---|---|---|
| 1 | Open-web search for the report and its NTIS handle | no open full text found |
| 2 | USGS Publications Warehouse API | **HTTP 403** — blocks automated fetch. (It is a **Bureau of Mines** report, not USGS, so a hit was unlikely regardless) |
| 3 | Wikidata `Q26367319` | **SUCCEEDED — metadata only** (see below) |
| 4 | HathiTrust | same 403 as §1 |
| 5 | NTIS / NTRL direct download | not reachable without a request through NTIS; handle `PB80228992` confirmed |

**RESOLVED BY EVIDENCE (corroboration only).** Wikidata records the report as
*"Evaluation of Metal Resources At and Near Proposed Deep Sea Mine Sites"*, 1980,
authors **Fewkes-RH · McFarland-WD · Reinhart-WR · Sorem-RK**, LoC control number
**PB80228992**, no DOI. That author list **matches Sorem 1989's reference-list
rendering exactly** (WET.3 §22a), which corroborates that rendering independently.

**STILL OPEN.** No full text; [02]'s methods — including whether its kg/m² are wet
or dry — remain unread. Nothing resolved by default.

**Not attempted:** NTIS paid retrieval and CU Boulder ILL — both Karl's to run.

---

## What these attempts changed, and what they did not

**Changed:** WET.3's citation discrepancy moved from *"recorded, not reconciled"* to
**resolved by evidence** — the four-author form is canonical, and the author-overlap
linkage between [02] and [04]'s source chapter is now an **identical four-person
set** under the canonical list rather than identical-under-one-of-two-readings.

**Not changed:** every open item that needs the *content* of these two documents.
The wet/dry gap, the M.W. classification, and [02]'s basis all stay open, each with
this log referenced from its BACKLOG entry so the next attempt starts from routes 1–5
rather than repeating them.
