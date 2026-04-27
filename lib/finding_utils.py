"""Pure utility functions for finding analysis – no framework dependencies."""


def _is_trusted_finding(line: str) -> bool:
    """Check if a findings.md line is a trusted, actionable finding.

    Requires [adr] tag for ADR promotion. Only findings that explicitly
    contain [adr] in the text are promoted to architectural decision records.
    """
    s = line.strip()
    return bool(s) and "[adr]" in s.lower()
