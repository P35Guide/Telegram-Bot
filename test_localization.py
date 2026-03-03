#!/usr/bin/env python3
"""
Тест системи локалізації / Localization System Test
"""

import sys
import os

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.utils.localization import i18n


def test_language_detection():
    """Тестування автоматичного визначення мови"""
    print("=== Language Detection Test ===\n")
    
    test_cases = [
        (1, 'en', 'en', 'English user'),
        (2, 'uk', 'uk', 'Ukrainian user'),
        (3, 'ua', 'uk', 'Ukrainian user (ua code)'),
        (4, 'ru', 'en', 'Russian user → English'),
        (5, 'be', 'en', 'Belarusian user → English'),
        (6, 'de', 'de', 'German user'),
        (7, 'fr', 'fr', 'French user'),
        (8, 'xx', 'en', 'Unknown language → English (default)'),
    ]
    
    for user_id, telegram_lang, expected_lang, description in test_cases:
        detected_lang = i18n.get_user_language(user_id, telegram_lang)
        status = "✓" if detected_lang == expected_lang else "✗"
        print(f"{status} User {user_id} ({description})")
        print(f"  Telegram: {telegram_lang} → Detected: {detected_lang} (Expected: {expected_lang})")
        
        # Тестуємо отримання перекладу
        welcome_msg = i18n.get(user_id, 'welcome')
        print(f"  Welcome message: {welcome_msg[:50]}...")
        print()


def test_manual_language_change():
    """Тестування ручної зміни мови"""
    print("\n=== Manual Language Change Test ===\n")
    
    user_id = 100
    
    # Спробуємо різні коди
    test_codes = ['en', 'uk', 'ua', 'de', 'fr', 'invalid']
    
    for code in test_codes:
        success = i18n.set_user_language(user_id, code)
        current_lang = i18n.get_user_language(user_id)
        status = "✓" if success else "✗"
        
        print(f"{status} Set language to '{code}': Success={success}, Current={current_lang}")
        
        # Показуємо переклад
        if success:
            settings_text = i18n.get(user_id, 'settings')
            print(f"  Settings text: {settings_text}")
        print()


def test_language_hints():
    """Тестування підказок з кодами мов"""
    print("\n=== Language Hints Test ===\n")
    
    hints = i18n.get_language_hints()
    print(hints)
    print()


def test_translation_with_params():
    """Тестування перекладів з параметрами"""
    print("\n=== Translation with Parameters Test ===\n")
    
    # Англійська
    user_id_en = 200
    i18n.set_user_language(user_id_en, 'en')
    city_en = i18n.get(user_id_en, 'city_found', city='London')
    print(f"EN: {city_en}")
    
    # Українська
    user_id_uk = 201
    i18n.set_user_language(user_id_uk, 'ua')  # Використовуємо 'ua'
    city_uk = i18n.get(user_id_uk, 'city_found', city='Київ')
    print(f"UK: {city_uk}")
    
    # Німецька
    user_id_de = 202
    i18n.set_user_language(user_id_de, 'de')
    city_de = i18n.get(user_id_de, 'city_found', city='Berlin')
    print(f"DE: {city_de}")
    print()


def test_available_languages():
    """Тестування списку доступних мов"""
    print("\n=== Available Languages Test ===\n")
    
    languages = i18n.get_available_languages()
    print("Available languages:")
    for code, name in languages.items():
        print(f"  {code:3} - {name}")
    print()


def main():
    """Запуск всіх тестів"""
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  Telegram Bot Localization System Test               ║")
    print("║  Тест системи локалізації Telegram бота              ║")
    print("╚═══════════════════════════════════════════════════════╝\n")
    
    try:
        test_language_detection()
        test_manual_language_change()
        test_language_hints()
        test_translation_with_params()
        test_available_languages()
        
        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("✓ Всі тести виконано успішно!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
