from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonCommands,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)


BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or ""
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://tolk-club.ru/baza/")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "846207345")
CONTACT_USERNAME = "mbikmay"
AUTO_CLIENT_PATH_SECONDS = 300


COUNTRIES = {
    "kz": {
        "name": "Казахстан",
        "city": "Алматы",
        "currency": "₸",
        "support": "@baza_support_kz",
        "phone": "+7 777 000 00 00",
        "location": "Казахстан, Алматинская область, 18 км от Капшагая, зона отдыха «Aq Samal Resort», участок 7",
        "short_address": "18 км от Капшагая, зона отдыха «Aq Samal Resort»",
        "about": (
            "«Aq Samal Resort» — уютная база отдыха рядом с водоёмом, где можно снять домик на выходные, "
            "отдохнуть с семьёй, пожарить шашлыки, сходить в баню и провести вечер на свежем воздухе."
        ),
    },
    "ru": {
        "name": "Россия",
        "city": "Москва",
        "currency": "₽",
        "support": "@baza_support_ru",
        "phone": "+7 999 000 00 00",
        "location": "Россия, Московская область, Истринский район, посёлок Лесное Озеро, база отдыха «Sosnovy Bereg», дом 4",
        "short_address": "Истринский район, посёлок Лесное Озеро, «Sosnovy Bereg»",
        "about": (
            "«Sosnovy Bereg» — загородная база отдыха среди леса, с тёплыми домиками, баней, беседками "
            "и спокойной атмосферой для семейных поездок, компаний и короткого отдыха за городом."
        ),
    },
}

HOUSE_PRICES = {
    "kz": {"house_2": 25000, "house_4": 35000, "house_6": 50000},
    "ru": {"house_2": 5000, "house_4": 7000, "house_6": 10000},
}


@dataclass(frozen=True)
class House:
    code: str
    title: str
    capacity: int
    description: str
    amenities: tuple[str, ...]
    photo: str


@dataclass(frozen=True)
class Service:
    code: str
    title: str
    description: str
    photo: str


HOUSES = {
    "house_2": House(
        code="house_2",
        title="Домик Comfort на 2 человека",
        capacity=2,
        description="Уютный домик для пары: кровать, санузел, мини-холодильник и мангальная зона рядом.",
        amenities=(
            "двуспальная кровать",
            "душ и санузел",
            "мини-холодильник",
            "чайник и базовая посуда",
            "постельное бельё и полотенца",
            "мангальная зона рядом",
        ),
        photo="webapp/photos_optimized/house_2.jpg",
    ),
    "house_4": House(
        code="house_4",
        title="Домик Family на 4 человека",
        capacity=4,
        description="Семейный вариант: две спальни, кухня, душ, терраса и отдельный мангал.",
        amenities=(
            "две спальни",
            "кухня с плитой и холодильником",
            "душ и санузел",
            "посуда для семьи",
            "постельное бельё и полотенца",
            "терраса",
            "отдельная мангальная зона",
        ),
        photo="webapp/photos_optimized/house_4.jpg",
    ),
    "house_6": House(
        code="house_6",
        title="Домик Grand на 6 человек",
        capacity=6,
        description="Большой домик для компании: гостиная, кухня, несколько спальных мест и зона отдыха.",
        amenities=(
            "несколько спальных мест",
            "просторная гостиная",
            "кухня с холодильником и плитой",
            "душ и санузел",
            "посуда для компании",
            "постельное бельё и полотенца",
            "терраса или зона отдыха",
            "мангал рядом с домиком",
        ),
        photo="webapp/photos_optimized/house_6.jpg",
    ),
}

SERVICES = {
    "gazebo": Service("gazebo", "Беседки", "Беседки для дневного отдыха, семьи и небольших мероприятий.", "webapp/photos_optimized/gazebo.jpg"),
    "bathhouse": Service("bathhouse", "Баня", "Баня для гостей базы отдыха. Можно добавить свободные часы, цену и отдельное бронирование.", "webapp/photos_optimized/bathhouse.jpg"),
    "pool": Service("pool", "Бассейн", "Бассейн на территории базы отдыха: время работы, правила посещения и стоимость.", "webapp/photos_optimized/pool.jpg"),
    "bbq": Service("bbq", "Мангальная зона", "Отдельная зона для приготовления еды и отдыха рядом с домиками.", "webapp/photos_optimized/bbq.jpg"),
}


