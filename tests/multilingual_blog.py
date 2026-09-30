"""Integration checks using isolated content fixtures; requires Hugo."""
import json
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs))

    def entries(self):
        return [link["href"] for link in self.links if link.get("class") == "entry-link"]

    def switch(self, language):
        return next(link for link in self.links
                    if link.get("hreflang") == language and "?lang=" in link.get("href", ""))


def build(source):
    subprocess.run(["hugo", "--source", str(source), "--minify"],
                   check=True, capture_output=True, text=True)


def post(source, filename, title, tag, translation_key=None):
    key = f'translationKey: "{translation_key}"\n' if translation_key else ""
    (source / "content/posts" / filename).write_text(
        f'---\ntitle: "{title}"\ndate: 2025-01-01\ntags: [{tag}]\n{key}---\n\n{title}\n')


with tempfile.TemporaryDirectory(prefix="akorba-blog-test-") as directory:
    source = Path(directory)
    shutil.copy2(PROJECT / "hugo.yaml", source / "hugo.yaml")
    shutil.copytree(PROJECT / "content", source / "content")
    for name in ["themes", "layouts", "assets", "data", "static"]:
        (source / name).symlink_to(PROJECT / name, target_is_directory=True)
    build(source)
    public = source / "public"
    assert "No English articles yet" not in (public / "en/posts/index.html").read_text()
    english_index = json.loads((public / "en/index.json").read_text())
    polish_index = json.loads((public / "index.json").read_text())
    for slug in ["mamba", "meta_weighting"]:
        url = f"https://akorba.pl/en/posts/{slug}/"
        assert url in Page(public / "en/posts/index.html").entries()
        assert any(item["permalink"] == url for item in english_index)
        assert not any(f"/posts/{slug}/" in item["permalink"] for item in polish_index)
        redirect = (public / "posts" / slug / "index.html").read_text()
        assert "http-equiv=refresh" in redirect and url in redirect
        assert f"/en/posts/{slug}/" in (public / "en/posts/index.xml").read_text()
        assert f"/posts/{slug}/" not in (public / "posts/index.xml").read_text()
    for slug in ["etf", "homelab", "rpm_python"]:
        assert not (public / "en/posts" / slug).exists()
        assert not (public / "posts" / slug).exists()
    assert (public / "posts/array_python/index.html").exists()
    assert (public / "posts/page/2/index.html").exists()
    link = Page(public / "posts/array_python/index.html").switch("en")
    assert link["href"] == "/en/posts/?lang=en"
    assert "brak tłumaczenia" in link["title"]

    post(source, "language-test-pl.pl.md", "Polish only fixture", "fixture-pl")
    post(source, "language-test-en.en.md", "English only fixture", "fixture-en")
    post(source, "language-test-pair.md", "Polish paired fixture", "fixture-pl")
    post(source, "language-test-pair.en.md", "English paired fixture", "fixture-en")
    post(source, "language-test-key.md", "Polish key fixture", "fixture-pl", "test-key")
    post(source, "language-test-other.en.md", "English key fixture", "fixture-en", "test-key")
    build(source)

    assert "No English articles yet" not in (public / "en/posts/index.html").read_text()
    for language, prefix, other in [("pl", "", "/en/posts/"), ("en", "en/", None)]:
        blog = Page(public / prefix / "posts/index.html")
        entries = blog.entries()
        assert entries
        if language == "en":
            assert all("/en/posts/" in url for url in entries)
        else:
            assert all(other not in url for url in entries)
        index = json.loads((public / prefix / "index.json").read_text())
        titles = {item["title"] for item in index}
        assert ("English only fixture" in titles) == (language == "en")
        assert ("Polish only fixture" in titles) == (language == "pl")
        assert ("English paired fixture" in titles) == (language == "en")
        assert ("Polish paired fixture" in titles) == (language == "pl")
        search = (public / prefix / "search/index.html").read_text()
        assert "../index.json" in search
        assert (public / prefix / "tags" / f"fixture-{language}" / "index.html").exists()
        wrong_tag = "fixture-pl" if language == "en" else "fixture-en"
        assert not (public / prefix / "tags" / wrong_tag).exists()
        rss = (public / prefix / "posts/index.xml").read_text()
        assert ("English only fixture" in rss) == (language == "en")
        assert ("Polish only fixture" in rss) == (language == "pl")

    assert not (public / "en/posts/language-test-pl").exists()
    assert not (public / "posts/language-test-en").exists()
    for route, language, target in [
        ("posts/language-test-pair", "en", "/en/posts/language-test-pair/"),
        ("en/posts/language-test-pair", "pl", "/posts/language-test-pair/"),
        ("posts/language-test-key", "en", "/en/posts/language-test-other/"),
        ("en/posts/language-test-other", "pl", "/posts/language-test-key/"),
        ("en/posts/language-test-en", "pl", "/posts/"),
        ("posts/language-test-pl", "en", "/en/posts/"),
        ("search", "en", "/en/search/"),
        ("en/search", "pl", "/search/"),
    ]:
        link = Page(public / route / "index.html").switch(language)
        assert link["href"] == target + "?lang=" + language, (route, link)

    # Exercise the empty state without changing the repository's actual posts.
    for article in (source / "content/posts").glob("*.en.md"):
        if not article.name.startswith("_index"):
            article.unlink()
    shutil.rmtree(public)
    build(source)
    assert "No English articles yet" in (public / "en/posts/index.html").read_text()

print("PASS: language-only lists, search, tags, RSS, translation links, redirects, draft visibility and empty state")
