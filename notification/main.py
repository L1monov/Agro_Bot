import asyncio
import aiohttp
import re
from datetime import date, datetime

from data.database import User, Notificaion, MessageLog
from config import BOT_TOKEN
from filter import contains_stop_words, STRICT_PRODUCT_KEYWORDS

# Инициализируем базы
NotificaionDB = Notificaion()
UserDB        = User()
LogDB         = MessageLog()


def build_text(declaration: dict, mirrored_date: str) -> str:
    def from_value(key):
        v = declaration.get(key)
        return v if v not in (None, "NULL", "null", "") else "Не указано"

    person_name = from_value("applicant_person_name") or from_value("manufacturer_person_name")
    short_name  = declaration.get("applicant_short_name") or from_value("applicant_full_name") or person_name
    addresses   = [
        from_value("applicant_activity_address"),
        from_value("applicant_location_address"),
        from_value("manufacturer_production_address"),
        from_value("manufacturer_location_address")
    ]
    full_address = next((a for a in addresses if a != "Не указано"), "Не указано")

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
    return text


async def send_msg(session, declaration: dict, tg_id: int, mirrored_date: str):
    # Строим текст и отправляем сообщение
    text = build_text(declaration, mirrored_date)
    url_req = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": tg_id,
        "text": text,
        "parse_mode": "HTML",
        "protect_content": True
    }
    async with session.post(url_req, json=payload) as response:
        resp_json = await response.json()
        if resp_json.get("ok"):
            message_id = resp_json["result"]["message_id"]
            # Сохраняем chat_id, message_id и текст в bot_messages
            await NotificaionDB.save_msg(tg_id, message_id, text)
            return message_id, text
    return None, None


async def send_new_declarations():
    async with aiohttp.ClientSession() as session:
        while True:
            new_declarations = await NotificaionDB.get_new_dec()
            users_with_subscription = await UserDB.get_users_with_subc()

            for declaration in new_declarations:
                # Обработка даты
                raw_date = declaration.get("declaration_date")
                if raw_date and raw_date not in ("NULL", "null", ""):
                    try:
                        if isinstance(raw_date, (datetime, date)):
                            mirrored_date = raw_date.strftime("%d.%m.%Y")
                        else:
                            mirrored_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d.%m.%Y")
                    except Exception as e:
                        print(f"[DATE ERROR] {raw_date} — {e}")
                        mirrored_date = "Не указано"
                else:
                    mirrored_date = "Не указано"

                product_name        = (declaration.get("product_name") or "").lower()
                product_designation = (declaration.get("product_designation") or "").lower()

                # Стоп-слова
                if contains_stop_words(product_name) or contains_stop_words(product_designation):
                    continue

                # Адреса для сопоставления регионов
                addresses = [
                    (declaration.get("applicant_activity_address") or "").lower(),
                    (declaration.get("applicant_location_address") or "").lower(),
                    (declaration.get("manufacturer_production_address") or "").lower(),
                    (declaration.get("manufacturer_location_address") or "").lower()
                ]

                for user in users_with_subscription:
                    user_products = user.get("products_list", [])
                    user_regions  = user.get("regions_list", [])
                    if not user_products or not user_regions:
                        continue

                    # Совпадение по продуктам
                    matched_products = []
                    for kw in user_products:
                        k = kw.lower()
                        if k in STRICT_PRODUCT_KEYWORDS:
                            if re.search(rf"\b{re.escape(k)}\b", product_name) or \
                               re.search(rf"\b{re.escape(k)}\b", product_designation):
                                matched_products = [kw]
                                break
                        elif k in product_name or k in product_designation:
                            matched_products.append(kw)
                    if not matched_products:
                        continue

                    # Совпадение по регионам
                    matched_regions = [
                        region for region in user_regions
                        if any(region.lower() in addr for addr in addresses)
                    ]
                    if not matched_regions:
                        continue

                    # Отправляем сообщение и получаем текст
                    message_id, message_text = await send_msg(session, declaration, user['tg_id'], mirrored_date)


            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(send_new_declarations())