FAQ_ANSWERS = {
    "Адрес": "Адрес базы отдыха:\n{location}\n\nДля реального клиента сюда добавляется точная геометка и ссылка на 2GIS/Google Maps.",
    "Что есть на территории": "На территории есть домики, беседки, баня, бассейн, мангальная зона, парковка и прогулочная зона.\n\nНажмите «Услуги», чтобы посмотреть карточки с фотографиями.",
    "Условия проживания": "Условия проживания:\n\n• заезд после 14:00\n• выезд до 12:00\n• бронь подтверждается после предоплаты или администратором\n• с животными — по согласованию\n• шумные мероприятия — по правилам базы",
    "Контакты": "Связь с администратором:\n\nТелефон / WhatsApp: {phone}\nTelegram-поддержка: {support}\n\nВ рабочем боте можно сделать кнопку прямого перехода в WhatsApp, Telegram или звонок.",
}

AFTER_PAYMENT_GUIDE = (
    "<b>Информация для гостя после бронирования</b>\n\n"
    "<b>Как добраться</b>\n"
    "• адрес: {location};\n"
    "• точную геометку можно отправить отдельной кнопкой или ссылкой на 2GIS/Google Maps;\n"
    "• при въезде назовите имя, на которое оформлена бронь.\n\n"
    "<b>Инструкция по заселению</b>\n"
    "• заезд после 14:00;\n"
    "• выезд до 12:00;\n"
    "• администратор встретит вас на территории или отправит инструкцию по получению ключей;\n"
    "• сохраните это сообщение, чтобы быстро найти важную информацию.\n\n"
    "<b>Как пользоваться домиком</b>\n"
    "• после заселения проверьте свет, воду и отопление/кондиционер;\n"
    "• мангал используйте только в разрешённой зоне;\n"
    "• посуду и кухонные принадлежности верните на место перед выездом;\n"
    "• если что-то не работает, сразу напишите в поддержку.\n\n"
    "<b>Что есть на базе отдыха</b>\n"
    "• домики и номера;\n"
    "• беседки;\n"
    "• баня;\n"
    "• бассейн;\n"
    "• мангальная зона;\n"
    "• парковка;\n"
    "• прогулочная зона.\n\n"
    "<b>Связь и поддержка</b>\n"
    "• Telegram: {support}\n"
    "• WhatsApp / телефон: {phone}\n\n"
    "В реальной версии сюда можно добавить кнопки: «Открыть карту», «Написать в WhatsApp», «Позвать администратора»."
)

FAQ_ANSWERS["Информация для гостя"] = AFTER_PAYMENT_GUIDE

dp = Dispatcher(storage=MemoryStorage())
AUTO_START_TASKS: dict[int, asyncio.Task] = {}


class BookingForm(StatesGroup):
    name = State()
    phone = State()
    guests = State()
    comment = State()


def country_from_code(code: str | None) -> str:
    return code if code in COUNTRIES else "kz"


async def get_country(state: FSMContext) -> str:
    data = await state.get_data()
    return country_from_code(data.get("country"))


def country_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Казахстан", callback_data="country:kz")],
            [InlineKeyboardButton(text="Россия", callback_data="country:ru")],
        ]
    )


def webapp_url(country: str) -> str:
    separator = "&" if "?" in WEBAPP_URL else "?"
    return f"{WEBAPP_URL}{separator}country={country}"


def main_keyboard(country: str = "kz") -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    if WEBAPP_URL:
        rows.append([KeyboardButton(text="Выбрать даты", web_app=WebAppInfo(url=webapp_url(country)))])

    rows.extend(
        [
            [KeyboardButton(text="Домики"), KeyboardButton(text="Услуги")],
            [KeyboardButton(text="Цены"), KeyboardButton(text="Что есть на территории")],
            [KeyboardButton(text="Условия проживания"), KeyboardButton(text="Адрес")],
            [KeyboardButton(text="Контакты"), KeyboardButton(text="Информация для гостя")],
            [KeyboardButton(text="Меню презентации")],
            [KeyboardButton(text="Сменить страну")],
        ]
    )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=False, input_field_placeholder="Выберите действие")


def sales_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Протестировать бота")],
            [KeyboardButton(text="Что решает бот"), KeyboardButton(text="Что можно настроить")],
            [KeyboardButton(text="Пример заявки админу"), KeyboardButton(text="Связаться")],
            [KeyboardButton(text="Сменить страну")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие",
    )


