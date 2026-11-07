# -*- coding: utf-8 -*-
import os
import sys
import random
import logging
from typing import List, Dict, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from places_data import PLACES, CATEGORY_NAMES, DISTANCE_GROUPS

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Токен берется из переменной окружения BOT_TOKEN или .env
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("BOT_TOKEN="):
                    TOKEN = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    break

if not TOKEN or TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("\n[!] ОШИБКА: Не указан токен бота в переменной BOT_TOKEN или в файле .env!")
    print("[!] Создай файл .env в этой папке и напиши: BOT_TOKEN=твой_токен")
    print("[!] Получить токен можно бесплатно у @BotFather в Telegram за 1 минуту.\n")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN) if TOKEN and TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE" else None
dp = Dispatcher()


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура бота."""
    kb = [
        [KeyboardButton(text="🚗 Выбрать по расстоянию")],
        [KeyboardButton(text="🌲 По категориям"), KeyboardButton(text="🎲 Случайное место")],
        [KeyboardButton(text="ℹ️ О гиде (Точка старта: Озерки)")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def format_place_card(place: Dict[str, Any]) -> str:
    """Форматирует карточку места со всеми деталями."""
    text = (
        f"📍 <b>{place['title']}</b>\n\n"
        f"⏱ <b>От м. Озерки:</b> ~{place['distance_km']} км ({place['car_time']})\n"
        f"✨ <b>Вайб (Pinterest/TikTok):</b> {place['vibe']}\n\n"
        f"📅 <b>Лучший сезон:</b> {place['season']}\n"
        f"🌅 <b>Время суток:</b> {place['time_of_day']}\n\n"
        f"🚙 <b>На машине (дорога и парковка):</b>\n{place['car_access']}\n\n"
        f"📸 <b>Идеи для фото:</b> {place['photo_tips']}\n"
    )
    return text


def get_place_keyboard(place: Dict[str, Any], back_action: str = "main") -> InlineKeyboardMarkup:
    """Инлайн-кнопки под карточкой места: Маршрут и Назад."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗺 Построить маршрут (Яндекс.Карты)",
            url=place["yandex_map"]
        )
    )
    if back_action.startswith("dist_"):
        dist_key = back_action.split("_", 1)[1]
        builder.row(InlineKeyboardButton(text="⬅️ Назад к этому расстоянию", callback_data=f"show_dist_{dist_key}"))
    elif back_action.startswith("cat_"):
        cat_key = back_action.split("_", 1)[1]
        builder.row(InlineKeyboardButton(text="⬅️ Назад к этой категории", callback_data=f"show_cat_{cat_key}"))
    
    builder.row(InlineKeyboardButton(text="🎲 Другое случайное место", callback_data="random_place"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_home"))
    return builder.as_markup()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Приветственное сообщение."""
    greeting = (
        "👋 <b>Привет, автопутешественник!</b>\n\n"
        "Этот гид собран специально для вылазок на машине из Санкт-Петербурга.\n"
        "📌 <b>Точка отсчета: метро «Озерки»</b> (север города, выезды на Выборгское шоссе, "
        "трассу «Скандинавия», Приморское шоссе и КАД).\n\n"
        "Все локации отобраны по трендам <b>Pinterest, TikTok и рекомендациям локалов</b> — "
        "эстетичные экотропы, северные маяки, песчаные пляжи залива, готические руины и карельские скалы.\n\n"
        "Куда поедем сегодня? Выбирай фильтр в меню ниже 👇"
    )
    await message.answer(greeting, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@dp.message(F.text == "🚗 Выбрать по расстоянию")
async def choose_distance(message: types.Message):
    """Меню выбора расстояния."""
    builder = InlineKeyboardBuilder()
    for key, label in DISTANCE_GROUPS.items():
        count = len([p for p in PLACES if p["range_group"] == key])
        builder.row(InlineKeyboardButton(text=f"{label} ({count})", callback_data=f"show_dist_{key}"))
    
    await message.answer(
        "📏 <b>На какое расстояние от м. Озерки готов поехать?</b>\n"
        "Выбирай радиус поездки:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.message(F.text == "🌲 По категориям")
async def choose_category(message: types.Message):
    """Меню выбора категории."""
    builder = InlineKeyboardBuilder()
    for cat_id, cat_name in CATEGORY_NAMES.items():
        count = len([p for p in PLACES if p["category"] == cat_id])
        builder.row(InlineKeyboardButton(text=f"{cat_name} ({count})", callback_data=f"show_cat_{cat_id}"))
    
    await message.answer(
        "✨ <b>Какой вайб поездки ищем сегодня?</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.message(F.text == "🎲 Случайное место")
async def random_place_cmd(message: types.Message):
    """Случайный выбор места."""
    place = random.choice(PLACES)
    card_text = format_place_card(place)
    await message.answer(
        f"🎲 <b>Твой рандомный спот на сегодня:</b>\n\n{card_text}",
        parse_mode="HTML",
        reply_markup=get_place_keyboard(place, back_action="main")
    )


@dp.message(F.text == "ℹ️ О гиде (Точка старта: Озерки)")
async def about_guide(message: types.Message):
    """Информация о точке старта."""
    about_text = (
        "🧭 <b>Почему точка отсчета — м. «Озерки»?</b>\n\n"
        "Озерки — главные 'северные ворота' Питера для загородных поездок на авто. "
        "Отсюда начинаются прямые скоростные выезды:\n"
        "• <b>Выборгское шоссе</b> — прямиком к озерам и карельским лесам\n"
        "• <b>Трасса «Скандинавия» (А-181)</b> — скоростной автобан до Выборга и Монрепо\n"
        "• <b>Трасса «Сортавала» (А-121)</b> — новая 4-полосная дорога на Вуоксу и Приозерск\n"
        "• <b>Северный участок КАД и ЗСД</b> — моментальный выезд на Курортный район и дамбу Кронштадта\n\n"
        "🚙 <b>Все локации проверены:</b> к каждой точке есть комфортный подъезд на обычном легковом автомобиле."
    )
    await message.answer(about_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


# ---------------- КАТАЛОГИ И КОЛЛБЭКИ ----------------

@dp.callback_query(F.data.startswith("show_dist_"))
async def list_places_by_distance(callback: types.CallbackQuery):
    dist_key = callback.data.split("_", 2)[2]
    filtered = [p for p in PLACES if p["range_group"] == dist_key]
    
    builder = InlineKeyboardBuilder()
    for p in filtered:
        builder.row(InlineKeyboardButton(text=f"📍 {p['title']} (~{p['distance_km']} км)", callback_data=f"place_{p['id']}_dist_{dist_key}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад к расстояниям", callback_data="back_to_dist"))
    
    group_name = DISTANCE_GROUPS.get(dist_key, "")
    await callback.message.edit_text(
        f"🚘 <b>Места в радиусе: {group_name}</b>\n\nВыбери локацию, чтобы посмотреть фото-гид и маршрут:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("show_cat_"))
async def list_places_by_category(callback: types.CallbackQuery):
    cat_key = callback.data.split("_", 2)[2]
    filtered = [p for p in PLACES if p["category"] == cat_key]
    
    builder = InlineKeyboardBuilder()
    for p in filtered:
        builder.row(InlineKeyboardButton(text=f"📍 {p['title']} (~{p['distance_km']} км)", callback_data=f"place_{p['id']}_cat_{cat_key}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="back_to_cat"))
    
    cat_name = CATEGORY_NAMES.get(cat_key, "")
    await callback.message.edit_text(
        f"🌲 <b>Категория: {cat_name}</b>\n\nВыбери локацию для подробностей:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("place_"))
async def view_place_details(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    place_id = parts[1]
    back_action = "_".join(parts[2:]) if len(parts) > 2 else "main"
    
    place = next((p for p in PLACES if p["id"] == place_id), None)
    if not place:
        await callback.answer("Локация не найдена!", show_alert=True)
        return
    
    card = format_place_card(place)
    await callback.message.edit_text(
        card,
        parse_mode="HTML",
        reply_markup=get_place_keyboard(place, back_action=back_action)
    )


@dp.callback_query(F.data == "random_place")
async def cb_random_place(callback: types.CallbackQuery):
    place = random.choice(PLACES)
    card = format_place_card(place)
    await callback.message.edit_text(
        f"🎲 <b>Случайная рекомендация:</b>\n\n{card}",
        parse_mode="HTML",
        reply_markup=get_place_keyboard(place, back_action="main")
    )


@dp.callback_query(F.data == "back_to_dist")
async def cb_back_to_dist(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for key, label in DISTANCE_GROUPS.items():
        count = len([p for p in PLACES if p["range_group"] == key])
        builder.row(InlineKeyboardButton(text=f"{label} ({count})", callback_data=f"show_dist_{key}"))
    
    await callback.message.edit_text(
        "📏 <b>Выбери расстояние от м. Озерки:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "back_to_cat")
async def cb_back_to_cat(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for cat_id, cat_name in CATEGORY_NAMES.items():
        count = len([p for p in PLACES if p["category"] == cat_id])
        builder.row(InlineKeyboardButton(text=f"{cat_name} ({count})", callback_data=f"show_cat_{cat_id}"))
    
    await callback.message.edit_text(
        "✨ <b>Выбери категорию локаций:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "menu_home")
async def cb_menu_home(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню. Выбирай действие кнопками внизу 👇",
        reply_markup=get_main_menu_keyboard()
    )


async def main():
    if not bot:
        print("[!] Не удалось запустить бота: токен отсутствует.")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 Бот локаций СПб (старт: м. Озерки) успешно запущен!")
    print("   Открой Telegram и напиши /start своему боту.")
    print("=" * 60)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[+] Бот остановлен.")
