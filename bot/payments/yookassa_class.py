import uuid
import json
import asyncio
from aiogram import Bot
from yookassa import Configuration, Payment
from data.database import PaymentDatabase
from config import account_id, secret_key
Configuration.account_id = account_id
Configuration.secret_key = secret_key

class PaymentClass:
    database = PaymentDatabase()

    def __init__(self, tg_id: int, id_subscription: int, bot: Bot):
        self.tg_id = tg_id
        self.chat_id = tg_id
        self.id_subscription = id_subscription
        self.bot = bot

    async def create_payment(self, trial_subscription: bool = True):
        inf_sub = await self.database.get_info_subscription(id_subs=self.id_subscription)
        self.info_subsription = inf_sub

        description = self.info_subsription['description']
        value = 1.00 if trial_subscription else self.info_subsription['price']
        value = round(float(value), 2)

        payment = Payment.create({
            "amount": {
                "value": str(value),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://example.com/payment_success"
            },
            "capture": True,
            "description": description,
            "save_payment_method": True,
            "receipt": {
                "tax_system_code": 6,
                "customer": {
                    "full_name": "Березников Вячеслав Олегович",
                    "email": "bere3nikov@gmail.com"
                },
                "items": [{
                    "description": description,
                    "quantity": 1.0,
                    "amount": {
                        "value": str(value),
                        "currency": "RUB"
                    },
                    "vat_code": 1,
                    "payment_subject": "service",
                    "payment_mode": "full_payment"
                }]
            }
        }, uuid.uuid4())

        payment_json = json.loads(payment.json())
        self.payment_id = payment_json['id']

        await self.database.add_payment(tg_id=self.tg_id, payment_id=self.payment_id, value=str(value))
        return payment_json['confirmation']['confirmation_url']

    # async def auto_payment(self, payment_method_id):
    #     payment = Payment.create({
    #         "amount": {
    #             "value": "2.00",
    #             "currency": "RUB"
    #         },
    #         "capture": True,
    #         "payment_method_id": payment_method_id,
    #         "description": "Заказ №37"
    #     })

    async def check_payment(self, trial_subscription: bool = True):
        from keyboards.builder import get_main_menu
        max_checks = 20  # 10 минут / 30 секунд

        for attempt in range(max_checks):
            check = Payment.find_one(payment_id=self.payment_id)
            result_json = json.loads(check.json())
            status = result_json.get("status")

            if status == "succeeded":
                payment_method_id = result_json['payment_method']['id']
                await self.database.succeeded_payment(payment_id=result_json['id'], payment_method_id=payment_method_id)

                await self.database.deactivate_current_subscription(self.tg_id)

                await self.database.activate_subscription(
                    tg_id=self.tg_id,
                    payment_id=result_json['id'],
                    subscription_id=self.id_subscription,
                    trial_subscription=trial_subscription
                )

                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text="✅ Ваша подписка активирована!",
                    reply_markup=await get_main_menu()
                )

                return result_json

            elif status in ["canceled", "waiting_for_capture", "expired", "failed"]:
                print(f"❌ Платеж завершился со статусом: {status}")
                return result_json

            await asyncio.sleep(30)

        return {"status": "timeout"}


