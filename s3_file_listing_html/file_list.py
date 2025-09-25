"""Module for rendering HTML file listings and copying static files."""

from datetime import UTC, datetime
from pathlib import Path

from .constants import TEMPLATE_ENV


def render_file_list(file_list: list[str], base_url: str, output_path: Path) -> None:
    """Render the HTML file list and save it to the output path."""
    base_url = base_url.removesuffix("/")

    template = TEMPLATE_ENV.get_template("filelist.html.j2")
    rendered = template.render(
        file_list=file_list, base_url=base_url, last_generated_date=int(datetime.now(tz=UTC).timestamp())
    )

    output_path = output_path / "filelist.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(rendered)
