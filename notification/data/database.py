from typing import List, Union
import asyncio

import aiomysql

from config import DB_LOGIN, DB_PASSWORD, DB_PORT, DB_HOST, DB_NAME

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

class User(AsyncDataBase):
    async def add_user(self, tg_id: int, username: str):
        check_query = "select * from users where tg_id = %s"
        chech_args = (tg_id)
        check_result = await self.execute_query(check_query, chech_args)
        if not check_result:
            query = "INSERT INTO `users`(`username`, `tg_id`) VALUES (%s, %s)"
            args = (username, tg_id)
            await self.execute_query(query, args)


    async def get_users_with_subc(self):
        """
        Получение пользователей с подпиской и преобразование списков id продуктов и регионов в имена.
        """
        # 1. Получаем пользователей
        query = """SELECT 
                  u.id,
                  u.username,
                  u.tg_id,
                  us.products_list,
                  us.regions_list
                FROM users u
                JOIN user_settings us ON u.id = us.user_id
                join user_subscriptions usub ON u.id = usub.user_id
                where usub.status = 1
                """
        users = await self.execute_query(query)
        # 2. Получаем все продукты
        products_query = "SELECT id, name_product FROM products"
        products_result = await self.execute_query(products_query)
        products = {item['id']: item['name_product'] for item in products_result}

        # 3. Получаем все регионы
        regions_query = "SELECT id, name FROM regions"
        regions_result = await self.execute_query(regions_query)
        regions = {item['id']: item['name'] for item in regions_result}

        # 4. Заменяем id на названия у каждого пользователя
        for user in users:
            # Обработка продуктов
            if user['products_list']:
                product_ids = (int(pid) for pid in user['products_list'].split(',') if pid.strip())
                user['products_list'] = [products.get(pid, f"Unknown Product ID {pid}") for pid in product_ids]
            else:
                user['products_list'] = []

            # Обработка регионов
            if user['regions_list']:
                region_ids = (int(rid) for rid in user['regions_list'].split(',') if rid.strip())
                user['regions_list'] = [regions.get(rid, f"Unknown Region ID {rid}") for rid in region_ids]
            else:
                user['regions_list'] = []

        return users

class Notificaion(AsyncDataBase):
    async def get_new_dec(self):
        # Сначала получаем все декларации с notification = 0
        query_select = 'SELECT * FROM declarations WHERE notification = 0'
        result = await self.execute_query(query_select)

        # Затем обновляем все эти декларации, ставим notification = 1
        query_update = 'UPDATE declarations SET notification = 1 WHERE notification = 0'
        await self.execute_query(query_update)

        return result

    async def save_msg(self, chat_id: int, message_id: int, text: str):
        # Теперь сохраняем также текст отправленного сообщения
        query = 'INSERT INTO bot_messages (`chat_id`, `message_id`, `text`) VALUES (%s, %s, %s)'
        args = (chat_id, message_id, text)
        await self.execute_query(query, args)

class MessageLog(AsyncDataBase):
    async def log(self,
                  chat_id: int,
                  message_id: int,
                  declaration_id: str,
                  user_id: int,
                  matched_products: list[str],
                  matched_regions: list[str],
                  message_text: str):
        query = """
            INSERT INTO message_logs
              (chat_id, message_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        args = (
            chat_id,
            message_id,
            declaration_id,
            user_id,
            ",".join(matched_products),
            ",".join(matched_regions),
            message_text
        )
        print(args)
        await self.execute_query(query, args)
