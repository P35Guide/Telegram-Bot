"""
Система багатомовності для Telegram бота.
Підтримує автоматичне визначення мови з Telegram та ручний вибір.
"""
import json
import os
from typing import Dict, Optional
from bot.utils.logger import logger


class Localization:
    """Клас для керування перекладами та мовами користувачів"""
    
    # Підтримувані мови (порядок відображення в меню)
    SUPPORTED_LANGUAGES = {
        'en': '🇬🇧 English',
        'uk': '🇺🇦 Українська',
        'de': '🇩🇪 Deutsch',
        'fr': '🇫🇷 Français',
        'es': '🇪🇸 Español',
        'it': '🇮🇹 Italiano',
        'pl': '🇵🇱 Polski',
        'pt': '🇵🇹 Português',
        'ja': '🇯🇵 日本語',
        'zh': '🇨🇳 中文',
    }
    
    # Коди мов з підказками
    LANGUAGE_CODES = {
        'ua': 'uk',  # ua -> uk (українська/ukrainian)
        'uk': 'uk',  # uk -> uk (українська)
        'en': 'en',  # en -> en (english)
        'de': 'de',  # de -> de (deutsch/german)
        'fr': 'fr',  # fr -> fr (français/french)
        'es': 'es',  # es -> es (español/spanish)
        'it': 'it',  # it -> it (italiano/italian)
        'pl': 'pl',  # pl -> pl (polski/polish)
        'pt': 'pt',  # pt -> pt (português/portuguese)
        'ja': 'ja',  # ja -> ja (japanese)
        'zh': 'zh',  # zh -> zh (chinese)
    }
    
    # Мапінг російської та білоруської мов на англійську
    LANGUAGE_MAPPING = {
        'ru': 'en',  # Російська -> Англійська
        'be': 'en',  # Білоруська -> Англійська
    }
    
    def __init__(self, locales_dir: str = 'locales'):
        """
        Ініціалізація системи локалізації
        
        Args:
            locales_dir: Директорія з JSON файлами перекладів
        """
        self.locales_dir = locales_dir
        self.translations: Dict[str, Dict] = {}
        self.user_languages: Dict[int, str] = {}
        self.default_lang = 'en'  # English за замовчуванням
        
        # Завантажуємо всі переклади
        self._load_all_translations()
    
    def _load_all_translations(self):
        """Завантаження всіх файлів перекладів з директорії"""
        if not os.path.exists(self.locales_dir):
            logger.warning(f"Директорія {self.locales_dir} не знайдена")
            return
        
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                lang_code = filename.replace('.json', '')
                filepath = os.path.join(self.locales_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                        logger.info(f"Завантажено переклад: {lang_code}")
                except Exception as e:
                    logger.error(f"Помилка завантаження {filepath}: {e}")
    
    def get_user_language(self, user_id: int, telegram_lang_code: Optional[str] = None) -> str:
        """
        Отримати мову користувача
        
        Args:
            user_id: ID користувача
            telegram_lang_code: Код мови з Telegram (user.language_code)
            
        Returns:
            Код мови (en, uk, de, тощо)
        """
        # Якщо мова вже збережена для користувача
        if user_id in self.user_languages:
            return self.user_languages[user_id]
        
        # Перевіряємо чи є мова в user_settings (завантажена з API)
        try:
            from bot.services.settings import user_settings
            if user_id in user_settings and "language" in user_settings[user_id]:
                saved_lang = user_settings[user_id]["language"]
                if saved_lang and saved_lang in self.SUPPORTED_LANGUAGES:
                    self.user_languages[user_id] = saved_lang
                    logger.info(f"Завантажено мову {saved_lang} з user_settings для user {user_id}")
                    return saved_lang
        except ImportError:
            pass
        
        # Якщо є мова з Telegram
        if telegram_lang_code:
            # Перевіряємо чи потрібно замапити (ru -> en, ua -> uk)
            mapped_lang = self.LANGUAGE_MAPPING.get(telegram_lang_code, telegram_lang_code)
            
            # Перевіряємо альтернативні коди (ua -> uk)
            normalized_lang = self.LANGUAGE_CODES.get(mapped_lang, mapped_lang)
            
            # Якщо мова підтримується
            if normalized_lang in self.SUPPORTED_LANGUAGES:
                self.user_languages[user_id] = normalized_lang
                logger.info(f"Встановлено мову {normalized_lang} для user {user_id} (з {telegram_lang_code})")
                return normalized_lang
        
        # За замовчуванням англійська
        self.user_languages[user_id] = self.default_lang
        logger.info(f"Встановлено мову за замовчуванням {self.default_lang} для user {user_id}")
        return self.default_lang
    
    def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """
        Встановити мову користу (en, uk, ua, de, тощо)
            
        Returns:
            True якщо мову встановлено успішно
        """
        # Нормалізуємо код мови (ua -> uk)
        normalized_code = self.LANGUAGE_CODES.get(lang_code.lower(), lang_code.lower())
        
        if normalized_code in self.SUPPORTED_LANGUAGES:
            self.user_languages[user_id] = normalized_code
            logger.info(f"Мову змінено на {normalized_code} для user {user_id} (з {lang_code})")
            return True
        
        logger.warning(f"Невідомий код мови {lang_code} для user {user_id}")
        if lang_code in self.SUPPORTED_LANGUAGES:
            self.user_languages[user_id] = lang_code
            logger.info(f"Мову змінено на {lang_code} для user {user_id}")
            return True
        return False
    
    def get(self, user_id: int, key: str, telegram_lang_code: Optional[str] = None, **kwargs) -> str:
        """
        Отримати переклад для користувача
        
        Args:
            user_id: ID користувача
            key: Ключ перекладу
            telegram_lang_code: Код мови з Telegram (опціонально)
            **kwargs: Параметри для форматування (name, count, тощо)
            
        Returns:
            Перекладений текст
        """
        lang = self.get_user_language(user_id, telegram_lang_code)
        text = self.translations.get(lang, {}).get(key)
        
        # Fallback на англійську, якщо не знайдено
        if text is None and lang != self.default_lang:
            text = self.translations.get(self.default_lang, {}).get(key)
        
        # Якщо і англійського немає, повертаємо ключ
        if text is None:
            logger.warning(f"Переклад не знайдено: {key} для мови {lang}")
            return key
        
        # Підстановка параметрів {name}, {count}, тощо
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Помилка форматування перекладу {key}: {e}")
        
        return text
    
    def get_translation(self, lang_code: str, key: str, **kwargs) -> str:
        """
        Отримати переклад безпосередньо за кодом мови (без user_id)
        
        Args:
            lang_code: Код мови (en, uk, de, тощо)
            key: Ключ перекладу
            **kwargs: Параметри для форматування
            
        Returns:
            Перекладений текст
        """
        text = self.translations.get(lang_code, {}).get(key)
        
        # Fallback на англійську, якщо не знайдено
        if text is None and lang_code != self.default_lang:
            text = self.translations.get(self.default_lang, {}).get(key)
        
        # Якщо і англійського немає, повертаємо ключ
        if text is None:
            logger.warning(f"Переклад не знайдено: {key} для мови {lang_code}")
            return key
        
        # Підстановка параметрів {name}, {count}, тощо
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Помилка форматування перекладу {key}: {e}")
        
        return text
    
    def get_language_hints(self) -> str:
        """Отримати підказки з кодами мов"""
        hints = []
        hints.append("Language codes / Коди мов:")
        hints.append("• en - English")
        hints.append("• ua / uk - Українська / Ukrainian")
        hints.append("• de - Deutsch / German")
        hints.append("• fr - Français / French")
        hints.append("• es - Español / Spanish")
        hints.append("• it - Italiano / Italian")
        hints.append("• pl - Polski / Polish")
        hints.append("• pt - Português / Portuguese")
        hints.append("• ja - 日本語 / Japanese")
        hints.append("• zh - 中文 / Chinese")
        return "\n".join(hints)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Отримати список доступних мов"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def reload_translations(self):
        """Перезавантажити всі переклади (корисно для оновлень без перезапуску)"""
        self.translations.clear()
        self._load_all_translations()


# Глобальний екземпляр localization
i18n = Localization()


def get_user_lang(user_id: int, telegram_lang_code: Optional[str] = None) -> str:
    """Швидкий доступ до мови користувача"""
    return i18n.get_user_language(user_id, telegram_lang_code)


def t(user_id: int, key: str, **kwargs) -> str:
    """Скорочена функція для отримання перекладу"""
    return i18n.get(user_id, key, **kwargs)
