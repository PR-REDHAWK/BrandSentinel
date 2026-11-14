import csv
import io
from typing import Any, Dict, List


def parse_approved_facts_csv(content: str) -> List[Dict[str, Any]]:
    """
    Parse an approved-facts CSV file into structured dictionaries.
    Supports standard and flexible column names.
    """
    reader = csv.DictReader(io.StringIO(content))
    facts: List[Dict[str, Any]] = []

    # Map possible column name variations to standard keys
    column_mappings = {
        "category": ["category", "cat", "topic", "domain"],
        "claim_pattern": ["claim_pattern", "claim", "claim pattern", "subject", "governed claim"],
        "approved_truth": ["approved_truth", "truth", "fact", "approved fact", "approved statement"],
        "mandatory_caveat": ["mandatory_caveat", "caveat", "disclaimer", "condition", "note"],
        "source_citation": ["source_citation", "source", "citation", "reference", "doc reference"],
        "effective_from": ["effective_from", "effective", "start_date", "valid_from"],
        "expires_at": ["expires_at", "expiry", "end_date", "valid_until"],
    }

    for row in reader:
        # Normalize keys in row to lowercase stripped
        normalized_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v}
        fact: Dict[str, Any] = {}

        for target_key, aliases in column_mappings.items():
            for alias in aliases:
                if alias in normalized_row:
                    fact[target_key] = normalized_row[alias]
                    break

        # Mandatory fields
        if "approved_truth" in fact and "source_citation" in fact:
            fact.setdefault("category", "General")
            fact.setdefault("claim_pattern", fact["approved_truth"])
            facts.append(fact)

    return facts
