"""arXiv: search research papers and read abstracts. No key. API: https://export.arxiv.org/api/query
(arXiv asks for at most one request every 3 seconds)."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from mcp.server.fastmcp import FastMCP

from _common import fetch, out

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
mcp = FastMCP("arxiv")


def parse(xml: bytes, abstract_chars: int) -> list[dict]:
    rows = []
    for e in ET.fromstring(xml).findall("a:entry", NS):
        text = lambda tag: " ".join((e.findtext(f"a:{tag}", "", NS) or "").split())  # noqa: E731
        rows.append({"id": text("id").rsplit("/abs/", 1)[-1], "title": text("title"),
                     "authors": [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)][:8],
                     "published": text("published")[:10], "updated": text("updated")[:10],
                     "abstract": text("summary")[:abstract_chars], "url": text("id")})
    return rows


@mcp.tool()
def search_papers(query: str, max_results: int = 5, sort_by: str = "relevance") -> str:
    """Search arXiv. query uses arXiv syntax, e.g. 'all:"conformal prediction" AND all:routing' or 'ti:misroute'.
    sort_by: relevance | submittedDate | lastUpdatedDate. Abstracts are cut to 400 characters."""
    xml = fetch(API, {"search_query": query, "max_results": min(max_results, 20), "sortBy": sort_by,
                      "sortOrder": "descending"})
    return out("arXiv API", parse(xml, 400))


@mcp.tool()
def get_paper(arxiv_id: str) -> str:
    """Title, authors, dates and the full abstract for one paper, e.g. '2503.13657'. Does not fetch the PDF."""
    rows = parse(fetch(API, {"id_list": arxiv_id}), 5000)
    return out("arXiv API", rows[0] if rows else {"error": f"no paper {arxiv_id}"})


if __name__ == "__main__":
    mcp.run()
