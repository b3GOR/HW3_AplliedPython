import logging
from fastapi import FastAPI
import uvicorn
from functions import check_cache_size, delete_expired_links
from router import router
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# Define CORS settings
origins = ["*"]  # Allow requests from any origin



app = FastAPI(title="Link Shortener Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

scheduler = BackgroundScheduler()


scheduler.add_job(delete_expired_links, 'interval', seconds=20)
scheduler.add_job(check_cache_size, 'interval', seconds=20)


@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000,reload=True)

    
     


