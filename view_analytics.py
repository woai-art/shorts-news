#!/usr/bin/env python3
"""
Просмотр аналитики системы shorts_news
"""

import sys
import os
sys.path.append('scripts')

from analytics import NewsAnalytics

def main():
    """Главная функция просмотра аналитики"""
    print("📊 ANALYTICS DASHBOARD")
    print("=" * 60)

    analytics = NewsAnalytics()

    # Общая сводка
    summary = analytics.get_summary()

    print("📈 OVERVIEW:")
    overview = summary['overview']
    print(f"  Total News: {overview['total_news']}")
    print(f"  Processed: {overview['processed']}")
    print(f"  Failed: {overview['failed']}")
    print(f"  Success Rate: {overview['success_rate']}")
    print(f"  Avg Processing Time: {overview['avg_processing_time']}")
    print()

    # Топ категорий
    print("🏷️ TOP CATEGORIES:")
    for category, count in summary['top_categories']:
        print(f"  {category}: {count}")
    print()

    # Топ источников
    print("📍 TOP SOURCES:")
    for source, count in summary['top_sources']:
        print(f"  {source}: {count}")
    print()

    # Языки
    print("🌐 LANGUAGES:")
    for lang, count in summary['languages'].items():
        print(f"  {lang}: {count}")
    print()

    # Ежедневная статистика
    print("📅 DAILY STATS (Last 7 days):")
    daily = analytics.get_daily_report(7)
    for day in daily:
        print(f"  {day['date']}: {day['processed']}✓ {day['failed']}✗ ({day['avg_time']})")
    print()

    # Полный отчет
    print("📋 FULL REPORT:")
    print("-" * 60)
    report = analytics.generate_report()
    print(report)

if __name__ == "__main__":
    main()
