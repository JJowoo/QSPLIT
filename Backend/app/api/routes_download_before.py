# app/api/routes_download.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import List
import io, zipfile, datetime, re

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

def _list_indices(n_qubits: int) -> List[int]:
    if not BASE_DIR.exists():
        return []
    indices = set()
    pat = re.compile(rf".*{n_qubits}QDummy(\d+)$")  # stem 끝의 숫자만
    for p in BASE_DIR.glob(f"*{n_qubits}QDummy*.py"):
        m = pat.match(p.stem)
        if m:
            indices.add(int(m.group(1)))
    return sorted(indices)

@router.get("/download-dummy-all")
def download_all_dummy_bundles(
    n_qubits: int = Query(6),
    include_info: bool = Query(False),
    allow_partial: bool = Query(False),
):
    if not BASE_DIR.exists():
        raise HTTPException(status_code=404, detail="generated_code directory not found")

    indices = _list_indices(n_qubits)
    if not indices:
        raise HTTPException(status_code=404, detail=f"No dummy files found for n_qubits={n_qubits}")

    # 고정 encoder(인덱스 없음)
    fixed_encoder = BASE_DIR / f"StateEncoder{n_qubits}QDummy.py"

    buf = io.BytesIO()
    missing_total = []  # allow_partial=False일 때 에러 메시지용

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 고정 encoder가 있으면 최상단에 포함
        if fixed_encoder.exists():
            zf.write(fixed_encoder, arcname=fixed_encoder.name)
            if include_info:
                info = _info_path(fixed_encoder)
                if info.exists():
                    zf.write(info, arcname=info.name)

        for idx in indices:
            # 각 index에 대해 3종 묶기(encoder는 더미형/StateEncoder형 둘 다 시도)
            encoder_candidates = [
                BASE_DIR / f"ENCODER{n_qubits}QDummy{idx}.py",
                BASE_DIR / f"StateEncoder{n_qubits}QDummy{idx}.py",
            ]
            encoder_file = next((p for p in encoder_candidates if p.exists()), None)

            pqc_file = BASE_DIR / f"PQC{n_qubits}QDummy{idx}.py"
            mea_file = BASE_DIR / f"MEA{n_qubits}QDummy{idx}.py"

            missing = []
            if encoder_file is None and (not fixed_encoder.exists()):
                # 고정 encoder도 없고, index encoder도 없으면 encoder missing으로 본다
                missing.append(f"ENCODER/StateEncoder (idx={idx})")
            if not pqc_file.exists():
                missing.append(f"PQC (idx={idx})")
            if not mea_file.exists():
                missing.append(f"MEA (idx={idx})")

            if missing and not allow_partial:
                missing_total.extend(missing)
                continue  # 일단 모았다가 아래에서 한 번에 404

            # ZIP 내부 경로: idx 폴더로 묶어주면 보기 좋음
            folder = f"dummy_{idx}/"

            if encoder_file and encoder_file.exists():
                zf.write(encoder_file, arcname=folder + encoder_file.name)
                if include_info:
                    info = _info_path(encoder_file)
                    if info.exists():
                        zf.write(info, arcname=folder + info.name)

            if pqc_file.exists():
                zf.write(pqc_file, arcname=folder + pqc_file.name)
                if include_info:
                    info = _info_path(pqc_file)
                    if info.exists():
                        zf.write(info, arcname=folder + info.name)

            if mea_file.exists():
                zf.write(mea_file, arcname=folder + mea_file.name)
                if include_info:
                    info = _info_path(mea_file)
                    if info.exists():
                        zf.write(info, arcname=folder + info.name)

        if missing_total and not allow_partial:
            raise HTTPException(
                status_code=404,
                detail="Missing files: " + ", ".join(missing_total),
            )

        zf.writestr(
            "manifest.txt",
            "\n".join([
                f"n_qubits={n_qubits}",
                f"indices={indices}",
                f"include_info={include_info}",
                f"allow_partial={allow_partial}",
                f"generated_at={datetime.datetime.utcnow().isoformat()}Z",
                f"fixed_encoder_included={fixed_encoder.exists()}",
            ])
        )

    buf.seek(0)
    filename = f"dummy_all_q{n_qubits}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/download-dummy/{index}")
def download_dummy_bundle(
    index: int,
    n_qubits: int = Query(6, description="Number of Qubits that writed in file name"),
    include_info: bool = Query(False, description="Is *_info.json included or not"),
    allow_partial: bool = Query(False, description="If even one is missing, should I compress only the ones that are present instead of returning 404?"),
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
