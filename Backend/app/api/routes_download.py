# app/api/routes_code.py

from fastapi import APIRouter, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import zipfile
import tempfile
import os

router = APIRouter()

@router.get("/download-dummies")
def download_dummies(
    background_tasks: BackgroundTasks,
    n_qubits: int = Query(6),
    include_info: bool = Query(True),
):
    base_dir = Path("generated_code").resolve()
    if not base_dir.exists():
        raise FileNotFoundError(f"generated_code not found: {base_dir}")

 
    py_files = sorted(base_dir.glob(f"*{n_qubits}QDummy*.py"))
    info_files = sorted(base_dir.glob(f"*{n_qubits}QDummy*_info.json")) if include_info else []

    if not py_files:
        raise FileNotFoundError(f"No dummy .py files for n_qubits={n_qubits} in {base_dir}")


    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    zip_path = tmp.name
    tmp.close()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in py_files:
            z.write(f, arcname=f.name)
        for f in info_files:
            z.write(f, arcname=f.name)

 
    background_tasks.add_task(os.remove, zip_path)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"dummies_nq{n_qubits}.zip",
    )
