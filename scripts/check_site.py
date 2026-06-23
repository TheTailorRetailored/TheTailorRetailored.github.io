"""Small, dependency-free checks for the static site."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self.images: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if element_id := values.get("id"):
            if element_id in self.ids:
                raise ValueError(f"duplicate id: {element_id}")
            self.ids.add(element_id)
        if tag == "a" and values.get("href"):
            self.links.append((tag, values["href"]))
        if tag == "link" and values.get("href"):
            self.links.append((tag, values["href"]))
        if tag == "img" and values.get("src"):
            self.images.append((values["src"], values.get("alt")))


def local_path(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme or url.startswith("//") or url.startswith("#") or url.startswith("mailto:"):
        return None
    return ROOT / parsed.path.lstrip("/")


def check_page(path: Path) -> list[str]:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for tag, target in parser.links:
        destination = local_path(target)
        if destination and not destination.exists():
            errors.append(f"{path.name}: missing {tag} target {target}")
    for source, alt in parser.images:
        destination = local_path(source)
        if destination and not destination.exists():
            errors.append(f"{path.name}: missing image {source}")
        if not alt:
            errors.append(f"{path.name}: image {source} needs alt text")
    return errors


def main() -> None:
    errors: list[str] = []
    for page in ROOT.glob("*.html"):
        errors.extend(check_page(page))
    for expected in ("styles.css", "robots.txt", "sitemap.xml", "assets/favicon.svg"):
        if not (ROOT / expected).exists():
            errors.append(f"missing required file: {expected}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Static site checks passed.")


if __name__ == "__main__":
    main()
