from fastapi import APIRouter
from app.services.runner_service import run_qnn_inference

router = APIRouter()

@router.get("/run-job")
def run_job():
    result = run_qnn_inference("generated_code", sample_count=10)
    print("acc", result["accuracy"])
    print("total", result["samples_evaluated"])
    return result
