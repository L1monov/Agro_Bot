import uuid
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import ChatMember
from data.database import User
from texts import *
from keyboards.builder import get_start_button, get_main_menu
from keyboards.tutotial import get_next_button



router = Router()
User = User()


@router.message(Command(commands=["start"]))
async def start(message: Message, bot: Bot):
    """
    Обработчик /start. Если приходит с аргументом (payload),
    сохраняем этот ref_id в поле `referal_link` таблицы `users`.
    """
    tg_id = message.from_user.id
    tg_username = message.from_user.username

    # Проверяем, есть ли аргумент после /start: берём message.text
    parts = message.text.split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""

    ref_id = None
    if payload:
        ref_id = payload

    # Проверяем, есть ли уже пользователь в БД
    user_created = await User.add_user(tg_id=tg_id, username=tg_username, referal_code=ref_id)
    if not user_created:
        # Если пользователь существует, запускаем триал, если нужно
        await User.start_trial_subscriptoin(tg_id=tg_id)

    # Шаг 1: пробный доступ
    text = await get_msg_trial_activated()
    # Кнопка «Далее» ведёт на шаг 2
    await message.answer(
        text=text,
        reply_markup=get_next_button(step=2),
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data and c.data.startswith("tutorial_step:"))
async def tutorial_step_handler(callback: CallbackQuery):
    _, step_str = callback.data.split(":")
    step = int(step_str)

    if step == 2:
        text = await get_msg_how_it_works()
        await callback.message.edit_text(
            text=text,
            reply_markup=get_next_button(step=3),
            parse_mode="HTML"
        )

    elif step == 3:
        text1 = await get_msg_bot_setup()
        await callback.message.edit_text(
            text=text1,
            reply_markup=None,
            parse_mode="HTML"
        )
        # Закрепляем отредактированное сообщение
        await callback.bot.pin_chat_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        text2 = "<b>‼️ Если меню пропало, нажмите на иконку в виде квадрата с четырьмя кругами рядом с полем ввода текста, чтобы открыть его снова ↘️</b>"
        sent = await callback.message.answer(
            text=text2,
            reply_markup=await get_main_menu(),
            parse_mode="HTML"
        )

    await callback.answer()


@router.message(Command(commands=["create_link"]))
async def create_link(message: Message, bot: Bot):
    """
    Создаёт уникальную реферальную ссылку с описанием.
    Пример: /create_link тестовая ссылка
    """
    # Вместо get_args() разбиваем message.text
    parts = message.text.split(maxsplit=1)
    description = parts[1].strip() if len(parts) > 1 else ""

    # Генерируем уникальный ID для ссылки
    ref_id = uuid.uuid4().hex

    # Строим глубокую ссылку на бота с параметром ref_id
    bot_username = (await bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={ref_id}"

    # Сохраняем в БД: ref_id, описание, саму ссылку и автора (tg_id)
    await User.save_link(
        tg_id=message.from_user.id,
        ref_id=ref_id,
        link=referral_link,
        description=description
    )

    # Отправляем ссылку пользователю
    response = (
        f"Ваша реферальная ссылка:\n\n"
        f"<code>{referral_link}</code>\n\n"
    )
    if description:
        response += f"Описание: {description}"
    else:
        response += "Без описания"

    await message.answer(
        text=response,
        parse_mode=ParseMode.HTML
    )


# Команда: создать промокод (только для админов)
@router.message(Command(commands=["send_msg"]))
async def create_promo(message: Message, bot: Bot):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.answer("❌ Используйте формат:\n/send_msg tg_id MESSAGE")

    tg_id, msg = int(args[1]), args[2]

    await bot.send_message(
        chat_id=tg_id,
        text=msg
    )

    await message.answer(
        text="Сообщение отправлено",
        parse_mode="HTML"
    )