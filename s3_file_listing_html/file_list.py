from .constants import EXPECTED_ENV_VARS, OPTIONAL_ENV_VARS, STATIC_PATH, TEMPLATES_PATH
import jinja2
import shutil
from pathlib import Path


def render_html(file_list: list[str], base_url: str, output_path: Path) -> None:
    base_url = base_url.removesuffix("/")
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=TEMPLATES_PATH), autoescape=True)

    template = template_env.get_template("filelist.html.j2")
    rendered = template.render(file_list=file_list, base_url=base_url)

    output_path = output_path / "filelist.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(rendered)


def copy_static_files(output_path: Path) -> None:
    if STATIC_PATH.exists():
        shutil.copytree(STATIC_PATH, output_path / "static", dirs_exist_ok=True)
