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


def parse_glossary_csv(content: str) -> List[Dict[str, Any]]:
    """
    Parse a glossary & banned-terms CSV file into structured dictionaries.
    """
    reader = csv.DictReader(io.StringIO(content))
    terms: List[Dict[str, Any]] = []

    for row in reader:
        normalized_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v}
        term = normalized_row.get("term")
        if not term:
            continue

        is_banned_val = normalized_row.get("is_banned", "false").lower()
        is_banned = is_banned_val in ["true", "1", "yes", "y"]

        case_sens_val = normalized_row.get("case_sensitive", "false").lower()
        case_sensitive = case_sens_val in ["true", "1", "yes", "y"]

        terms.append({
            "term": term,
            "is_banned": is_banned,
            "preferred_term": normalized_row.get("preferred_term"),
            "definition_or_rule": normalized_row.get("definition_or_rule", "Glossary term definition"),
            "case_sensitive": case_sensitive,
        })

    return terms
