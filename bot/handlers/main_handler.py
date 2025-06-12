from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.types import CallbackQuery
from keyboards.builder import get_choice_products, get_choice_regions, subscription_management_keyboard
from texts import get_msg_choice_product, get_tex_podderjka, get_actual_price_msg
from data.database import Declaration, User, Sellers
from utils.filter import filter_sellers
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

router = Router()
User = User()
Sellers = Sellers()

from aiogram.fsm.state import State, StatesGroup
from keyboards.builder import get_seller_culture, get_basis_keyboard
from texts import get_end_subscription
class PriceStates(StatesGroup):
    choosing_culture = State()
    choosing_basis = State()



@router.message(F.text == "Выбор продукции")
async def start(message: Message, bot: Bot):
    info_user_subscription = await User.get_info_subscription_user(tg_id=message.from_user.id)
    if not info_user_subscription:
        text = await get_end_subscription()
        return await message.answer(
            text=text
            , parse_mode="HTML"
        )
    keyboard = await get_choice_products(tg_id=message.from_user.id)
    msg = await get_msg_choice_product()
    return await message.answer(text=msg, reply_markup=keyboard)

@router.message(F.text == "Выбор региона")
async def choice_region(message: Message, bot: Bot):
    keyboard = await get_choice_regions(tg_id=message.from_user.id, page=1)
    info_user_subscription = await User.get_info_subscription_user(tg_id=message.from_user.id)
    if not info_user_subscription:
        text = await get_end_subscription()
        return await message.answer(
            text=text, parse_mode="HTML"
        )
    msg = "Выберите регион:"
    return await message.answer(text=msg, reply_markup=keyboard)





@router.message(F.text == "Актуальные цены")
async def cmd_actual_prices(message: Message, state: FSMContext):
    await state.clear()
    keyboard = await get_seller_culture()
    msg = await get_actual_price_msg()
    await message.answer(
        text=msg,
        reply_markup=keyboard
    )
    await state.set_state(PriceStates.choosing_culture)


@router.callback_query(PriceStates.choosing_culture, F.data.startswith("get_seller_"))
async def process_culture_choice(callback: CallbackQuery, state: FSMContext):
    culture = callback.data.removeprefix("get_seller_")
    await state.update_data(chosen_culture=culture)

    basis_kb = await get_basis_keyboard()
    await callback.message.edit_text(
        text=f"Вы выбрали: <b>{culture}</b>\n\nТеперь выберите базис приёма:",
        reply_markup=basis_kb,
        parse_mode="HTML"
    )
    await state.set_state(PriceStates.choosing_basis)
    await callback.answer()


@router.callback_query(PriceStates.choosing_basis, F.data.startswith("get_basis_"))
async def process_basis_choice(callback: CallbackQuery, state: FSMContext):
    raw_basis = callback.data.removeprefix("get_basis_")
    await state.update_data(chosen_basis=raw_basis)

    data = await state.get_data()
    culture = data["chosen_culture"]

    # Если выбрали «Все базы»
    if raw_basis == "all":
        basis = ""
        display_text = f"Вы выбрали: <b>{culture}</b> — <i>все базы приёма</i>"
    else:
        basis = raw_basis
        # Формируем текстовый ответ для пользователя
        display_text = f"Вы выбрали: <b>{culture}</b> — <i>{basis}</i>"
        # Если это порт, убираем «Порт » из фильтра
        if "Порт" in basis:
            basis = basis.replace("Порт ", "")

    # Изменяем текст в сообщении, чтобы показать выбор, и убираем старую клавиатуру
    await callback.message.edit_text(
        text=display_text + "\n\nСобираю актуальные цены...",
        parse_mode="HTML"
    )
    await callback.answer()

    # Получаем все предложения: если basis == "", фильтра по адресу не будет
    sellers = await Sellers.get_sellers(basis=basis, culture=culture)
    grouped = await filter_sellers(announcements=sellers)
    if not grouped:
        return await callback.message.answer(text="По вашим фильтрам нет предложений")

    for company, addresses in grouped.items():
        for address, offers in addresses.items():
            lines = []
            for o in offers:
                specs = o.get("specs", "").strip()
                if not specs:
                    continue
                price = o.get("price", "").strip() or "—"
                lines.append(f"{specs} – {price}")

            if not lines:
                continue

            text = (
                f"<b>{company.upper()}</b>\n"
                f"{address}:\n\n"
                + "\n\n".join(lines)
            )
            try:
                await callback.message.answer(text=text, parse_mode="HTML")
            except Exception:
                print(f"[TOO LONG MESSAGE]\n{text}")
                continue

    await state.clear()
    await callback.message.answer(text="Готово – показаны все актуальные цены.")



