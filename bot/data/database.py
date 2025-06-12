from typing import List, Union,  Optional
from datetime import datetime

import asyncio
import aiomysql

from config import DB_LOGIN, DB_PASSWORD, DB_PORT, DB_HOST, DB_NAME
from utils.filter import match_product_keywords

class AsyncDataBase:
    def __init__(self):
        self.pool = None

    async def init(self):
        if not self.pool:
            self.pool = await aiomysql.create_pool(
                host=DB_HOST,
                port=int(DB_PORT),
                user=DB_LOGIN,
                password=DB_PASSWORD,
                db=DB_NAME,
                cursorclass=aiomysql.DictCursor
            )

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute_query(self, query: str, args: tuple = ()) -> Union[None, List]:
        await self.init()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, args)
                await conn.commit()
                result = await cursor.fetchall()
                return result

    async def get_id_user(self, tg_user: int):

        query = 'select * from users where tg_id = %s'
        args = (tg_user, )
        result = await self.execute_query(query, args)
        return result[0]['id_user']

    async def log_message(
            self,
            message_id: int,
            user_id: int,
            text: str,
            sender: str,
            timestamp: Optional[datetime] = None,
            type_log: int = 1
    ):
        user_id = await self.get_id_user(tg_user=user_id)

        """Записать в таблицу сообщение."""
        ts = timestamp or datetime.utcnow()
        query = """
            INSERT INTO messages_log
                (id_message, id_user, sender, text, type_log)
            VALUES (%s, %s, %s, %s, %s)
        """
        await self.execute_query(query, (message_id, user_id, sender, text, type_log))

class User(AsyncDataBase):

    async def get_all_users_tg(self):
        query = 'select * from users'
        result = await self.execute_query(query)
        return [user['tg_id'] for user in result]

    async def add_user(self, tg_id: int, username: str, referal_code: str = None):
        check_query = "select * from users where tg_id = %s"
        chech_args = (tg_id, )
        check_result = await self.execute_query(check_query, chech_args)
        if not check_result:
            query = "INSERT INTO `users`(`username`, `tg_id`, `referred_code`) VALUES (%s, %s, %s)"
            args = (username, tg_id, referal_code)
            await self.execute_query(query, args)
            return False
        return True

    async def get_info_user(self, tg_id: int):
        query = '''SELECT 
                  u.id_user,
                  u.username,
                  u.tg_id,
                  us.products_list ,
                  us.regions_list
                FROM users u
                JOIN user_filters us ON u.id_user = us.id_user
                where u.tg_id = %s
                '''
        args = (tg_id,)
        result = await self.execute_query(query, args)
        return result[0]

    async def start_trial_subscriptoin(self, tg_id: int):
        user_id = await self.get_id_user(tg_user=tg_id)

        query = """
                INSERT INTO user_subscriptions 
              (id_user, id_subscription, start_date, end_date, status, payment_id, auto_payment)
            VALUES
              (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), 1, %s, 0);
                """
        args = (user_id, 998, "")
        await self.execute_query(query, args)

    async def user_subscription(self, tg_id):
        user_id = await self.get_id_user(tg_user=tg_id)
        query = 'SELECT * FROM `user_subscriptions` WHERE id_user = %s'

        args = (user_id,)
        result = await self.execute_query(query, args)
        if result:
            return result[-1]['status']
        if not result:
            await self.start_trial_subscriptoin(tg_id=tg_id)
            return 1

    async def get_info_subscription_user(self, tg_id: int):
        user_id = await self.get_id_user(tg_user=tg_id)
        query = 'SELECT * FROM `user_subscriptions` where status = %s and id_user = %s'
        args = (1, user_id,)
        result = await self.execute_query(query, args)
        if result:
            return result[-1]
        else:
            return {}

    async def save_link(self, tg_id: int, ref_id: str, link: str, description: str):
        """
        Сохраняет новую реферальную ссылку в таблицу referral_links.
        Параметры:
          - tg_id: Telegram-ID создателя ссылки
          - ref_id: уникальный идентификатор (например, UUID)
          - link: полная глубокая ссылка (https://t.me/…?start=<ref_id>)
          - description: текстовое описание (может быть пустым)
        """
        id_user = await self.get_id_user(tg_user=tg_id)
        query = """
            INSERT INTO ad_links (
                ad_code,
                created_user_id,
                description,
                ad_link
            ) VALUES (%s, %s, %s, %s)
        """
        args = (ref_id, id_user, description, link)
        await self.execute_query(query, args)
        return True

    # Убрал потому что в start в add_user добавил реф ссылку
    # async def set_referral_link(self, tg_id: int, ref_id: str):
    #     """
    #     Записывает в колонку `referal_link` таблицы `users` значение ref_id
    #     для пользователя с данным tg_id.
    #     """
    #     query = """
    #         UPDATE users
    #         SET referal_link = %s
    #         WHERE tg_id = %s
    #     """
    #     args = (ref_id, tg_id)
    #     await self.execute_query(query, args)
    #     return True

    async def create_user_referal(self, tg_id: int ):
        import uuid
        user_id = await self.get_id_user(tg_user=tg_id)
        ref_id = uuid.uuid4().hex
        query = 'INSERT INTO `users_referrals_code`(`code`, `id_user`) VALUES (%s, %s)'
        args = (ref_id, user_id)
        await self.execute_query(query, args)

    async def get_user_referal(self, tg_id: int):
        user_id = await self.get_id_user(tg_user=tg_id)
        query_for_check = "select * from users_referrals_code where id_user = %s"
        args_for_check = (user_id,)
        result = await self.execute_query(query_for_check, args_for_check)
        if result:
            return result[0]['code']
        if not result:
            await self.create_user_referal(tg_id=tg_id)
            query_for_check = "select * from users_referrals_code where id_user = %s"
            args_for_check = (user_id,)
            result = await self.execute_query(query_for_check, args_for_check)
            return result[0]['code']

