#!/usr/bin/env python3
"""Fetch a small, auditable candidate list from the arXiv Atom API."""
import argparse
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

NS = {"a": "http://www.w3.org/2005/Atom"}


def search(query: str, limit: int):
    params = {
        "search_query": query if ":" in query else f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        root = ET.fromstring(response.read())
    papers = []
    for entry in root.findall("a:entry", NS):
        arxiv_url = entry.findtext("a:id", namespaces=NS)
        papers.append(
            {
                "title": " ".join((entry.findtext("a:title", namespaces=NS) or "").split()),
                "arxiv_url": arxiv_url,
                "published": entry.findtext("a:published", namespaces=NS),
                "authors": [
                    a.findtext("a:name", namespaces=NS)
                    for a in entry.findall("a:author", NS)
                ],
                "summary": " ".join((entry.findtext("a:summary", namespaces=NS) or "").split()),
            }
        )
    return papers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="sources/arxiv-candidates.json")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    queries = [
        "all:tactile AND all:VLA",
        "all:tactile AND all:language AND all:action",
        "all:visuo-tactile AND all:manipulation",
    ]
    results = []
    seen = set()
    errors = []
    for query in queries:
        try:
            found = search(query, args.limit)
        except Exception as exc:
            errors.append(f"{query}: {exc}")
            continue
        for paper in found:
            key = paper["arxiv_url"]
            if key not in seen:
                seen.add(key)
                paper["query"] = query
                results.append(paper)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "arXiv Atom API",
        "verification": "candidate metadata only; human review required",
        "papers": results,
        "warning": (
            ("No results returned; check arXiv availability and query syntax. " if not results else "")
            + ("; ".join(errors) if errors else "")
        ) or None,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
