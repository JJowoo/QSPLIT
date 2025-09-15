# app/api/routes_upload.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import hashlib

router = APIRouter()

PART_FILENAME = {
    "se": "StateEncoder6QDummy.py",
    "pqc": "PQC6QDummy.py",
    "mea": "MEA6QDummy.py",
}

@router.post("/upload-code")
async def upload_code(
    part: str = Form(..., description="se | pqc | mea"),
    file: UploadFile = File(..., description="Python source file (.py)"),
):
    part_key = part.strip().lower()
    if part_key not in PART_FILENAME:
        raise HTTPException(status_code=400, detail="part must be one of: se, pqc, mea")


    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are allowed")

    save_dir = Path("generated_code")
    save_dir.mkdir(parents=True, exist_ok=True)

    dest = save_dir / PART_FILENAME[part_key]


    content = await file.read()
    dest.write_bytes(content)


    sha256 = hashlib.sha256(content).hexdigest()
    return {
        "part": part_key,
        "saved_as": str(dest),
        "bytes": len(content),
        "sha256": sha256,
        "message": "Uploaded successfully",
    }
