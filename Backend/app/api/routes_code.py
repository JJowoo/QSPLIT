from fastapi import APIRouter, Query
from pydantic import BaseModel
from pathlib import Path
import shutil
from app.services.generate_dummy import generate_dummy_variants
import json

router = APIRouter()

class GenerateRequest(BaseModel):
    part: str  
    class_name: str
    n_qubits: int
    layers: list[str] = []  # mea는 빈거 요청 가능

@router.get("/generate-code")
def generate_code(
    target_parts: list[str] = Query(default=["encoder"]),
    n_qubits: int = 6,
    variant_count: int = 5,
    depth: int = 2
):
    base_dir = Path("generated_code")
    base_dir.mkdir(parents=True, exist_ok=True)

    # remove previous dummy files but keep uploaded code
    for entry in base_dir.iterdir():
        if entry.name == "upload":
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink(missing_ok=True)
    all_parts = {"encoder", "pqc", "mea"}
    selected_parts = set(target_parts)
    dummy_parts = all_parts - selected_parts

    dummy_sets = {}
    for part in dummy_parts:
        dummy_sets[part] = generate_dummy_variants(
            part=part,
            base_class_name=f"{part.upper()}{n_qubits}QDummy",
            n_qubits=n_qubits,
            count=variant_count,
            save_path=base_dir,
            depth=depth
        )

    results = []

    for i in range(variant_count):
        dummy_info = {}
        for part in dummy_parts:
            py_path = dummy_sets[part][i]
            json_path = py_path.with_name(py_path.stem + "_info.json")
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
            except FileNotFoundError:
                info = {"error": "info not found"}
            dummy_info[part] = {
                "py_file": str(py_path),
                "info": info
            }

        results.append({
            # NOTE: run-multi-test 및 로그 표기와 맞추기 위해 dummy_id는 1부터 시작
            "dummy_id": i + 1,
            "dummy_parts": dummy_info
        })

    return {"total_variants": variant_count, "results": results}