def sales_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Протестировать бота", callback_data="sales:test")],
            [
                InlineKeyboardButton(text="Что решает бот", callback_data="sales:benefits"),
                InlineKeyboardButton(text="Что можно настроить", callback_data="sales:customization"),
            ],
            [
                InlineKeyboardButton(text="Пример заявки админу", callback_data="sales:example"),
                InlineKeyboardButton(text="Связаться", callback_data="sales:contact"),
            ],
        ]
    )


def booking_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заявку", callback_data="form:start")],
            [InlineKeyboardButton(text="Открыть поддержку", callback_data="support:open")],
        ]
    )


def final_booking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Имитировать бронь", callback_data="pay:demo")],
            [InlineKeyboardButton(text="Открыть поддержку", callback_data="support:open")],
        ]
    )


def skip_keyboard(callback_data: str = "form:skip") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data=callback_data)]])


def house_price(house: House, country: str) -> int:
    return HOUSE_PRICES.get(country, HOUSE_PRICES["kz"]).get(house.code, HOUSE_PRICES["kz"][house.code])


def money(value: int, country: str = "kz") -> str:
    currency = COUNTRIES[country_from_code(country)]["currency"]
    return f"{value:,}".replace(",", " ") + f" {currency}"


def format_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return value


def render_template(text: str, country: str) -> str:
    info = COUNTRIES[country_from_code(country)]
    return text.format(**info)


def owner_intro_text() -> str:
    return (
        "<b>Демо чат-бота для базы отдыха</b>\n\n"
        "Это пример бота, который можно адаптировать под вашу базу отдыха: "
        "добавить ваши домики, фотографии, цены, свободные даты, правила, контакты и способ оплаты.\n\n"
        "<b>Что можно сделать в демо:</b>\n"
        "• пройти путь гостя от выбора дат до брони;\n"
        "• посмотреть, как выглядят домики и услуги;\n"
        "• увидеть расчёт стоимости;\n"
        "• получить пример инструкции после бронирования.\n\n"
        "Нажмите «Протестировать бота», чтобы посмотреть путь клиента."
    )


def benefits_text() -> str:
    return (
        "<b>Что решает такой бот</b>\n\n"
        "<b>1. Больше прямых бронирований</b>\n"
        "Гость может забронировать напрямую через Telegram, без лишних переходов и переписок. "
        "Это помогает меньше зависеть от агрегаторов и сервисов бронирования, где комиссия может быть 15-20%.\n\n"
        "<b>2. Меньше ручной переписки</b>\n"
        "Бот сам отвечает на частые вопросы: цены, адрес, условия, что есть на территории, как добраться. "
        "Администратору не нужно десятки раз писать одно и то же.\n\n"
        "<b>3. Заявки не теряются</b>\n"
        "Бот собирает имя, телефон, даты, количество гостей, домик и комментарий. "
        "Заявку можно отправлять в Telegram-чат, Google Sheets или CRM.\n\n"
        "<b>4. Сбор базы гостей</b>\n"
        "Контакты гостей можно сохранять и потом использовать для повторных продаж: акции, свободные даты, сезонные предложения.\n\n"
        "<b>5. Быстрее доводит до решения</b>\n"
        "Гость сразу видит фото, свободные даты, стоимость и следующий шаг. "
        "Чем меньше вопросов и ожидания, тем выше шанс, что он оставит заявку.\n\n"
        "<b>6. Инструкции после брони</b>\n"
        "После оформления бот может автоматически отправить адрес, правила, инструкцию по заселению и контакты поддержки."
    )


def customization_text() -> str:
    return (
        "<b>Что можно настроить под вашу базу</b>\n\n"
        "• ваши домики, номера, беседки и услуги;\n"
        "• ваши фотографии и описания;\n"
        "• цены по сезонам и дням недели;\n"
        "• календарь свободных дат;\n"
        "• онлайн-оплату, предоплату или заявку админу;\n"
        "• Google Sheets или CRM;\n"
        "• адрес, геометку, правила проживания;\n"
        "• поддержку через Telegram, WhatsApp или звонок;\n"
        "• рассылки по гостям и акции."
    )


