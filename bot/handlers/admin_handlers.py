from data.database import PaymentDatabase
import secrets
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from keyboards.builder import get_main_menu

PaymentDatabase = PaymentDatabase
router = Router()
admins_list = [218881994, 854686840]


# Состояние для FSM
class PromoState(StatesGroup):
    waiting_for_code = State()


# Команда: создать промокод (только для админов)
@router.message(Command(commands=["create_promo"]))
async def create_promo(message: Message):
    if message.from_user.id not in admins_list:
        return await message.answer("⛔ У вас нет прав для использования этой команды.")

    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        return await message.answer("❌ Используйте формат:\n/create_promo <активаций> <дней>\nПример: /create_promo 5 7")

    activation_count, duration_days = int(args[1]), int(args[2])
    promo_code = secrets.token_hex(11).upper()

    await PaymentDatabase.add_promo(promo=promo_code, days_activate=duration_days, count_activate=activation_count)

    await message.answer(
        f"🎁 Вот ваш промо: <code>/promo {promo_code}</code>\n"
        f"Кол-во активаций: <b>{activation_count}</b>\n"
        f"Длительность подписки: <b>{duration_days} дней</b>",
        parse_mode="HTML"
    )


# Команда: активация промокода через /promo
@router.message(Command(commands=["promo"]))
async def promo_command_handler(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Укажите промокод. Пример: /promo AB12CD34")

    await handle_promo_code(message, args[1].strip(), state)


# Кнопка: "Активировать промокод"
@router.message(F.text == "Активировать промокод")
async def activate_promo_button(message: Message, state: FSMContext):
    await message.answer("""Совершая активацию, вы соглашаетесь с <a href="http://xn--80aaakg2dnbd.xn--p1ai/oferta">офертой</a>.\n\n🔐 Введите промокод:""",
                         parse_mode="HTML")
    await state.set_state(PromoState.waiting_for_code)


# Inline-кнопка: "Активировать промокод"
@router.callback_query(F.data == "activate_promo")
async def activate_promo_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("""Совершая активацию, вы соглашаетесь с <a href="http://xn--80aaakg2dnbd.xn--p1ai/oferta">офертой</a>.\n\n🔐 Введите промокод:""",
                                     parse_mode="HTML")
    await state.set_state(PromoState.waiting_for_code)


# Обработка ввода промокода
@router.message(PromoState.waiting_for_code)
async def promo_input_handler(message: Message, state: FSMContext):
    await handle_promo_code(message, message.text.strip(), state)


# Универсальная функция активации
async def handle_promo_code(message: Message, promo_code: str, state: FSMContext):
    db = PaymentDatabase
    promo_code = promo_code.upper()

    result = await db.execute_query('SELECT * FROM promocodes WHERE promocode = %s', (promo_code,))
    if not result:
        await state.clear()
        return await message.answer("❌ Промокод не найден.")

    promo = result[0]
    if promo["number_of_activations"] <= 0:
        await state.clear()
        return await message.answer("❌ У этого промокода закончились активации.")

    await db.activate_promo_subscription(
        tg_id=message.from_user.id,
        promo_code=promo_code,
        duration_days=promo["days_activate"]
    )

    await db.execute_query('UPDATE promocodes SET count_activated = count_activated - 1 WHERE promocode = %s', (promo_code,))
    keyboard = await get_main_menu()
    await message.answer(
        f"✅ Подписка по промокоду активирована на {promo['days_activate']} дней!",
        reply_markup=keyboard
    )
    await state.clear()