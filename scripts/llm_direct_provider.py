#!/usr/bin/env python3

"""
Альтернативный LLM провайдер с прямым HTTP вызовом к Gemini API
Обходит проблему OAuth redirect_uri_mismatch
"""

import os
import json
import requests
import logging
from typing import Optional, Dict, Any, List
from logger_config import logger
from scripts.llm_base import LLMProvider

class GeminiDirectProvider(LLMProvider):
    """Gemini провайдер с прямым HTTP вызовом"""

    def __init__(self, api_key: str, model: str = "models/gemini-2.0-flash", config: Dict = None):
        if not api_key or len(api_key) < 10:
             raise ValueError("Получен недействительный Gemini API ключ.")

        self.api_key = api_key
        # Логируем маскированный ключ для отладки
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}"
        logger.info(f"🔑 [DEBUG] Используется прямой API Gemini с ключом: {masked_key}")

        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ShortsNews/1.0'
        })

        # Настройки из конфигурации
        self.temperature = config.get('temperature', 0.7) if config else 0.7
        self.max_tokens = config.get('max_tokens', 2000) if config else 2000

        logger.info("✅ Инициализирован прямой Gemini провайдер")

    def _call_gemini_api(self, prompt: str, temperature: float = None) -> Optional[str]:
        """Прямой вызов Gemini API"""
        if temperature is None:
            temperature = self.temperature

        # Для API используем короткое имя модели
        model_name = self.model.replace("models/", "") if self.model.startswith("models/") else self.model
        url = f"{self.base_url}/{model_name}:generateContent"
        params = {'key': self.api_key}

        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": self.max_tokens,
                "topP": 1,
                "topK": 1
            }
        }

        try:
            logger.debug(f"Отправка запроса к Gemini API: {prompt[:100]}...")
            response = self.session.post(url, params=params, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        return content['parts'][0]['text']

            logger.error(f"Gemini API вернул ошибку {response.status_code}: {response.text[:300]}")
            return None

        except requests.exceptions.Timeout:
            logger.error("Timeout при вызове Gemini API")
            return None
        except Exception as e:
            logger.error(f"Ошибка при вызове Gemini API: {e}")
            return None

    def summarize_for_video(self, text: str) -> str:
        """Создание краткого текста для видео"""
        prompt = f"""
        Summarize the following news into a clear, neutral, and informative script for a short video. 

        Requirements:
        - Language: English, for an international audience
        - Style: professional, factual, neutral, news-report tone
        - Length: 400–600 characters (about 4–6 sentences)
        - Must cover: WHO, WHAT, WHEN, WHERE, WHY, and IMPACT
        - Ensure all political titles and positions are current and accurate for 2025
        - If the news contains a direct quote, include it exactly as written and in quotation marks
        - Focus on the main thesis of the news, avoid speculation or misleading interpretation
        - Provide necessary context and significance in a concise way
        - Write in complete sentences, with smooth narrative flow
        - No abbreviations, no subjective language, no cut-off sentences

        News: {text}

        Final factual short video summary in English:
        """
    
        result = self._call_gemini_api(prompt)
        if result:
            # Очищаем от лишних символов
            result = result.strip()
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            
            # Создаем русскую версию для логов
            russian_prompt = f"""
            Переведи этот английский текст на русский язык, сохраняя смысл и структуру:
            {result}
            
            Русский перевод:
            """
            russian_result = self._call_gemini_api(russian_prompt)
            if russian_result:
                russian_result = russian_result.strip()
                if russian_result.startswith('"') and russian_result.endswith('"'):
                    russian_result = russian_result[1:-1]
                logger.info(f"📝 Русский текст для понимания: '{russian_result}'")
            
            return result

        # Fallback
        return text[:100] + "..." if len(text) > 100 else text

    def generate_seo_package(self, text: str, source_url: str = "") -> Dict[str, Any]:
        """Генерация SEO пакета для YouTube Shorts"""
        prompt = f"""TASK: Create YouTube Shorts SEO package for news content.

OUTPUT FORMAT: JSON only, no explanations
{{
  "title": "...",
  "description": "...",
  "tags": ["...", "..."]
}}

TITLE RULES:
- Maximum 65 characters
- Clickbait style but factual
- Start with action words or shocking facts
- NO generic words like 'news', 'update', 'breaking'
- Examples: 'Putin meets Trump at Alaska hotel', 'Bitcoin crashes 40% in single day', 'Ukraine captures Russian general'

DESCRIPTION RULES:
- 1-2 SHORT sentences maximum
- Add context or key details not in title
- Can be empty if title says everything
- Include 5 relevant hashtags at the end with # symbol
- ALWAYS add source link at the end: "Source: {source_url}"

TAGS RULES:
- Exactly 12-15 tags
- Mix of: specific names, general topics, emotions, locations
- Single words or short phrases (max 3 words)
- NO '#' symbols
- Include: relevant people names, countries, topics, trending keywords
- Examples: ['putin', 'trump', 'politics', 'russia', 'america', 'meeting', 'diplomacy', 'world news', 'leadership', 'international', 'alaska', 'summit']

SOURCE TEXT:
{text}

JSON:"""

        result = self._call_gemini_api(prompt, temperature=0.3)
        if result:
            try:
                # Извлекаем JSON из ответа
                json_text = self._extract_json_from_text(result)
                if json_text:
                    return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON из ответа Gemini: {e}")

        # Fallback
        return {
            "title": text[:87] + "..." if len(text) > 87 else text,
            "description": text[:147] + "..." if len(text) > 147 else text,
            "tags": ["news", "shorts"],
            "hashtags": ["#news", "#shorts"]
        }

    def generate_complete_news_package(self, news_data: Dict) -> Dict[str, Any]:
        """Генерация полного пакета данных для новости"""
        text = news_data.get('description', '') or news_data.get('title', '')
        source_name = news_data.get('source', 'Unknown')
        
        prompt = f"""
        Create a complete news data package based on this article. Return ONLY valid JSON in this exact format:

        {{
            "content": {{
                "title": "Concise, engaging title (max 80 characters)",
                "summary": "Neutral, factual summary in professional news style (400-600 characters). If the main news contains important quotes, include them EXACTLY as written in quotation marks. Extract main points and avoid misleading interpretation.",
                "key_points": ["main point 1", "main point 2", "main point 3"],
                "quotes": [
                    {{"text": "exact quote text", "speaker": "speaker name"}}
                ]
            }},
            "seo": {{
                "youtube_title": "SEO-optimized YouTube title (max 120 characters, can be 2-3 lines)",
                "youtube_description": "YouTube description with hashtags and context (max 500 characters)",
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
                "hashtags": ["#news", "#breaking", "#politics"],
                "category": "News & Politics"
            }},
            "metadata": {{
                "language": "en",
                "confidence_score": 0.95
            }}
        }}

        Requirements:
        - Write in professional, neutral, factual tone
        - Preserve important quotes EXACTLY as written
        - Focus on WHO, WHAT, WHEN, WHERE, WHY, IMPACT
        - No speculation or misleading interpretation
        - Complete sentences only, no cut-offs

        Article from {source_name}: {text}
        """

        result = self._call_gemini_api(prompt, temperature=0.3)
        if result:
            try:
                json_text = self._extract_json_from_text(result)
                if json_text:
                    return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON из ответа Gemini: {e}")

        # Fallback
        return self._generate_fallback_package(news_data)

    def _generate_fallback_package(self, news_data: Dict) -> Dict[str, Any]:
        """Создание fallback пакета когда LLM не работает"""
        title = news_data.get('title', 'News Update')
        description = news_data.get('description', '')
        source = news_data.get('source', 'News Source')
        
        return {
            "content": {
                "title": title[:80] + ('...' if len(title) > 80 else ''),
                "summary": description[:400] + ('...' if len(description) > 400 else ''),
                "key_points": [description[:100] + ('...' if len(description) > 100 else '')],
                "quotes": []
            },
            "seo": {
                "youtube_title": title[:120] + ('...' if len(title) > 120 else ''),
                "youtube_description": f"{description[:300]}... #news #breaking #{source.lower().replace(' ', '')}",
                "tags": ["news", "breaking", "update", source.lower()],
                "hashtags": ["#news", "#breaking", f"#{source.lower().replace(' ', '')}"],
                "category": "News & Politics"
            },
            "metadata": {
                "language": "en",
                "confidence_score": 0.5
            }
        }

    def generate_structured_content(self, news_data: Dict) -> Dict[str, Any]:
        """Генерация структурированного контента для анимации (совместимость)"""
        # Используем новый метод для создания полного пакета
        complete_package = self.generate_complete_news_package(news_data)
        
        # Возвращаем в старом формате для совместимости
        content = complete_package.get('content', {})
        return {
            "main_title": content.get('title', ''),
            "subtitle": content.get('summary', '')[:100] + ('...' if len(content.get('summary', '')) > 100 else ''),
            "key_points": content.get('key_points', []),
            "animation_style": "fade",
            "duration_seconds": 30
        }

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Извлечение JSON из текста ответа"""
        import re

        # Ищем JSON блок
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)

        # Ищем блок с ```json
        json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block:
            return json_block.group(1)

        return None

def test_direct_provider():
    """Тест прямого провайдера"""
    print("🧪 ТЕСТИРОВАНИЕ ПРЯМОГО GEMINI ПРОВАЙДЕРА")
    print("=" * 60)

    # Получаем API ключ
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ API ключ не найден!")
        return False

    print(f"✅ API ключ найден (длина: {len(api_key)} символов)")

    # Создаем провайдер
    provider = GeminiDirectProvider(api_key)

    # Тестируем простой запрос
    test_text = "Test news about technology and AI."
    print(f"📤 Тестирование summarization: {test_text}")

    summary = provider.summarize_for_video(test_text)
    if summary:
        print(f"✅ Summarization: {summary}")
    else:
        print("❌ Summarization failed")
        return False

    # Тестируем SEO
    print("\\n📤 Тестирование SEO generation...")
    seo = provider.generate_seo_package(test_text)
    if seo:
        print(f"✅ SEO Title: {seo.get('title', 'N/A')}")
        print(f"✅ SEO Tags: {seo.get('tags', [])}")
    else:
        print("❌ SEO generation failed")
        return False

    # Тестируем structured content
    print("\\n📤 Тестирование structured content...")
    structured = provider.generate_structured_content({'title': 'Test', 'description': test_text})
    if structured:
        print(f"✅ Main Title: {structured.get('main_title', 'N/A')}")
        print(f"✅ Key Points: {len(structured.get('key_points', []))}")
    else:
        print("❌ Structured content failed")
        return False

    return True

if __name__ == "__main__":
    success = test_direct_provider()
    if success:
        print("\\n🎉 ПРЯМОЙ ПРОВАЙДЕР РАБОТАЕТ!")
        print("✅ Можно использовать в основной системе")
    else:
        print("\\n💥 ПРЯМОЙ ПРОВАЙДЕР НЕ РАБОТАЕТ!")
        print("🔧 Проверьте API ключ и интернет соединение")