def admin_request_example_text(country: str) -> str:
    return (
        "<b>Как может выглядеть заявка для администратора</b>\n\n"
        "Новая заявка на бронирование\n\n"
        "Домик: Family на 4 человека\n"
        "Даты: 12.07 - 14.07\n"
        "Гостей: 4\n"
        f"Сумма: {money(HOUSE_PRICES[country]['house_4'] * 2, country)}\n"
        "Клиент: Алия\n"
        "Телефон: +7 ...\n"
        "Статус: ожидает подтверждения\n\n"
        "Заявку можно отправлять в Telegram-чат, Google Sheets или CRM."
    )


def contact_text() -> str:
    return (
        "<b>Хотите такого бота для своей базы?</b>\n\n"
        f"Напишите мне в Telegram: @{CONTACT_USERNAME}\n\n"
        "Для оценки проекта достаточно прислать:\n"
        "1. список домиков и услуг;\n"
        "2. цены;\n"
        "3. фотографии;\n"
        "4. правила проживания;\n"
        "5. как сейчас принимаете бронирования."
    )


async def notify_owner(bot: Bot, message: Message, action: str) -> None:
    if not ADMIN_CHAT_ID:
        return

    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "без username"
    name = message.from_user.full_name if message.from_user else "неизвестно"
    await bot.send_message(
        ADMIN_CHAT_ID,
        "<b>Интерес к демо-боту</b>\n\n"
        f"Действие: {action}\n"
        f"Пользователь: {name}\n"
        f"Username: {username}\n"
        f"User ID: {message.from_user.id if message.from_user else 'неизвестно'}",
        parse_mode="HTML",
    )


async def notify_owner_from_callback(query: CallbackQuery, action: str) -> None:
    if not ADMIN_CHAT_ID:
        return

    username = f"@{query.from_user.username}" if query.from_user.username else "без username"
    await query.bot.send_message(
        ADMIN_CHAT_ID,
        "<b>Интерес к демо-боту</b>\n\n"
        f"Действие: {action}\n"
        f"Пользователь: {query.from_user.full_name}\n"
        f"Username: {username}\n"
        f"User ID: {query.from_user.id}",
        parse_mode="HTML",
    )


def prices_text(country: str) -> str:
    return (
        f"<b>Цены демо-версии</b>\n\n"
        f"• Домик на 2 человека — {money(HOUSE_PRICES[country]['house_2'], country)} / сутки\n"
        f"• Домик на 4 человека — {money(HOUSE_PRICES[country]['house_4'], country)} / сутки\n"
        f"• Домик на 6 человек — {money(HOUSE_PRICES[country]['house_6'], country)} / сутки\n"
        f"• Беседка — от {money(20000 if country == 'kz' else 4000, country)} / день\n"
        f"• Баня — от {money(15000 if country == 'kz' else 3000, country)}\n\n"
        "Точная сумма считается после выбора дат и объекта."
    )


def booking_summary(data: dict, house: House) -> str:
    country = country_from_code(data.get("country"))
    nights = int(data.get("nights", 1))
    price = house_price(house, country)
    total = price * nights
    return (
        f"<b>Вы выбрали:</b>\n\n"
        f"<b>{house.title}</b>\n"
        f"Вместимость: до {house.capacity} гостей\n"
        f"Заезд: {format_date(str(data.get('check_in', '')))}\n"
        f"Выезд: {format_date(str(data.get('check_out', '')))}\n"
        f"Ночей: {nights}\n\n"
        f"Цена за сутки: {money(price, country)}\n"
        f"<b>Итого: {money(total, country)}</b>\n\n"
        "Можно перейти к демо-оплате или обратиться в поддержку."
    )


def house_card_text(house: House, country: str) -> str:
    amenities = "\n".join(f"• {item}" for item in house.amenities)
    return (
        f"<b>{house.title}</b>\n"
        f"Вместимость: до {house.capacity} гостей\n"
        f"Цена: {money(house_price(house, country), country)} / сутки\n\n"
        f"{house.description}\n\n"
        f"<b>Что есть в домике:</b>\n{amenities}"
    )


async def answer_photo_or_text(
    message: Message,
    photo_path: str,
    text: str,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
) -> None:
    if os.path.exists(photo_path):
        await message.answer_photo(FSInputFile(photo_path), caption=text, reply_markup=reply_markup, parse_mode="HTML")
        return
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


