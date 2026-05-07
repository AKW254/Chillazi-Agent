import os
from types import SimpleNamespace
from typing import Any

from jinja2 import Environment, FileSystemLoader


def _to_template_value(value: Any) -> Any:
    """Convert nested dict payloads into attribute-friendly objects for Jinja."""
    if isinstance(value, dict):
        return SimpleNamespace(
            **{key: _to_template_value(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return [_to_template_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_template_value(item) for item in value)
    return value


class TemplateRenderer:
    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_path))

    def render_template(self, template_name, context):
        template = self.env.get_template(template_name)
        normalized_context = {
            key: _to_template_value(value) for key, value in context.items()
        }
        return template.render(**normalized_context)
