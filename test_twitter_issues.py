#!/usr/bin/env python3
"""
Тест для диагностики проблем с Twitter контентом
"""

import logging
from scripts.llm_processor import LLMProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_twitter_processing():
    """Тест обработки Twitter контента"""
    
    logger.info("🐦 Тестируем обработку Twitter контента...")
    
    try:
        # Инициализируем LLM процессор
        processor = LLMProcessor('config/config.yaml')
        logger.info("✅ LLM процессор инициализирован")
        
        # Тестовые данные Twitter
        twitter_data = {
            'title': 'Tweet от OSINTdefender о военных действиях в Украине',
            'description': 'OSINT анализ ситуации на фронте с картой и деталями операций',
            'url': 'https://x.com/sentdefender/status/1967799197513470458',
            'source': 'TWITTER',
            'media': [
                'https://pbs.twimg.com/media/G08G8POWYAAqZyV?format=gif&name=medium'
            ],
            'published': '2025-09-16T03:54:23+00:00'
        }
        
        logger.info(f"🧪 Тестовый Twitter пост: '{twitter_data['title']}'")
        logger.info(f"📝 Описание: '{twitter_data['description']}'")
        
        # Тестируем каждый шаг отдельно
        logger.info("\n🔍 Тестируем summarize_for_video...")
        video_text = processor.provider.summarize_for_video(twitter_data['description'])
        logger.info(f"📝 Video text: '{video_text[:100]}...'")
        
        logger.info("\n🔍 Тестируем generate_seo_package...")
        seo_result = processor.provider.generate_seo_package(twitter_data['description'], twitter_data['url'])
        logger.info(f"🎯 SEO title: '{seo_result.get('title', '')}'")
        
        logger.info("\n🔍 Тестируем полную обработку...")
        result = processor.process_news_for_shorts(twitter_data)
        
        logger.info("✅ Twitter контент обработан!")
        
        # Анализ результатов
        print(f"\n📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
        print(f"🎯 Title: '{result.get('title', '')}'")
        print(f"📝 Summary: '{result.get('summary', '')[:100]}...'")
        print(f"🎬 Video text: '{result.get('video_text', '')[:100]}...'")
        
        seo = result.get('seo_package', {})
        print(f"📺 SEO title: '{seo.get('title', '')}'")
        print(f"📝 SEO description: '{seo.get('description', '')[:100]}...'")
        
        # Проверяем проблемы
        print(f"\n🔍 ДИАГНОСТИКА ПРОБЛЕМ:")
        
        video_text_issue = result.get('video_text', '').startswith('Please provide')
        print(f"   Video text заглушка: {'❌' if video_text_issue else '✅'}")
        
        title_issue = result.get('title', '').startswith('Breaking:')
        print(f"   Title с 'Breaking:': {'❌' if title_issue else '✅'}")
        
        empty_summary = len(result.get('summary', '')) < 50
        print(f"   Summary слишком короткий: {'❌' if empty_summary else '✅'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_twitter_processing()
    
    if success:
        logger.info("✅ Тест Twitter контента завершен!")
    else:
        logger.error("❌ Тест не прошел")
