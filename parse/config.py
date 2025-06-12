import dotenv
import os

dotenv.load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_LOGIN = os.getenv("DB_LOGIN")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv('DB_NAME')

# Список стран
list_country = [
        {
            "FDM-56204": False,
            "name": "Переходное Исламское Государство Афганистан",
            "shortName": "АФГАНИСТАН",
            "id": "004",
            "displayName": "АФГАНИСТАН",
            "masterId": 16,
            "isActual": True,
            "eeuMember": False,
            "FDM-53896": "AFG",
            "alpha2": "AF",
            "FDM-53902": "system",
            "FDM-53901": "18.10.2017 00:00:00",
            "FDM-53899": "18.10.2017 00:00:00",
            "FDM-1000498": 0
        },

    ]

# Список стран
list_status = [
        {
            "id": 20,
            "name": "Черновик"
        },]
# Типо Объекта
typesLegalSybjects = {
    1: "Юридическое лицо",
    2: "Индивидуальный предприниматель",
    3: "Иностранное лицо"
}
# Типо заявителя
types_aplication = {
            1: "Уполномоченное изготовителем лицо",
            2: "Продавец",
            3: "Поставщик",
            4: "Изготовитель",
        }

