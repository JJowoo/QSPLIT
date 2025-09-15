from fastapi import APIRouter, Query
from pathlib import Path
import torch
from app.services.runner_service import run_qnn_inference, load_class, log_to_queue
from typing import List

router = APIRouter()

@router.get("/test-saved-weights")
def test_saved_weights(
    parts_to_test: List[str] = Query(default=["encoder"]),
    n_qubits: int = 6,
    sample_count: int = 10,
    weights_dir: str = "./trained_weights",
    code_dir: str = "generated_code"
):
    results = []
    file_map = {}

    for part in ["encoder", "pqc", "mea"]:
        file_name = (
            f"StateEncoder{n_qubits}QDummy.py" if part == "encoder"
            else f"{part.upper()}{n_qubits}QDummy.py"
        )
        file_map[part] = Path(code_dir) / file_name

    for part in parts_to_test:
        weight_path = Path(weights_dir) / f"{part}_only.pt"
        if not weight_path.exists():
            results.append({"part": part, "error": f"No weights found at {weight_path}"})
            continue

        # run inference with weight loading
        result = run_qnn_inference(
            code_dir=code_dir,
            sample_count=sample_count,
            file_map=file_map,
            load_weights={part: str(weight_path)},  # pass weight path for loading
            target_parts=[part],  # just for logging maybe
            save_weights=False,
            log_callback=log_to_queue
        )
        result["part"] = part
        results.append(result)

    return {"tested_parts": parts_to_test, "results": results}