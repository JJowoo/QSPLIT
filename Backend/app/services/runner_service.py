import torch
import importlib.util
from pathlib import Path
from torchvision import transforms
from torch.utils.data import DataLoader
from medmnist import INFO
import medmnist
import torch.nn as nn
import asyncio
import anyio
from typing import List, Optional
from app.services.log_broadcaster import log_broadcaster
from app.services.log_queue import log_queue
import traceback
import linecache
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import ast
import time
import math

def _safe_float(v) -> float:
    """Convert value to float, replacing NaN/Inf with 0.0 or None-safe value."""
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        return 0.0

@dataclass
class CodeLoadError(Exception):
    part: str
    file: str
    line: Optional[int]
    code_line: str
    exc_type: str
    exc_msg: str

    def to_dict(self) -> dict:
        return {
            "part": self.part,
            "file": self.file,
            "line": self.line,
            "code_line": self.code_line,
            "exc_type": self.exc_type,
            "exc_msg": self.exc_msg,
        }

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}" if self.line else self.file
        msg = f"{self.exc_type}: {self.exc_msg}"
        if self.code_line:
            return f"{self.part} load failed at {loc}\n>> {self.code_line}\n{msg}"
        return f"{self.part} load failed at {loc}\n{msg}"
    
@dataclass
class ConfigError(Exception):
    part: str
    expected: int
    provided: int
    hint: str = ""

    def to_dict(self) -> dict:
        return {
            "part": self.part,
            "expected": self.expected,
            "provided": self.provided,
            "hint": self.hint,
        }

    def __str__(self) -> str:
        msg = f"{self.part} configuration mismatch: expected n_qubits={self.expected}, provided n_qubits={self.provided}"
        if self.hint:
            msg += f" | {self.hint}"
        return msg

def log_to_queue(message: dict):
    try:
        anyio.from_thread.run(log_queue.put, message)
    except RuntimeError:
        print("[log_queue] Event loop not running, skipping log.")

def infer_default_n_qubits_from_init(py_file: Path, class_name: str) -> Optional[int]:
    """
    class_name 클래스의 __init__(..., n_qubits=<default>) default 값을 파싱해서 반환.
    찾지 못하면 None.
    """
    try:
        src = py_file.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception:
        return None

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == "__init__":
                    # __init__(self, ..., n_qubits=6, ...)
                    args = fn.args
                    arg_names = [a.arg for a in args.args]  # self 포함
                    if "n_qubits" not in arg_names:
                        return None
                    idx = arg_names.index("n_qubits")

                    # defaults는 "마지막 N개 인자"에 대응
                    # (self 포함한 args.args 기준)에서 defaults 매핑
                    # 예: args=[self,n_qubits], defaults=[6]
                    num_args = len(args.args)
                    num_defaults = len(args.defaults)
                    default_start = num_args - num_defaults
                    default_map = {}
                    for i, d in enumerate(args.defaults):
                        name = args.args[default_start + i].arg
                        default_map[name] = d

                    dnode = default_map.get("n_qubits")
                    if isinstance(dnode, ast.Constant) and isinstance(dnode.value, int):
                        return int(dnode.value)
                    return None
    return None

def log_to_websockets(message: dict):
    asyncio.create_task(log_broadcaster.broadcast(message))

# 동적 로딩 함수