class Settings(AsyncDataBase):

    async def get_all_products(self):
        query = "select * from products"
        result = await self.execute_query(query)
        return result

    async def add_product(self, id_product: int, tg_id: int):
        await self.init()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Найти user_id по tg_id
                await cursor.execute("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))
                user_row = await cursor.fetchone()
                if not user_row:
                    return  # пользователь не найден
                user_id = user_row['id_user']

                # Получить текущий список продуктов
                await cursor.execute("SELECT products_list  FROM user_filters WHERE id_user = %s", (user_id,))
                settings_row = await cursor.fetchone()
                current_list = settings_row['products_list'] if settings_row else ""

                # Преобразуем строку в список
                products = [p for p in current_list.split(',') if p.strip()] if current_list else []

                if str(id_product) not in products:
                    products.append(str(id_product))
                    new_list = ",".join(products)
                    # Обновляем список продуктов
                    await cursor.execute(
                        "UPDATE user_filters SET products_list  = %s WHERE id_user = %s",
                        (new_list, user_id)
                    )
                    await conn.commit()

    async def remove_product(self, id_product: int, tg_id: int):
        await self.init()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Найти user_id по tg_id
                await cursor.execute("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))
                user_row = await cursor.fetchone()
                if not user_row:
                    return  # пользователь не найден
                user_id = user_row['id_user']

                # Получить текущий список продуктов
                await cursor.execute("SELECT products_list  FROM user_filters WHERE id_user = %s", (user_id,))
                settings_row = await cursor.fetchone()
                current_list = settings_row['products_list'] if settings_row else ""

                # Преобразуем строку в список
                products = [p for p in current_list.split(',') if p.strip()] if current_list else []

                # Удаляем id_product, если он есть
                if str(id_product) in products:
                    products.remove(str(id_product))
                    new_list = ",".join(products)
                    # Обновляем список продуктов
                    await cursor.execute(
                        "UPDATE user_filters SET products_list  = %s WHERE id_user = %s",
                        (new_list, user_id)
                    )
                    await conn.commit()

    async def reset_products(self, tg_id: int):
        # Найти user_id по tg_id
        user_row = await self.execute_query("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))

        if not user_row:
            return  # пользователь не найден
        user_id = user_row[0]['id_user']
        query = "UPDATE user_filters SET products_list  = %s WHERE id_user = %s"
        args = ("", user_id)
        await self.execute_query(query, args)

    async def select_all_products(self, tg_id: int):
        # Найти user_id по tg_id
        user_row = await self.execute_query("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))
        if not user_row:
            return  # пользователь не найден
        user_id = user_row[0]['id_user']

        products_list = await self.get_all_products()
        products = [product['id_product'] for product in products_list]
        products_str = ",".join(str(p) for p in products)

        query = 'update user_filters set products_list  = %s where id_user = %s'
        args = (products_str, user_id)
        await self.execute_query(query, args)

    # REGIONS

    async def get_all_regions(self):
        query = "select * from regions"
        result = await self.execute_query(query)
        return result

    async def add_region(self, id_region: int, tg_id: int):
        await self.init()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Найти user_id по tg_id
                await cursor.execute("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))
                user_row = await cursor.fetchone()
                if not user_row:
                    return  # пользователь не найден
                user_id = user_row['id_user']

                # Получить текущий список продуктов
                await cursor.execute("SELECT regions_list FROM user_filters WHERE id_user = %s", (user_id,))
                settings_row = await cursor.fetchone()
                current_list = settings_row['regions_list'] if settings_row else ""

                # Преобразуем строку в список
                products = [p for p in current_list.split(',') if p.strip()] if current_list else []

                if str(id_region) not in products:
                    products.append(str(id_region))
                    new_list = ",".join(products)
                    # Обновляем список продуктов
                    await cursor.execute(
                        "UPDATE user_filters SET regions_list = %s WHERE id_user = %s",
                        (new_list, user_id)
                    )
                    await conn.commit()

    async def remove_region(self, id_region: int, tg_id: int):
        await self.init()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Найти user_id по tg_id
                await cursor.execute("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))
                user_row = await cursor.fetchone()
                if not user_row:
                    return  # пользователь не найден
                user_id = user_row['id_user']

                # Получить текущий список продуктов
                await cursor.execute("SELECT regions_list FROM user_filters WHERE id_user= %s", (user_id,))
                settings_row = await cursor.fetchone()
                current_list = settings_row['regions_list'] if settings_row else ""

                # Преобразуем строку в список
                products = [p for p in current_list.split(',') if p.strip()] if current_list else []

                # Удаляем id_product, если он есть
                if str(id_region) in products:
                    products.remove(str(id_region))
                    new_list = ",".join(products)
                    # Обновляем список продуктов
                    await cursor.execute(
                        "UPDATE user_filters SET regions_list = %s WHERE id_user = %s",
                        (new_list, user_id)
                    )
                    await conn.commit()

    async def reset_regions(self, tg_id: int):
        # Найти user_id по tg_id
        user_row = await self.execute_query("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))

        if not user_row:
            return  # пользователь не найден
        user_id = user_row[0]['id_user']
        query = "UPDATE user_filters SET regions_list = %s WHERE id_user = %s"
        args = ("", user_id)
        await self.execute_query(query, args)

    async def select_all_regions(self, tg_id: int):
        # Найти user_id по tg_id
        user_row = await self.execute_query("SELECT id_user FROM users WHERE tg_id = %s", (tg_id,))
        if not user_row:
            return  # пользователь не найден
        user_id = user_row[0]['id_user']

        all_regions = await self.get_all_regions()
        products = [region['id_region'] for region in all_regions]
        products_str = ",".join(str(p) for p in products)

        query = 'update user_filters set regions_list = %s where id_user = %s'
        args = (products_str, user_id)
        await self.execute_query(query, args)

class PaymentDatabase(AsyncDataBase):
    async def add_payment(self, tg_id: int, payment_id: str, value: str):
        user_id = await self.get_id_user(tg_user=tg_id)

        query = """INSERT INTO `payments`(`id_payment`, `id_user`, `status`, `value`) VALUES (%s, %s, %s, %s)"""
        args = (payment_id, user_id, "pending", value)
        await self.execute_query(query, args)

    async def succeeded_payment(self, payment_id: str, payment_method_id: str):
        query = 'update payments set status = %s, payment_method_id = %s where id_payment = %s'
        args = ("succeeded", payment_method_id, payment_id)
        await self.execute_query(query, args)

    async def activate_subscription(self, tg_id: int, payment_id: str, subscription_id: int,
                                    trial_subscription: bool = False):
        user_id = await self.get_id_user(tg_user=tg_id)

        if trial_subscription:
            query = """
            INSERT INTO user_subscriptions
              (id_user, id_subscription, start_date, end_date, status, payment_id)
            VALUES
              (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), 1, %s)
               
            """
            args = (user_id, subscription_id, payment_id)
        else:
            # узнаём длительность подписки в месяцах
            query_duration = "SELECT duration_months FROM subscriptions WHERE id_subscription = %s"
            duration_result = await self.execute_query(query_duration, (subscription_id,))
            duration = duration_result[0]['duration_months']

            query = """
            INSERT INTO user_subscriptions
              (id_user, id_subscription, start_date, end_date, status, payment_id, auto_payment)
            VALUES
              (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL %s MONTH), 1, %s, 1)
            
            update user_subscriptions set  id_subscription = %s, start_date = NOW() end_date = DATE_ADD(NOW(), INTERVAL %s MONTH), 
            status = %s, payment_id = %s
              where id_user = %s
            """
            args = (subscription_id, duration, "active", payment_id, user_id)

        await self.execute_query(query, args)

    async def get_info_subscription(self, id_subs: int):
        query = 'select * from subscriptions where id_subscription = %s'
        args = (id_subs,)
        result = await self.execute_query(query, args)
        if result:
            return result[0]
        else:
            return "Not found subs"

    async def get_all_subscriptions(self):
        query = "SELECT * FROM `subscriptions`"
        result = await self.execute_query(query)
        return result

    async def disable_auto_payment(self, tg_id: int ):
        user_id = await self.get_id_user(tg_user=tg_id)

        query = 'update user_subscriptions set auto_payment = %s where id_user = %s and status = %s'
        args = (0, user_id, 1)
        await self.execute_query(query, args)

    async def resolve_auto_payment(self, tg_id: int):
        user_id = await self.get_id_user(tg_user=tg_id)

        query = 'update user_subscriptions set auto_payment = %s where id_user = %s and status = %s'
        args = (1, user_id, 1)
        await self.execute_query(query, args)

    async def activate_promo_subscription(self, tg_id: int, promo_code: str, duration_days: int):
        user_id = await self.get_id_user(tg_user=tg_id)

        query = """
        update user_subscriptions set id_subscription = %s, start_date = CURDATE(), end_date = DATE_ADD(CURDATE(), INTERVAL %s DAY), status = 1, payment_id = %s
         where id_user = %s
        
        """
        # subscription_id = 0 → для промокодов
        args = (999, duration_days, None, user_id)  # payment_id = None, если промо


        await self.execute_query(query, args)

    async def add_promo(self, promo: str, count_activate: int, days_activate: int):
        query = 'INSERT INTO `promocodes`(`promocode`, `count_activated`, `days_activate`) VALUES (%s, %s, %s)'
        args = (promo, count_activate, days_activate)
        await self.execute_query(query, args)

    async def deactivate_current_subscription(self, tg_id: int):
        user_id = await self.get_id_user(tg_user=tg_id)

        # Завершить текущую подписку (если есть)
        query = """
        UPDATE user_subscriptions
        SET status = 0, auto_payment = 0
        WHERE id_user = %s AND status = 1
        """
        await self.execute_query(query, (user_id,))

class Declaration(AsyncDataBase):

    async def get_last_declaration(self, tg_id: int):
        user_info = await User().get_info_user(tg_id)
        products_list = user_info.get("products_list", "")
        regions_list = user_info.get("regions_list", "")

        product_ids = [p.strip() for p in products_list.split(",") if p.strip()]
        region_ids = [r.strip() for r in regions_list.split(",") if r.strip()]

        if not product_ids or not region_ids:
            return []

        all_products = await Settings().get_all_products()
        all_regions = await Settings().get_all_regions()

        selected_product_names = [p["name_product"].lower() for p in all_products if str(p["id_product"]) in product_ids]
        selected_region_names = [r["name_region"].lower() for r in all_regions if str(r["id_region"]) in region_ids]

        # жесткое совпадение



        query = "SELECT * FROM declarations ORDER BY time_add DESC"
        all_declarations = await self.execute_query(query)

        result = []
        for decl in all_declarations:
            product_name = (decl.get("product_name") or "").lower()
            product_designation = (decl.get("product_designation") or "").lower()
            addresses = [
                (decl.get("applicant_activity_address") or "").lower(),
                (decl.get("applicant_location_address") or "").lower(),
                (decl.get("manufacturer_production_address") or "").lower(),
                (decl.get("manufacturer_location_address") or "").lower(),
            ]

            product_matched = match_product_keywords(
                selected_product_names,
                product_name,
                product_designation
            )

            region_matched = any(rn in addr for addr in addresses for rn in selected_region_names)

            if product_matched and region_matched:
                result.append(decl)

        return result

class Sellers(AsyncDataBase):

    async def get_sellers(self, basis: str, culture: str):
        if basis == "Ростов":
            basis = "Ростов-На-Дону"
        # Список разрешённых компаний (в нижнем регистре)
        allowed_companies = [
            "деметра трейдинг",
            "озк",
            "астон",
            "тамбовский бекон",
            "эфко",
            "черкизово",
            "юг руси",
            "доставка морем",
            "содружество",
        ]

        # Составляем условия вида LOWER(name_company) LIKE %s OR …
        company_like_clauses = " OR ".join(
            "LOWER(name_company) LIKE %s" for _ in allowed_companies
        )
        # Оборачиваем в скобки, чтобы группировать OR
        company_filter_sql = f"({company_like_clauses})"

        # Фильтр по культуре
        base_filter = "LOWER(name_product) LIKE %s"
        culture_arg = f"%{culture.lower()}%"

        if "рынок рф" in basis.lower():
            # при basis == "Рынок РФ" ещё исключаем адреса по ключевым городам
            query = f"""
                SELECT *
                FROM `sellers`
                WHERE {base_filter}
                  AND {company_filter_sql}
                  AND LOWER(company_address) NOT LIKE %s
                  AND LOWER(company_address) NOT LIKE %s
                  AND LOWER(company_address) NOT LIKE %s
                  AND LOWER(company_address) NOT LIKE %s
            """
            args = (
                culture_arg,
                # сюда по одной идут шаблоны для company_filter_sql
                *[f"%{c}%" for c in allowed_companies],
                # и затем исключения по адресам
                "%ростов%",
                "%азов%",
                "%тамань%",
                "%новороссийск%",
            )
        else:
            # для любых других basis — поиск по вхождению basis в адрес
            query = f"""
                SELECT *
                FROM `sellers`
                WHERE {base_filter}
                  AND {company_filter_sql}
                  AND LOWER(company_address) LIKE %s
            """
            args = (
                culture_arg,
                *[f"%{c}%" for c in allowed_companies],
                f"%{basis.lower()}%",
            )
        result = await self.execute_query(query, args)
        return result


async def main():
    user = User()
    result = await user.add_user(tg_id=854686840, username='123')
    print(result)

if __name__ == '__main__':
    asyncio.run(main())

