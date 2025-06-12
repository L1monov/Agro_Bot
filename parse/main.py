import datetime
import time

import aiohttp
import asyncio
import json
from typing import List, Dict

from data.database import AsyncDataBase
from telegram import send_msg

database = AsyncDataBase()

# Список групп ЕЕУ для парса
ids_GroupEEU = [
16393,
16396,
16394,

]
# Список продуктов ЕЕУ для парса
ids_ProductEEU = [
11,
32,
12,
21,
22,
23,
24,
25,
26,
27,
28,
29,
30,
13,
31,
14,
15,
16,
17,
18,
19,
20,
33,
34,
35,
36,
37,
38,
39,
40,

]
# Список продуктов РФ для парса
ids_ProductRU = [

394,
396,
397,
425,
426,
432,
434,
663,
665,
669,
671,
673,
720,
721,
724,
725,
730,
734,
736,
745,
746,
747,
748,
749,
750,
751,
752,
753,
754,
737,
755,
756,
757,
758,
738,
739,
740,
741,
742,
743,
744,
928,
393,
395,
424,
662,
664,
709,
719,
733,
735,
927,
1388,
1392,
1352,
1378,
1386,
1233,
1231,
1232,
1235,
1234,
1237,
1276,
1353,
1379,
1381,
1383,
1385,
1390,
1391,
1389,
1413,
1403,
1395,
1418,
1393,
1401,
1399,
1417,
1405,
1404,
1414,
1406,
1411,
1400,
1408,
1410,
1402,
1412,
1415,
1397,
1409,
1398,
1396,
1407,

]

from headers_cookies import cookies, headers

MAX_CONCURRENT_REQUESTS = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def check_declaration_in_db(id_declaration: int):
    check = await database.get_info_declaration(id_deaclaration=id_declaration)
    return check


async def get_dop_info(session: aiohttp.ClientSession, id_declaration: int) -> Dict:
    url = f'https://pub.fsa.gov.ru/api/v1/rds/common/declarations/{id_declaration}'
    async with semaphore:  # Ограничение на количество одновременных запросов
        async with session.get(url) as response:
            return await response.json()


async def fetch_declarations(session: aiohttp.ClientSession, filter_key: str, id_list: List[int]) -> List[Dict]:
    today = datetime.datetime.today().strftime('%Y-%m-%d')

    json_data = {
        'size': 100,
        'page': 0,
        'filter': {
            'status': [], 'idDeclType': [], 'idCertObjectType': [],
            'idProductType': [], 'idGroupRU': [], 'idGroupEEU': [],
            'idTechReg': [], 'idApplicantType': [], 'idProductOrigin': [],
            'idProductEEU': [], 'idProductRU': [], 'idDeclScheme': [],
            'regDate': {'minDate': None, 'maxDate': None},
            'endDate': {'minDate': None, 'maxDate': None},
            'columnsSearch': [],
            'number': None,
            'awaitOperatorCheck': None,
            'editApp': None,
            'violationSendDate': None,
            'isProtocolInvalid': None,
            'checkerAIResult': None,
            'checkerAIProtocolsResults': None,
            'checkerAIProtocolsMistakes': None,
            'hiddenFromOpen': None,
        },
        'regDate': {
            'minDate': today,
            'maxDate': today,
        },
        'columnsSort': [{'column': 'declDate', 'sort': 'DESC'}],
    }

    json_data['filter'][filter_key] = id_list
    url = 'https://pub.fsa.gov.ru/api/v1/rds/common/declarations/get'

    async with session.post(url, json=json_data) as response:
        if response.status != 200:
            send_msg(text=f"Status: {response.status}\nTime: {datetime.datetime.now()}")
        res = await response.json()
        items = res.get('items', [])

    detailed_items = []

    tasks = []
    for item in items:
        id_decl = item['id']
        # Проверка есть ли в БД
        if not await check_declaration_in_db(id_decl):
            tasks.append(get_dop_info(session, id_decl))

    if tasks:
        detailed_items = await asyncio.gather(*tasks)

    return detailed_items


async def collect_all_data() -> List[Dict]:
    result = []

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(cookies=cookies, headers=headers, timeout=timeout) as session:
        group_data_task = fetch_declarations(session, 'idGroupEEU', ids_GroupEEU)
        product_eeu_data_task = fetch_declarations(session, 'idProductEEU', ids_ProductEEU)
        product_ru_data_task = fetch_declarations(session, 'idProductRU', ids_ProductRU)

        group_data, product_eeu_data, product_ru_data = await asyncio.gather(
            group_data_task,
            product_eeu_data_task,
            product_ru_data_task,
        )

        result.extend(group_data)
        result.extend(product_eeu_data)
        result.extend(product_ru_data)

    return result


async def main():
    while True:
        final_result = await collect_all_data()


        if len(final_result) != 0:
            send_msg(text=f"Собрано {len(final_result)}\nTime: {datetime.datetime.now()}")

        print(f"Собрано новых деклараций: {len(final_result)}")

        # Сохраняем в БД
        for item in final_result:
            await database.insert_declaration(data=item)

        await asyncio.sleep(30)


if __name__ == '__main__':
    asyncio.run(main())
