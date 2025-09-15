from fastapi import APIRouter, Query
from app.services.runner_service import run_qnn_inference, log_to_queue
from app.services.generate_dummy import generate_dummy_variants
from pathlib import Path
from typing import List
import asyncio
from app.services.log_broadcaster import log_broadcaster  # 공용 broadcaster
import json

# def log_to_websockets(message: dict):
#     try:
#         loop = asyncio.get_event_loop()
#         loop.create_task(log_broadcaster.broadcast(message))
#     except RuntimeError:
#         print("[log_callback] Event loop not running, skipping log.")

router = APIRouter()

@router.get("/run-multi-test")
def run_multi_test(
    target_parts: List[str] = Query(default=["encoder"]),
    n_qubits: int = 6,
    variant_count: int = 3,
    sample_count: int = 10,
    train_epochs: int = 5
):
    base_dir = Path("generated_code")
    results = []

    all_parts = {"encoder", "pqc", "mea"}
    #dummy_parts = all_parts - {target_part}
    selected_parts = set(target_parts)
    dummy_parts = all_parts - selected_parts

    dummy_sets = {}
    for part in dummy_parts:
        dummy_sets[part] = generate_dummy_variants(
            part=part,
            base_class_name=f"{part.upper()}{n_qubits}QDummy",
            n_qubits=n_qubits,
            count=variant_count,
            save_path=base_dir
        )

    user_file_map = {}
    for part in selected_parts:
        file_name = (
            f"StateEncoder{n_qubits}QDummy.py" if part == "encoder"
            else f"{part.upper()}{n_qubits}QDummy.py"
        )
        user_file_map[part] = base_dir / file_name

    for i in range(variant_count):
        dummy_files = {
            "pqc": dummy_sets["pqc"][i] if "pqc" in dummy_sets else base_dir / f"PQC{n_qubits}QDummy.py",
            "mea": dummy_sets["mea"][i] if "mea" in dummy_sets else base_dir / f"MEA{n_qubits}QDummy.py",
            "encoder": base_dir / f"StateEncoder{n_qubits}QDummy.py"
        }
        combined_map = {
            part: dummy_sets[part][i] for part in dummy_sets  # dummy로 생성된 부분
        }
        combined_map.update(user_file_map)
        dummy_info = {}
        for part in dummy_parts:
            json_path = dummy_sets[part][i].with_name(dummy_sets[part][i].stem + "_info.json")
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    dummy_info[part] = json.load(f)
            except FileNotFoundError:
                dummy_info[part] = {"error": "info not found"}

        result = run_qnn_inference(
            code_dir=str(base_dir),
            sample_count=sample_count,
            file_map=combined_map,
            target_parts=target_parts,
            save_weights=True,
            save_dir="./trained_weights",
            log_callback=log_to_queue,
            train_epochs=train_epochs,
            dummy_id=i+1
        )
        results.append({
            "dummy_id": i,
            "accuracy": result["accuracy"],
            "details": result["results"],
            "info": dummy_info
        })

    return {"total_variants": variant_count, "results": results}
