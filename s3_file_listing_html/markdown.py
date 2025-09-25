"""Module to render markdown files to HTML."""

import re
from pathlib import Path
import bs4

import markdown
from markdown.extensions.tables import TableExtension
from .constants import TEMPLATE_ENV

FIND_MARKDOWN_TITLE = [
    re.compile(r"^# (.+)$", re.MULTILINE),
    re.compile(r"^(.+)\n===+$", re.MULTILINE),
]

TITLE_CLEANUP = re.compile(r"[^a-zA-Z0-9 _-]+")


def render_markdown_files(markdown_path: Path, output_path: Path) -> None:
    """Render markdown files from the markdown_path to HTML files in the output_path."""
    if not markdown_path.exists() or not markdown_path.is_dir():
        return

    for md_file in markdown_path.glob("*.md"):
        with md_file.open("r", encoding="utf-8") as f:
            text = f.read()

        title = md_file.stem
        for pattern in FIND_MARKDOWN_TITLE:
            match = pattern.search(text)
            if match:
                title = match.group(1).strip()
                break

        title = TITLE_CLEANUP.sub("", title).strip()

        html = markdown.markdown(text, extensions=[TableExtension()])

        template = TEMPLATE_ENV.get_template("md.html.j2")
        rendered = template.render(content=html, title=title)

        soup = bs4.BeautifulSoup(rendered, "html.parser")
        rendered = soup.prettify()

        output_file = output_path / (md_file.stem + ".html")
        with output_file.open("w", encoding="utf-8") as f:
            f.write(rendered)
