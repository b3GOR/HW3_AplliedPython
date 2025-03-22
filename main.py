import logging
from fastapi import FastAPI
from router import router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = FastAPI()


app.include_router(router)