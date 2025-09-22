#!/usr/bin/env python3
"""
Модуль обработки новостей через LLM для создания контента шортсов
Поддерживает различные провайдеры: Gemini, OpenAI, Anthropic
Использует новый Google AI SDK genai с Google Search Grounding
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import yaml
from datetime import datetime

from scripts.llm_direct_provider import GeminiDirectProvider
from logger_config import logger
from scripts.llm_base import LLMProvider
from scripts.prompt_loader import load_prompts, format_prompt

# Оставляем только новый SDK
try:
    import google.generativeai as genai
    USE_NEW_SDK = True
    logger.info("Используется новый Google AI SDK (genai)")
except ImportError:
    USE_NEW_SDK = False
    logger.warning("Новый SDK google.genai не найден. Проверка фактов будет недоступна.")


class GeminiProvider(LLMProvider):
    """Provider for the Google Gemini API using the new SDK."""

    def __init__(self, api_key: str, model: str = "models/gemini-1.5-flash", config: Dict = None):
        self.api_key = api_key
        self.model_name = model
        self.config = config or {}
        self.client = None
        self._initialize_sdk(api_key)

    def _initialize_sdk(self, api_key: str):
        try:
            genai.configure(api_key=api_key)
            logger.info(f"Gemini API configured successfully.")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise

    def generate_video_package(self, news_data: Dict) -> Dict[str, Any]:
        """Generates a complete video data package using a single prompt via the SDK Client."""
        text = news_data.get('description', '') or news_data.get('title', '')
        source_name = news_data.get('source', 'Unknown')
        source_url = news_data.get('url', '')

        prompts = load_prompts()
        template = prompts.get('video_package', {}).get('generate', '')
        prompt = format_prompt(template, text=text, source_name=source_name, source_url=source_url)

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            # Use regex to find the JSON block
            import re
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                json_text = match.group(0)
                return json.loads(json_text)
            else:
                raise ValueError("No JSON object found in the response")
        except Exception as e:
            logger.error(f"Error generating video package via SDK Client: {e}")
            raise Exception(f"LLM API failed: {e}")


class LLMProcessor:
    """Основной класс для обработки новостей через LLM"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.provider = self._init_provider()
        # Validation/fact-guard rules from config (optional)
        self.validation_rules = (self.config.get('validation') or {}).get('rules', {})

    # ---------------------- FactGuard (lightweight) ----------------------
    def _fact_guard_normalize(self, text: str, published_iso: str = "") -> str:
        """Lightweight normalizer for official titles and common fact phrasing errors.

        Uses config-driven rules if provided. Falls back to safe defaults.
        This is NOT a hardcoded rewrite of content – only safe, unambiguous
        replacements for well-known roles as of a given effective date.
        """
        if not text:
            return text

        try:
            import re
            normalized = text

            # 1) Roles from config (preferred)
            # Format example in config:
            # validation:
            #   rules:
            #     roles:
            #       - role: "President of the United States"
            #         person: "Donald Trump"
            #         effective_from: "2025-01-20"
            roles = (self.validation_rules.get('roles') or [])

            def date_ok(effective_from: str) -> bool:
                if not effective_from:
                    return True
                try:
                    from datetime import datetime
                    pub = datetime.fromisoformat(published_iso.replace('Z', '+00:00')) if published_iso else datetime.now()
                    eff = datetime.fromisoformat(effective_from + 'T00:00:00+00:00') if 'T' not in effective_from else datetime.fromisoformat(effective_from)
                    return pub >= eff
                except Exception:
                    return True

            for r in roles:
                role = (r.get('role') or '').lower()
                person = r.get('person') or ''
                eff = r.get('effective_from') or ''
                if not role or not person:
                    continue
                if not date_ok(eff):
                    continue
                # Common mislabels like "former <role> <person>" -> "<role> <person>"
                patterns = [
                    rf"former\s+{re.escape(person)}",
                    rf"former\s+{re.escape(role)}\s+{re.escape(person)}",
                    rf"ex[- ]{re.escape(role)}\s+{re.escape(person)}",
                    rf"ex[- ]{re.escape(person)}",
                ]
                for p in patterns:
                    normalized = re.sub(p, person, normalized, flags=re.IGNORECASE)
                # Also handle "former U.S. President Trump" -> "U.S. President Trump"
                alt_role = role.replace('president of the united states', 'u.s. president')
                patterns_alt = [
                    rf"former\s+{re.escape(alt_role)}\s+{re.escape(person)}",
                ]
                for p in patterns_alt:
                    normalized = re.sub(p, f"{alt_role} {person}", normalized, flags=re.IGNORECASE)

            # 2) Safe default for widely-known current role (if no config):
            if not roles:
                # As of 2025-01-20, Donald Trump is U.S. President
                # Normalize "former ... Trump" -> "President Trump"
                patterns_default = [
                    r"former\s+(u\.?s\.?\s+)?president\s+trump",
                    r"ex[- ](u\.?s\.?\s+)?president\s+trump",
                ]
                for p in patterns_default:
                    normalized = re.sub(p, "President Trump", normalized, flags=re.IGNORECASE)

            return normalized
        except Exception:
            return text

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _init_provider(self) -> LLMProvider:
        """Инициализация LLM провайдера"""
        llm_config = self.config['llm']
        provider_name = llm_config['provider'].lower()

        if provider_name == 'gemini':
            api_key = os.getenv(llm_config['api_key_env'])
            if not api_key:
                raise ValueError(f"API ключ для {provider_name} не найден в переменных окружения")
            
            # Добавляем очистку ключа прямо здесь
            api_key = api_key.strip()
            masked_key = f"{api_key[:4]}...{api_key[-4:]}"
            logger.info(f"🔑 [DEBUG] Инициализация Gemini провайдера с ключом: {masked_key}")

            return GeminiProvider(api_key, llm_config['model'], llm_config)

        elif provider_name == 'openai':
            # Реализация для OpenAI будет добавлена позже
            raise NotImplementedError("OpenAI провайдер пока не реализован")

        elif provider_name == 'anthropic':
            # Реализация для Anthropic будет добавлена позже
            raise NotImplementedError("Anthropic провайдер пока не реализован")

        else:
            raise ValueError(f"Неподдерживаемый LLM провайдер: {provider_name}")

    def process_news_for_shorts(self, news_data: Dict) -> Dict[str, Any]:
        """Processes news to create a complete video package."""
        logger.info(f"Processing news item: {news_data.get('title', '')[:50]}...")

        try:
            # The provider is now expected to have a method that returns the complete package.
            if hasattr(self.provider, 'generate_video_package'):
                logger.info(f"Provider has generate_video_package method")
                video_package = self.provider.generate_video_package(news_data)
                logger.info(f"Generated video_package: {video_package}")
                logger.info(f"Successfully generated video package for news ID {news_data.get('id')}")
                return {
                    'status': 'success',
                    'video_package': video_package
                }
            else:
                # Fallback to legacy method if the new one is not implemented
                logger.warning("Provider does not have 'generate_video_package', falling back to legacy processing.")
                return self._process_news_legacy(news_data)

        except Exception as e:
            logger.error(f"Error processing news ID {news_data.get('id')}: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }

    def batch_process_news(self, news_list: List[Dict]) -> List[Dict]:
        """Пакетная обработка списка новостей"""
        results = []

        for news in news_list:
            result = self.process_news_for_shorts(news)
            results.append(result)

        logger.info(f"Обработано {len(results)} новостей")
        return results

def main():
    """Тестовая функция"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

    try:
        processor = LLMProcessor(config_path)

        # Тестовая новость
        test_news = {
            'id': 1,
            'title': 'Президент США объявил о новых санкциях против России',
            'description': 'Джо Байден заявил о введении дополнительных экономических ограничений в ответ на последние события на Украине.',
            'source': 'Reuters',
            'published': datetime.now().isoformat(),
            'category': 'Политика'
        }

        result = processor.process_news_for_shorts(test_news)

        print("Результат обработки:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Ошибка в тестовой функции: {e}")
        print(f"Убедитесь, что установлена переменная окружения {processor.config['llm']['api_key_env']}")

if __name__ == "__main__":
    main()
