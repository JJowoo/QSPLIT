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

#실행 코드
#uvicorn app.main:app --host 0.0.0.0 --port 8000

#접속주소(내부 임시)
#http://127.0.0.1:8000/docs

#.\squad\Scripts\activate

'''
실시간 로그 테스트
웹 콘솔에서 다음 입력

let ws = new WebSocket("ws://localhost:8000/ws/train-logs");

ws.onmessage = function(event) {
  console.log("print acc log real time", event.data);
};

'''

'''
API코드 생성 요청

{
  "part": "encoder",
  "class_name": "StateEncoder6QDummy",
  "n_qubits": 6,
  "layers": []
}


{
  "part": "pqc",
  "class_name": "PQC6QDummy",
  "n_qubits": 6,
  "layers": ["RXYZCXLayer0"]
}

{
  "part": "mea",
  "class_name": "MEA6QDummy",
  "n_qubits": 6,
  "layers": []
}

'''
