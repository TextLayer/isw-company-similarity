from jinja2 import Template

from isw.core.errors import NotFoundException


def load_html(name: str, **kwargs) -> str:
    try:
        return Template(open(f"textlayer/templates/html/{name}.html").read()).render(**kwargs)
    except Exception as e:
        raise NotFoundException(f"HTML template {name} not found") from e


__all__ = ["load_html"]
