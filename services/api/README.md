# services/api

The read-only FastAPI (E5.1). It serves what a run manifest RECORDS — computes
nothing, derives nothing, re-hashes nothing — from a runs root of directories
produced by `python -m engine.prospectivity.harness` (E5.5).

    python -m services.api.app <runs_root>        # http://127.0.0.1:8000/docs

Read-only is structural: only GET handlers exist and `tests/test_api.py`
asserts it over the app's own route table. A directory that is not a run is
refused by name at construction, never served as an empty catalog. See
`app.py`'s docstring for the endpoints and the three rules.
