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
from scripts.prompt_loader import load_prompts, format_prompt

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
        prompts = load_prompts()
        template = prompts.get('content', {}).get('summarize_for_video', '')
        prompt = format_prompt(template, text=text)
        
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
        prompts = load_prompts()
        template = prompts.get('seo', {}).get('generate_seo_package', '')
        prompt = format_prompt(template, text=text, source_url=source_url)

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

    def generate_video_package(self, news_data: Dict) -> Dict[str, Any]:
        """Generates a complete video data package using a single prompt."""
        text = news_data.get('description', '') or news_data.get('title', '')
        source_name = news_data.get('source', 'Unknown')
        source_url = news_data.get('url', '')

        prompts = load_prompts()
        template = prompts.get('video_package', {}).get('generate', '')
        prompt = format_prompt(template, text=text, source_name=source_name, source_url=source_url)

        result = self._call_gemini_api(prompt, temperature=0.5)
        if result:
            try:
                json_text = self._extract_json_from_text(result)
                if json_text:
                    return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from Gemini in generate_video_package: {e}")
                # Если JSON не парсится, используем fallback
                logger.info("Using fallback due to JSON parsing error")
                return self._generate_fallback_video_package(news_data)
        else:
            # Если API не вернул результат, используем fallback
            logger.info("Using fallback due to API error")

        # Fallback
        return self._generate_fallback_video_package(news_data)

    def _generate_fallback_video_package(self, news_data: Dict) -> Dict[str, Any]:
        """Creates a fallback video package when the LLM fails."""
        title = news_data.get('title', 'News Update')
        description = news_data.get('description', '')

        return {
            "video_content": {
                "title": title[:80],
                "summary": description[:250]  # Ограничиваем до 250 символов
            },
            "seo_package": {
                "youtube_title": title,
                "youtube_description": f"{description[:200]}... #news #breaking",
                "tags": ["news", "breaking", "update"]
            }
        }

    def generate_structured_content(self, news_data: Dict) -> Dict[str, Any]:
        """Генерация структурированного контента для анимации (совместимость)"""
        # Используем новый метод для создания полного пакета
        complete_package = self.generate_complete_news_package(news_data)
        
        # Возвращаем в старом формате для совместимости
        content = complete_package.get('content', {})
        
        # Очищаем заголовок от лишней технической информации
        import re
        title = content.get('title', '').strip()
        
        # Удаляем технические хвосты
        cleanup_patterns = [
            r"\s*-\s*Live Updates\s*-\s*POLITICO\s*$",
            r"\s*\|\s*POLITICO\s*$",
            r"\s*-\s*POLITICO\s*$",
            r"\s*–\s*POLITICO\s*$",
            r"\s*\(.*?\)\s*$",
            r"\s*\[.*?\]\s*$",
        ]
        for pattern in cleanup_patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE)
        
        # Удаляем запрещенные слова
        banned_words = ["live updates", "explainer", "opinion", "analysis", "breaking", "news", "today", "update"]
        for word in banned_words:
            title = re.sub(rf"\b{re.escape(word)}\b", "", title, flags=re.IGNORECASE)
        
        # Удаляем разделители и лишние пробелы
        title = re.sub(r"\s+\|\s+.*$", "", title)
        title = re.sub(r"\s+", " ", title).strip().rstrip('.!')
        
        # Ограничиваем длину
        if len(title) > 60:
            cut = title[:60]
            if ' ' in cut:
                cut = cut[:cut.rfind(' ')]
            title = cut
        
        return {
            "main_title": title,
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
