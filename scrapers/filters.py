"""
Keyword filters for SAP Finance roles and C2C contract type.
Returns are typed precisely so the pipeline can act on each case.
"""

import re
from typing import Union

# --- SAP Finance keywords ---

SAP_TITLE_KEYWORDS = [
    "sap finance", "sap fi", "sap co", "sap fico", "sap fi/co",
    "sap fi co", "sap financial", "sap management accounting",
    "sap s/4hana finance", "sap s4hana finance", "sap s4 hana finance",
    "sap controlling", "sap financial accounting", "sap gl", "sap ap",
    "sap ar", "sap asset accounting", "sap product costing",
    "sap profitability analysis", "sap copa", "sap finance consultant",
    "sap fico consultant", "sap finance analyst",
]

SAP_DESCRIPTION_KEYWORDS = [
    "sap fico", "sap fi/co", "s/4hana finance", "s4hana finance",
    "sap financial accounting", "sap management accounting",
    "sap controlling module", "sap fi module", "sap co module",
    "general ledger sap", "accounts payable sap", "accounts receivable sap",
]


def is_sap_finance_role(title: str, description: str) -> bool:
    """Return True if job is a SAP Finance related role."""
    title_lower = title.lower()
    desc_lower = description.lower()

    # Check title first (strong signal)
    for kw in SAP_TITLE_KEYWORDS:
        if kw in title_lower:
            return True

    # Fall back to description
    for kw in SAP_DESCRIPTION_KEYWORDS:
        if kw in desc_lower:
            return True

    return False


# --- C2C filters ---

C2C_POSITIVE = [
    r"\bc2c\b",
    r"corp[\s\-]*to[\s\-]*corp",
    r"corporation[\s\-]*to[\s\-]*corporation",
    r"\b1099\b",
    r"c2c[\s\-]*preferred",
    r"c2c[\s\-]*ok",
    r"w2\s*or\s*c2c",
    r"c2c\s*or\s*w2",
    r"contract[\s\-]*only",
    r"contract[\s\-]*position.*corp",
]

C2C_EXCLUSIONS = [
    r"\bno\s+c2c\b",
    r"w[\-]?2\s+only",
    r"no\s+corp[\s\-]*to[\s\-]*corp",
    r"no\s+1099",
    r"full[\s\-]*time\s+only",
    r"permanent\s+only",
    r"w2\s+employees?\s+only",
]

# "no third party" can mean no staffing firms but NOT always no C2C
# We flag these for manual review rather than hard-exclude
MANUAL_REVIEW = [
    r"no\s+third[\s\-]*party",
    r"no\s+3rd[\s\-]*party",
    r"third[\s\-]*party\s+not\s+accepted",
]


def _matches_any(patterns: list[str], text: str) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def is_c2c_role(description: str) -> Union[bool, str]:
    """
    Returns:
      True           — confirmed C2C or 1099 role
      False          — explicitly excluded (W2 only, no C2C, etc.)
      "excluded"     — soft-excluded (no explicit C2C mention at all)
      "manual_review"— "no third party" detected, needs human check
    """
    text = description

    # Hard exclusions first
    if _matches_any(C2C_EXCLUSIONS, text):
        return False

    # Manual review trigger
    if _matches_any(MANUAL_REVIEW, text):
        return "manual_review"

    # Confirmed C2C
    if _matches_any(C2C_POSITIVE, text):
        return True

    # No C2C signal found at all — exclude silently
    return "excluded"
