import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    Path("index.html"),
    Path("zh/index.html"),
    Path("projects/index.html"),
    Path("zh/projects/index.html"),
)
LANGUAGE_PAIRS = (
    (Path("index.html"), Path("zh/index.html")),
    (Path("projects/index.html"), Path("zh/projects/index.html")),
)
RETIRED_PAGES = (
    Path("work/bosgogo/index.html"),
    Path("work/olympiad/index.html"),
    Path("work/china-trailhead/index.html"),
    Path("zh/work/bosgogo/index.html"),
    Path("zh/work/olympiad/index.html"),
    Path("zh/work/china-trailhead/index.html"),
)
REQUIRED_ASSETS = (
    Path("assets/styles.css"),
    Path("assets/favicon.svg"),
    Path("assets/og-card.svg"),
    Path("assets/lifestyle-brandeis.webp"),
    Path("assets/Xi_Yu_AI_Product_Manager_Resume_EN.pdf"),
)
FACT_ID = re.compile(r"\b(?:BGG|AIO|CTH|PAL|VIP|SOHU|EDU|COMM|RUN|VOL|SKILL)-\d+\b")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.meta = {}
        self.claims = set()
        self.lang = None
        self.title_depth = 0
        self.title = ""
        self.json_ld = 0
        self.has_icon = False
        self.photo_slots = 0
        self.community_entries = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append(tag)
        if tag == "html":
            self.lang = attributes.get("lang")
        if tag == "title":
            self.title_depth += 1
        if tag == "meta":
            key = attributes.get("name") or attributes.get("property")
            if key:
                self.meta[key] = attributes.get("content", "")
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self.json_ld += 1
        if tag == "link" and "icon" in attributes.get("rel", "").split():
            self.has_icon = True
        claim = attributes.get("data-claim")
        if claim:
            self.claims.add(claim)
        if "data-photo-slot" in attributes:
            self.photo_slots += 1
        if "data-community-entry" in attributes:
            self.community_entries += 1
        for attribute in ("href", "src"):
            if attributes.get(attribute):
                self.links.append((tag, attribute, attributes[attribute], attributes))

    def handle_endtag(self, tag):
        if tag == "title":
            self.title_depth -= 1

    def handle_data(self, data):
        if self.title_depth:
            self.title += data


def parse_page(relative_path):
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(source)
    return source, parser


class PortfolioContractTests(unittest.TestCase):
    def test_expected_public_files_exist(self):
        for relative_path in PAGES + REQUIRED_ASSETS:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_long_form_case_pages_are_retired(self):
        for relative_path in RETIRED_PAGES:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists(), relative_path)

    def test_pages_have_semantics_metadata_and_no_internal_fact_ids(self):
        for relative_path in PAGES:
            with self.subTest(path=relative_path):
                source, page = parse_page(relative_path)
                self.assertTrue(source.lstrip().lower().startswith("<!doctype html>"))
                self.assertIn(page.lang, {"en", "zh-CN"})
                self.assertEqual(page.tags.count("h1"), 1)
                self.assertIn("main", page.tags)
                self.assertIn("nav", page.tags)
                self.assertTrue(page.has_icon, "missing favicon link")
                self.assertGreater(len(page.title.strip()), 12)
                for key in (
                    "description",
                    "og:title",
                    "og:description",
                    "og:type",
                    "og:image",
                ):
                    self.assertTrue(page.meta.get(key), f"missing {key}")
                self.assertIsNone(FACT_ID.search(source))
                self.assertNotIn("fully autonomous", source.lower())
                self.assertNotIn("autonomous agent", source.lower())

    def test_home_pages_include_structured_person_data(self):
        for relative_path in (Path("index.html"), Path("zh/index.html")):
            with self.subTest(path=relative_path):
                _, page = parse_page(relative_path)
                self.assertEqual(page.json_ld, 1)
                self.assertEqual(page.photo_slots, 1)

    def test_home_pages_render_lifestyle_photo(self):
        for relative_path in (Path("index.html"), Path("zh/index.html")):
            with self.subTest(path=relative_path):
                source, page = parse_page(relative_path)
                photos = [
                    (url, attributes)
                    for tag, attribute, url, attributes in page.links
                    if tag == "img" and attribute == "src" and "data-photo-slot" in attributes
                ]
                self.assertEqual(len(photos), 1)
                self.assertEqual(photos[0][0], "assets/lifestyle-brandeis.webp" if relative_path.parent == Path(".") else "../assets/lifestyle-brandeis.webp")
                self.assertTrue(photos[0][1].get("alt"))
                self.assertNotIn("photo<br>to be added", source)
                self.assertNotIn("生活照片<br>待补充", source)

    def test_project_pages_link_directly_to_real_products(self):
        expected = {
            "https://www.bosgogo.com/",
            "https://www.bostonsitepilot.site/",
            "https://chinatrailhead.com/",
        }
        for relative_path in (Path("projects/index.html"), Path("zh/projects/index.html")):
            with self.subTest(path=relative_path):
                _, page = parse_page(relative_path)
                urls = {url for tag, _, url, _ in page.links if tag == "a"}
                self.assertTrue(expected.issubset(urls))

    def test_community_sections_use_resume_entries(self):
        for relative_path in (Path("index.html"), Path("zh/index.html")):
            with self.subTest(path=relative_path):
                source, page = parse_page(relative_path)
                self.assertEqual(page.community_entries, 4)
                self.assertEqual(
                    re.findall(r'data-community-entry="([^"]+)"', source),
                    ["mara", "civic", "reading", "running"],
                )
                self.assertEqual(source.count("2025–2026"), 2)
                self.assertEqual(source.count("2023–2024"), 2)

        english_source, _ = parse_page(Path("index.html"))
        self.assertIn("<h3>Volunteer</h3>", english_source)
        self.assertNotIn("<h3>Civic Volunteer</h3>", english_source)

    def test_internal_urls_are_relative_and_resolve(self):
        for relative_path in PAGES:
            _, page = parse_page(relative_path)
            for tag, attribute, raw_url, attributes in page.links:
                with self.subTest(page=relative_path, url=raw_url):
                    self.assertFalse(raw_url.startswith("/"), "root-relative URL breaks Pages subpaths")
                    parsed = urlsplit(raw_url)
                    if parsed.scheme in {"http", "https"}:
                        if tag == "a":
                            self.assertEqual(attributes.get("target"), "_blank")
                            self.assertIn("noopener", attributes.get("rel", ""))
                        continue
                    if parsed.scheme in {"mailto", "tel", "data"} or not parsed.path:
                        continue
                    target = relative_path.parent / unquote(parsed.path)
                    if raw_url.split("#", 1)[0].endswith("/"):
                        target /= "index.html"
                    self.assertTrue((ROOT / target).is_file(), f"missing local target {target}")

    def test_language_pairs_expose_the_same_claim_groups(self):
        for english, chinese in LANGUAGE_PAIRS:
            with self.subTest(english=english, chinese=chinese):
                _, en_page = parse_page(english)
                _, zh_page = parse_page(chinese)
                self.assertGreater(len(en_page.claims), 3)
                self.assertSetEqual(en_page.claims, zh_page.claims)

    def test_shared_css_covers_focus_motion_and_responsive_layout(self):
        css = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("box-shadow", css)
        self.assertNotIn("@keyframes", css)
        self.assertNotIn("project-grid", css)


if __name__ == "__main__":
    unittest.main()
