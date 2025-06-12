import asyncio
from typing import List, Union, Dict
import json
import aiomysql

from config import DB_LOGIN, DB_PASSWORD, DB_PORT, DB_HOST, DB_NAME
from config import list_country, list_status, types_aplication, typesLegalSybjects



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
                cursorclass=aiomysql.DictCursor,
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

                # Попробуем получить результат, если он есть
                try:
                    return await cursor.fetchall()
                except Exception:
                    return None


    async def insert_declaration(self, data: dict):
        await self.init()

        insert_query = """
        INSERT INTO declarations (
            declaration_id,
            declaration_status,
            declaration_date,
            declaration_url,

            applicant_full_name,
            applicant_short_name,
            applicant_type,
            applicant_inn,
            applicant_person_name,
            applicant_manager_position,
            applicant_activity_address,
            applicant_location_address,
            applicant_phone,
            applicant_email,

            manufacturer_full_name,
            manufacturer_short_name,
            manufacturer_type,
            manufacturer_inn,
            manufacturer_person_name,
            manufacturer_phone,
            manufacturer_email,
            manufacturer_production_address,
            manufacturer_location_address,

            product_name,
            product_designation,
            batch_size,
            country_of_origin
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        );
        """

        applicant = data.get('applicant', {})
        manufacturer = data.get('manufacturer', {})
        product = data.get('product', {})

        adresses_applicant = applicant.get('addresses', [])
        contacts_applicant = applicant.get('contacts', [])
        contacts_manufacturer = manufacturer.get('contacts', [])
        addresses_manufacturer = manufacturer.get('addresses', [])
        manufacturer_filials = data.get("manufacturerFilials", [])

        def get_contact(contacts, type_id):
            return next((c.get('value') for c in contacts if c.get('idContactType') == type_id), None)

        def get_address(addresses, type_id):
            return next((a.get('fullAddress') for a in addresses if a.get('idAddrType') == type_id), None)

        def get_first_identification_name(identifications):
            if isinstance(identifications, list) and len(identifications) > 0:
                return identifications[0].get("name")
            return None

        def get_production_address_from_filials(filials):
            if isinstance(filials, list) and len(filials) > 0:
                addresses = filials[0].get("addresses", [])
                if isinstance(addresses, list) and len(addresses) > 0:
                    return addresses[0].get("fullAddress")
            return None

        values = (
            data.get('idDeclaration') or None,  # ID декларации
            next((status['name'] for status in list_status if status['id'] == data.get('idStatus')), None),  # Статус
            data.get('declRegDate') or None,  # Дата
            f"https://pub.fsa.gov.ru/rds/declaration/view/{data.get('idDeclaration')}" if data.get(
                'idDeclaration') else None,  # Ссылка

            applicant.get('fullName') or None,
            applicant.get('shortName') or None,
            types_aplication.get(applicant.get('idApplicantType')) or None,
            applicant.get('inn') or None,
            " ".join(filter(None, [
                applicant.get('surname'),
                applicant.get('firstName'),
                applicant.get('patronymic')
            ])) or None,
            applicant.get('headPosition') or None,
            get_address(adresses_applicant, 3) or None,
            get_address(adresses_applicant, 1) or None,
            get_contact(contacts_applicant, 1) or None,
            get_contact(contacts_applicant, 4) or None,

            manufacturer.get('fullName') or None,
            manufacturer.get('shortName') or None,
            typesLegalSybjects.get(manufacturer.get('idLegalSubjectType')) or None,
            manufacturer.get('inn') or None,
            " ".join(filter(None, [
                manufacturer.get('surname'),
                manufacturer.get('firstName'),
                manufacturer.get('patronymic')
            ])) or None,
            get_contact(contacts_manufacturer, 1) or None,
            get_contact(contacts_manufacturer, 4) or None,
            get_production_address_from_filials(manufacturer_filials) or None,
            get_address(addresses_manufacturer, 1) or None,

            product.get('fullName') or None,
            get_first_identification_name(product.get('identifications')) or None,
            product.get('batchSize') or None,
            next((country['shortName'] for country in list_country if str(country['id']) == str(product.get('idProductOrigin'))), None)

        )

        try:
            await self.execute_query(insert_query, values)
        except Exception as ex:
            print(f"{data.get('idDeclaration')} {ex}")
            for value in values:
                print(value)
            input("wait")

    async def get_info_declaration(self, id_deaclaration: int):
        query = 'select * from declarations where declaration_id = %s'
        args = (id_deaclaration,)
        result = await self.execute_query(query, args)
        if result:
            return True
        else:
            return False