def load_class(class_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(class_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

def _format_user_code_error(exc: Exception, file_path: Path, part: str, dummy_id: Optional[int] = None) -> str:
    """
    사용자 제공 코드 로드/실행 중 예외를 파일/라인/코드라인까지 포함해 문자열로 만든다.
    SyntaxError는 별도로 처리한다.
    """
    file_path = Path(file_path)
    exc_type = type(exc).__name__

    # SyntaxError는 filename/lineno/text 등을 직접 제공함
    if isinstance(exc, SyntaxError):
        err_file = Path(getattr(exc, "filename", str(file_path)))
        lineno = getattr(exc, "lineno", None)
        offset = getattr(exc, "offset", None)
        text = getattr(exc, "text", None)

        code_line = ""
        if text:
            code_line = text.rstrip("\n")
        elif lineno:
            code_line = linecache.getline(str(err_file), lineno).rstrip("\n")

        caret = ""
        if offset and code_line:
            caret = " " * (max(0, offset - 1)) + "^"

        msg = getattr(exc, "msg", str(exc))

        return (
            f"[Dummy {dummy_id}] ERROR: Failed to load {part}\n"
            f"  {exc_type}: {msg}\n"
            f"  at {err_file}:{lineno}\n"
            f"  >> {code_line}\n"
            f"  {caret}".rstrip()
        )

    # 그 외 예외: traceback에서 사용자 파일(file_path) 프레임을 찾아 위치를 뽑는다
    tb = exc.__traceback__
    target_file = str(file_path.resolve())
    found_file, found_line = None, None

    while tb:
        fname = str(Path(tb.tb_frame.f_code.co_filename).resolve())
        if fname == target_file:
            found_file = fname
            found_line = tb.tb_lineno
        tb = tb.tb_next

    # 못 찾으면 마지막 프레임(가장 안쪽) 사용
    if found_file is None:
        te = traceback.TracebackException.from_exception(exc)
        # 마지막 stack frame이 가장 안쪽
        if te.stack and len(te.stack) > 0:
            last = te.stack[-1]
            found_file = last.filename
            found_line = last.lineno
        else:
            found_file = str(file_path)
            found_line = None

    code_line = ""
    if found_line:
        code_line = linecache.getline(found_file, found_line).rstrip("\n")

    return (
        f"[Dummy {dummy_id}] ERROR: Failed to load {part}\n"
        f"  {exc_type}: {str(exc)}\n"
        f"  at {found_file}:{found_line}\n"
        f"  >> {code_line}".rstrip()
    )


def load_class_safe(class_name: str, file_path: Path, part: str):
    try:
        spec = importlib.util.spec_from_file_location(class_name, str(file_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # 여기서 SyntaxError 등 발생 가능
        return getattr(module, class_name)  # AttributeError 가능
    except Exception as e:
        exc_type = type(e).__name__
        exc_msg = str(e)

        # SyntaxError는 lineno/text가 잘 나옴
        if isinstance(e, SyntaxError):
            err_file = str(getattr(e, "filename", str(file_path)))
            lineno = getattr(e, "lineno", None)
            text = getattr(e, "text", None)
            code_line = (text.rstrip("\n") if text else linecache.getline(err_file, lineno).rstrip("\n")) if lineno else ""
            raise CodeLoadError(part=part, file=err_file, line=lineno, code_line=code_line,
                                exc_type=exc_type, exc_msg=getattr(e, "msg", exc_msg))

        # 일반 예외는 traceback에서 user 파일 프레임을 탐색
        target_file = str(Path(file_path).resolve())
        tb = e.__traceback__
        found_line = None
        while tb:
            fname = str(Path(tb.tb_frame.f_code.co_filename).resolve())
            if fname == target_file:
                found_line = tb.tb_lineno
            tb = tb.tb_next

        code_line = linecache.getline(target_file, found_line).rstrip("\n") if found_line else ""
        raise CodeLoadError(part=part, file=target_file, line=found_line, code_line=code_line,
                            exc_type=exc_type, exc_msg=exc_msg)

# 데이터셋 로드

def load_medmnist_loader(split: str = "train", batch_size: int = 100, shuffle: bool = True):
    data_flag = "pathmnist"
    info = INFO[data_flag]
    DataClass = getattr(medmnist, info["python_class"])

    # PathMNIST는 RGB(3채널)라면 아래처럼 mean/std를 3개로 맞추는 것이 정석입니다.
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[.5, .5, .5], std=[.5, .5, .5])
    ])

    dataset = DataClass(split=split, transform=transform, download=True)

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle if split == "train" else False,
        num_workers=0,
        pin_memory=False
    )
    return loader, len(info["label"]), len(dataset)


# 실행 파이프라인
# def run_qnn_inference(code_dir: str, sample_count: int = 10) -> dict:
#     base_path = Path(code_dir)

#     encoder_cls = load_class("StateEncoder6QDummy", base_path / "StateEncoder6QDummy.py")
#     pqc_cls     = load_class("PQC6QDummy", base_path / "PQC6QDummy.py")
#     mea_cls     = load_class("MEA6QDummy", base_path / "MEA6QDummy.py")

#     encoder = encoder_cls(n_qubits=6)
#     pqc = pqc_cls(n_qubits=6)
#     mea = mea_cls(n_qubits=6)

#     loader, _ = load_medmnist_loader()

#     results = []
#     correct = 0
#     total = 0

#     for i, (images, labels) in enumerate(loader):
#         if i >= sample_count:
#             break

#         inputs = images.view(images.size(0), -1)
#         labels = labels.view(-1)

#         with torch.no_grad():
#             qstate1 = encoder(inputs)
#             qstate2 = pqc(qstate1)
#             output = mea(qstate2)

#             print(f"output.shape: {output.shape}")

#             label = int(labels.item())  # only 1 label per sample

#             if output.ndim == 1 and output.shape[0] > 1:
#                 pred_label = torch.argmax(output).item()  # multi-class
#             elif output.ndim == 1 and output.shape[0] == 1:
#                 pred_label = int((output > 0).item())
#             else:
#                 raise ValueError(f"Unsupported output shape: {output.shape}")

#             results.append({
#                 "sample": i,
#                 "predicted": pred_label,
#                 "ground_truth": label
#             })