@router.message(F.text == "Поддержка")
async def help(message: Message, bot: Bot):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Написать в поддержку", url="https://t.me/agroradar_support")]
        ]
    )
    msg = await get_tex_podderjka()

    try:
        await message.edit_text(text=msg, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        # Если редактировать нельзя (например, если это обычное сообщение от пользователя) — отправляем новое
        await message.answer(text=msg, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "Поделиться ботом")
async def send_welcome(message: Message, bot: Bot):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.types.copy_text_button import CopyTextButton

    bot_username = (await bot.get_me()).username

    tg_id = message.from_user.id
    referral_code = await User.get_user_referal(tg_id=tg_id)  # Получаем реферальный код

    bot_link = f"https://t.me/{bot_username}?start={referral_code}"

    # Кнопка для отправки реферальной ссылки
    copy_button = InlineKeyboardButton(
        text="📋 Копировать ссылку",
        copy_text=CopyTextButton(text=bot_link)
    )
    copy_keyboard = InlineKeyboardMarkup(inline_keyboard=[[copy_button]])

    msg = f"""<b>Поделитесь ссылкой и получите бонус!</b>
За каждого оформившего подписку по вашей ссылке — 14 дней бесплатного доступа.

Скопируйте и отправьте эту ссылку:
    """
    try:
        await message.edit_text(text=msg,parse_mode="HTML")
        await message.answer(text=bot_link, parse_mode="HTML")
    except Exception:
        await message.answer(text=msg, parse_mode="HTML")
        await message.answer(text=bot_link,  parse_mode="HTML")


PAGE_SIZE = 10
MAX_DECLS = 50

async def _send_declarations_page(chat, state: FSMContext):
    data = await state.get_data()
    decls = data.get("decls", [])
    offset = data.get("offset", 0)

    page = decls[offset : offset + PAGE_SIZE]
    page.reverse()
    for declaration in page:
        from datetime import datetime, date

        from_value = lambda key: declaration.get(key) if declaration.get(key) not in [None, "NULL", "null", ""] else "Не указано"

        addresses = [
            from_value("applicant_activity_address"),
            from_value("applicant_location_address"),
            from_value("manufacturer_production_address"),
            from_value("manufacturer_location_address")
        ]
        full_address = next((a for a in addresses if a != "Не указано"), "Не указано")

        raw_date = declaration.get("declaration_date")
        if raw_date and raw_date not in ["NULL", "null", ""]:
            try:
                if isinstance(raw_date, (datetime, date)):
                    mirrored_date = raw_date.strftime("%d.%m.%Y")
                else:
                    mirrored_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            except:
                mirrored_date = "Не указано"
        else:
            mirrored_date = "Не указано"

        person_name = from_value("applicant_person_name") or from_value("manufacturer_person_name")
        short_name = declaration.get("applicant_short_name") or from_value("applicant_full_name") or from_value("manufacturer_person_name")

        text = f"""
<b>ID декларации:</b> {from_value("declaration_id")}
<b>Наименование продукции:</b> {from_value("product_name")}
<b>Обозначение продукции:</b> {from_value("product_designation")}
<b>Размер партии:</b> {from_value("batch_size")}
<b>Дата декларации:</b> {mirrored_date}
<b>Заявитель:</b> {short_name}
<b>ИНН:</b> {from_value("applicant_inn")}
<b>Адрес:</b> {full_address}
<b>Имя заявителя:</b> {person_name}
<b>Телефон:</b> {from_value("applicant_phone") or from_value("manufacturer_phone")}
<b>Почта:</b> {from_value("applicant_email") or from_value("manufacturer_email")}
""".strip()

        # не отправляем слишком длинные
        if len(text) <= 4000:
            await chat.answer(text=text, protect_content=True, parse_mode="HTML")

    # после вывода страницы — кнопка "Показать ещё?", если остались
    new_offset = offset + PAGE_SIZE
    total = len(decls)
    if new_offset < total:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="Показать ещё",
                    callback_data="show_more_decls"
                )]
            ]
        )
    else:
        kb = None

    await chat.answer(
        text=f"{min(new_offset, total)} последних деклараций показано",
        reply_markup=kb
    )

