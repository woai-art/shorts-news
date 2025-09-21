import os
import yaml
from typing import Any, Dict

_PROMPTS_CACHE: Dict[str, Any] = {}


def load_prompts() -> Dict[str, Any]:
    global _PROMPTS_CACHE
    if _PROMPTS_CACHE:
        return _PROMPTS_CACHE

    # Support absolute and relative paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config', 'prompts.yaml')

    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        _PROMPTS_CACHE = yaml.safe_load(f) or {}
    return _PROMPTS_CACHE


def format_prompt(template: str, **kwargs) -> str:
    if not template:
        return ''
    return template.format(**kwargs)