async def show_houses(message: Message | CallbackQuery, state: FSMContext) -> None:
    country = await get_country(state)
    target = message.message if isinstance(message, CallbackQuery) else message
    await target.answer("Выберите домик для бронирования:", parse_mode="HTML")

    for house in HOUSES.values():
        await answer_photo_or_text(
            target,
            house.photo,
            house_card_text(house, country),
            InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Выбрать этот домик", callback_data=f"house:{house.code}")]]),
        )

    if isinstance(message, CallbackQuery):
        await message.answer()


async def show_services(message: Message | CallbackQuery) -> None:
    target = message.message if isinstance(message, CallbackQuery) else message
    await target.answer("<b>Карточки услуг на территории:</b>", parse_mode="HTML")
    for service in SERVICES.values():
        await answer_photo_or_text(target, service.photo, f"<b>{service.title}</b>\n\n{service.description}")
    if isinstance(message, CallbackQuery):
        await message.answer()


async def show_start(message: Message, state: FSMContext, country: str) -> None:
    info = COUNTRIES[country]
    if not WEBAPP_URL:
        await message.answer(
            "Календарь бронирования ещё не подключён.\n\n"
            "Нужно разместить папку `webapp` на HTTPS-хостинге и запустить бота так:\n\n"
            '$env:WEBAPP_URL="https://ваша-ссылка"\n'
            '$env:BOT_TOKEN="токен-бота"\n'
            "python demo_bot.py",
            reply_markup=main_keyboard(country),
        )
        return

    await message.answer(
        "<b>Путь клиента: вымышленная база отдыха</b>\n\n"
        "Сейчас вы увидите пример, как бот может выглядеть для гостя.\n"
        "База отдыха вымышленная, а фотографии домиков и услуг сделаны с помощью ИИ.\n\n"
        "Здесь гость может посмотреть домики и услуги, выбрать свободные даты, "
        "подобрать подходящий домик и увидеть итоговую стоимость бронирования.\n\n"
        f"<b>О нас:</b>\n{info['about']}\n\n"
        "<b>Как забронировать:</b>\n"
        "1. Нажмите «Выбрать даты».\n"
        "2. Выберите заезд, выезд и домик.\n"
        "3. Вернитесь в чат, чтобы увидеть сводку.\n"
        "4. Нажмите «Демо-оплата» или обратитесь в поддержку.\n\n"
        "В меню ниже также есть быстрые ответы: цены, адрес, условия проживания, услуги и информация для гостя.",
        reply_markup=main_keyboard(country),
        parse_mode="HTML",
    )


async def show_owner_landing(message: Message, state: FSMContext, country: str) -> None:
    await state.update_data(country=country, client_path_started=False)
    await message.answer(owner_intro_text(), reply_markup=sales_inline_keyboard(), parse_mode="HTML")
    schedule_auto_client_path(message, state, country)


def cancel_auto_client_path(user_id: int) -> None:
    task = AUTO_START_TASKS.pop(user_id, None)
    if task and not task.done():
        task.cancel()


def schedule_auto_client_path(message: Message, state: FSMContext, country: str) -> None:
    user_id = message.from_user.id
    cancel_auto_client_path(user_id)

    async def runner() -> None:
        try:
            await asyncio.sleep(AUTO_CLIENT_PATH_SECONDS)
            data = await state.get_data()
            if data.get("client_path_started"):
                return
            await state.update_data(client_path_started=True)
            await message.answer(
                "Автоматически запускаю путь клиента, чтобы вы могли посмотреть демо бронирования.",
                reply_markup=main_keyboard(country),
            )
            await show_start(message, state, country)
        except asyncio.CancelledError:
            return

    AUTO_START_TASKS[user_id] = asyncio.create_task(runner())


@dp.message(CommandStart(deep_link=True))
async def start_deeplink(message: Message, command: CommandObject, state: FSMContext) -> None:
    country = country_from_code(command.args)
    cancel_auto_client_path(message.from_user.id)
    await state.clear()
    await state.update_data(country=country)
    await show_owner_landing(message, state, country)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    cancel_auto_client_path(message.from_user.id)
    await state.clear()
    await message.answer(
        "<b>Выберите страну</b>",
        reply_markup=country_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("country:"))
async def choose_country(query: CallbackQuery, state: FSMContext) -> None:
    country = country_from_code(query.data.split(":", 1)[1])
    await state.update_data(country=country)
    await query.message.answer(f"Выбрано: {COUNTRIES[country]['name']}")
    await show_owner_landing(query.message, state, country)
    await query.answer()


