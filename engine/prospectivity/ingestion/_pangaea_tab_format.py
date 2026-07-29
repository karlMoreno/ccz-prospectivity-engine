"""Shared PANGAEA raw tab-export parsing helpers — factored out of
`nodule_aggregate_adapter.py` (D8, 2026-07-27 review) once a SECOND real
PANGAEA source ([01] PANGAEA.904967, wired in `boxcore_summary_adapter.py`)
needed the exact same header-terminator detection and event-comment
extraction as [05] PANGAEA.904962. Not one of CLAUDE.md's named seams —
private implementation-sharing infrastructure, same spirit as
`_column_mapping.py`/`_contract_paths.py`.
"""

from __future__ import annotations

import re

_METADATA_TERMINATOR = "*/"

# An event's own recovery notes ("GER Trial; failed") live in the header's
# `Event(s):` block, one event per line (the first line carries the
# `Event(s):` label; every following event is a tab-indented continuation),
# shaped like: "<event label> (<alias>) * LATITUDE: ... * ... * COMMENT: <text>".
# Not hardcoded to SO268's own label format -- matches any "<token> (...)"
# opener followed eventually by a COMMENT field, which is PANGAEA's own
# Event(s) block convention, so it should work for the next PANGAEA export too.
_EVENT_COMMENT_RE = re.compile(r"^\s*(?:Event\(s\):)?\s*(\S+)\s*\([^)]*\).*?COMMENT:\s*(.+?)\s*$")

FAILED_RE = re.compile(r"failed", re.IGNORECASE)


def split_header_and_data(raw_text: str) -> tuple[str, str]:
    """Detect the PANGAEA metadata block's terminator line (exactly "*/")
    rather than hardcoding a skiprows count -- [01]'s real file has a
    64-line header, [05]'s has 63; a fixed skiprows would misparse one of
    them."""
    lines = raw_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == _METADATA_TERMINATOR:
            return "\n".join(lines[: index + 1]), "\n".join(lines[index + 1 :])
    raise ValueError(
        f"Could not find the PANGAEA metadata block terminator ({_METADATA_TERMINATOR!r})"
    )


def parse_event_comments(header_text: str) -> dict[str, str]:
    """{event_label: comment_text} from the header's `Event(s):` block."""
    comments: dict[str, str] = {}
    for line in header_text.splitlines():
        match = _EVENT_COMMENT_RE.match(line)
        if match:
            comments[match.group(1)] = match.group(2)
    return comments
