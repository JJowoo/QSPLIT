# app/api/routes_download.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import List
import io, zipfile, datetime

router = APIRouter()
BASE_DIR = Path("generated_code")

def _candidate_paths(n_qubits: int, index: int) -> List[Path]:
    """
    ENCODER는 두 가지 네이밍(ENCODER / StateEncoder)을 모두 시도.
    """
    candidates: List[Path] = []
    # ENCODER
    candidates.append(BASE_DIR / f"ENCODER{n_qubits}QDummy{index}.py")
    candidates.append(BASE_DIR / f"StateEncoder{n_qubits}QDummy{index}.py")
    # PQC
    candidates.append(BASE_DIR / f"PQC{n_qubits}QDummy{index}.py")
    # MEA
    candidates.append(BASE_DIR / f"MEA{n_qubits}QDummy{index}.py")
    return candidates

def _info_path(py_path: Path) -> Path:
    return py_path.with_name(py_path.stem + "_info.json")

@router.get("/download-dummy/{index}")
def download_dummy_bundle(
    index: int,
    n_qubits: int = Query(6, description="파일명에 들어가는 qubit 수"),
    include_info: bool = Query(False, description="*_info.json도 포함할지"),
    allow_partial: bool = Query(False, description="하나라도 없으면 404 대신 있는 것만 압축할지"),
):
    if not BASE_DIR.exists():
        raise HTTPException(status_code=404, detail="generated_code directory not found")

    # 찾기
    encoder_paths = [
        BASE_DIR / f"ENCODER{n_qubits}QDummy{index}.py",
        BASE_DIR / f"StateEncoder{n_qubits}QDummy{index}.py",
    ]
    encoder_file = next((p for p in encoder_paths if p.exists()), None)

    pqc_file = BASE_DIR / f"PQC{n_qubits}QDummy{index}.py"
    mea_file = BASE_DIR / f"MEA{n_qubits}QDummy{index}.py"

    files = []
    missing = []

    if encoder_file and encoder_file.exists():
        files.append(encoder_file)
    else:
        missing.append("ENCODER/StateEncoder")

    if pqc_file.exists():
        files.append(pqc_file)
    else:
        missing.append("PQC")

    if mea_file.exists():
        files.append(mea_file)
    else:
        missing.append("MEA")

    if missing and not allow_partial:
        raise HTTPException(
            status_code=404,
            detail=f"Missing files for index={index}, n_qubits={n_qubits}: {', '.join(missing)}",
        )

    # ZIP 생성 (메모리)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            # zip 내부 경로: just filename
            zf.write(f, arcname=f.name)
            if include_info:
                info = _info_path(f)
                if info.exists():
                    zf.write(info, arcname=info.name)
        # manifest.txt 추가(선택)
        manifest = [
            f"index={index}",
            f"n_qubits={n_qubits}",
            f"include_info={include_info}",
            f"generated_at={datetime.datetime.utcnow().isoformat()}Z",
            "files:",
            *[f" - {f.name}" for f in files],
        ]
        zf.writestr("manifest.txt", "\n".join(manifest))

    buf.seek(0)
    filename = f"dummy_bundle_q{n_qubits}_{index}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/list-dummy-indices")
def list_dummy_indices(n_qubits: int = Query(6)):
   
    if not BASE_DIR.exists():
        return {"indices": []}

    indices = set()
    for p in BASE_DIR.glob(f"*{n_qubits}QDummy*.py"):
        
        stem = p.stem  # e.g. PQC6QDummy3
        try:
            idx_str = stem.split("QDummy")[1]
            idx = int(idx_str)
            indices.add(idx)
        except Exception:
            continue
    return {"indices": sorted(indices)}
