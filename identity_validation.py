from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from author_matching import normalize_name, short_openalex_id


ORCID_SEARCH_ENDPOINT = "https://pub.orcid.org/v3.0/expanded-search"


def short_orcid(value: str | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.rstrip("/").split("/")[-1]


def normalize_doi(value: str | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    doi = value.strip()
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("https://dx.doi.org/", "")
    doi = doi.replace("http://dx.doi.org/", "")
    return "https://doi.org/" + doi.lower()


def doi_cache_key(doi: str) -> str:
    normalized = normalize_doi(doi) or doi
    normalized = normalized.replace("https://doi.org/", "")
    return normalized.replace("/", "_").replace(":", "_")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, default=str, indent=2))


def orcid_cache_key(name: str) -> str:
    key = normalize_name(name).replace(" ", "_") or "_empty"
    return key + ".json"


def search_orcid_org(
    name: str,
    cache_dir: Path,
    allow_network: bool = False,
    sleep: float = 0.1,
    rows: int = 50,
) -> dict[str, Any]:
    path = cache_dir / orcid_cache_key(name)
    cached = read_json(path)
    if isinstance(cached, dict):
        return {**cached, "cache_path": str(path), "cache_hit": True}
    if isinstance(cached, list):
        return {
            "query_name": name,
            "candidate_orcids": cached,
            "status": "cached_legacy",
            "cache_path": str(path),
            "cache_hit": True,
        }

    if not allow_network:
        return {
            "query_name": name,
            "candidate_orcids": [],
            "status": "not_fetched_network_disabled",
            "cache_path": str(path),
            "cache_hit": False,
        }

    safe_name = name.replace('"', "").strip()
    params = {"q": f'"{safe_name}"', "rows": rows}
    headers = {"Accept": "application/json"}
    payload = {
        "query_name": name,
        "candidate_orcids": [],
        "status": "fetch_error",
    }

    try:
        response = requests.get(
            ORCID_SEARCH_ENDPOINT,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        payload["candidate_orcids"] = [
            short_orcid(hit.get("orcid-id"))
            for hit in data.get("expanded-result") or []
            if hit.get("orcid-id")
        ]
        payload["status"] = "fetched"
    except Exception as exc:
        payload["error"] = str(exc)

    write_json(path, payload)
    if sleep > 0:
        time.sleep(sleep)
    return {**payload, "cache_path": str(path), "cache_hit": False}


def extract_author_paper_urls_from_profile(html: str | None) -> list[str]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for block in soup.find_all("div", class_="contribution-year"):
        for anchor in block.find_all("a", href=True):
            text = anchor.get_text(strip=True)
            if not text.startswith("Author of"):
                continue
            url = anchor["href"]
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def paper_cache_key(paper_url: str) -> str:
    digest = hashlib.sha1(paper_url.encode("utf-8")).hexdigest()[:10]
    slug = paper_url.rstrip("/").split("/")[-1] or "paper"
    slug = re.sub(r"[^A-Za-z0-9_-]", "_", slug)[:60]
    return f"{slug}_{digest}.html"


def read_profile_html(profile_dir: Path, researchr_id: str) -> str | None:
    path = profile_dir / f"{researchr_id}.html"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def fetch_researchr_paper_html(
    paper_url: str,
    cache_dir: Path,
    allow_network: bool = False,
    sleep: float = 0.2,
) -> tuple[str | None, str, Path]:
    path = cache_dir / paper_cache_key(paper_url)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace"), "cached", path

    if not allow_network:
        return None, "not_fetched_network_disabled", path

    html = None
    status = "fetch_error"
    try:
        response = requests.get(paper_url, timeout=30)
        response.raise_for_status()
        html = response.text
        status = "fetched"
    except Exception as exc:
        html = f"<!-- fetch_error: {exc} -->"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html or "", encoding="utf-8")
    if sleep > 0 and status == "fetched":
        time.sleep(sleep)
    return html if status == "fetched" else None, status, path


def parse_researchr_paper_doi(html: str | None) -> str | None:
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "doi.org" in href:
            return normalize_doi(href)
    return None


def fetch_openalex_work_by_doi(
    doi: str,
    cache_dir: Path,
    allow_network: bool = False,
    api_key: str | None = None,
    sleep: float = 0.05,
) -> tuple[dict[str, Any] | None, str, Path]:
    normalized = normalize_doi(doi)
    if not normalized:
        return None, "no_doi", cache_dir / "missing.json"

    path = cache_dir / f"{doi_cache_key(normalized)}.json"
    cached = read_json(path)
    if isinstance(cached, dict):
        if cached.get("error"):
            return None, "cached_fetch_error", path
        if not cached.get("id"):
            return None, "cached_not_found", path
        return cached, "cached", path
    if path.exists():
        return None, "cached_not_found", path

    if not allow_network:
        return None, "not_fetched_network_disabled", path

    params = {}
    if api_key:
        params["api_key"] = api_key

    status = "fetch_error"
    data = None
    try:
        response = requests.get(
            "https://api.openalex.org/works/" + normalized,
            params=params,
            timeout=30,
        )
        if response.status_code == 404:
            status = "not_found"
        else:
            response.raise_for_status()
            data = response.json()
            status = "fetched"
    except Exception as exc:
        data = {"error": str(exc)}

    write_json(path, data or {})
    if sleep > 0 and status == "fetched":
        time.sleep(sleep)
    return data if status == "fetched" else None, status, path


def extract_work_authors(work: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    if not isinstance(work, dict):
        return rows

    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        rows.append(
            {
                "author_id": short_openalex_id(author.get("id")),
                "author_name": author.get("display_name"),
                "orcid": short_orcid(author.get("orcid") or authorship.get("raw_orcid")),
                "author_position": authorship.get("author_position")
                or authorship.get("position"),
            }
        )
    return rows
