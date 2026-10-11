"""The marketing site is a test surface: links, taxonomy, sitemap.

These tests import scripts/verify_site.py rather than reimplementing it, so
"what the manual script checks" and "what CI checks" are the same code. They
run on Linux, macOS, and Windows because they are file and JSON checks with
no network and no shell.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_site  # noqa: E402


def test_site_pages_are_clean():
    assert verify_site.problems() == []


def test_taxonomy_registry_declares_the_kraken_project():
    registry = verify_site.load_registry()
    projects = registry["taxonomies"]["project"]
    slugs = [t["slug"] for t in projects["terms"]]
    assert "kraken" in slugs
    for term in projects["terms"]:
        assert term["name"]
        assert term["description"]


def test_new_pages_are_tagged_and_in_the_sitemap():
    sitemap = (verify_site.SITE / "sitemap.xml").read_text()
    for page in ("compare.html", "blog-why-kraken.html"):
        text = (verify_site.SITE / page).read_text()
        assert 'content="project:kraken"' in text
        assert 'data-taxonomy="project:kraken"' in text
        assert f"https://kraken.topta.co/{page}" in sitemap


def test_compare_and_blog_pages_link_each_other():
    compare = (verify_site.SITE / "compare.html").read_text()
    blog = (verify_site.SITE / "blog-why-kraken.html").read_text()
    assert 'href="blog-why-kraken.html"' in compare
    assert 'href="compare.html"' in blog


def test_verifier_catches_a_broken_link(tmp_path):
    """The check has teeth. Also the regression test for the two broken
    references (logo-k-transparent-128.png, img/nyx-avatar.jpg) that shipped
    on the site before this verifier existed."""
    page = verify_site.SITE / "zz-link-check-probe.html"
    page.write_text(
        "<!doctype html><html><body>"
        '<a href="does-not-exist.html">broken</a>'
        '<a href="./">root</a>'
        "</body></html>"
    )
    try:
        found = verify_site.problems()
        assert any("does-not-exist.html" in p for p in found)
    finally:
        page.unlink()
    assert verify_site.problems() == []


def test_verifier_rejects_an_unregistered_taxonomy_term():
    page = verify_site.SITE / "zz-taxonomy-probe.html"
    page.write_text(
        '<!doctype html><html><head><meta name="taxonomy" content="project:nope">'
        '</head><body data-taxonomy="project:nope"></body></html>'
    )
    try:
        found = verify_site.problems()
        assert any("unregistered term" in p for p in found)
    finally:
        page.unlink()
