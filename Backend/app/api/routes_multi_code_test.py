from fastapi import APIRouter, Query
from app.services.runner_service import run_qnn_inference, log_to_queue, CodeLoadError, ConfigError
from app.services.generate_dummy import generate_dummy_variants
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from app.services.log_broadcaster import log_broadcaster  # 공용 broadcaster
import json

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed, wait, FIRST_COMPLETED
import traceback

import time, uuid
from datetime import datetime

import queue  
import multiprocessing as mp

# def log_to_websockets(message: dict):
#     try:
#         loop = asyncio.get_event_loop()
#         loop.create_task(log_broadcaster.broadcast(message))
#     except RuntimeError:
#         print("[log_callback] Event loop not running, skipping log.")

router = APIRouter()

try:
    mp.set_start_method("spawn")
except RuntimeError:
    pass

def _worker_run_single_dummy(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    워커 프로세스에서 더미 1개 실행하고 결과를 dict로 반환.
    - log_callback은 워커에서 직접 웹소켓 전송하지 않음(IPC 없으면 불안정).
    - 예외는 status + error dict로 포장해서 반환.
    """
    mp_log_q = job.get("mp_log_q", None)

    def cb(msg: dict):
        # msg는 {"message": "..."} 형태로 보내는 게 가장 안전
        if mp_log_q is not None:
            mp_log_q.put(msg)

    try:
        result = run_qnn_inference(
            code_dir=job["code_dir"],
            n_qubits=job["n_qubits"],
            sample_count=job["sample_count"],   # 여기서는 eval 샘플 수 제한으로만 사용
            file_map=job["file_map"],           # {part: "abs/path.py"} 형태
            target_parts=job["target_parts"],
            save_weights=True,
            save_dir=job["save_dir"],
            log_callback=cb,                  # 병렬에서는 부모에서만 log_to_queue
            train_epochs=job["train_epochs"],
            dummy_id=job["dummy_id"],
        )

        return {
            "dummy_id": job["dummy_id"],
            "status": "ok",
            "accuracy": result.get("accuracy", 0.0),
            "details": result.get("results", []),
            "train_seconds": result.get("train_seconds", 0.0),
            "inference_seconds": result.get("inference_seconds", 0.0),
            "total_seconds": result.get("total_seconds", 0.0),
        }

    except CodeLoadError as e:
        return {
            "dummy_id": job["dummy_id"],
            "status": "compile_error",
            "accuracy": 0.0,
            "details": [],
            "error": e.to_dict(),
            "log_message": (
                f"[Dummy {job['dummy_id']}] COMPILE_ERROR in {e.part}\n"
                f"  at {e.file}:{e.line}\n"
                f"  >> {e.code_line}\n"
                f"  {e.exc_type}: {e.exc_msg}"
            )
        }

    except ConfigError as e:
        return {
            "dummy_id": job["dummy_id"],
            "status": "config_error",
            "accuracy": 0.0,
            "details": [],
            "error": e.to_dict(),
            "log_message": (
                f"[Dummy {job['dummy_id']}] CONFIG_ERROR: {e.part} n_qubits mismatch "
                f"(expected={e.expected}, provided={e.provided})"
            )
        }

    except Exception as e:
        return {
            "dummy_id": job["dummy_id"],
            "status": "runtime_error",
            "accuracy": 0.0,
            "details": [],
            "error": {"exc_type": type(e).__name__, "exc_msg": str(e)},
            "log_message": f"[Dummy {job['dummy_id']}] RUNTIME_ERROR: {type(e).__name__}: {str(e)}",
            # 디버깅 필요하면 주석 해제
            # "traceback": traceback.format_exc(),
        }

@router.get("/run-multi-test")
def run_multi_test(
    target_parts: List[str] = Query(default=["encoder"]),
    n_qubits: int = 6,
    variant_count: int = 3,
    sample_count: int = 10,
    train_epochs: int = 5,
    max_concurrent: int = 3,   # 추가: 동시에 돌릴 더미 수
):
    base_dir = Path("generated_code").resolve()
    results: List[Dict[str, Any]] = []

    all_parts = {"encoder", "pqc", "mea"}
    selected_parts = set(target_parts)
    dummy_parts = all_parts - selected_parts

    mgr = mp.Manager()
    mp_log_q = mgr.Queue()

    # 1) 더미 생성(여기는 그대로 순차)
    dummy_sets = {}
    for part in dummy_parts:
        dummy_sets[part] = generate_dummy_variants(
            part=part,
            base_class_name=f"{part.upper()}{n_qubits}QDummy",
            n_qubits=n_qubits,
            count=variant_count,
            save_path=base_dir
        )

    # 2) 사용자 파일 매핑
    user_file_map = {}
    for part in selected_parts:
        file_name = (
            f"StateEncoder{n_qubits}QDummy.py" if part == "encoder"
            else f"{part.upper()}{n_qubits}QDummy.py"
        )
        user_file_map[part] = base_dir / file_name

    # 3) 더미별 info.json 로드 + job 구성
    dummy_info_map: Dict[int, Dict[str, Any]] = {}
    jobs: List[Dict[str, Any]] = []

    for i in range(variant_count):
        dummy_id = i + 1

        combined_map = {part: dummy_sets[part][i] for part in dummy_sets}
        combined_map.update(user_file_map)

        # 멀티프로세싱에 안전하도록 Path -> abs str
        combined_map_str = {k: str(Path(v).resolve()) for k, v in combined_map.items()}

        dummy_info = {}
        for part in dummy_parts:
            json_path = dummy_sets[part][i].with_name(dummy_sets[part][i].stem + "_info.json")
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    dummy_info[part] = json.load(f)
            except FileNotFoundError:
                dummy_info[part] = {"error": "info not found"}

        dummy_info_map[dummy_id] = dummy_info

        jobs.append({
            "dummy_id": dummy_id,
            "code_dir": str(base_dir),
            "n_qubits": n_qubits,
            "sample_count": sample_count,
            "file_map": combined_map_str,
            "target_parts": target_parts,
            "save_dir": "./trained_weights",
            "train_epochs": train_epochs,
            "mp_log_q": mp_log_q,
        })

    # 4) 병렬 실행
    max_workers = max(1, min(max_concurrent, variant_count))
    ctx = mp.get_context("spawn")

    log_to_queue({"message": f"Starting parallel run: variants={variant_count}, max_concurrent={max_workers}"})

    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
        fut_map = {ex.submit(_worker_run_single_dummy, job): job["dummy_id"] for job in jobs}
        pending = set(fut_map.keys())

        while pending:
            done, pending = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)

            # (A) 중간 로그 drain
            while True:
                try:
                    msg = mp_log_q.get(False)   # ✅ get_nowait() 대신
                    log_to_queue(msg)
                except queue.Empty:
                    break

            # (B) 완료된 future 처리
            for fut in done:
                dummy_id = fut_map[fut]
                out = fut.result()

                if "log_message" in out:
                    log_to_queue({"message": out["log_message"]})
                else:
                    if out.get("status") == "ok":
                        log_to_queue({
                            "message": f"[Dummy {dummy_id}] Done. Acc={out.get('accuracy',0.0):.3f}, train={out.get('train_seconds',0.0):.2f}s"
                        })

                out["info"] = dummy_info_map.get(dummy_id, {})
                results.append(out)

    # 종료 직전 잔여 로그 drain (권장)
    while True:
        try:
            msg = mp_log_q.get(False)
            log_to_queue(msg)
        except queue.Empty:
            break

    # 5) 응답은 dummy_id 순으로 정렬해서 프론트가 보기 좋게
    results.sort(key=lambda x: x["dummy_id"])
    return {"total_variants": variant_count, "results": results}
