from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from data.database import User, Settings, PaymentDatabase
import math


User = User()
Settings = Settings()
PaymentDatabase = PaymentDatabase()

REGIONS_PER_PAGE = 10
COLUMNS = 1

async def get_start_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text='Активировать пробный период'),
    )
    builder.row(
        KeyboardButton(text='Активировать промокод'),
    )

    return builder.as_markup(resize_keyboard=True)

async def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text='Выбор продукции'),
        KeyboardButton(text='Выбор региона')
    )
    builder.row(
        KeyboardButton(text='Актуальные цены'),
        KeyboardButton(text='Последние данные')

    )
    builder.row(
        KeyboardButton(text='Поделиться ботом')
    )
    builder.row(
        KeyboardButton(text='Поддержка'),
        KeyboardButton(text='Управление подпиской')
    )

    return builder.as_markup(resize_keyboard=True)


async def get_choice_products(tg_id: int):
    info_user = await User.get_info_user(tg_id=tg_id)
    list_product = await Settings.get_all_products()
    user_list_product = info_user.get("products_list", "").split(',')
    builder = InlineKeyboardBuilder()

    row = []
    for idx, product in enumerate(list_product, 1):
        is_selected = str(product['id_product']) in user_list_product
        text = f"✅{product['name_product']}" if is_selected else product['name_product']
        callback = f"delete_product_{product['id_product']}" if is_selected else f"add_product_{product['id_product']}"
        builder.button(text=text, callback_data=callback)

    builder.adjust(3)

    builder.row(
        InlineKeyboardButton(text="🔄 Сбросить", callback_data="reset_products"),
        InlineKeyboardButton(text="✅ Выбрать все", callback_data="select_all_products")
    )

    builder.row(
        InlineKeyboardButton(text="Сохранить настройки", callback_data="main_menu")
    )

    return builder.as_markup()



async def get_choice_regions(tg_id: int, page: int = 1):
    info_user = await User.get_info_user(tg_id=tg_id)
    selected_regions = info_user.get("regions_list", "").split(',')

    all_regions = await Settings.get_all_regions()
    total_pages = math.ceil(len(all_regions) / REGIONS_PER_PAGE)

    # Ограничим страницу в допустимых пределах
    page = max(1, min(page, total_pages))

    # Получаем регионы для текущей страницы
    start = (page - 1) * REGIONS_PER_PAGE
    end = start + REGIONS_PER_PAGE
    regions_on_page = all_regions[start:end]

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки по 2 в ряд
    row = []
    for idx, region in enumerate(regions_on_page, 1):
        is_selected = str(region['id_region']) in selected_regions

        # Перенос длинного названия региона
        name = region['name_region']
        text = f"✅{name}" if is_selected else name
        callback = f"delete_region_{page}_{region['id_region']}" if is_selected else f"add_region_{page}_{region['id_region']}"
        row.append(InlineKeyboardButton(text=text, callback_data=callback))

        if len(row) == COLUMNS:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    # Пагинация
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"regions_page_{page - 1}"))
    if page < total_pages:
        pagination_buttons.append(InlineKeyboardButton(text="▶️ Далее", callback_data=f"regions_page_{page + 1}"))

    if pagination_buttons:
        builder.row(*pagination_buttons)

    # Финальные кнопки
    builder.row(
        InlineKeyboardButton(text="🔄 Сбросить", callback_data="reset_regions"),
        InlineKeyboardButton(text="✅ Выбрать все", callback_data="select_all_regions")
    )
    builder.row(
        InlineKeyboardButton(text="Сохранить настройки", callback_data="main_menu")
    )

    return builder.as_markup()


