#!/usr/bin/env python3
"""
Модуль экспорта анимаций в видео для shorts_news
Основной экспортер использует MoviePy для надежного создания видео.
Резервный (старый) экспортер использует Selenium.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
import yaml
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy import (
    ColorClip, CompositeVideoClip, ImageClip, VideoFileClip, AudioFileClip,
    concatenate_audioclips
)
import cv2  # OpenCV все еще нужен для Selenium-версии

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import io
import subprocess

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Импорт нашего модуля для логотипов
try:
    from logo_manager import LogoManager
except ImportError:
    LogoManager = None
    logger.warning("LogoManager не доступен")


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    """Helper function to wrap text into lines."""
    words = text.strip().split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = (" ".join(current + [word])).strip()
        w = draw.textbbox((0, 0), trial, font=font)[2]
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


class VideoExporter:
    """
    Класс для создания видео-шортсов с использованием MoviePy.
    Эта версия основана на предоставленном рабочем примере и более надежна,
    чем рендеринг через HTML/Selenium.
    """
    def __init__(self, video_config: Dict, paths_config: Dict):
        self.video_config = video_config
        self.paths_config = paths_config

        # Основные параметры видео
        self.width = int(video_config.get('width', 1080))
        self.height = int(video_config.get('height', 1920))
        self.duration = int(video_config.get('duration_seconds', 8))
        self.fps = int(video_config.get('fps', 30))
        
        # Отслеживание активных клипов для правильного закрытия
        self._active_clips = []

        # Разметка
        self.header_ratio = float(video_config.get('header_ratio', 0.35))
        self.title_ratio = float(video_config.get('title_ratio', 0.15))
        self.middle_ratio = float(video_config.get('middle_ratio', 0.40))
        
        # Стили
        self.title_bg_rgb = tuple(video_config.get('title_bg_rgb', [60, 60, 60]))
        self.middle_bg_rgb = tuple(video_config.get('middle_bg_rgb', [40, 40, 40]))
        self.footer_bg_rgb = tuple(video_config.get('footer_bg_rgb', [0, 0, 0]))
        
        # Разные шрифты для разных элементов
        self.title_font_path = video_config.get('title_font_path', 'resources/fonts/Arsenal-Bold.ttf')
        self.middle_font_path = video_config.get('middle_font_path', 'resources/fonts/Arsenal-Bold.ttf')
        self.footer_font_path = video_config.get('footer_font_path', 'resources/fonts/Arsenal-Bold.ttf')
        
        # Конфигурация источников новостей
        self.news_sources = video_config.get('news_sources', {})
        self.logos_dir = self.paths_config.get('logos_dir', 'resources/logos')
        
        # Инициализация менеджера логотипов
        self.logo_manager = None
        if LogoManager:
            try:
                # Предполагаем, что config находится рядом со скриптами
                config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
                self.logo_manager = LogoManager(str(config_path))
                logger.info("🎨 LogoManager инициализирован")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать LogoManager: {e}")

        # Эффекты
        self.header_zoom_start = float(video_config.get('header_zoom_start', 1.05))
        self.header_zoom_end = float(video_config.get('header_zoom_end', 1.00))

    def _load_font(self, font_path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Загружает шрифт или возвращает стандартный."""
        font_file = Path(font_path)
        if font_file.exists():
            try:
                return ImageFont.truetype(str(font_file), size=size)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки шрифта '{font_file}': {e}")
        else:
            logger.warning(f"⚠️ Шрифт '{font_file}' не найден.")
        
        logger.warning("Используется стандартный шрифт.")
        return ImageFont.load_default(size)

    def _make_header_clip(self, media_path: Optional[str], header_size: Tuple[int, int]):
        """Создает клип для шапки из изображения или видео."""
        target_w, target_h = header_size  # Целевой размер для медиа (16:9)
        full_w, full_h = self.width, self.height  # Размер всего видео (9:16)
        logger.info(f"🎬 Создание шапки: медиа='{media_path}', целевой размер={target_w}x{target_h}, полный размер={full_w}x{full_h}")
        
        if media_path and Path(media_path).exists():
            suffix = Path(media_path).suffix.lower()
            try:
                if suffix in {'.mp4', '.mov', '.mkv', '.avi', '.webm'}:
                    # Поддержка старта с заданного времени (секунды) если передано через news_data
                    start_offset = float(getattr(self, 'header_video_start_seconds', 0) or 0)
                    base_clip = VideoFileClip(media_path).without_audio()
                    if start_offset > 0 and start_offset < max(0.1, getattr(base_clip, 'duration', 0)):
                        video_clip = base_clip.subclipped(start_offset)
                    else:
                        video_clip = base_clip
                    if video_clip.duration > self.duration:
                        video_clip = video_clip.with_duration(self.duration)
                    
                    # Убираем чёрные края перед масштабированием
                    video_clip = self._crop_video_black_borders(video_clip)
                    # Масштабируем видео, чтобы заполнить всю область шапки
                    scale_factor = max(target_w / video_clip.w, target_h / video_clip.h)
                    scaled_w, scaled_h = int(video_clip.w * scale_factor), int(video_clip.h * scale_factor)
                    video_clip = video_clip.resized((scaled_w, scaled_h))
                    
                    # Обрезаем видео до размера области шапки, если нужно
                    if scaled_w > target_w or scaled_h > target_h:
                        x_crop = max(0, (scaled_w - target_w) // 2)
                        y_crop = max(0, (scaled_h - target_h) // 2)
                        video_clip = video_clip.cropped(x1=x_crop, y1=y_crop, x2=x_crop+target_w, y2=y_crop+target_h)
                    
                    # Создаём чёрный фон размером всего видео
                    background = ColorClip(size=(full_w, full_h), color=(0, 0, 0)).with_duration(self.duration)
                    
                    # Размещаем видео шапки в верхней части (заполняем всю ширину)
                    x_offset = 0  # Заполняем всю ширину
                    y_offset = 0  # Размещаем в самом верху
                    video_clip = video_clip.with_position((x_offset, y_offset)).with_duration(self.duration)
                    video_clip = CompositeVideoClip([background, video_clip], size=(full_w, full_h))
                    
                    final_clip = video_clip.with_duration(self.duration)
                    logger.info("✅ Видео для шапки успешно обработано")
                    return self._add_header_effects(final_clip)
                elif suffix == '.gif':
                    # Обработка GIF файлов
                    try:
                        # Пробуем загрузить как видео
                        gif_clip = VideoFileClip(media_path).without_audio()
                        if gif_clip.duration > self.duration:
                            # Зацикливаем GIF на время видео
                            gif_clip = gif_clip.loop(duration=self.duration)
                        else:
                            gif_clip = gif_clip.with_duration(self.duration)
                        
                        # Масштабируем GIF, чтобы заполнить всю область шапки
                        scale_factor = max(target_w / gif_clip.w, target_h / gif_clip.h)
                        scaled_w, scaled_h = int(gif_clip.w * scale_factor), int(gif_clip.h * scale_factor)
                        gif_clip = gif_clip.resized((scaled_w, scaled_h))
                        
                        # Обрезаем GIF до размера области шапки, если нужно
                        if scaled_w > target_w or scaled_h > target_h:
                            x_crop = max(0, (scaled_w - target_w) // 2)
                            y_crop = max(0, (scaled_h - target_h) // 2)
                            gif_clip = gif_clip.cropped(x1=x_crop, y1=y_crop, x2=x_crop+target_w, y2=y_crop+target_h)
                        
                        # Создаём чёрный фон размером всего видео
                        background = ColorClip(size=(full_w, full_h), color=(0, 0, 0)).with_duration(self.duration)
                        
                        # Размещаем GIF в верхней части
                        x_offset = 0
                        y_offset = 0
                        gif_clip = gif_clip.with_position((x_offset, y_offset))
                        gif_clip = CompositeVideoClip([background, gif_clip], size=(full_w, full_h))
                        
                        final_clip = gif_clip.with_duration(self.duration)
                        logger.info("✅ GIF для шапки успешно обработан")
                        return self._add_header_effects(final_clip)
                    except Exception as gif_error:
                        logger.warning(f"⚠️ Не удалось обработать GIF как видео: {gif_error}")
                        logger.info("Обрабатываем GIF как статичное изображение")
                        # Fallback: обрабатываем как обычное изображение
                        try:
                            pil_img = Image.open(media_path).convert('RGB')
                            # Убираем чёрные края перед обработкой
                            pil_img = self._crop_black_borders(pil_img)
                            
                            # Умная обработка изображения
                            pil_img = self._smart_image_processing(pil_img, target_w, target_h)
                            
                            # Создаём чёрный фон размером всего видео
                            background = Image.new('RGB', (full_w, full_h), color=(0, 0, 0))
                            # Размещаем изображение шапки в верхней части
                            x_offset = 0
                            y_offset = 0
                            background.paste(pil_img, (x_offset, y_offset))
                            
                            # Конвертируем в ImageClip
                            img_clip = ImageClip(np.array(background)).with_duration(self.duration)
                            logger.info("✅ GIF обработан как статичное изображение")
                            return self._add_header_effects(img_clip)
                        except Exception as fallback_error:
                            logger.error(f"❌ Ошибка при обработке GIF как изображение: {fallback_error}")
                            # Используем fallback фон
                else:
                    pil_img = Image.open(media_path).convert('RGB')
                    # Убираем чёрные края перед обработкой
                    pil_img = self._crop_black_borders(pil_img)
                    
                    # Умная обработка изображения
                    pil_img = self._smart_image_processing(pil_img, target_w, target_h)
                    
                    # Создаём чёрный фон размером всего видео
                    background = Image.new('RGB', (full_w, full_h), color=(0, 0, 0))
                    # Размещаем изображение шапки в верхней части (без центрирования по горизонтали)
                    x_offset = 0  # Заполняем всю ширину
                    y_offset = 0  # Размещаем в самом верху
                    background.paste(pil_img, (x_offset, y_offset))
                    
                    clip = ImageClip(np.array(background))
                    logger.info("✅ Изображение для шапки успешно обработано")
                    return self._add_header_effects(clip.with_duration(self.duration))
            except Exception as e:
                logger.error(f"❌ Ошибка обработки медиа '{media_path}': {e}", exc_info=True)

        logger.warning("⚠️ Медиа для шапки не найдено или ошибка. Используем fallback фон.")
        bg_path = Path('resources') / 'default_backgrounds' / 'news_default.jpg'
        if bg_path.exists():
            try:
                clip = ImageClip(str(bg_path)).resized(height=target_h)
                # Центрируем и обрезаем изображение
                x_center = clip.w / 2
                y_center = clip.h / 2
                x1 = max(0, int(x_center - target_w / 2))
                y1 = max(0, int(y_center - target_h / 2))
                x2 = min(clip.w, x1 + target_w)
                y2 = min(clip.h, y1 + target_h)
                clip = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
                return self._add_header_effects(clip.with_duration(self.duration))
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки fallback фона {bg_path}: {e}")

        return self._add_header_effects(ColorClip(size=(target_w, target_h), color=(25, 25, 50)).with_duration(self.duration))

    def _add_header_effects(self, clip):
        """Добавляет эффект плавного зума: 3 сек увеличение + 3 сек уменьшение."""
        def zoom_resize(t: float) -> float:
            half_duration = self.duration / 2
            
            # Первая половина (0-3 сек): плавное увеличение от 1.0 до header_zoom_start (1.05)
            if t <= half_duration:
                progress = t / half_duration  # 0 -> 1 за первую половину
                return 1.0 + (self.header_zoom_start - 1.0) * progress
            
            # Вторая половина (3-6 сек): плавное уменьшение от header_zoom_start (1.05) обратно к 1.0
            else:
                progress = (t - half_duration) / half_duration  # 0 -> 1 за вторую половину
                return self.header_zoom_start - (self.header_zoom_start - 1.0) * progress
                
        return clip.resized(zoom_resize)

    def _smart_image_processing(self, image: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Умная обработка изображений: определяет лучший способ подгонки под формат."""
        orig_w, orig_h = image.size
        target_ratio = target_w / target_h  # 16:9 ≈ 1.78
        orig_ratio = orig_w / orig_h
        
        logger.info(f"🧠 Умная обработка: оригинал {orig_w}x{orig_h} (соотношение {orig_ratio:.2f}) -> цель {target_w}x{target_h} (соотношение {target_ratio:.2f})")
        
        # Определяем стратегию обработки
        ratio_diff = abs(orig_ratio - target_ratio)
        
        if ratio_diff < 0.3:  # Соотношения близки - просто масштабируем
            logger.info("📏 Соотношения близки, масштабируем без обрезки")
            return image.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        elif orig_ratio > target_ratio * 1.5:  # Очень широкое изображение - используем размытый фон
            logger.info("🖼️ Широкое изображение, создаем размытый фон")
            return self._create_blurred_background_composition(image, target_w, target_h)
        
        elif orig_ratio < target_ratio / 1.5:  # Очень высокое изображение - тоже размытый фон
            logger.info("📱 Высокое изображение, создаем размытый фон")
            return self._create_blurred_background_composition(image, target_w, target_h)
        
        else:  # Средние различия - умная обрезка
            logger.info("✂️ Умная обрезка с сохранением важного контента")
            return self._smart_crop(image, target_w, target_h)
    
    def _create_blurred_background_composition(self, image: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Создает композицию с размытым фоном и центральным изображением."""
        # Создаем размытый фон из того же изображения
        background = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=20))
        
        # Затемняем фон
        background = Image.blend(background, Image.new('RGB', (target_w, target_h), (0, 0, 0)), 0.4)
        
        # Масштабируем основное изображение, чтобы оно поместилось целиком
        scale_factor = min(target_w / image.width, target_h / image.height) * 0.85  # 85% от максимального размера
        new_w, new_h = int(image.width * scale_factor), int(image.height * scale_factor)
        scaled_image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Размещаем изображение в центре
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        background.paste(scaled_image, (x_offset, y_offset))
        
        return background
    
    def _smart_crop(self, image: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Умная обрезка: пытается сохранить важный контент в центре."""
        orig_w, orig_h = image.size
        
        # Масштабируем изображение, чтобы заполнить целевую область
        scale_factor = max(target_w / orig_w, target_h / orig_h)
        new_w, new_h = int(orig_w * scale_factor), int(orig_h * scale_factor)
        scaled_image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Умная обрезка - пытаемся сохранить центральную область
        if new_w > target_w:
            # Горизонтальная обрезка - берем центр, но с небольшим смещением вверх для лиц
            left = (new_w - target_w) // 2
        else:
            left = 0
            
        if new_h > target_h:
            # Вертикальная обрезка - смещаем немного вверх (важная информация обычно в верхней части)
            top = int((new_h - target_h) * 0.3)  # 30% от избытка сверху, 70% снизу
        else:
            top = 0
        
        return scaled_image.crop((left, top, left + target_w, top + target_h))

    def _crop_black_borders(self, img: Image.Image, threshold: int = 10) -> Image.Image:
        """Автоматически обрезает чёрные края изображения."""
        # Конвертируем в numpy для анализа
        img_array = np.array(img)
        
        # Находим границы непустого контента (не чёрного)
        # Ищем пиксели, которые не являются почти чёрными
        mask = np.any(img_array > threshold, axis=2)
        
        # Находим координаты непустых пикселей
        coords = np.argwhere(mask)
        
        if coords.size == 0:
            # Если изображение полностью чёрное, возвращаем как есть
            return img
            
        # Определяем границы обрезки
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # Обрезаем изображение
        cropped = img.crop((x_min, y_min, x_max + 1, y_max + 1))
        
        logger.info(f"🔪 Обрезка чёрных краёв: {img.width}x{img.height} -> {cropped.width}x{cropped.height}")
        return cropped

    def _crop_video_black_borders(self, video_clip, threshold: int = 10):
        """Автоматически обрезает чёрные края видео на основе первого кадра."""
        # Получаем первый кадр как изображение PIL
        first_frame = video_clip.get_frame(0)
        pil_frame = Image.fromarray(first_frame.astype('uint8'))
        
        # Находим границы обрезки на первом кадре
        img_array = np.array(pil_frame)
        mask = np.any(img_array > threshold, axis=2)
        coords = np.argwhere(mask)
        
        if coords.size == 0:
            # Если кадр полностью чёрный, возвращаем как есть
            return video_clip
            
        # Определяем границы обрезки
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # Применяем обрезку к видео (MoviePy 2.x)
        try:
            # В MoviePy 2.x используется метод cropped
            cropped_video = video_clip.cropped(x1=x_min, y1=y_min, x2=x_max + 1, y2=y_max + 1)
        except AttributeError:
            try:
                # Fallback для старых версий MoviePy
                cropped_video = video_clip.crop(x1=x_min, y1=y_min, x2=x_max + 1, y2=y_max + 1)
            except AttributeError:
                # Если ни один не работает, возвращаем оригинал
                logger.warning("⚠️ Не удалось обрезать видео, используем оригинал")
                return video_clip
        
        logger.info(f"🔪 Обрезка чёрных краёв видео: {video_clip.w}x{video_clip.h} -> {cropped_video.w}x{cropped_video.h}")
        return cropped_video

    def _render_title_image(self, title: str, size: Tuple[int, int]) -> np.ndarray:
        """Рендерит заголовок новости."""
        w, h = size
        img = Image.new('RGB', (w, h), color=self.title_bg_rgb)
        draw = ImageDraw.Draw(img)
        
        # Используем более крупный шрифт для заголовка (Cinzel)
        title_font_size = int(self.height * 0.025)  # ~48px для 1920px высоты
        font = self._load_font(self.title_font_path, title_font_size)
        
        # Отступы
        padding = int(w * 0.05)  # 5% от ширины
        max_width = w - 2 * padding
        
        # Разбиваем заголовок на строки
        lines = _wrap_text(draw, title, font, max_width)
        
        # Рассчитываем общую высоту текста
        line_height = int(title_font_size * 1.2)
        total_text_height = len(lines) * line_height
        
        # Центрируем по вертикали
        y_start = (h - total_text_height) // 2
        
        # Рендерим каждую строку
        for i, line in enumerate(lines):
            y_pos = y_start + i * line_height
            
            # Центрируем по горизонтали
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (w - text_width) // 2
            
            # Рисуем текст белым цветом
            draw.text((x_pos, y_pos), line, fill=(255, 255, 255), font=font)
        
        return np.array(img)

    def _render_text_image(self, text: str, size: Tuple[int, int]) -> np.ndarray:
        """Рендерит текстовый блок на изображении."""
        w, h = size
        img = Image.new('RGB', (w, h), color=self.middle_bg_rgb)
        draw = ImageDraw.Draw(img)

        font_size = 80
        font = self._load_font(self.middle_font_path, font_size)
        max_width = int(w * 0.9)
        max_height = int(h * 0.85)
        line_spacing = 12
        padding_y = (h - max_height) // 2

        while font_size > 20:
            lines = _wrap_text(draw, text, font, max_width)
            if not lines:
                break
            
            line_heights = [draw.textbbox((0, 0), L, font=font)[3] for L in lines]
            total_height = sum(line_heights) + (len(lines) - 1) * line_spacing
            
            if total_height <= max_height:
                break
            font_size -= 2
            font = self._load_font(self.middle_font_path, font_size)
        
        y = padding_y + (max_height - total_height) // 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2]
            x = (w - line_w) // 2
            
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 128)) # Shadow
            draw.text((x, y), line, font=font, fill=(255, 255, 255)) # Text
            y += line_heights[i] + line_spacing
            
        return np.array(img)

    def _render_footer_image(self, left_text: str, right_text: str, size: Tuple[int, int]) -> np.ndarray:
        """Рендерит футер с датой и источником."""
        w, h = size
        img = Image.new('RGB', (w, h), color=self.footer_bg_rgb)
        draw = ImageDraw.Draw(img)
        font = self._load_font(self.footer_font_path, 36)

        draw.text((int(w * 0.05), int(h * 0.25)), left_text, font=font, fill=(255, 255, 255))
        
        right_bbox = draw.textbbox((0, 0), right_text, font=font)
        rx = w - right_bbox[2] - int(w * 0.05)
        draw.text((rx, int(h * 0.25)), right_text, font=font, fill=(255, 255, 255))
        
        return np.array(img)

    def _render_smart_footer_image(self, left_text: str, news_data: Dict, size: Tuple[int, int]) -> np.ndarray:
        """Рендерит умный футер с логотипом источника и аватаром автора (для Twitter)."""
        w, h = size
        img = Image.new('RGB', (w, h), color=self.footer_bg_rgb)
        draw = ImageDraw.Draw(img)
        font = self._load_font(self.footer_font_path, 32)  # Немного уменьшили шрифт для лучшего размещения
        
        url = news_data.get('url', '')
        
        # Получаем информацию об источнике
        source_info = self._get_source_info(url)
        source_name = source_info['name']
        logo_path = source_info['logo_path']
        
        # Отступы
        padding = int(w * 0.05)
        
        # Рисуем дату слева - центрируем по вертикали
        date_bbox = draw.textbbox((0, 0), left_text, font=font)
        date_h = date_bbox[3] - date_bbox[1]
        date_y = (h - date_h) // 2  # Центрируем по вертикали
        draw.text((padding, date_y), left_text, font=font, fill=(255, 255, 255))
        
        # Проверяем, является ли источником Twitter/X для особой обработки
        is_twitter = any(domain in url.lower() for domain in ['twitter.com', 'x.com'])
        
        if is_twitter:
            # Специальная обработка для Twitter: дата, аватар автора, никнейм, логотип X
            self._render_twitter_footer_elements(img, draw, font, news_data, w, h, padding)
        else:
            # Центральная подпись источника (для улучшения читаемости бренда) - только для НЕ-Twitter источников
            try:
                center_font = self._load_font(self.footer_font_path, 30)
                center_text = source_name.upper()

                # Ограничиваем ширину центральной подписи (оставляя поля слева/справа под дату и логотип)
                max_center_width = int(w * 0.5)
                text_w, text_h = draw.textbbox((0, 0), center_text, font=center_font)[2:4]

                # Функция усечения текста с троеточием, чтобы влезал
                def _fit_text(text: str) -> str:
                    if draw.textbbox((0, 0), text, font=center_font)[2] <= max_center_width:
                        return text
                    ellipsis = '…'
                    for cut in range(len(text) - 1, 0, -1):
                        candidate = text[:cut].rstrip() + ellipsis
                        if draw.textbbox((0, 0), candidate, font=center_font)[2] <= max_center_width:
                            return candidate
                    return ellipsis

                center_text = _fit_text(center_text)

                # Лёгкая тень для контраста
                cx = (w - draw.textbbox((0, 0), center_text, font=center_font)[2]) // 2
                cy = (h - draw.textbbox((0, 0), center_text, font=center_font)[3]) // 2
                shadow_offset = 2
                draw.text((cx + shadow_offset, cy + shadow_offset), center_text, font=center_font, fill=(0, 0, 0))
                draw.text((cx, cy), center_text, font=center_font, fill=(230, 230, 230))
            except Exception as _e:
                pass
            
            # Стандартная обработка для других источников
            self._render_standard_footer_elements(img, draw, font, source_name, logo_path, w, h, padding)
        
        return np.array(img)
    
    def _render_twitter_footer_elements(self, img: Image.Image, draw: ImageDraw.ImageDraw, 
                                      font: ImageFont.ImageFont, news_data: Dict, 
                                      w: int, h: int, padding: int):
        """Рендерит элементы футера для Twitter постов."""
        # Получаем данные автора
        username = news_data.get('username', '')
        url = news_data.get('url', '')
        
        if not username and url:
            # Извлекаем username из URL если не передан напрямую
            import re
            username_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)', url)
            if username_match:
                username = username_match.group(1)
        
        # Позиции элементов (справа налево)
        current_x = w - padding
        
        # 1. Логотип X (самый правый)
        x_logo_path = Path(self.logos_dir) / 'X.png'
        if x_logo_path.exists():
            try:
                x_logo = Image.open(x_logo_path).convert('RGBA')
                max_logo_size = int(h * 0.6)
                logo_scale = min(max_logo_size / x_logo.height, max_logo_size / x_logo.width)
                new_w = int(x_logo.width * logo_scale)
                new_h = int(x_logo.height * logo_scale)
                x_logo = x_logo.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                logo_x = current_x - new_w
                logo_y = (h - new_h) // 2
                
                if x_logo.mode == 'RGBA':
                    img.paste(x_logo, (logo_x, logo_y), x_logo)
                else:
                    img.paste(x_logo, (logo_x, logo_y))
                
                current_x = logo_x - padding // 2
                logger.info("📱 Добавлен логотип X")
                
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить логотип X: {e}")
        
        # 2. Никнейм (справа от аватара) - центрируем по вертикали
        if username:
            nickname_text = f"@{username}" if not username.startswith('@') else username
            nickname_bbox = draw.textbbox((0, 0), nickname_text, font=font)
            nickname_w = nickname_bbox[2] - nickname_bbox[0]
            nickname_h = nickname_bbox[3] - nickname_bbox[1]
            
            nickname_x = current_x - nickname_w
            nickname_y = (h - nickname_h) // 2  # Центрируем по вертикали
            
            draw.text((nickname_x, nickname_y), nickname_text, font=font, fill=(255, 255, 255))
            current_x = nickname_x - padding // 2
            
            logger.info(f"👤 Добавлен никнейм: {nickname_text}")
        
        # 3. Аватар автора (левее никнейма) - уже центрирован
        if username:
            # Пробуем разные варианты имен файлов аватарок
            avatar_paths = [
                Path(self.logos_dir) / f'avatar_{username}.png',  # Новый формат от Twitter движка
                Path(self.logos_dir) / f'twitter_{username}.png',  # Старый формат
                Path(self.logos_dir) / f'avatar_{username.lstrip("@")}.png'  # Без @
            ]
            
            avatar_path = None
            for path in avatar_paths:
                if path.exists():
                    avatar_path = path
                    break
            
            if avatar_path and avatar_path.exists():
                logger.info(f"🖼️ Найден аватар: {avatar_path}")
                try:
                    avatar = Image.open(avatar_path).convert('RGBA')
                    avatar_size = int(h * 0.7)  # Аватар занимает 70% высоты футера
                    avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                    
                    # Делаем аватар круглым
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    
                    avatar_x = current_x - avatar_size
                    avatar_y = (h - avatar_size) // 2  # Уже центрирован
                    
                    # Создаем круглый аватар
                    output = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
                    output.paste(avatar, (0, 0))
                    output.putalpha(mask)
                    
                    img.paste(output, (avatar_x, avatar_y), output)
                    current_x = avatar_x - padding // 2
                    
                    logger.info(f"🖼️ Добавлен аватар: {avatar_path.name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось загрузить аватар {avatar_path}: {e}")
            else:
                logger.warning(f"⚠️ Аватар для @{username} не найден. Проверенные пути: {avatar_paths}")
    
    def _render_standard_footer_elements(self, img: Image.Image, draw: ImageDraw.ImageDraw,
                                       font: ImageFont.ImageFont, source_name: str, logo_path: str,
                                       w: int, h: int, padding: int):
        """Рендерит стандартные элементы футера для обычных источников."""
        print(f"🔍 DEBUG: _render_standard_footer_elements - source_name: '{source_name}', logo_path: '{logo_path}'")
        # Если есть логотип, добавляем его справа
        if logo_path and Path(logo_path).exists():
            try:
                # Загружаем и масштабируем логотип
                logo_img = Image.open(logo_path).convert('RGBA')
                
                # Определяем размер логотипа (максимум 60% высоты футера)
                max_logo_height = int(h * 0.6)
                logo_scale = min(max_logo_height / logo_img.height, max_logo_height / logo_img.width)
                
                new_logo_w = int(logo_img.width * logo_scale)
                new_logo_h = int(logo_img.height * logo_scale)
                
                logo_img = logo_img.resize((new_logo_w, new_logo_h), Image.Resampling.LANCZOS)
                
                # Позиционируем логотип справа
                logo_x = w - new_logo_w - padding
                logo_y = (h - new_logo_h) // 2

                # Подложка с мягкими углами для повышения контраста логотипа
                try:
                    bg_pad = max(4, int(min(new_logo_w, new_logo_h) * 0.15))
                    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    from PIL import ImageDraw as _ImageDraw
                    odraw = _ImageDraw.Draw(overlay)
                    rect = (logo_x - bg_pad, logo_y - bg_pad, logo_x + new_logo_w + bg_pad, logo_y + new_logo_h + bg_pad)
                    odraw.rounded_rectangle(rect, radius=int(bg_pad*0.8), fill=(255, 255, 255, 42))  # светлая полупрозрачная
                    # Небольшая тень
                    odraw.rounded_rectangle((rect[0]+2, rect[1]+2, rect[2]+2, rect[3]+2), radius=int(bg_pad*0.8), outline=None, fill=(0,0,0,10))
                    img_alpha = img.convert('RGBA')
                    img_alpha.alpha_composite(overlay)
                    img.paste(img_alpha.convert('RGB'))
                except Exception as _e:
                    pass
                
                # Создаём маску для правильного наложения PNG с прозрачностью
                if logo_img.mode == 'RGBA':
                    img.paste(logo_img, (logo_x, logo_y), logo_img)
                else:
                    img.paste(logo_img, (logo_x, logo_y))
                    
                logger.info(f"📰 Добавлен логотип {source_name}: {Path(logo_path).name}")
                
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить логотип {logo_path}: {e}")
                # Если логотип не загрузился, рисуем текст - центрируем по вертикали
                right_bbox = draw.textbbox((0, 0), source_name, font=font)
                text_h = right_bbox[3] - right_bbox[1]
                rx = w - right_bbox[2] - padding
                ry = (h - text_h) // 2  # Центрируем по вертикали
                draw.text((rx, ry), source_name, font=font, fill=(255, 255, 255))
        else:
            # Если логотипа нет, рисуем название источника текстом - центрируем по вертикали
            right_bbox = draw.textbbox((0, 0), source_name, font=font)
            text_h = right_bbox[3] - right_bbox[1]
            rx = w - right_bbox[2] - padding
            ry = (h - text_h) // 2  # Центрируем по вертикали
            draw.text((rx, ry), source_name, font=font, fill=(255, 255, 255))
    
    def _extract_source_name(self, url: str) -> str:
        """Извлекает имя источника из URL (упрощенная версия)."""
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.split('.')[0].upper()
        except Exception:
            return "NEWS"

    def _get_source_info(self, url: str) -> Dict[str, str]:
        """Получает информацию об источнике: название, логотип."""
        from urllib.parse import urlparse
        
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Ищем соответствие в конфигурации источников
            print(f"🔍 DEBUG: _get_source_info - domain: '{domain}', news_sources: {list(self.news_sources.keys())}")
            for source_key, source_config in self.news_sources.items():
                print(f"🔍 DEBUG: Проверяем {source_key}: domains={source_config.get('domains', [])}")
                if domain in source_config.get('domains', []):
                    logo_path = Path(self.logos_dir) / source_config.get('logo_file', '')
                    
                    # Если логотип существует, используем его
                    if logo_path.exists():
                        return {
                            'name': source_config.get('display_name', source_key.upper()),
                            'logo_path': str(logo_path)
                        }
                    
                    # Если логотипа нет, пробуем скачать автоматически
                    if self.logo_manager:
                        logger.info(f"🎨 Пробуем скачать логотип для {source_key} из {url}")
                        downloaded_logo = self.logo_manager.get_logo_path(url, source_config)
                        if downloaded_logo:
                            logger.info(f"✅ Логотип скачан: {downloaded_logo}")
                            return {
                                'name': source_config.get('display_name', source_key.upper()),
                                'logo_path': downloaded_logo
                            }
                        else:
                            logger.warning(f"❌ Не удалось скачать логотип для {source_key}")
                    
                    # Возвращаем без логотипа
                    return {
                        'name': source_config.get('display_name', source_key.upper()),
                        'logo_path': ''
                    }
            
            # Если источник не найден в конфигурации, пробуем автоматическое скачивание
            if self.logo_manager:
                downloaded_logo = self.logo_manager.get_logo_path(url, {})
                if downloaded_logo:
                    return {
                        'name': domain.split('.')[0].upper(),
                        'logo_path': downloaded_logo
                    }
            
            # Если ничего не помогло, возвращаем стандартную информацию
            return {
                'name': domain.split('.')[0].upper(),
                'logo_path': ''
            }
            
        except Exception as e:
            logger.warning(f"Ошибка определения источника для {url}: {e}")
            return {'name': 'NEWS', 'logo_path': ''}

    def create_news_short_video(self, news_data: Dict, output_path: str) -> Optional[str]:
        """
        Создает видео-шортс на основе данных новости, используя MoviePy.
        """
        try:
            logger.info(f"Начинаем создание видео: {output_path}")
            
            # 1. Разметка областей
            header_h = int(self.height * self.header_ratio)
            title_h = int(self.height * self.title_ratio)
            middle_h = int(self.height * self.middle_ratio)
            footer_h = self.height - header_h - title_h - middle_h

            # 2. Создание клипа для шапки
            media_path = news_data.get('local_video_path') or news_data.get('local_image_path')
            
            # Используем полную ширину видео для шапки
            header_clip = self._make_header_clip(media_path, (self.width, header_h))

            # 3. Создание клипа с заголовком
            news_title = news_data.get('title', 'Breaking News')
            title_img = self._render_title_image(news_title, (self.width, title_h))
            title_clip = ImageClip(title_img).with_duration(self.duration)

            # 4. Создание клипа с текстом
            short_text = news_data.get('summary', 'Новость дня')
            middle_img = self._render_text_image(short_text, (self.width, middle_h))
            middle_clip = ImageClip(middle_img).with_duration(self.duration)
            
            # 5. Создание умного футера с логотипом и аватаром автора
            date_str = news_data.get('publish_date', datetime.now().strftime('%d.%m.%Y'))
            footer_img = self._render_smart_footer_image(date_str, news_data, (self.width, footer_h))
            footer_clip = ImageClip(footer_img).with_duration(self.duration)

            # 6. Сборка всех клипов
            # Шапка заполняет всю ширину и полный размер видео, остальные клипы накладываем поверх
            final_clip = CompositeVideoClip([
                header_clip,  # Фон (полный размер)
                title_clip.with_position((0, header_h)),
                middle_clip.with_position((0, header_h + title_h)),
                footer_clip.with_position((0, header_h + title_h + middle_h)),
            ], size=(self.width, self.height))

            # 7. Добавление аудио
            music_dir = self.paths_config.get('music_dir', 'resources/music')
            music_files = [f for f in Path(music_dir).glob('*.mp3')]
            if music_files:
                import random
                music_path = random.choice(music_files)
                try:
                    audio_clip = AudioFileClip(str(music_path))
                    if audio_clip.duration >= self.duration:
                        audio = audio_clip.with_duration(self.duration)
                    else:
                        # Повторяем аудио несколько раз, чтобы покрыть нужную длительность
                        repeats = int(self.duration / audio_clip.duration) + 1
                        audio = concatenate_audioclips([audio_clip] * repeats)
                        audio = audio.with_duration(self.duration)
                    
                    final_clip = final_clip.with_audio(audio.with_volume_scaled(0.3)) # Делаем музыку тише
                    logger.info(f"🎵 Добавлена музыка: {music_path.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить аудио: {e}")
            else:
                logger.warning("⚠️ Музыкальные файлы не найдены.")

            # 7. Запись видео
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Добавляем клипы в список для отслеживания
            self._active_clips.extend([header_clip, title_clip, middle_clip, footer_clip, final_clip])
            if 'audio' in locals():
                self._active_clips.append(audio)
            
            try:
                final_clip.write_videofile(
                    output_path,
                    fps=self.fps,
                    codec='libx264',
                    audio_codec='aac',
                    preset='medium',
                    threads=os.cpu_count() or 2,
                    logger='bar'
                )
                logger.info(f"✅ Видео успешно сохранено: {output_path}")
                return output_path
            finally:
                # Принудительно закрываем все клипы после записи
                self._close_all_clips()

        except Exception as e:
            logger.error(f"❌ Критическая ошибка при создании видео: {e}", exc_info=True)
            return None

    def _close_all_clips(self):
        """Закрывает все активные клипы и освобождает ресурсы."""
        try:
            for clip in self._active_clips:
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                    elif hasattr(clip, 'reader') and hasattr(clip.reader, 'close'):
                        clip.reader.close()
                    elif hasattr(clip, 'audio') and hasattr(clip.audio, 'close'):
                        clip.audio.close()
                except Exception as e:
                    logger.debug(f"Ошибка закрытия клипа: {e}")
            
            self._active_clips.clear()
            
            # Принудительная сборка мусора
            import gc
            gc.collect()
            
        except Exception as e:
            logger.warning(f"Ошибка при закрытии клипов: {e}")

    def close(self):
        """Метод для совместимости с оркестратором."""
        self._close_all_clips()

    def __del__(self):
        """Деструктор для автоматического закрытия ресурсов."""
        try:
            self._close_all_clips()
        except Exception:
            pass


class SeleniumVideoExporter:
    """Класс для экспорта анимаций в видео (старый метод через Selenium)"""

    def __init__(self, video_config: Dict, paths_config: Dict):
        self.video_config = video_config
        self.paths_config = paths_config
        self.driver = None

        self._setup_selenium()

    def _setup_selenium(self):
        """Настройка Selenium WebDriver для headless режима"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"--window-size={self.video_config['width']},{self.video_config['height']}")
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            # Отключаем GCM для избежания ошибок регистрации
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации Selenium: {e}")
            raise

    def generate_html_from_template(self, animation_data: Dict, logo_path: Optional[str] = None) -> str:
        """Генерация HTML файла из шаблона с данными анимации"""

        template_path = os.path.join(
            self.paths_config['templates_dir'],
            'animation_template.html'
        )

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        js_data = {
            'header': animation_data.get('animation_content', {}).get('header', {}),
            'body': animation_data.get('animation_content', {}).get('body', {}),
            'footer': animation_data.get('animation_content', {}).get('footer', {}),
            'style': animation_data.get('animation_content', {}).get('style', {}),
            'logo_url': logo_path or ''
        }

        js_data_json = json.dumps(js_data, ensure_ascii=False, indent=2)
        html_content = template.replace('{{ANIMATION_DATA}}', js_data_json)
        return html_content

    def render_animation_to_video(self, animation_data: Dict, output_path: str,
                               logo_path: Optional[str] = None) -> str:
        """Рендеринг анимации в видео файл"""
        try:
            html_content = self.generate_html_from_template(animation_data, logo_path)
            temp_html_path = os.path.join(
                self.paths_config['temp_dir'],
                f"temp_animation_{int(time.time())}.html"
            )

            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Преобразуем относительный путь в абсолютный для file URI
            absolute_path = os.path.abspath(temp_html_path)
            file_url = Path(absolute_path).as_uri()
            self.driver.get(file_url)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "container"))
            )

            frames = self._capture_animation_frames()
            video_path = self._create_video_from_frames(frames, output_path)

            os.remove(temp_html_path)
            self._cleanup_temp_frames(output_path)

            logger.info(f"Видео успешно создано: {video_path}")
            return video_path
        except Exception as e:
            logger.error(f"Ошибка при рендеринге видео: {e}")
            raise

    def _capture_animation_frames(self) -> list:
        """Захват кадров анимации"""
        frames = []
        fps = self.video_config['fps']
        duration = self.video_config['duration_seconds']
        num_frames = int(duration * fps)

        for i in range(num_frames):
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
            if image.size != (self.video_config['width'], self.video_config['height']):
                image = image.resize((self.video_config['width'], self.video_config['height']))
            frames.append(image)
            time.sleep(1/fps)
        
        logger.info(f"Захвачено {len(frames)} кадров анимации")
        return frames

    def _create_video_from_frames(self, frames: list, output_path: str) -> str:
        """Создание видео файла из кадров"""
        height, width, _ = cv2.cvtColor(np.array(frames[0]), cv2.COLOR_RGB2BGR).shape
        # Используем кодек avc1 (H.264), он более совместим, чем mp4v
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        video_writer = cv2.VideoWriter(output_path, fourcc, self.video_config['fps'], (width, height))

        for frame in frames:
            video_writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))

        video_writer.release()
        return output_path
    
    def _cleanup_temp_frames(self, video_path: str):
        pass

    def export_animation(self, animation_data: Dict, news_id: int,
                       logo_path: Optional[str] = None) -> Optional[str]:
        """Экспорт анимации в видео файл"""
        try:
            output_dir = self.paths_config['outputs_dir']
            output_filename = f"short_{news_id}_{int(time.time())}.mp4"
            output_path = os.path.join(output_dir, output_filename)

            video_path = self.render_animation_to_video(
                animation_data,
                output_path,
                logo_path
            )

            logger.info(f"Анимация успешно экспортирована: {video_path}")
            return video_path
        except Exception as e:
            logger.error(f"Ошибка экспорта анимации для новости {news_id}: {e}")
            return None

    def close(self):
        """Закрытие WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver закрыт")

    def __del__(self):
        """Деструктор для автоматического закрытия"""
        self.close()

    def create_news_short_video(self, news_data: Dict, output_path: str) -> str:
        """
        Создает видео news short на основе нового шаблона
        
        Args:
            news_data: Данные новости
            output_path: Путь для сохранения видео
            
        Returns:
            str: Путь к созданному видео или None при ошибке
        """
        try:
            # Создаем HTML файл для news short
            temp_html_path = self._create_news_short_html(news_data)
            if not temp_html_path:
                return None
            
            # Конвертируем в абсолютный URI для браузера
            temp_html_uri = Path(os.path.abspath(temp_html_path)).as_uri()
            
            # Загружаем HTML в браузер
            self.driver.get(temp_html_uri)
            
            # Ждем загрузки страницы и ресурсов
            time.sleep(3)
            
            # Записываем анимацию в видео (6 секунд, 30 FPS)
            frames = self._capture_animation_frames()
            video_path = self._create_video_from_frames(frames, output_path)
            
            # Очищаем временный файл
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)
            
            logger.info(f"News short видео создано: {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании news short: {e}")
            return None

    def _create_news_short_html(self, news_data: Dict) -> str:
        """
        Создает HTML файл для news short на основе нового шаблона
        
        Args:
            news_data: Данные новости
            
        Returns:
            str: Путь к созданному HTML файлу
        """
        try:
            # Читаем шаблон
            template_path = "templates/news_short_template.html"
            if not os.path.exists(template_path):
                logger.error(f"Шаблон не найден: {template_path}")
                return None
                
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Определяем источник и логотип
            source_name = self._extract_source_name(news_data.get('url', ''))
            print(f"🔍 DEBUG: URL: '{news_data.get('url', '')}', извлеченный источник: '{source_name}'")
            print(f"🔍 DEBUG: news_data source: '{news_data.get('source', '')}'")
            
            # Для Twitter используем logo_manager для скачивания аватарки
            if news_data.get('source', '').upper() == 'TWITTER' and news_data.get('username'):
                source_logo_path = self._get_twitter_avatar_path(news_data.get('username'), news_data.get('url', ''))
            else:
                source_logo_path = self._get_source_logo_path(source_name)
            
            # Получаем изображение новости
            news_image_path = self._get_news_image(news_data)
            
            # Получаем видео новости (если есть)
            news_video_path = self._get_news_video(news_data)
            
            # Получаем фоновую музыку
            background_music_path = self._get_background_music()
            
            # Подготавливаем данные для подстановки
            replacements = {
                '{{NEWS_IMAGE}}': news_image_path or '../resources/default_backgrounds/news_default.jpg',
                '{{NEWS_VIDEO}}': news_video_path or '',
                '{{SOURCE_LOGO}}': source_logo_path,
                '{{TWITTER_AVATAR}}': self._get_twitter_avatar_path(news_data) if news_data.get('source', '').upper() == 'TWITTER' else '',
                '{{SOURCE_NAME}}': source_name,  # Только название источника (например, "CNN")
                '{{NEWS_TITLE}}': (news_data.get('title', 'Заголовок новости')[:80] + ('...' if len(news_data.get('title', '')) > 80 else '')),
                '{{NEWS_BRIEF}}': news_data.get('summary', news_data.get('description', ''))[:500] + ('...' if len(news_data.get('summary', news_data.get('description', ''))) > 500 else ''),
                '{{PUBLISH_DATE}}': news_data.get('publish_date', 'Сегодня'),
                '{{PUBLISH_TIME}}': news_data.get('publish_time', 'Сейчас'),
                '{{BACKGROUND_MUSIC}}': background_music_path
            }
            
            # Выполняем подстановки
            html_content = template_content
            for placeholder, value in replacements.items():
                html_content = html_content.replace(placeholder, str(value))
            
            # Создаем временный HTML файл
            temp_html_path = os.path.join(
                self.paths_config.get('temp_dir', 'temp'),
                f"news_short_{int(time.time())}.html"
            )
            
            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return temp_html_path
            
        except Exception as e:
            logger.error(f"Ошибка создания HTML: {e}")
            return None

    def _extract_source_name(self, url: str) -> str:
        """Извлекает имя источника из URL"""
        if 'cnn.com' in url.lower():
            return 'CNN'
        elif 'foxnews.com' in url.lower():
            return 'FoxNews'
        elif 'nytimes.com' in url.lower():
            return 'NYTimes'
        elif 'washingtonpost.com' in url.lower():
            return 'WashingtonPost'
        elif 'reuters.com' in url.lower():
            return 'Reuters'
        elif 'ap.org' in url.lower() or 'apnews.com' in url.lower():
            return 'AssociatedPress'
        elif 'wsj.com' in url.lower():
            return 'WSJ'
        elif 'cnbc.com' in url.lower():
            return 'CNBC'
        elif 'aljazeera.com' in url.lower():
            return 'ALJAZEERA'
        elif 'abc' in url.lower():
            return 'ABC'
        elif 'nbcnews.com' in url.lower():
            return 'NBCNEWS'
        else:
            return 'News'

    def _get_twitter_avatar_path(self, username: str, url: str) -> str:
        """Получает путь к аватарке Twitter пользователя"""
        try:
            logger.info(f"🐦 Попытка скачать аватарку для @{username} из {url}")
            if self.logo_manager:
                # Используем logo_manager для скачивания аватарки
                avatar_path = self.logo_manager.get_logo_path(url, {})
                logger.info(f"🐦 LogoManager вернул: {avatar_path}")
                if avatar_path and os.path.exists(avatar_path):
                    logger.info(f"✅ Аватарка найдена: {avatar_path}")
                    return f"../{avatar_path}"
                else:
                    logger.warning(f"❌ Аватарка не найдена или не существует: {avatar_path}")
            else:
                logger.warning("❌ LogoManager не инициализирован")
            
            # Если не удалось скачать, используем дефолтный логотип X
            logger.info("🔄 Используем дефолтный логотип X")
            return "../media/X_logo.png"
        except Exception as e:
            logger.warning(f"Ошибка получения аватарки Twitter для @{username}: {e}")
            return "../media/X_logo.png"

    def _get_twitter_avatar_path(self, news_data: Dict[str, Any]) -> str:
        """Получает путь к аватару Twitter пользователя"""
        try:
            username = news_data.get('username', '').lstrip('@')
            if not username:
                return ''
            
            # Ищем аватар в папке logos
            logos_avatar = f"resources/logos/avatar_{username}.png"
            if os.path.exists(logos_avatar):
                return logos_avatar
            
            # Если не найден, возвращаем пустую строку
            return ''
            
        except Exception as e:
            logger.warning(f"Ошибка получения пути к аватару Twitter: {e}")
            return ''
    
    def _get_source_logo_path(self, source_name: str) -> str:
        """Получает путь к логотипу источника"""
        logo_files = {
            'CNN': 'media/CNN.jpg',
            'FoxNews': 'media/FoxNews.png',
            'NYTimes': 'media/NYTimes.png',
            'WashingtonPost': 'media/WashingtonPost.jpg',
            'Reuters': 'media/Reuters.jpg',
            'AssociatedPress': 'media/AssociatedPress.jpg',
            'WSJ': 'media/WSJ.jpg',
            'CNBC': 'media/CNBC.png',
            'ALJAZEERA': 'media/ALJAZEERA.jpg',
            'ABC': 'media/ABC.jpg',
            'NBC': 'media/NBCNews.png',
            'NBCNEWS': 'media/NBCNews.png'
        }
        
        logo_path = logo_files.get(source_name, 'media/CNN.jpg')  # CNN как дефолт
        logger.info(f"🔍 DEBUG: Источник: '{source_name}', логотип: '{logo_path}'")
        
        # Проверяем, существует ли файл
        if os.path.exists(logo_path):
            return f"../{logo_path}"
        else:
            logger.warning(f"Логотип не найден: {logo_path}")
            return "../media/CNN.jpg"  # Фоллбэк

    def _get_news_image(self, news_data: Dict) -> str:
        """Получает изображение новости"""
        # Проверяем, есть ли локальный путь к изображению
        if 'local_image_path' in news_data and news_data['local_image_path']:
            local_path = news_data['local_image_path']
            if os.path.exists(local_path):
                return f"../{local_path}"
        
        # Проверяем старый формат
        if 'image_path' in news_data and os.path.exists(news_data['image_path']):
            return f"../{news_data['image_path']}"
        
        # Если есть URL изображения, попробуем использовать медиа-менеджер
        if 'images' in news_data and news_data['images']:
            try:
                from scripts.media_manager import MediaManager
                # Создаем конфигурацию для MediaManager из имеющихся данных
                config_path = 'config/config.yaml'
                media_manager = MediaManager(config_path)
                media_result = media_manager.process_news_media(news_data)
                
                if media_result.get('local_image_path'):
                    return f"../{media_result['local_image_path']}"
            except Exception as e:
                logger.warning(f"Не удалось обработать изображение через MediaManager: {e}")
        
        # Возвращаем дефолтное изображение
        return "../resources/default_backgrounds/news_default.jpg"

    def _get_news_video(self, news_data: Dict) -> str:
        """Получает видео новости"""
        # Проверяем, есть ли локальный путь к видео
        if 'local_video_path' in news_data and news_data['local_video_path']:
            local_path = news_data['local_video_path']
            if os.path.exists(local_path):
                return f"../{local_path}"
        
        # Проверяем, есть ли URL видео в данных
        if 'video_url' in news_data and news_data['video_url']:
            # В будущем здесь можно добавить загрузку видео
            # Пока возвращаем пустую строку
            pass
        
        # Если видео нет, возвращаем пустую строку
        return ""

    def _get_background_music(self) -> str:
        """Получает путь к фоновой музыке"""
        try:
            from scripts.media_manager import MediaManager
            config_path = 'config/config.yaml'
            media_manager = MediaManager(config_path)
            music_path = media_manager.get_background_music()
            
            if music_path:
                return f"../{music_path}"
            else:
                return ""
                
        except Exception as e:
            logger.warning(f"Ошибка получения фоновой музыки через MediaManager: {e}")
            
            # Fallback к старому методу
            music_dir = "resources/music"
            
            if not os.path.exists(music_dir):
                logger.info(f"Папка с музыкой не найдена: {music_dir}")
                return ""
                
            audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
            
            for file in os.listdir(music_dir):
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    music_path = os.path.join(music_dir, file)
                    logger.info(f"Найдена фоновая музыка: {file}")
                    return f"../{music_path}"
                    
            logger.info("Фоновая музыка не найдена в папке resources/music")
            return ""

    def _export_frames_to_video_fallback(self, frames: List[np.ndarray], output_path: str, fps: int, music_path: Optional[str] = None):
        """Резервный метод экспорта кадров в видео с помощью OpenCV и FFMPEG для аудио"""
        if not frames:
            logger.error("Нет кадров для экспорта в видео.")
            return

        height, width, layers = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        # Если есть музыка, сначала создаем видео без звука
        silent_video_path = output_path
        if music_path and os.path.exists(music_path.replace('../', '')):
            silent_video_path = os.path.join(os.path.dirname(output_path), f"silent_{os.path.basename(output_path)}")

        video = cv2.VideoWriter(silent_video_path, fourcc, fps, (width, height))
        for frame in frames:
            video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        video.release()

        logger.info(f"Видео без звука создано: {silent_video_path}")

        # Добавляем аудио дорожку с помощью FFMPEG
        actual_music_path = music_path.replace('../', '')
        if music_path and os.path.exists(actual_music_path):
            logger.info(f"🎵 Добавляем аудиодорожку '{actual_music_path}' с помощью FFMPEG...")
            command = [
                'ffmpeg',
                '-y',  # Перезаписывать выходной файл без запроса
                '-i', silent_video_path,
                '-i', actual_music_path,
                '-c:v', 'copy',  # Копировать видеопоток без перекодирования
                '-c:a', 'aac',   # Кодировать аудио в AAC
                '-shortest',     # Длительность видео будет равна самому короткому потоку
                '-loglevel', 'error', # Скрыть лишние логи
                output_path
            ]
            
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                logger.info(f"✅ Аудиодорожка успешно добавлена в '{output_path}'")
                # Удаляем временное видео без звука
                os.remove(silent_video_path)
            except FileNotFoundError:
                logger.error("❌ FFMPEG не найден. Убедитесь, что он установлен и доступен в PATH.")
                # Если FFMPEG нет, оставляем видео без звука
                if silent_video_path != output_path:
                    os.rename(silent_video_path, output_path)
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Ошибка FFMPEG при добавлении аудио: {e.stderr}")
                # Если FFMPEG выдал ошибку, оставляем видео без звука
                if silent_video_path != output_path:
                    os.rename(silent_video_path, output_path)
        else:
            if not music_path:
                logger.info("🎶 Музыка не выбрана, видео будет без звука.")
            else:
                logger.warning(f"⚠️ Файл музыки не найден: '{actual_music_path}', видео будет без звука.")
        
    def create_short_from_html(self, news_data: Dict) -> Optional[str]:
        """Создает видео-шорт из HTML-шаблона"""
        try:
            temp_html_path = self._create_news_short_html(news_data)
            self.driver.get(f"file:///{os.path.abspath(temp_html_path)}")
            
            # Ждем инициализации GSAP и медиа
            time.sleep(2)

            frames = []
            duration_seconds = self.video_config.get('duration_seconds', 5)
            fps = self.video_config.get('fps', 30)
            num_frames = duration_seconds * fps

            for i in range(num_frames):
                screenshot = self.driver.get_screenshot_as_png()
                img = Image.open(io.BytesIO(screenshot))
                frames.append(np.array(img))
                time.sleep(1 / fps)
            
            logger.info(f"Захвачено {len(frames)} кадров анимации")
            
            output_filename = f"short_{news_data.get('id', 'temp')}_{int(time.time())}.mp4"
            output_path = os.path.join(self.paths_config.get('output_dir', 'outputs'), output_filename)

            # Получаем музыку для передачи в экспортер
            music_path = self._get_background_music()

            # Используем MoviePy если доступен
            logger.info("Используем MoviePy для создания видео (логика не реализована).")
            self._export_frames_to_video_fallback(frames, output_path, fps, music_path)

            os.remove(temp_html_path)
            logger.info(f"News short видео создано: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка при создании видео из HTML: {e}")
            return None


def main():
    """Тестовая функция"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

    try:
        # Загрузка конфигурации
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Тестовые данные
        test_animation_data = {
            'animation_content': {
                'header': {
                    'text': 'BBC News',
                    'animation': 'fadeIn',
                    'duration': 1.5
                },
                'body': {
                    'text': 'Президент объявил о новых реформах в экономике страны',
                    'animation': 'typewriter',
                    'duration': 2.5
                },
                'footer': {
                    'date': '30.08.2025',
                    'animation': 'slideUp',
                    'duration': 1.0
                },
                'style': {
                    'theme': 'dark',
                    'accent_color': '#FF6B35'
                }
            }
        }

        # Попытка использовать основной экспортер
        try:
            exporter = VideoExporter(config['video'], config['paths'])
            output_path = os.path.join(
                os.path.dirname(__file__), '..', 'outputs', 'test_video.mp4'
            )
            # Для теста нужно передать news_data
            test_news_data = {
                'summary': 'Это тестовый текст новости для проверки генерации видео. Он должен быть достаточно длинным, чтобы переноситься на несколько строк.',
                'local_image_path': 'resources/media/news/Test_Trump_Tariffs_N_086fd1c7.jpg',
                'url': 'https://www.bcs.com/test-news',
                'publish_date': '13.09.2025'
            }
            result = exporter.create_news_short_video(test_news_data, output_path)
            print(f"Видео создано: {result}")

        except Exception as e:
            print(f"Основной экспортер не доступен: {e}")
            print("Используем резервный экспортер...")
            # Тут можно будет протестировать SeleniumVideoExporter если нужно
            # fallback_exporter = SeleniumVideoExporter(config['video'], config['paths'])
            # ...

    except Exception as e:
        logger.error(f"Ошибка в тестовой функции: {e}", exc_info=True)


if __name__ == "__main__":
    main()
