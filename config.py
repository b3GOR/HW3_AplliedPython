from dotenv import load_dotenv
import os
import redis
from sqlalchemy import URL

load_dotenv()

ALGORITHM = os.getenv('ALGORITHM')
SECRET_KEY = os.getenv('SECRET_KEY')
DOMAIN = os.getenv('DOMAIN')
MAX_SIZE = int(os.getenv('MAX_SIZE'))
USERNAME=os.getenv('USERNAME')
HOST=os.getenv("HOST")
PORT_DB=os.getenv('PORT_DB')
PORT_REDIS=os.getenv('PORT_REDIS')
DATABASE=os.getenv("LONG_SHORT_LINKS")
PASSWORD=os.getenv('PASSWORD')

redis_client = redis.Redis(host=HOST, port=PORT_REDIS, db=0,decode_responses=True)
DB_URL = URL.create(
    drivername='postgresql+psycopg2',
    username=USERNAME,
    host=HOST,
    port=PORT_DB,
    password=PASSWORD,
    database=DATABASE
)