async def get_choice_subscription():
    subscriptions = await PaymentDatabase.get_all_subscriptions()
    builder = InlineKeyboardBuilder()

    # Добавляем первую строку: две кнопки рядом


    for subs in subscriptions:
        if subs['id_subscription'] not in  [999, 998]:
            price_formate = [_ for _ in str(int(subs['price']))]
            price_formate = f"{''.join(price_formate[:len(price_formate) - 3])} {''.join(price_formate[-3:])}"

            builder.row(
                InlineKeyboardButton(text=f"7 дней за 1₽, затем {subs['name']} за {price_formate}₽", callback_data=f"subscription_{subs['id_subscription']}")
            )

    return builder.as_markup()

async def subscription_management_keyboard(tg_id: int):
    info_user_subscription = await User.get_info_subscription_user(tg_id=tg_id)
    autopayment_user = info_user_subscription.get('auto_payment', None)
    builder = InlineKeyboardBuilder()
    if info_user_subscription:
        if info_user_subscription['id_subscription'] == 998:
            builder.row(
                InlineKeyboardButton(text="Оформить подписку", callback_data='start_subscriptions')
            )
        else:
            builder.row(
                InlineKeyboardButton(text="Изменить тариф", callback_data='chaige_subscriptions')
            )
    if not info_user_subscription:
        builder.row(
            InlineKeyboardButton(text="Оформить подписку", callback_data='start_subscriptions')
        )
    builder.row(
        InlineKeyboardButton(text="Активировать промокод", callback_data='activate_promo')
    )

    if autopayment_user:
        builder.row(
            InlineKeyboardButton(text='Отменить подписку', callback_data='disable_autopayment')
        )

    return builder.as_markup()

async def chage_subscription():
    subscriptions = await PaymentDatabase.get_all_subscriptions()
    builder = InlineKeyboardBuilder()

    # Добавляем первую строку: две кнопки рядом


    for subs in subscriptions:
        if subs['id_subscription'] not in [998, 999]:
            price_formate = [_ for _ in str(int(subs['price']))]
            price_formate = f"{''.join(price_formate[:len(price_formate) - 3])} {''.join(price_formate[-3:])}"

            builder.row(
                InlineKeyboardButton(text=f"{subs['name']} за {price_formate} рублей", callback_data=f"chage_subscriptions_{subs['id_subscription']}")
            )

    return builder.as_markup()


async def start_subscription():
    subscriptions = await PaymentDatabase.get_all_subscriptions()
    builder = InlineKeyboardBuilder()

    # Добавляем первую строку: две кнопки рядом


    for subs in subscriptions:
        if subs['id_subscription'] not in [998, 999]:
            price_formate = [_ for _ in str(int(subs['price']))]
            price_formate = f"{''.join(price_formate[:len(price_formate) - 3])} {''.join(price_formate[-3:])}"

            builder.row(
                InlineKeyboardButton(text=f"{subs['name']} за {price_formate} рублей", callback_data=f"start_subscriptions_{subs['id_subscription']}")
            )

    return builder.as_markup()

async def get_seller_culture():
    list_products = [
        "Пшеница",
        "Кукуруза",
        "Подсолнечник",
        "Ячмень",
        "Горох",
        "Рапс",
        "Лён",
        "Соя",
    ]

    builder = InlineKeyboardBuilder()
    for i in range(0, len(list_products), 2):
        row_buttons = []
        for name in list_products[i : i + 2]:
            callback = f"get_seller_{name}"
            row_buttons.append(
                InlineKeyboardButton(text=name, callback_data=callback)
            )
        builder.row(*row_buttons)

    return builder.as_markup()


async def get_basis_keyboard():
    bases = [
        "Порт Ростов",
        "Порт Азов",
        "Порт Тамань",
        "Порт Новороссийск",
        "Рынок РФ (переработка)"
    ]
    builder = InlineKeyboardBuilder()

    # Кнопка «Выбрать все базы»


    # Остальные варианты как раньше
    for name in bases:
        builder.row(
            InlineKeyboardButton(text=name, callback_data=f"get_basis_{name}")
        )

    builder.row(
        InlineKeyboardButton(text="Выбрать все", callback_data="get_basis_all")
    )

    return builder.as_markup()