@dp.message(F.text == "Сменить страну")
async def change_country(message: Message) -> None:
    cancel_auto_client_path(message.from_user.id)
    await message.answer("Выберите страну:", reply_markup=country_keyboard())


@dp.message(F.text == "Протестировать бота")
async def test_bot(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    cancel_auto_client_path(message.from_user.id)
    await state.update_data(client_path_started=True)
    await notify_owner(message.bot, message, "нажал «Протестировать бота»")
    await show_start(message, state, country)


@dp.callback_query(F.data == "sales:test")
async def test_bot_inline(query: CallbackQuery, state: FSMContext) -> None:
    country = await get_country(state)
    cancel_auto_client_path(query.from_user.id)
    await state.update_data(client_path_started=True)
    await notify_owner_from_callback(query, "нажал «Протестировать бота»")
    await show_start(query.message, state, country)
    await query.answer()


@dp.message(F.text == "Что решает бот")
async def benefits(message: Message) -> None:
    await message.answer(benefits_text(), reply_markup=sales_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "sales:benefits")
async def benefits_inline(query: CallbackQuery) -> None:
    await query.message.answer(benefits_text(), reply_markup=sales_inline_keyboard(), parse_mode="HTML")
    await query.answer()


@dp.message(F.text == "Что можно настроить")
async def customization(message: Message) -> None:
    await message.answer(customization_text(), reply_markup=sales_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "sales:customization")
async def customization_inline(query: CallbackQuery) -> None:
    await query.message.answer(customization_text(), reply_markup=sales_inline_keyboard(), parse_mode="HTML")
    await query.answer()


@dp.message(F.text == "Пример заявки админу")
async def admin_request_example(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    await message.answer(admin_request_example_text(country), reply_markup=sales_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "sales:example")
async def admin_request_example_inline(query: CallbackQuery, state: FSMContext) -> None:
    country = await get_country(state)
    await query.message.answer(admin_request_example_text(country), reply_markup=sales_inline_keyboard(), parse_mode="HTML")
    await query.answer()


@dp.message(F.text == "Связаться")
async def contact(message: Message) -> None:
    cancel_auto_client_path(message.from_user.id)
    await notify_owner(message.bot, message, "нажал «Связаться»")
    await message.answer(contact_text(), reply_markup=sales_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "sales:contact")
async def contact_inline(query: CallbackQuery) -> None:
    cancel_auto_client_path(query.from_user.id)
    await notify_owner_from_callback(query, "нажал «Связаться»")
    await query.message.answer(contact_text(), reply_markup=sales_inline_keyboard(), parse_mode="HTML")
    await query.answer()


@dp.message(F.text == "Меню презентации")
async def owner_menu(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    await show_owner_landing(message, state, country)


@dp.message(Command("book"))
async def book_command(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    cancel_auto_client_path(message.from_user.id)
    await state.update_data(client_path_started=True)
    await notify_owner(message.bot, message, "открыл бронирование через /book")
    await show_start(message, state, country)


@dp.message(Command("support"))
async def support_command(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    info = COUNTRIES[country]
    await message.answer(
        f"<b>Поддержка</b>\n\nTelegram: {info['support']}\nТелефон / WhatsApp: {info['phone']}",
        reply_markup=main_keyboard(country),
        parse_mode="HTML",
    )


@dp.message(F.web_app_data)
async def webapp_booking_data(message: Message, state: FSMContext) -> None:
    raw_data = message.web_app_data.data
    try:
        booking = json.loads(raw_data)
    except json.JSONDecodeError:
        await message.answer(f"Данные из календаря получены, но бот не смог их разобрать.\n\nПолучено: {raw_data}")
        return

    current = await state.get_data()
    country = country_from_code(booking.get("country") or current.get("country"))
    await state.update_data(
        country=country,
        check_in=booking.get("check_in"),
        check_out=booking.get("check_out"),
        nights=booking.get("nights", 1),
        selected_house=booking.get("house_code"),
    )

    house = HOUSES.get(str(booking.get("house_code", "")))
    if not house:
        await message.answer(
            "Даты получены.\n\n"
            f"Заезд: {format_date(str(booking.get('check_in', '')))}\n"
            f"Выезд: {format_date(str(booking.get('check_out', '')))}\n"
            f"Ночей: {booking.get('nights', 1)}\n\n"
            "Домик не выбран. Откройте календарь ещё раз и выберите домик.",
            reply_markup=main_keyboard(country),
        )
        return

    data = await state.get_data()
    await answer_photo_or_text(message, house.photo, "Отлично, выбор получен!\n\n" + booking_summary(data, house), booking_actions_keyboard())


@dp.message(F.text == "Домики")
async def houses(message: Message, state: FSMContext) -> None:
    await show_houses(message, state)


@dp.message(F.text == "Услуги")
async def services(message: Message) -> None:
    await show_services(message)


@dp.message(F.text == "Цены")
async def prices(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    await message.answer(prices_text(country), reply_markup=main_keyboard(country), parse_mode="HTML")


@dp.message(F.text.in_(FAQ_ANSWERS.keys()))
async def faq(message: Message, state: FSMContext) -> None:
    country = await get_country(state)
    await message.answer(render_template(FAQ_ANSWERS[message.text], country), reply_markup=main_keyboard(country), parse_mode="HTML")


@dp.callback_query(F.data == "booking:houses")
async def booking_houses(query: CallbackQuery, state: FSMContext) -> None:
    await show_houses(query, state)


@dp.callback_query(F.data == "support:open")
async def support_callback(query: CallbackQuery, state: FSMContext) -> None:
    country = await get_country(state)
    info = COUNTRIES[country]
    await query.message.answer(
        f"<b>Поддержка</b>\n\nTelegram: {info['support']}\nТелефон / WhatsApp: {info['phone']}",
        reply_markup=main_keyboard(country),
        parse_mode="HTML",
    )
    await query.answer()


@dp.callback_query(F.data == "form:start")
async def form_start(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingForm.name)
    await query.message.answer(
        "<b>Оформим демо-заявку</b>\n\n"
        "Введите имя гостя.\n"
        "Можно написать вымышленное имя, это демонстрация.",
        parse_mode="HTML",
    )
    await query.answer()


@dp.message(BookingForm.name)
async def form_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip() if message.text else ""
    if len(name) < 2:
        await message.answer("Введите имя гостя, например: Алия")
        return

    await state.update_data(guest_name=name)
    await state.set_state(BookingForm.phone)
    await message.answer(
        "Введите номер телефона или нажмите «Пропустить».\n\n"
        "Для демо можно не оставлять настоящий номер.",
        reply_markup=skip_keyboard("form:skip_phone"),
    )


@dp.callback_query(F.data == "form:skip_phone")
async def form_skip_phone(query: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(guest_phone="не указан")
    await state.set_state(BookingForm.guests)
    await query.message.answer("Сколько гостей планируется? Например: 4")
    await query.answer()


@dp.message(BookingForm.phone)
async def form_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip() if message.text else ""
    await state.update_data(guest_phone=phone or "не указан")
    await state.set_state(BookingForm.guests)
    await message.answer("Сколько гостей планируется? Например: 4")


@dp.message(BookingForm.guests)
async def form_guests(message: Message, state: FSMContext) -> None:
    guests = message.text.strip() if message.text else ""
    if not guests:
        await message.answer("Введите количество гостей, например: 4")
        return

    await state.update_data(guest_count=guests)
    await state.set_state(BookingForm.comment)
    await message.answer(
        "Есть комментарий к бронированию?\n\n"
        "Например: нужен домик ближе к бассейну, нужна баня, едем с детьми.\n"
        "Можно нажать «Пропустить».",
        reply_markup=skip_keyboard("form:skip_comment"),
    )


@dp.callback_query(F.data == "form:skip_comment")
async def form_skip_comment(query: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(guest_comment="нет комментария")
    await finish_booking_form(query.message, state)
    await query.answer()


@dp.message(BookingForm.comment)
async def form_comment(message: Message, state: FSMContext) -> None:
    comment = message.text.strip() if message.text else ""
    await state.update_data(guest_comment=comment or "нет комментария")
    await finish_booking_form(message, state)


async def finish_booking_form(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    data = await state.get_data()
    country = country_from_code(data.get("country"))
    house = HOUSES.get(data.get("selected_house"))
    if not house:
        await message.answer("Домик не найден. Откройте календарь и выберите домик ещё раз.", reply_markup=main_keyboard(country))
        return

    nights = int(data.get("nights", 1))
    total = house_price(house, country) * nights
    await message.answer(
        "<b>Демо-заявка сформирована</b>\n\n"
        f"Имя: {data.get('guest_name')}\n"
        f"Телефон: {data.get('guest_phone')}\n"
        f"Гостей: {data.get('guest_count')}\n"
        f"Комментарий: {data.get('guest_comment')}\n\n"
        f"Домик: {house.title}\n"
        f"Заезд: {format_date(str(data.get('check_in', '')))}\n"
        f"Выезд: {format_date(str(data.get('check_out', '')))}\n"
        f"Ночей: {nights}\n"
        f"Сумма: <b>{money(total, country)}</b>\n\n"
        "Теперь можно имитировать бронь. В реальном боте эта заявка может уйти администратору, в Google Sheets или в CRM.",
        reply_markup=final_booking_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("house:"))
async def choose_house(query: CallbackQuery, state: FSMContext) -> None:
    house_code = query.data.split(":", 1)[1]
    house = HOUSES.get(house_code)
    if not house:
        await query.answer("Домик не найден", show_alert=True)
        return

    data = await state.get_data()
    country = country_from_code(data.get("country"))
    await state.update_data(selected_house=house.code)

    if not data.get("check_in") or not data.get("check_out"):
        await answer_photo_or_text(
            query.message,
            house.photo,
            house_card_text(house, country) + "\n\nДля расчёта стоимости сначала нажмите «Выбрать даты».",
            main_keyboard(country),
        )
        await query.answer()
        return

    data = await state.get_data()
    await answer_photo_or_text(query.message, house.photo, booking_summary(data, house), booking_actions_keyboard())
    await query.answer()


@dp.callback_query(F.data == "pay:demo")
async def demo_payment(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    country = country_from_code(data.get("country"))
    house = HOUSES.get(data.get("selected_house"))
    if not house:
        await query.answer("Сначала выберите домик", show_alert=True)
        return

    nights = int(data.get("nights", 1))
    total = house_price(house, country) * nights
    await query.message.answer(
        "<b>Бронь имитирована</b>\n\n"
        f"Имя: {data.get('guest_name', 'не указано')}\n"
        f"Телефон: {data.get('guest_phone', 'не указан')}\n"
        f"Гостей: {data.get('guest_count', 'не указано')}\n"
        f"Комментарий: {data.get('guest_comment', 'нет комментария')}\n\n"
        f"Домик: {house.title}\n"
        f"Заезд: {format_date(str(data.get('check_in', '')))}\n"
        f"Выезд: {format_date(str(data.get('check_out', '')))}\n"
        f"Сумма: <b>{money(total, country)}</b>\n\n"
        "В готовом боте можно выбрать нужную логику:\n"
        "• сразу принять онлайн-оплату;\n"
        "• отправить заявку администратору на подтверждение;\n"
        "• совместить оба варианта: заявка + предоплата.\n\n"
        "Для демо сейчас показан сценарий после бронирования.",
        reply_markup=main_keyboard(country),
        parse_mode="HTML",
    )
    await notify_owner_from_callback(query, "нажал «Имитировать бронь»")
    await query.message.answer(render_template(AFTER_PAYMENT_GUIDE, country), reply_markup=main_keyboard(country), parse_mode="HTML")

    if ADMIN_CHAT_ID:
        await query.bot.send_message(
            ADMIN_CHAT_ID,
            "Новая демо-бронь\n\n"
            f"Страна: {COUNTRIES[country]['name']}\n"
            f"Домик: {house.title}\n"
            f"Заезд: {format_date(str(data.get('check_in', '')))}\n"
            f"Выезд: {format_date(str(data.get('check_out', '')))}\n"
            f"Ночей: {nights}\n"
            f"Имя: {data.get('guest_name', 'не указано')}\n"
            f"Телефон: {data.get('guest_phone', 'не указан')}\n"
            f"Гостей: {data.get('guest_count', 'не указано')}\n"
            f"Комментарий: {data.get('guest_comment', 'нет комментария')}\n"
            f"Сумма: {money(total, country)}\n"
            f"Клиент: @{query.from_user.username or 'без username'}",
        )

    await query.answer("Готово")


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable before running the bot.")

    if not WEBAPP_URL:
        print("WEBAPP_URL is not set. The bot will explain how to connect the Mini App.")

    bot = Bot(BOT_TOKEN)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить демо"),
            BotCommand(command="book", description="Открыть бронирование"),
            BotCommand(command="support", description="Связаться с поддержкой"),
        ]
    )
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