#             correct += int(pred_label == label)
#             total += 1

#     acc = correct / total
#     print(f"acc{acc}")
#     print(f"total{total}")
#     return {
#         "accuracy": acc,
#         "samples_evaluated": total,
#         "results": results
#     }

def save_selected_weights(part_name: str, model: nn.Module, save_dir: str):
    save_path = Path(save_dir) / f"{part_name}_only.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"Saved {part_name} weights to: {save_path}")


def run_qnn_inference(
    code_dir: str,
    n_qubits: int = 6,
    sample_count: int = 200,
    file_map: dict = None,
    target_parts: List[str] = None,
    save_weights: bool = True,
    save_dir: str = "./trained_weights",
    load_weights: dict = None,
    log_callback=None,
    train_epochs: int = 0,
    train_parts: List[str] = ["encoder", "pqc", "mea"],
    dummy_id: Optional[int] = None,
    run_id: Optional[str] = None,
) -> dict:

    file_map = file_map or {}
    base_path = Path(code_dir).resolve()   # (수정) 워커에서도 안정적

    encoder_path = Path(file_map["encoder"]) if "encoder" in file_map else base_path / "StateEncoder6QDummy.py"
    pqc_path     = Path(file_map["pqc"])     if "pqc"     in file_map else base_path / "PQC6QDummy.py"
    mea_path     = Path(file_map["mea"])     if "mea"     in file_map else base_path / "MEA6QDummy.py"

    print(f"Loaded encoder: {encoder_path.resolve()}")
    print(f"Loaded pqc:     {pqc_path.resolve()}")
    print(f"Loaded mea:     {mea_path.resolve()}")

    encoder_cls = load_class_safe(encoder_path.stem, encoder_path, part="encoder")
    pqc_cls     = load_class_safe(pqc_path.stem,     pqc_path,     part="pqc")
    mea_cls     = load_class_safe(mea_path.stem,     mea_path,     part="mea")

    # (수정) Config 체크를 인스턴스 생성 전에 수행
    enc_expected = infer_default_n_qubits_from_init(encoder_path, encoder_path.stem)
    if enc_expected is not None and enc_expected != n_qubits:
        raise ConfigError(
            part="encoder",
            expected=enc_expected,
            provided=n_qubits,
            hint=f"StateEncoder __init__(n_qubits={enc_expected}) default differs from request n_qubits={n_qubits}."
        )

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # 사용자 요청: Log panel에 CUDA/디바이스 정보는 보내지 않음
    print(f"[Dummy {dummy_id}] Using device: {device}")

    print("device:", device)

    encoder = encoder_cls(n_qubits=n_qubits).to(device)
    pqc     = pqc_cls(n_qubits=n_qubits).to(device)
    mea     = mea_cls(n_qubits=n_qubits).to(device)

    model_map = {"encoder": encoder, "pqc": pqc, "mea": mea}

    # ---------- training setup ----------
    trainable_params = []
    for part in train_parts:
        if part in model_map:
            model_map[part].train()
            part_params = list(model_map[part].parameters())
            if part_params:
                trainable_params += part_params
            else:
                print(f"[DEBUG] {part} has no trainable parameters.")

    # ---------- optional weight loading ----------
    if load_weights:
        for part, weight_path in load_weights.items():
            if part in model_map and Path(weight_path).exists():
                if log_callback:
                    log_callback({"message": f"Loading weights for {part} from {weight_path}"})
                state_dict = torch.load(weight_path, map_location=device)
                model_map[part].load_state_dict(state_dict)

    # (수정) 기본값 초기화: 학습 안 해도 안전
    train_seconds = 0.0
    inference_seconds = 0.0
    history: List[dict] = []

    
    

    # ---------- TRAIN ----------
    last_train_loss = None
    last_train_acc = None
    max_train_acc = None
    if train_epochs > 0 and trainable_params:
        optimizer = torch.optim.Adam(trainable_params, lr=1e-3)
        criterion = nn.CrossEntropyLoss()
        train_loader, num_classes, train_size = load_medmnist_loader(split="train", batch_size=100, shuffle=True)

        images0, labels0 = next(iter(train_loader))
        inputs0 = images0.view(images0.size(0), -1).to(device, non_blocking=True)
        labels0 = labels0.view(-1).long().to(device)
        with torch.no_grad():
            out0 = mea(pqc(encoder(inputs0)))
        print("num_classes:", num_classes)
        print("output shape:", out0.shape)
        print("labels min/max:", labels0.min().item(), labels0.max().item())

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        print("[CUDA] device:", device)
        print("[CUDA] encoder param device:", next(encoder.parameters(), torch.empty(0, device=device)).device)
        print("[CUDA] inputs device:", inputs0.device)
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = mea(pqc(encoder(inputs0)))
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        print("[CUDA] one forward sec:", time.perf_counter() - t0)

        log_every = 500
        t_train_start = time.perf_counter()   # (수정) 여기서만 시작

        for epoch in range(train_epochs):
            encoder.train(); pqc.train(); mea.train()
            total_loss, correct, total = 0.0, 0, 0

            for step, (images, labels) in enumerate(train_loader, start=1):
                inputs = images.view(images.size(0), -1).to(device, non_blocking=True)
                labels = labels.view(-1).long().to(device, non_blocking=True)


                optimizer.zero_grad()
                logits = mea(pqc(encoder(inputs)))
                if logits.ndim == 1:
                    logits = logits.unsqueeze(0)

                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item() * labels.size(0)
                pred = torch.argmax(logits, dim=1)
                correct += (pred == labels).sum().item()
                total += labels.size(0)

                if (step % log_every) == 0:
                    avg_loss_step = total_loss / total if total else 0.0
                    acc_step = correct / total if total else 0.0
                    print(f"[Dummy {dummy_id}] Epoch {epoch+1} Step {step}: Loss={avg_loss_step:.4f}, Acc={acc_step:.4f}")

                

            

            avg_loss = total_loss / total if total else 0.0
            acc_train = correct / total if total else 0.0
            print(f"[Dummy {dummy_id}] Epoch {epoch+1}: Loss={avg_loss:.4f}, Acc={acc_train:.4f}")
            
            safe_loss = _safe_float(avg_loss)
            safe_acc = _safe_float(acc_train)
            
            last_train_loss = safe_loss
            last_train_acc = safe_acc

            history.append({
                "epoch": int(epoch + 1),
                "train_loss": safe_loss,
                "train_acc": safe_acc,
            })

            if log_callback:
                # --- real-time progress (per epoch) ---
                log_callback({
                    "type": "train_epoch_end",
                    "run_id": run_id,
                    "dummy_id": dummy_id,
                    "epoch": int(epoch + 1),
                    "train_loss": safe_loss,
                    "train_acc": safe_acc,
                })
                log_callback({
                    "run_id": run_id,
                    "message": f"[Dummy {dummy_id}] Epoch {epoch+1}: Loss={avg_loss:.4f}, Acc={acc_train:.4f}"
                })

        train_seconds = time.perf_counter() - t_train_start  

    elif train_epochs > 0 and not trainable_params:
        print("[WARNING] No trainable parameters found. Skipping training.")
        if log_callback:
            log_callback({"message": "[WARNING] No trainable parameters found. Skipping training."})

    # ---------- EVAL ----------
    encoder.eval(); pqc.eval(); mea.eval()
    test_loader, _, test_size = load_medmnist_loader(split="test", batch_size=100, shuffle=False)

    t_inf_start = time.perf_counter()
    results = []
    correct = 0
    total = 0

    max_eval = sample_count
    eval_seen = 0

    for i, (images, labels) in enumerate(test_loader):
        if max_eval is not None and eval_seen >= max_eval:
            break

        inputs = images.view(images.size(0), -1).to(device, non_blocking=True)
        labels = labels.view(-1).long().to(device, non_blocking=True)

        with torch.no_grad():
            logits = mea(pqc(encoder(inputs)))
            if logits.ndim == 1:
                logits = logits.unsqueeze(0)
            pred = torch.argmax(logits, dim=1).view(-1)

        min_len = min(len(pred), len(labels))
        for b in range(min_len):
            results.append({
                "sample": eval_seen + b,
                "predicted": int(pred[b].item()),
                "ground_truth": int(labels[b].item())
            })

        correct += (pred[:min_len] == labels[:min_len]).sum().item()
        total += min_len
        eval_seen += min_len

    inference_seconds = time.perf_counter() - t_inf_start
    acc = correct / total if total > 0 else 0.0   
    safe_test_acc = _safe_float(acc)

    # if log_callback:
    #     log_callback({"run_id": run_id, "message": f"Inference complete. Accuracy: {acc:.3f}"})

    # ---------- save weights ----------
    if save_weights and target_parts:
        for part in target_parts:
            if part in model_map:
                save_selected_weights(part_name=part, model=model_map[part], save_dir=save_dir)
                if log_callback:
                    log_callback({"message": f"Saved weights for {part}."})


    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


    if history:
        try:
            max_train_acc = max(h.get("train_acc", 0.0) for h in history)
        except Exception:
            max_train_acc = None

    return {
        "accuracy": safe_test_acc,
        "test_accuracy": safe_test_acc,
        "train_loss": last_train_loss,
        "train_acc": last_train_acc,
        "max_train_acc": max_train_acc,
        "samples_evaluated": total,
        "results": results,
        "train_seconds": _safe_float(train_seconds),
        "history": history
    }
