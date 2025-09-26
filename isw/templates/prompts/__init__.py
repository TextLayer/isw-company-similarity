from jinja2 import Template

from isw.core.errors import NotFoundException


def load_prompt(name: str, **kwargs) -> str:
    try:
        return Template(open(f"textlayer/templates/prompts/{name}.md").read()).render(**kwargs)
    except Exception as e:
        raise NotFoundException(f"Prompt {name} not found") from e


__all__ = ["load_prompt"]
