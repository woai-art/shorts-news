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

# Оставляем только новый SDK
try:
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
    logger.info("Используется новый Google AI SDK (genai)")
except ImportError:
    USE_NEW_SDK = False
    logger.warning("Новый SDK google.genai не найден. Проверка фактов будет недоступна.")


class GeminiProvider(LLMProvider):
    """Провайдер для Google Gemini"""

    def __init__(self, api_key: str, model: str = "models/gemini-2.0-flash", config: Dict = None):
        self.api_key = api_key
        self.model_name = model
        self.config = config or {}
        self.direct_provider = None
        self.grounding_config = self.config.get('grounding', {})
        
        # Устанавливаем grounding_is_available для всех путей
        self.grounding_is_available = self.grounding_config.get('enable_fact_checking', False)
        
        # Устанавливаем force_direct_api для всех путей
        self.force_direct_api = self.config.get('force_direct_api', False)

        if self.force_direct_api:
            logger.info("⚡ Используется прямой API вызов (force_direct_api: true)")
            self.direct_provider = GeminiDirectProvider(api_key=self.api_key, model=self.model_name, config=self.config)
            if self.grounding_is_available:
                logger.info("✅ Google Search Grounding доступен (через прямой API)")
            else:
                logger.info("✅ Google Search Grounding отключен в конфигурации")
        else:
            # Инициализируем SDK
            self._initialize_sdk(api_key)
            self.model = self.model_name  # Для совместимости
            logger.info("✅ Gemini инициализирован с SDK")
            if self.grounding_is_available:
                 logger.info("✅ Google Search Grounding доступен")
            else:
                logger.info("✅ Google Search Grounding отключен в конфигурации")

    def _initialize_sdk(self, api_key: str):
        try:
            # Принудительно используем Google AI Studio вместо Vertex AI
            import os
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'False'
            logger.info("🔧 Установили GOOGLE_GENAI_USE_VERTEXAI=False для использования AI Studio")
            
            # Инициализируем клиент для Google AI Studio
            self.client = genai.Client(api_key=api_key)
            
            # Базовая конфигурация
            self.generation_config = types.GenerateContentConfig(
                temperature=self.config.get('temperature', 0.7),
                max_output_tokens=self.config.get('max_tokens', 2000),
            )
            
            # Конфигурация с Google Search Grounding
            if self.grounding_is_available:
                self.grounding_config = types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=self.config.get('grounding', {}).get('grounding_temperature', 0.3),
                )
                logger.info("✅ Google Search Grounding (проверка фактов) доступен через SDK.")
            else:
                self.grounding_config = None
        except Exception as e:
            logger.error(f"⚠️ Ошибка инициализации SDK genai: {e}. Переключаемся на прямой API.")
            self.force_direct_api = True
            self._initialize_direct_provider(self.api_key, self.model_name, self.config)

    def _initialize_direct_provider(self, api_key, model, config):
        """Инициализация прямого API провайдера"""
        try:
            self.direct_provider = GeminiDirectProvider(api_key, model, config)
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации прямого API: {e}")
            self.direct_provider = None

    def _verify_facts_with_search(self, news_text: str, context: str = "") -> Dict[str, Any]:
        """Проверка фактов через Google Search Grounding"""
        # Проверяем, включена ли проверка фактов
        if not self.grounding_is_available:
            logger.info("Проверка фактов отключена в конфигурации")
            return {
                'fact_check': {
                    'accuracy_score': 1.0,
                    'issues_found': [],
                    'corrections': [],
                    'verification_status': 'skipped'
                },
                'grounding_data': {'chunks': [], 'supports': []},
                'verification_sources': []
            }

        # Если нет поддержки grounding, используем базовую проверку
        if not self.force_direct_api and (not USE_NEW_SDK or not self.grounding_config):
            logger.info("Google Search Grounding недоступен, используем базовую проверку")
            return self._basic_fact_check(news_text, context)

        prompt = f"""
        Проверь факты в этой новости и убедись в их актуальности.
        Особое внимание обрати на:
        - Текущий статус политических фигур (президент, экспрезидент и т.д.)
        - Актуальность дат и событий
        - Корректность названий и терминов

        Новость: {news_text}

        {f"Контекст: {context}" if context else ""}

        Верни анализ в формате JSON:
        {{
            "fact_check": {{
                "accuracy_score": 0.0-1.0,
                "issues_found": ["список проблем"],
                "corrections": ["список исправлений"],
                "verification_status": "verified|needs_check|incorrect"
            }},
            "current_context": {{
                "key_figures_status": {{"имя": "текущий статус"}},
                "recent_events": ["важные события"],
                "breaking_news": "критичная информация"
            }}
        }}
        """

        try:
            # Если включен прямой вызов, используем базовую проверку
            if self.force_direct_api:
                logger.info("Используем базовую проверку фактов (прямой API)")
                return self._basic_fact_check(news_text, context)
            
            # Используем правильный API согласно спецификации
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self.grounding_config
            )

            # Извлекаем grounding данные для проверки источников
            grounding_data = {
                'chunks': [],
                'supports': [],
                'search_entry_point': None
            }

            if hasattr(response.candidates[0], 'grounding_metadata'):
                metadata = response.candidates[0].grounding_metadata
                if metadata.grounding_chunks:
                    grounding_data['chunks'] = [
                        {
                            'title': chunk.web.title,
                            'uri': chunk.web.uri,
                            'content': getattr(chunk.web, 'snippet', '')
                        } for chunk in metadata.grounding_chunks
                    ]
                if metadata.grounding_supports:
                    grounding_data['supports'] = [
                        {
                            'confidence_scores': support.confidence_scores,
                            'segment': {
                                'start_index': support.segment.start_index,
                                'end_index': support.segment.end_index,
                                'text': support.segment.text
                            } if support.segment else None
                        } for support in metadata.grounding_supports
                    ]

            # Обрабатываем parts как список
            parts = response.candidates[0].content.parts
            if isinstance(parts, list):
                result_text = parts[0].text
            else:
                result_text = parts.text
            
            # Пытаемся парсить как JSON, если не получается - создаем структуру
            try:
                fact_check_data = json.loads(result_text)
                logger.info("✅ Получен JSON ответ от Google Search Grounding")
            except json.JSONDecodeError:
                logger.info("📝 Получен текстовый ответ от Google Search Grounding, создаем структуру")
                # Создаем структуру на основе текстового ответа и grounding данных
                accuracy_score = 0.8 if grounding_data['chunks'] else 0.5
                fact_check_data = {
                    'fact_check': {
                        'accuracy_score': accuracy_score,
                        'verification_status': 'verified' if grounding_data['chunks'] else 'needs_check',
                        'corrections': self._extract_corrections_from_text(result_text),
                        'verified_facts': result_text[:500],  # Первые 500 символов как проверенные факты
                        'confidence': 'high' if grounding_data['chunks'] else 'medium'
                    }
                }

            # Проверяем порог точности
            accuracy_score = fact_check_data.get('fact_check', {}).get('accuracy_score', 0.5)
            if accuracy_score < self.config.get('grounding', {}).get('fact_check_threshold', 0.7):
                logger.warning(f"Низкая точность фактов: {accuracy_score}")

            return {
                'fact_check': fact_check_data['fact_check'],
                'grounding_data': grounding_data,
                'verification_sources': grounding_data['chunks'],
                'grounding_text': result_text  # Добавляем оригинальный текст
            }

        except Exception as e:
            logger.warning(f"Ошибка проверки фактов через Google Search: {e}")
            return {
                'fact_check': {
                    'accuracy_score': 0.5,
                    'issues_found': ['Не удалось проверить факты'],
                    'corrections': [],
                    'verification_status': 'needs_check'
                },
                'grounding_data': {'chunks': [], 'supports': []},
                'verification_sources': []
            }
    
    def _extract_corrections_from_text(self, text: str) -> List[str]:
        """Извлекает исправления из текстового ответа"""
        corrections = []
        
        # Простые паттерны для поиска исправлений
        correction_patterns = [
            r"действующий президент",
            r"президент сша.*трамп",
            r"трамп.*президент",
            r"исправление",
            r"на самом деле",
            r"фактически"
        ]
        
        import re
        for pattern in correction_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                corrections.append(f"Найдено исправление по паттерну: {pattern}")
        
        return corrections

    def _basic_fact_check(self, news_text: str, context: str = "") -> Dict[str, Any]:
        """Базовая проверка фактов без Google Search Grounding"""
        prompt = f"""
        Ты эксперт по проверке фактов. Проанализируй новость на точность и актуальность.
        
        ЗАДАЧА: Найди фактические ошибки в тексте, особенно:
        - Неправильные или устаревшие политические титулы и должности
        - Устаревшую информацию о текущих событиях
        - Логические противоречия
        - Неточности в датах и временных рамках
        
        КОНТЕКСТ: Текущий год - 2025. Проверь актуальность всей информации.
        
        ТЕКСТ: {news_text}
        
        Верни ТОЛЬКО JSON (без markdown, без комментариев):
        {{
            "fact_check": {{
                "accuracy_score": 0.9,
                "issues_found": ["найденная проблема"],
                "corrections": ["правильная информация"],
                "verification_status": "verified"
            }}
        }}
        """

        try:
            # Если включен прямой вызов, используем его
            if self.force_direct_api and self.direct_provider:
                response_text = self.direct_provider._call_gemini_api(prompt, temperature=0.3)
                if not response_text:
                    raise ValueError("Прямой вызов API не вернул результат для проверки фактов.")
                # Убираем возможные markdown-обертки
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                result = json.loads(response_text.strip())

            elif USE_NEW_SDK and hasattr(self, 'client') and self.client:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json"
                    )
                )
                # Обрабатываем parts как список
                parts = response.candidates[0].content.parts
                if isinstance(parts, list):
                    text = parts[0].text.strip()
                else:
                    text = parts.text.strip()
                result = json.loads(text)
            else:
                # Старый SDK
                response = self.client.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.3
                    )
                )
                # Извлекаем JSON из ответа
                text_response = response.text.strip()
                # Убираем возможные markdown-обертки
                if text_response.startswith('```json'):
                    text_response = text_response[7:]
                if text_response.endswith('```'):
                    text_response = text_response[:-3]
                result = json.loads(text_response.strip())

            return {
                'fact_check': result['fact_check'],
                'grounding_data': {'chunks': [], 'supports': []},
                'verification_sources': []
            }

        except Exception as e:
            logger.warning(f"Ошибка базовой проверки фактов: {e}")
            return {
                'fact_check': {
                    'accuracy_score': 0.5,
                    'issues_found': ['Не удалось выполнить проверку'],
                    'corrections': [],
                    'verification_status': 'uncertain'
                },
                'grounding_data': {'chunks': [], 'supports': []},
                'verification_sources': []
            }

    def summarize_for_video(self, text: str, context: str = "") -> str:
        """Создание краткого текста для видео с проверкой фактов"""
        
        # Если используется прямой API, делегируем вызов
        if self.force_direct_api and self.direct_provider:
            return self.direct_provider.summarize_for_video(text)
        
        # Сначала проверяем факты
        fact_check = self._verify_facts_with_search(text, context)

        # Улучшаем промпт на основе проверки фактов
        corrections_text = ""
        if fact_check.get('fact_check', {}).get('issues_found'):
            corrections_text = f"""
            ОБЯЗАТЕЛЬНЫЕ ИСПРАВЛЕНИЯ (основаны на проверке фактов):
            {chr(10).join(f"- {issue}" for issue in fact_check['fact_check']['issues_found'])}

            ПРАВИЛЬНЫЕ ФАКТЫ:
            {chr(10).join(f"- {correction}" for correction in fact_check['fact_check'].get('corrections', []))}
            """
        elif fact_check.get('fact_check', {}).get('corrections'):
            corrections_text = f"""
            ПРАВИЛЬНЫЕ ФАКТЫ (основаны на проверке фактов):
            {chr(10).join(f"- {correction}" for correction in fact_check['fact_check']['corrections'])}
            """

        prompt = f"""
        Summarize the following news into a clear, neutral, and informative script for a short video.

        Requirements:
        - Language: English, for an international audience
        - Style: professional, factual, neutral, news-report tone
        - Length: 400–600 characters (about 4–6 sentences)
        - Must cover: WHO, WHAT, WHEN, WHERE, WHY, and IMPACT
        - If the news contains a direct quote, include it exactly as written and in quotation marks
        - Focus on the main thesis of the news, avoid speculation or misleading interpretation
        - Provide necessary context and significance in a concise way
        - Write in complete sentences, with smooth narrative flow
        - No abbreviations, no subjective language, no cut-off sentences
        - No emojis, no hashtags, no social media style

        {corrections_text}

        News: {text}

        Final factual short video summary in English:
        """

        try:
            if self.force_direct_api:
                # Используем прямой API провайдер
                return self.direct_provider.summarize_for_video(text)
            elif USE_NEW_SDK and self.client:
                # Используем новый SDK
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self.generation_config
                )
                # Обрабатываем parts как список
                parts = response.candidates[0].content.parts
                if isinstance(parts, list):
                    return parts[0].text.strip()
                else:
                    return parts.text.strip()
            else:
                # Fallback
                return self._fallback_summarize(text)
        except Exception as e:
            logger.error(f"Ошибка при генерации текста для видео: {e}")
            return self._fallback_summarize(text)

    def _fallback_summarize(self, text: str) -> str:
        """Резервный метод суммаризации"""
        if len(text) <= 150:
            return text
        return text[:147] + "..."

    def generate_seo_package(self, text: str, source_url: str = "") -> Dict[str, Any]:
        """Генерация SEO пакета с проверкой фактов"""
        
        # Если используется прямой API, делегируем вызов
        if self.force_direct_api and self.direct_provider:
            return self.direct_provider.generate_seo_package(text, source_url)
        
        # Проверяем факты перед генерацией SEO
        fact_check = self._verify_facts_with_search(text)

        corrections_text = ""
        if fact_check.get('fact_check', {}).get('issues_found'):
            corrections_text = f"""
            ВАЖНО: Учитывай эти исправления при генерации SEO контента:
            {chr(10).join(f"- {issue}" for issue in fact_check['fact_check']['issues_found'])}
            """
        elif fact_check.get('fact_check', {}).get('corrections'):
            corrections_text = f"""
            ВАЖНО: Учитывай эти исправления при генерации SEO контента:
            {chr(10).join(f"- {correction}" for correction in fact_check['fact_check']['corrections'])}
            """

        prompt = f"""
        TASK: Create YouTube Shorts SEO package for international news content.

        OUTPUT FORMAT: JSON only, no explanations
        {{
          "title": "...",
          "description": "...",
          "tags": ["...", "..."]
        }}

        TITLE RULES:
        - Maximum 100 characters
        - Clickbait style but factual
        - Start with action words or shocking facts
        - NO generic words like 'news', 'update', 'breaking'
        - Examples: 'Putin meets Trump at Alaska hotel', 'Bitcoin crashes 40% in single day', 'Ukraine captures Russian general'

        DESCRIPTION RULES:
        - 1-2 SHORT sentences maximum
        - Add context or key details not in title
        - Can be empty if title says everything
        - Include 5 relevant hashtags at the end with # symbol

        TAGS RULES:
        - Exactly 12-15 tags
        - Mix of: specific names, general topics, emotions, locations
        - Single words or short phrases (max 3 words)
        - NO '#' symbols
        - Include: relevant people names, countries, topics, trending keywords
        - Examples: ['putin', 'trump', 'politics', 'russia', 'america', 'meeting', 'diplomacy', 'world news', 'leadership', 'international', 'alaska', 'summit']

        {corrections_text}

        SOURCE TEXT:
        {text}

        JSON:
        """

        try:
            if self.force_direct_api:
                # Используем прямой API провайдер
                return self.direct_provider.generate_seo_package(text, source_url)
            elif USE_NEW_SDK and self.client:
                # Новый SDK
                config = types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config
                )
                # Обрабатываем parts как список
                parts = response.candidates[0].content.parts
                if isinstance(parts, list):
                    text = parts[0].text.strip()
                else:
                    text = parts.text.strip()
                try:
                    result = json.loads(text)
                except json.JSONDecodeError:
                    logger.warning(f"Не удалось парсить JSON в generate_seo_package: {text[:100]}...")
                    return self._fallback_seo_package(text)
            else:
                # Fallback
                return self._fallback_seo_package(text)

            # Проверяем, что result - это словарь
            if not isinstance(result, dict):
                logger.warning(f"LLM вернул не словарь в generate_seo_package: {type(result)}")
                return self._fallback_seo_package(text)

            # Валидация и пост-обработка
            title = (result.get('title') or '').strip()
            if not title:
                title = (text[:70] + '...') if len(text) > 70 else text

            # Добавляем хештеги к заголовку если их нет
            if '#' not in title and result.get('tags'):
                tags = result.get('tags', [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',') if t.strip()]

                if tags:
                    title_hashtags = [f"#{tag.replace(' ', '')}" for tag in tags[:3]]
                    title_with_hashtags = f"{title} {' '.join(title_hashtags)}"

                    if len(title_with_hashtags) > 90:
                        max_title_len = 90 - len(' '.join(title_hashtags)) - 1
                        title = title[:max_title_len].rstrip() + "..."
                        title = f"{title} {' '.join(title_hashtags)}"
                    else:
                        title = title_with_hashtags

            description = (result.get('description') or '').strip()
            if len(description) > 280:
                description = description[:279].rstrip() + '...'

            tags = result.get('tags') or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]

            # Минимум 5 тегов
            base_tags = ['новини', 'news', 'shorts']
            tags = list(dict.fromkeys([*tags, *base_tags]))[:15]
            if len(tags) < 5:
                tags += ['updates', 'video', 'world']
                tags = tags[:15]

            return {
                'title': title,
                'description': description,
                'tags': tags,
                'category': result.get('category', 'Новости'),
                'fact_verification': fact_check['fact_check'],
                'sources_used': fact_check['verification_sources']
            }

        except Exception as e:
            logger.error(f"Ошибка при генерации SEO пакета через Gemini: {e}")
            return self._fallback_seo_package(text)

    def categorize_news(self, news_text: str) -> Dict[str, Any]:
        """Категоризация новости"""
        categories = ["politics", "business", "technology", "sports", "entertainment", "health", "science"]

        prompt = f"""
        Определи категорию для этой новости. Доступные категории: {', '.join(categories)}

        Новость: {news_text}

        Верни JSON в формате:
        {{
            "category": "основная_категория",
            "confidence": 0.0-1.0,
            "tags": ["тег1", "тег2", "тег3"],
            "language": "язык_новости"
        }}
        """

        try:
            if USE_NEW_SDK:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json"
                    )
                )
                # Обрабатываем parts как список
                parts = response.candidates[0].content.parts
                if isinstance(parts, list):
                    text = parts[0].text.strip()
                else:
                    text = parts.text.strip()
                result = json.loads(text)
            else:
                response = self.client.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(temperature=0.3)
                )
                text_response = response.text.strip()
                if text_response.startswith('```json'):
                    text_response = text_response[7:]
                if text_response.endswith('```'):
                    text_response = text_response[:-3]
                result = json.loads(text_response.strip())

            return result

        except Exception as e:
            logger.warning(f"Ошибка категоризации: {e}")
            return {
                "category": "general",
                "confidence": 0.5,
                "tags": ["news"],
                "language": "unknown"
            }

    def generate_structured_content(self, news_data: Dict) -> Dict[str, Any]:
        """Генерация структурированного контента для анимации с проверкой фактов"""
        
        # Если используется прямой API, делегируем вызов
        if self.force_direct_api and self.direct_provider:
            return self.direct_provider.generate_structured_content(news_data)
        
        # Проверяем факты для точности контента
        news_text = f"{news_data.get('title', '')}. {news_data.get('description', '')}"
        fact_check = self._verify_facts_with_search(news_text)

        corrections_text = ""
        if fact_check.get('fact_check', {}).get('issues_found'):
            corrections_text = f"""
            ВАЖНЫЕ ИСПРАВЛЕНИЯ ДЛЯ АНИМАЦИИ:
            {chr(10).join(f"- {issue}" for issue in fact_check['fact_check']['issues_found'])}
            """
        elif fact_check.get('fact_check', {}).get('corrections'):
            corrections_text = f"""
            ВАЖНЫЕ ИСПРАВЛЕНИЯ ДЛЯ АНИМАЦИИ:
            {chr(10).join(f"- {correction}" for correction in fact_check['fact_check']['corrections'])}
            """

        prompt = f"""
        Create structured content for YouTube Shorts animation based on the news.
        Return JSON in format:
        {{
            "header": {{
                "text": "Brief title for the top part - IN ENGLISH",
                "animation": "fadeIn",
                "duration": 1.5
            }},
            "body": {{
                "text": "Main news text - IN ENGLISH",
                "animation": "typewriter",
                "duration": 2.5
            }},
            "footer": {{
                "source": "News source",
                "date": "Date in DD.MM.YYYY format",
                "animation": "slideUp",
                "duration": 1.0
            }},
            "style": {{
                "theme": "dark|light",
                "accent_color": "#HEX_COLOR",
                "font_size": "medium"
            }}
        }}

        {corrections_text}

        Исходная новость:
        Заголовок: {news_data.get('title', '')}
        Описание: {news_data.get('description', '')}
        Источник: {news_data.get('source', '')}
        Дата: {news_data.get('published', '')}
        """

        try:
            if self.force_direct_api:
                # Используем прямой API провайдер
                return self.direct_provider.generate_structured_content(news_data)
            elif USE_NEW_SDK and self.client:
                # Новый SDK
                config = types.GenerateContentConfig(
                    temperature=0.5,
                    response_mime_type="application/json"
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config
                )
                # Обрабатываем parts как список
                parts = response.candidates[0].content.parts
                if isinstance(parts, list):
                    text = parts[0].text.strip()
                else:
                    text = parts.text.strip()
                try:
                    result = json.loads(text)
                except json.JSONDecodeError:
                    logger.warning(f"Не удалось парсить JSON в generate_structured_content: {text[:100]}...")
                    return self._fallback_structured_content(news_data)
            else:
                # Fallback
                return self._fallback_structured_content(news_data)

            # Проверяем, что result - это словарь
            if not isinstance(result, dict):
                logger.warning(f"LLM вернул не словарь в generate_structured_content: {type(result)}")
                return self._fallback_structured_content(news_data)

            # Валидация и дополнение данных
            if not result.get('footer', {}).get('date'):
                # Парсим дату из published
                published = news_data.get('published', '')
                if isinstance(published, str) and 'T' in published:
                    try:
                        dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        result['footer']['date'] = dt.strftime('%d.%m.%Y')
                    except:
                        result['footer']['date'] = datetime.now().strftime('%d.%m.%Y')
                else:
                    result['footer']['date'] = datetime.now().strftime('%d.%m.%Y')

            # Добавляем информацию о проверке фактов
            result['fact_verification'] = fact_check['fact_check']
            result['verification_sources'] = fact_check['verification_sources']

            return result

        except Exception as e:
            logger.error(f"Ошибка при генерации структурированного контента через Gemini: {e}")
            return self._fallback_structured_content(news_data)

    def _fallback_seo_package(self, text: str) -> Dict[str, Any]:
        """Резервный SEO пакет при ошибке LLM"""
        return {
            'title': f"Breaking: {text[:40]}..." if len(text) > 40 else f"Breaking: {text}",
            'description': '',
            'tags': ['news', 'breaking', 'shorts', 'updates', 'video'],
            'category': 'News & Politics'
        }

    def _fallback_structured_content(self, news_data: Dict) -> Dict[str, Any]:
        """Резервный структурированный контент"""
        return {
            "header": {
                "text": news_data.get('title', '')[:50] + "..." if len(news_data.get('title', '')) > 50 else news_data.get('title', ''),
                "animation": "fadeIn",
                "duration": 1.5
            },
            "body": {
                "text": news_data.get('description', '')[:100] + "..." if len(news_data.get('description', '')) > 100 else news_data.get('description', ''),
                "animation": "typewriter",
                "duration": 2.5
            },
            "footer": {
                "source": news_data.get('source', ''),
                "date": datetime.now().strftime('%d.%m.%Y'),
                "animation": "slideUp",
                "duration": 1.0
            },
            "style": {
                "theme": "dark",
                "accent_color": "#FF6B35",
                "font_size": "medium"
            }
        }

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
        """Обработка новости для создания shorts контента с проверкой фактов"""
        logger.info(f"Обработка новости: {news_data.get('title', '')[:50]}...")

        try:
            # Используем новый подход с полным пакетом данных
            if hasattr(self.provider, 'generate_complete_news_package'):
                logger.info("🚀 Используется новый метод полного пакета данных")
                complete_package = self.provider.generate_complete_news_package(news_data)
                
                # Преобразуем в старый формат для совместимости
                processed_data = {
                    'status': 'success',
                    'title': complete_package.get('content', {}).get('title', ''),
                    'summary': complete_package.get('content', {}).get('summary', ''),
                    'video_text': complete_package.get('content', {}).get('summary', ''),
                    'seo_package': complete_package.get('seo', {}),
                    'structured_content': complete_package,
                    'fact_check': complete_package.get('metadata', {}).get('fact_check', None)
                }
                
                logger.info(f"✅ Создан полный пакет данных с {complete_package.get('metadata', {}).get('confidence_score', 0):.1%} уверенности")
                return processed_data
            
            # Fallback к старому методу
            return self._process_news_legacy(news_data)

        except Exception as e:
            logger.error(f"Ошибка обработки новости ID {news_data.get('id')}: {e}")
            return {
                'news_id': news_data.get('id'),
                'status': 'error',
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }

    def _process_news_legacy(self, news_data: Dict) -> Dict[str, Any]:
        """Старый метод обработки новостей (для совместимости)"""
        # Инициализируем результат
        processed_data = {
            'status': 'success',
            'title': '',
            'summary': '',
            'video_text': '',
            'seo_package': {},
            'structured_content': {},
            'fact_check': None
        }

        # Подготовка полного текста новости для анализа
        full_text = f"{news_data.get('description', '')}"

        # --- Проверка фактов (если включена) ---
        if self.provider.grounding_is_available:
            logger.info(f"Проверка фактов для новости {news_data.get('id', 'N/A')}...")
            fact_check_result = self.provider._verify_facts_with_search(full_text)
            processed_data['fact_check'] = fact_check_result

        # Контекст для проверки фактов (источник, дата публикации)
        context = f"""
        Источник: {news_data.get('source', '')}
        Дата публикации: {news_data.get('published', '')}
        Категория: {news_data.get('category', '')}
        """

        # Генерация краткого текста для видео с проверкой фактов
        try:
            short_text = self.provider.summarize_for_video(full_text, context)
            # Normalize roles/titles to avoid "former President Trump" kind of errors
            short_text = self._fact_guard_normalize(short_text, news_data.get('published', ''))
            logger.info(f"  ✅ LLM summarize_for_video результат: {len(short_text) if short_text else 0} символов")
            processed_data['video_text'] = short_text
            processed_data['summary'] = short_text  # Дублируем для совместимости
        except Exception as e:
            logger.error(f"  ❌ Ошибка summarize_for_video: {e}")
            # Создаем краткое содержание из описания (первые 300 символов)
            description = news_data.get('description', 'Brief news summary')
            processed_data['video_text'] = description[:300] + ('...' if len(description) > 300 else '')
            processed_data['summary'] = processed_data['video_text']

        # Генерация SEO пакета с проверкой фактов
        try:
            source_url = news_data.get('url', '')
            seo_package = self.provider.generate_seo_package(full_text, source_url)
            logger.info(f"  ✅ LLM generate_seo_package результат: {bool(seo_package)}")
            processed_data['seo_package'] = seo_package
            if seo_package and 'title' in seo_package:
                # Normalize title as well
                processed_data['title'] = self._fact_guard_normalize(seo_package['title'], news_data.get('published', ''))
                logger.info(f"  ✅ Сгенерированный заголовок: {processed_data['title'][:50]}...")
            else:
                # Создаем краткий заголовок из исходного (первые 60 символов)
                original_title = news_data.get('title', 'Заголовок новости')
                processed_data['title'] = original_title[:60] + ('...' if len(original_title) > 60 else '')
        except Exception as e:
            logger.error(f"  ❌ Ошибка generate_seo_package: {e}")
            # Создаем краткий заголовок из исходного (первые 60 символов)
            original_title = news_data.get('title', 'Заголовок новости')
            processed_data['title'] = original_title[:60] + ('...' if len(original_title) > 60 else '')

        # Генерация структурированного контента для анимации
        try:
            if hasattr(self.provider, 'generate_structured_content'):
                structured_content = self.provider.generate_structured_content(news_data)
                logger.info(f"  ✅ LLM generate_structured_content результат: {bool(structured_content)}")
                processed_data['structured_content'] = structured_content
        except Exception as e:
            logger.error(f"  ❌ Ошибка generate_structured_content: {e}")
            processed_data['structured_content'] = {}

        # Возвращаем обработанные данные
        logger.info(f"✅ Успешно обработана новость ID {news_data.get('id')} с проверкой фактов")
        return processed_data

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
