from aiogram import Router
from aiogram.types import CallbackQuery

from utils.substing_check import ContainsSubstringFilter
from data.database import Settings
from keyboards.builder import get_choice_products, get_main_menu, get_choice_regions

router = Router()
settings = Settings()

async def _edit_keyboard(callback: CallbackQuery, keyboard) -> None:
    """Обновляет текст и клавиатуру у сообщения пользователя."""
    text = callback.message.text or ''
    await callback.message.edit_text(text=text, reply_markup=keyboard)

# --- Обработчики для выбора продукции ---

@router.callback_query(ContainsSubstringFilter('add_product_'))
async def add_product(callback: CallbackQuery) -> None:
    """Добавляет продукт в настройки пользователя и обновляет клавиатуру."""
    product_id = int(callback.data.rsplit('_', 1)[1])
    await settings.add_product(id_product=product_id, tg_id=callback.from_user.id)
    keyboard = await get_choice_products(tg_id=callback.from_user.id)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('delete_product_'))
async def delete_product(callback: CallbackQuery) -> None:
    """Удаляет продукт из настроек пользователя и обновляет клавиатуру."""
    product_id = int(callback.data.rsplit('_', 1)[1])
    await settings.remove_product(id_product=product_id, tg_id=callback.from_user.id)
    keyboard = await get_choice_products(tg_id=callback.from_user.id)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('reset_products'))
async def reset_products(callback: CallbackQuery) -> None:
    """Сбрасывает выбор всех продуктов и обновляет клавиатуру."""
    await settings.reset_products(tg_id=callback.from_user.id)
    keyboard = await get_choice_products(tg_id=callback.from_user.id)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('select_all_products'))
async def select_all_products(callback: CallbackQuery) -> None:
    """Выбирает все продукты и обновляет клавиатуру."""
    await settings.select_all_products(tg_id=callback.from_user.id)
    keyboard = await get_choice_products(tg_id=callback.from_user.id)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('main_menu'))
async def show_main_menu(callback: CallbackQuery) -> None:
    """Показывает главное меню после сохранения настроек."""
    keyboard = await get_main_menu()
    await callback.message.answer(text="Настройки сохранены✅", reply_markup=keyboard)

# --- Обработчики для выбора регионов ---

@router.callback_query(ContainsSubstringFilter('regions_page_'))
async def paginate_regions(callback: CallbackQuery) -> None:
    """Обрабатывает переключение страниц списка регионов."""
    page = int(callback.data.rsplit('_', 1)[1])
    keyboard = await get_choice_regions(tg_id=callback.from_user.id, page=page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(ContainsSubstringFilter('add_region_'))
async def add_region(callback: CallbackQuery) -> None:
    """Добавляет регион в настройки пользователя и обновляет клавиатуру."""
    parts = callback.data.split('_')
    page, region_id = int(parts[-2]), int(parts[-1])
    await settings.add_region(id_region=region_id, tg_id=callback.from_user.id)
    keyboard = await get_choice_regions(tg_id=callback.from_user.id, page=page)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('delete_region_'))
async def delete_region(callback: CallbackQuery) -> None:
    """Удаляет регион из настроек пользователя и обновляет клавиатуру."""
    parts = callback.data.split('_')
    page, region_id = int(parts[-2]), int(parts[-1])
    await settings.remove_region(id_region=region_id, tg_id=callback.from_user.id)
    keyboard = await get_choice_regions(tg_id=callback.from_user.id, page=page)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('reset_regions'))
async def reset_regions(callback: CallbackQuery) -> None:
    """Сбрасывает выбор всех регионов и обновляет клавиатуру."""
    await settings.reset_regions(tg_id=callback.from_user.id)
    keyboard = await get_choice_regions(tg_id=callback.from_user.id)
    await _edit_keyboard(callback, keyboard)

@router.callback_query(ContainsSubstringFilter('select_all_regions'))
async def select_all_regions(callback: CallbackQuery) -> None:
    """Выбирает все регионы и обновляет клавиатуру."""
    await settings.select_all_regions(tg_id=callback.from_user.id)
    keyboard = await get_choice_regions(tg_id=callback.from_user.id)
    await _edit_keyboard(callback, keyboard)
