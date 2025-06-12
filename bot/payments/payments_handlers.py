import asyncio

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.types import CallbackQuery

from utils.substing_check import ContainsSubstringFilter
from keyboards.builder import  subscription_management_keyboard
from payments.yookassa_class import PaymentClass
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


from data.database import User, PaymentDatabase

PaymentDatabase = PaymentDatabase()
User = User()
router = Router()




@router.callback_query(ContainsSubstringFilter('subscription_'))
async def main_event_fill_day(callback_query: CallbackQuery, bot: Bot):
    id_subscrion = callback_query.data.split("_")[-1]
    Payment = PaymentClass(tg_id=callback_query.from_user.id, id_subscription=int(id_subscrion),bot=bot )
    url_payment = await Payment.create_payment()

    price_formate = [_ for _ in str(int(Payment.info_subsription['price']))]
    price_formate = f"{''.join(price_formate[:len(price_formate) - 3])} {''.join(price_formate[-3:])}"

    msg = f"""Вы выбрали тарифный план <b>“{Payment.info_subsription['description']}“</b> 
Стоимостью <b>{price_formate}</b> рублей. 
Для активации пробного периода перейдите по ссылке и выполните оплату.

<a href="{url_payment}">Ссылка на оплату</a>
"""


    await callback_query.message.edit_text(
        text=msg,
        parse_mode="HTML"
    )
    # ⏳ Запуск отслеживания в фоне
    asyncio.create_task(Payment.check_payment())


@router.message(F.text == "Управление подпиской")
async def manage_sub(message: Message, bot: Bot):
    info_subscription = await User.get_info_subscription_user(tg_id=message.from_user.id)
    keyboard = await subscription_management_keyboard(tg_id=message.from_user.id)
    if info_subscription and info_subscription['status'] == 1:
        end_date = info_subscription['end_date'].strftime("%d.%m.%Y")  # формат: 04.05.2025
        if info_subscription['subscription_id'] == 998:
            msg = f"Пробный доступ активен до <b>{end_date}</b>."

        else:
            msg = f"📅 Ваша подписка активна до <b>{end_date}</b>."
    else:
        msg = "У вас нет активной подписки."

    return await message.answer(text=msg, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(ContainsSubstringFilter('disable_autopayment'))
async def main_event_fill_day(callback_query: CallbackQuery, bot: Bot):

    await PaymentDatabase.disable_auto_payment(tg_id=callback_query.from_user.id)

    text = f"""Вы успешно отменили подписку"""

    await callback_query.message.edit_text(
        text=text,
        parse_mode="HTML"
    )

@router.callback_query(ContainsSubstringFilter('resolve_autopayment'))
async def main_event_fill_day(callback_query: CallbackQuery, bot: Bot):

    await PaymentDatabase.resolve_auto_payment(tg_id=callback_query.from_user.id)

    text = f"""Вы успешно включили автоплатёж"""

    await callback_query.message.edit_text(
        text=text,
        parse_mode="HTML"
    )

@router.callback_query(ContainsSubstringFilter('start_subscriptions'))
async def handle_start_subscription(callback_query: CallbackQuery, bot: Bot):
    subscriptions = await PaymentDatabase.get_all_subscriptions()
    buttons = []

    for subs in subscriptions:
        if subs['id_subscription'] in [998, 999]:
            continue

        payment_instance = PaymentClass(
            tg_id=callback_query.from_user.id,
            id_subscription=subs['id_subscription'],
            bot=bot
        )
        url = await payment_instance.create_payment(trial_subscription=False)

        price = int(subs["price"])
        formatted_price = f"{price:,}".replace(",", " ")

        buttons.append(
            InlineKeyboardButton(
                text=f"{subs['name']} — {formatted_price}₽",
                url=url
            )
        )

        asyncio.create_task(payment_instance.check_payment(trial_subscription=False))

    keyboard = InlineKeyboardBuilder()
    for btn in buttons:
        keyboard.row(btn)

    await callback_query.message.edit_text(
        text=(
            "Оформляя подписку, вы соглашаетесь с "
            "<a href='http://xn--80aaakg2dnbd.xn--p1ai/oferta'>офертой</a>."
            "\n\n"
            "<b>Выберите тариф и перейдите по ссылке для оплаты</b>"
        ),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
@router.callback_query(ContainsSubstringFilter('chaige_subscriptions'))
async def handle_change_subscription(callback_query: CallbackQuery, bot: Bot):
    subscriptions = await PaymentDatabase.get_all_subscriptions()
    buttons = []

    for subs in subscriptions:
        if subs['id'] in [998, 999]:
            continue

        payment_instance = PaymentClass(
            tg_id=callback_query.from_user.id,
            id_subscription=subs['id'],
            bot=bot
        )
        url = await payment_instance.create_payment(trial_subscription=False)

        price = int(subs["price"])
        formatted_price = f"{price:,}".replace(",", " ")

        buttons.append(
            InlineKeyboardButton(
                text=f"{subs['name']} — {formatted_price}₽",
                url=url
            )
        )

        asyncio.create_task(payment_instance.check_payment(trial_subscription=False))

    keyboard = InlineKeyboardBuilder()
    for btn in buttons:
        keyboard.row(btn)

    await callback_query.message.edit_text(
        text=(
            "<b>Выберите новый тариф и перейдите по ссылке для оплаты</b>"
        ),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )


