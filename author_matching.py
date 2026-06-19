from __future__ import annotations

from collections import Counter
from typing import Iterable
import unicodedata

import pandas as pd


FOLD_MAP = str.maketrans(
    {
        "ø": "o",
        "Ø": "O",
        "æ": "ae",
        "Æ": "AE",
        "œ": "oe",
        "Œ": "OE",
        "ß": "ss",
        "ł": "l",
        "Ł": "L",
        "đ": "d",
        "Đ": "D",
        "þ": "th",
        "Þ": "Th",
        "ð": "d",
        "Ð": "D",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
    }
)


def normalize_name(name: str | None) -> str:
    if not name:
        return ""

    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.translate(FOLD_MAP)
    text = text.replace(".", " ")
    return " ".join(text.lower().split())


def short_openalex_id(value: str | None) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.rstrip("/").split("/")[-1]


def mode_or_none(values: Iterable[str | None]) -> str | None:
    clean_values = [value for value in values if isinstance(value, str) and value]
    if not clean_values:
        return None
    counter = Counter(clean_values)
    top_value, top_count = counter.most_common(1)[0]
    if list(counter.values()).count(top_count) > 1:
        return None
    return top_value


def confidence_from_candidates(
    n_candidate_ids: int,
    n_candidate_orcids: int,
    top_id_share: float | None,
    n_evidence: int | None = None,
) -> tuple[str, bool]:
    if n_candidate_ids == 0:
        return "unmatched", True

    share = 0.0 if top_id_share is None else float(top_id_share)
    evidence = 0 if n_evidence is None else int(n_evidence)

    if evidence < 3 and n_candidate_orcids == 0:
        return "medium", True

    if n_candidate_ids == 1 and n_candidate_orcids <= 1:
        return "high", False

    if share >= 0.8 and n_candidate_orcids <= 1:
        return "medium", False

    if share >= 0.8:
        return "medium", True

    return "low", True


def build_pc_people(pc_members: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for researcher_id, group in pc_members.groupby("canonical_researchr_id"):
        observed_names = [str(name) for name in group["name"].dropna() if str(name)]
        names = sorted(set(observed_names))
        normalized_names = sorted({normalize_name(name) for name in names if normalize_name(name)})
        display_name = mode_or_none(observed_names) or (names[0] if names else researcher_id)

        rows.append(
            {
                "canonical_researchr_id": researcher_id,
                "name": display_name,
                "name_variants": names,
                "normalized_names": normalized_names,
                "n_pc_rows": len(group),
                "n_conferences": group["conference"].nunique(),
                "first_observed_pc_year": int(group["year"].min()),
                "last_observed_pc_year": int(group["year"].max()),
            }
        )

    return pd.DataFrame(rows).sort_values("canonical_researchr_id").reset_index(drop=True)


def build_reference_author_index(ref_authors: pd.DataFrame) -> pd.DataFrame:
    ref = ref_authors.copy()
    ref["ref_author_id"] = ref["ref_author_id"].map(short_openalex_id)
    ref["ref_norm"] = ref["ref_author_name"].map(normalize_name)
    ref = ref[(ref["ref_norm"] != "") & ref["ref_author_id"].notna()].copy()

    grouped = (
        ref.groupby(["ref_norm", "ref_author_id"], dropna=False)
        .agg(
            n_evidence=("ref_author_id", "size"),
            ref_author_names=("ref_author_name", lambda x: sorted(set(x.dropna().astype(str)))),
            orcids=("ref_orcid", lambda x: sorted(set(x.dropna().astype(str)))),
            citing_papers=("work_id", "nunique"),
            cited_works=("referenced_work_id", "nunique"),
        )
        .reset_index()
    )

    return grouped.sort_values(["ref_norm", "n_evidence"], ascending=[True, False])


def candidate_rows_for_person(
    person: pd.Series,
    reference_author_index: pd.DataFrame,
) -> list[dict]:
    normalized_names = person["normalized_names"] or []
    candidates = reference_author_index[
        reference_author_index["ref_norm"].isin(normalized_names)
    ].copy()

    if candidates.empty:
        return []

    total_evidence = int(candidates["n_evidence"].sum())
    rows = []

    for _, candidate in candidates.iterrows():
        rows.append(
            {
                "canonical_researchr_id": person["canonical_researchr_id"],
                "name": person["name"],
                "matched_normalized_name": candidate["ref_norm"],
                "candidate_openalex_id": candidate["ref_author_id"],
                "candidate_n_evidence": int(candidate["n_evidence"]),
                "candidate_share": (
                    float(candidate["n_evidence"]) / total_evidence
                    if total_evidence
                    else 0.0
                ),
                "candidate_orcids": candidate["orcids"],
                "candidate_ref_author_names": candidate["ref_author_names"],
                "candidate_citing_papers": int(candidate["citing_papers"]),
                "candidate_cited_works": int(candidate["cited_works"]),
            }
        )

    return rows
