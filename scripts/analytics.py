#!/usr/bin/env python3
"""
Система аналитики и статистики для shorts_news
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class NewsAnalytics:
    """Система аналитики для новостей"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.stats_file = self.data_dir / "analytics.json"
        self.load_stats()

    def load_stats(self):
        """Загружает статистику из файла"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
                self.stats = self._default_stats()
        else:
            self.stats = self._default_stats()

    def _default_stats(self) -> Dict[str, Any]:
        """Создает структуру статистики по умолчанию"""
        return {
            "start_date": datetime.now().isoformat(),
            "total_news": 0,
            "processed_news": 0,
            "failed_news": 0,
            "categories": {},
            "sources": {},
            "languages": {},
            "daily_stats": {},
            "performance": {
                "avg_processing_time": 0,
                "success_rate": 0,
                "error_rate": 0
            }
        }

    def save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

    def record_news_processing(self, news_data: Dict, success: bool, processing_time: float = 0):
        """Записывает обработку новости"""
        self.stats["total_news"] += 1

        if success:
            self.stats["processed_news"] += 1
        else:
            self.stats["failed_news"] += 1

        # Категория
        category = news_data.get("category", "unknown")
        if category not in self.stats["categories"]:
            self.stats["categories"][category] = 0
        self.stats["categories"][category] += 1

        # Источник
        source = news_data.get("source", "unknown")
        if source not in self.stats["sources"]:
            self.stats["sources"][source] = 0
        self.stats["sources"][source] += 1

        # Язык
        language = news_data.get("language", "unknown")
        if language not in self.stats["languages"]:
            self.stats["languages"][language] = 0
        self.stats["languages"][language] += 1

        # Ежедневная статистика
        today = datetime.now().date().isoformat()
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "processed": 0,
                "failed": 0,
                "categories": {},
                "processing_times": []
            }

        daily = self.stats["daily_stats"][today]
        if success:
            daily["processed"] += 1
        else:
            daily["failed"] += 1

        if processing_time > 0:
            daily["processing_times"].append(processing_time)

        # Обновляем производительность
        total_processed = self.stats["processed_news"] + self.stats["failed_news"]
        if total_processed > 0:
            self.stats["performance"]["success_rate"] = self.stats["processed_news"] / total_processed
            self.stats["performance"]["error_rate"] = self.stats["failed_news"] / total_processed

        if processing_time > 0:
            # Рассчитываем среднее время обработки
            all_times = []
            for day_stats in self.stats["daily_stats"].values():
                all_times.extend(day_stats.get("processing_times", []))

            if all_times:
                self.stats["performance"]["avg_processing_time"] = sum(all_times) / len(all_times)

        self.save_stats()

    def get_summary(self) -> Dict[str, Any]:
        """Получает сводку статистики"""
        return {
            "overview": {
                "total_news": self.stats["total_news"],
                "processed": self.stats["processed_news"],
                "failed": self.stats["failed_news"],
                "success_rate": f"{self.stats['performance']['success_rate']:.1%}",
                "avg_processing_time": f"{self.stats['performance']['avg_processing_time']:.1f}s"
            },
            "top_categories": sorted(
                self.stats["categories"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "top_sources": sorted(
                self.stats["sources"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "languages": self.stats["languages"]
        }

    def get_daily_report(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получает ежедневный отчет за последние N дней"""
        today = datetime.now().date()
        report = []

        for i in range(days):
            date = (today - timedelta(days=i)).isoformat()
            if date in self.stats["daily_stats"]:
                daily_data = self.stats["daily_stats"][date]
                report.append({
                    "date": date,
                    "processed": daily_data["processed"],
                    "failed": daily_data["failed"],
                    "total": daily_data["processed"] + daily_data["failed"],
                    "avg_time": f"{sum(daily_data.get('processing_times', [0])) / max(len(daily_data.get('processing_times', [1])), 1):.1f}s"
                })
            else:
                report.append({
                    "date": date,
                    "processed": 0,
                    "failed": 0,
                    "total": 0,
                    "avg_time": "0.0s"
                })

        return report

    def generate_report(self) -> str:
        """Генерирует текстовый отчет"""
        summary = self.get_summary()
        daily = self.get_daily_report(3)

        report = "📊 ANALYTICS REPORT\n"
        report += "=" * 50 + "\n\n"

        # Обзор
        overview = summary["overview"]
        report += "📈 OVERVIEW:\n"
        report += f"  Total News: {overview['total_news']}\n"
        report += f"  Processed: {overview['processed']}\n"
        report += f"  Failed: {overview['failed']}\n"
        report += f"  Success Rate: {overview['success_rate']}\n"
        report += f"  Avg Processing Time: {overview['avg_processing_time']}\n\n"

        # Топ категорий
        report += "🏷️ TOP CATEGORIES:\n"
        for category, count in summary["top_categories"]:
            report += f"  {category}: {count}\n"
        report += "\n"

        # Топ источников
        report += "📍 TOP SOURCES:\n"
        for source, count in summary["top_sources"]:
            report += f"  {source}: {count}\n"
        report += "\n"

        # Ежедневная статистика
        report += "📅 DAILY STATS (Last 3 days):\n"
        for day in daily:
            report += f"  {day['date']}: {day['processed']} processed, {day['failed']} failed\n"

        return report
