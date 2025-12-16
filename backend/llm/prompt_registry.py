from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import os

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except Exception:  # noqa: BLE001
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore
    select_autoescape = None  # type: ignore


class PromptRegistry:
    """
    Loads prompt templates from backend/llm/prompt_templates and performs
    simple {{var}} replacements.
    """

    PROMPT_DIR = Path(__file__).resolve().parent / "prompt_templates"
    _jinja_env = None

    @classmethod
    def _load_template(cls, template_name: str) -> Optional[str]:
        path = cls.PROMPT_DIR / template_name
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    @classmethod
    def _get_env(cls):
        if Environment is None:
            return None
        if cls._jinja_env is None:
            cls._jinja_env = Environment(
                loader=FileSystemLoader(str(cls.PROMPT_DIR)),
                autoescape=select_autoescape(enabled_extensions=(".j2",)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return cls._jinja_env

    @staticmethod
    def _fallback_render(content: str, values: Dict[str, Any]) -> str:
        # Minimal replacement if Jinja2 isn't available
        rendered = content
        for k, v in values.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

    @classmethod
    def get_system_prompt(cls, template_name: str = "player_system.j2", **kwargs) -> Optional[str]:
        # Prefer Jinja2 templates by name if available
        env = cls._get_env()
        if env is not None:
            try:
                template = env.get_template(template_name)
                return template.render(**kwargs)
            except Exception:
                pass
        # Fallback to raw file load + simple replacement
        content = cls._load_template(template_name)
        if content is None:
            return None
        return cls._fallback_render(content, kwargs)

    @classmethod
    def get_turn_prompt(cls, template_name: str = "player_turn.j2", **kwargs) -> Optional[str]:
        env = cls._get_env()
        if env is not None:
            try:
                template = env.get_template(template_name)
                return template.render(**kwargs)
            except Exception:
                pass
        content = cls._load_template(template_name)
        if content is None:
            return None
        return cls._fallback_render(content, kwargs)

    @classmethod
    def enabled(cls) -> bool:
        # Allow toggle via env var or presence of templates dir
        if os.environ.get("LT_PROMPTS_TEMPLATES", "").lower() in {"1", "true", "yes"}:
            return True
        return cls.PROMPT_DIR.exists()
