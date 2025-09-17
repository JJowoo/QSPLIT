from fastapi import FastAPI
from app.api import routes_code, routes_runner
from app.api.ws_logging import router as ws_logging_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_multi_code_test import router as multi_test_router
from app.api.routes_test_trained_weights import router as test_weights_router  
from app.api.routes_upload import router as upload_router 
from app.api.routes_download import router as download_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 혹은 ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_code.router)
# app.include_router(routes_runner.router)
app.include_router(ws_logging_router)
app.include_router(multi_test_router)
app.include_router(test_weights_router)
app.include_router(upload_router)
app.include_router(download_router)

# run backend server
# uvicorn app.main:app --host 0.0.0.0 --port 8000

# swagger library local address
# http://127.0.0.1:8000/docs
