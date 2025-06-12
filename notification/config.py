import dotenv
import os

dotenv.load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_LOGIN = os.getenv("DB_LOGIN")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv('DB_NAME')

def get_url_database():
    url = f'mysql://{DB_LOGIN}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    return url