@router.message(F.text == "Последние данные")
async def get_last_declarations(message: Message, state: FSMContext):
    from utils.filter import contains_stop_words, should_skip_company

    # проверяем подписку
    info_user_subscription = await User.get_info_subscription_user(tg_id=message.from_user.id)
    if not info_user_subscription:
        text = await get_end_subscription()
        return await message.answer(
            text=text, parse_mode="HTML"
        )

    # получаем все декларации
    declarationDB = Declaration()
    all_decls = await declarationDB.get_last_declaration(tg_id=message.from_user.id)

    # фильтрация стоп-слов и компаний, собираем максимум MAX_DECLS
    selected = []
    for decl in all_decls:
        if len(selected) >= MAX_DECLS:
            break

        pn = (decl.get("product_name") or "").lower()
        des = (decl.get("product_designation") or "").lower()
        # особое исключение для сафлор
        if "масло" in pn and "сафлор" in pn or "масло" in des and "сафлор" in des:
            continue

        company = (
            decl.get("applicant_short_name")
            or decl.get("manufacturer_short_name")
            or decl.get("applicant_full_name")
            or decl.get("manufacturer_full_name") or ""
        ).strip()
        if should_skip_company(company, pn, des):
            continue

        allow_k = "крахмал" in pn or "крахмал" in des
        allow_m = "масло" in pn
        if contains_stop_words(pn, allow_k, allow_m) or contains_stop_words(des, allow_k, allow_m):
            continue

        selected.append(decl)

    if not selected:
        return await message.answer("По вашим фильтрам пока нет деклараций.")


    # сохраняем список и сбрасываем offset
    await state.update_data(decls=selected, offset=0)
    # отправляем первую страницу
    await _send_declarations_page(message, state)

@router.callback_query(F.data == "show_more_decls")
async def show_more_declarations(callback: CallbackQuery, state: FSMContext):
    info_subscription = await User.get_info_subscription_user(tg_id=callback.from_user.id)
    is_trial = False
    if info_subscription and info_subscription.get("id_subscription") == 998:
        if info_subscription.get("status") == "active":
            is_trial = True
    if is_trial:
        msg = (
            "Сейчас доступны 10 последних деклараций.\n\n"
            "С подпиской вы сможете просматривать до 50 последних деклараций "
            "по выбранной продукции и регионам."
        )
        # Получаем клавиатуру управления подпиской (как в хендлере «Управление подпиской»)
        kb = await subscription_management_keyboard(tg_id=callback.from_user.id)
        await callback.message.answer(text=msg, reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return

    # 3) Иначе — обычная логика «показать ещё»
    data = await state.get_data()
    offset = data.get("offset", 0) + PAGE_SIZE
    await state.update_data(offset=offset)
    await _send_declarations_page(callback.message, state)
    await callback.answer()


