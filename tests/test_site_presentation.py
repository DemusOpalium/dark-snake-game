"""Contract checks for the standalone Pages presentation (stdlib only)."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.anchors = []
        self.images = []
        self.attributes = []
        self.lang_buttons = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            assert a["id"] not in self.ids, f"Duplicate anchor {a['id']}"
            self.ids.add(a["id"])
        if tag == "a":
            self.anchors.append(a)
        if tag == "img":
            self.images.append(a)
        if tag == "button" and "data-language" in a:
            self.lang_buttons.append(a["data-language"])
        self.attributes.append((tag, a))


def test_pages_contract_and_links():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    assert 'lang="de"' in html
    assert parser.lang_buttons == ["de", "en"]
    assert "class=\"de\"" in html and "class=\"en\"" in html
    assert len(parser.images) >= 10
    for a in parser.anchors:
        href = a["href"]
        assert href.startswith(("https://github.com/DemusOpalium/dark-snake-game", "#"))
        if href.startswith("#"):
            assert href[1:] in parser.ids
    for img in parser.images:
        assert img.get("alt") is not None
        if img["alt"] != "":
            assert img.get("data-alt-de") and img.get("data-alt-en")
        src = img["src"]
        assert not src.startswith(("http://", "https://"))
        assert (SITE / src).is_file(), src
        if src not in ("media/boss-fight.png", "media/boss-medusa.png",
                       "media/boss-hunter.png", "media/boss-guardian.png"):
            assert img.get("loading") == "lazy", src
    for asset in ("styles.css", "main.js", "favicon.svg", "asset-manifest.json"):
        assert (SITE / asset).is_file(), asset
    assert len(html.encode("utf-8")) < 27000
    assert (SITE / "main.js").stat().st_size < 3500
    ET.parse(SITE / "favicon.svg")


def test_all_web_media_are_tracked_and_pngs():
    manifest = json.loads((SITE / "asset-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == 1
    assert len(manifest["media"]) >= 10
    for media in manifest["media"]:
        p = SITE / media["website"]
        assert p.is_file()
        assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", str(p)
        assert p.stat().st_size == media["bytes"]
        assert media["source"].startswith(("GamePICs/", "Dark_Snake/assets/graphics/"))
