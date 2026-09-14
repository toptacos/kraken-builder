"""Marketing site: pages parse, required meta, local links exist, sitemap covers launch URLs."""
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "website"

REQUIRED = {
    "index.html",
    "docs.html",
    "beta.html",
    "register.html",
    "publish.html",
    "nyx.html",
    "courses.html",
    "tutorial-tentacles.html",
    "before.html",
    "languages.html",
    "pricing.html",
    "security.html",
    "docker.html",
    "brand.html",
    "saas.html",
}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta = []
        self.links = []
        self.lang_ok = False

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "html" and ad.get("lang"):
            self.lang_ok = True
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            self.meta.append(ad)
        if tag == "a" and "href" in ad:
            self.links.append(ad["href"])
        if tag == "link" and ad.get("rel") == "canonical":
            self.links.append(ad.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def test_required_pages_exist():
    missing = [n for n in REQUIRED if not (SITE / n).exists()]
    assert missing == []


def test_pages_have_title_lang_viewport():
    for name in REQUIRED:
        raw = (SITE / name).read_text(encoding="utf-8", errors="replace")
        p = Page()
        p.feed(raw)
        assert p.lang_ok, name
        assert p.title.strip(), name
        viewport = any(m.get("name") == "viewport" for m in p.meta)
        assert viewport, name


def test_index_seo_basics():
    raw = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'meta name="description"' in raw
    assert "og:title" in raw
    assert "application/ld+json" in raw
    assert "pricing.html" in raw or 'id="pricing"' in raw


def test_local_links_resolve():
    broken = []
    for html in SITE.glob("*.html"):
        p = Page()
        p.feed(html.read_text(encoding="utf-8", errors="replace"))
        for href in p.links:
            if not href or href.startswith(("http", "mailto:", "#", "{")):
                continue
            path = href.split("#")[0].split("?")[0]
            if not path or path.startswith("../docs"):
                continue
            target = (SITE / path).resolve()
            if not target.exists():
                broken.append(f"{html.name} -> {href}")
    assert broken == [], broken


def test_sitemap_and_robots():
    sm = (SITE / "sitemap.xml").read_text()
    robots = (SITE / "robots.txt").read_text()
    assert "Sitemap:" in robots
    for slug in ("/", "docs.html", "publish.html", "languages.html", "pricing.html", "tutorial-tentacles.html"):
        assert slug in sm


def test_catalog_has_free_and_premium():
    import json
    data = json.loads((SITE / "catalog.json").read_text())
    names = {t["name"] for t in data["tentacles"]}
    assert "geo" in names and "weather-pro" in names
    assert "docker-env" in names
    licenses = {t["license"] for t in data["tentacles"]}
    assert "free" in licenses and "premium" in licenses
