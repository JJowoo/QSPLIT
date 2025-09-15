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


def log_to_queue(message: dict):
    try:
        anyio.from_thread.run(log_queue.put, message)
    except RuntimeError:
        print("[log_queue] Event loop not running, skipping log.")

def log_to_websockets(message: dict):
    asyncio.create_task(log_broadcaster.broadcast(message))

# 동적 로딩 함수

def load_class(class_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(class_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

# 데이터셋 로드

def load_medmnist_loader(batch_size=1):
    data_flag = "pathmnist"
    info = INFO[data_flag]
    DataClass = getattr(medmnist, info["python_class"])

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[.5], std=[.5])
    ])

    test_dataset = DataClass(split='test', transform=transform, download=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    return test_loader, len(info['label'])


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


def run_qnn_inference(code_dir: str,
    sample_count: int = 10,
    file_map: dict = None,
    target_parts: List[str] = None,
    save_weights: bool = True,
    save_dir: str = "./trained_weights",
    load_weights: dict = None,
    log_callback=None,
    train_epochs: int = 0,
    train_parts: List[str] = ["encoder", "pqc", "mea"],
    dummy_id: Optional[int] = None
) -> dict:

    file_map = file_map or {}
    base_path = Path(code_dir)

    # 파일 경로 직접 지정 또는 기본 경로 사용
    encoder_path = Path(file_map["encoder"]) if "encoder" in file_map else base_path / "StateEncoder6QDummy.py"
    pqc_path     = Path(file_map["pqc"])     if "pqc"     in file_map else base_path / "PQC6QDummy.py"
    mea_path     = Path(file_map["mea"])     if "mea"     in file_map else base_path / "MEA6QDummy.py"

    if log_callback:
        log_callback({"message": f" Loading modules..."})

    print(f"Loaded encoder: {file_map['encoder']}")
    print(f"Loaded pqc:     {file_map['pqc']}")
    print(f"Loaded mea:     {file_map['mea']}")
    

    encoder_cls = load_class(encoder_path.stem, encoder_path)
    pqc_cls     = load_class(pqc_path.stem, pqc_path)
    mea_cls     = load_class(mea_path.stem, mea_path)

    encoder = encoder_cls(n_qubits=6)
    pqc     = pqc_cls(n_qubits=6)
    mea     = mea_cls(n_qubits=6)

    model_map = {
        "encoder": encoder,
        "pqc": pqc,
        "mea": mea
    }


    train_parts = train_parts

    trainable_params = []
    for part in train_parts:
        if part in model_map:
            model_map[part].train()
            part_params = list(model_map[part].parameters())
            if part_params:
                trainable_params += part_params
            else:
                print(f"[DEBUG] {part} has no trainable parameters.")

    if not trainable_params:
        print("[WARNING] No trainable parameters found. Skipping training.")
    else:
        print(f"Trainable parameters: {[p.shape for p in trainable_params]}")
        print(f"Trainable parts: {train_parts}")
        optimizer = torch.optim.Adam(trainable_params, lr=1e-3)
        criterion = nn.CrossEntropyLoss()

        loader, _ = load_medmnist_loader()

        for epoch in range(train_epochs):
            total_loss = 0.0
            correct = 0
            total = 0
            for i, (images, labels) in enumerate(loader):
                if i >= sample_count:
                    break
                inputs = images.view(images.size(0), -1)

                optimizer.zero_grad()
                qstate1 = encoder(inputs)
                qstate2 = pqc(qstate1)
                if qstate2.ndim == 2 and qstate2.shape[1] == 1:
                    qstate2 = qstate2.view(1, -1)
                
                output = mea(qstate2)
                

                criterion = nn.CrossEntropyLoss()

                # output: shape [6] → [1, 6]
                output = output.view(1, -1)

                # labels: shape [1], 값은 정수 클래스 인덱스 (e.g., 3)
                labels = labels.view(-1).long()
                #print(f"Label: {labels}, Max class index allowed: {output.shape[1] - 1}")

                loss = criterion(output, labels)
                pred = torch.argmax(output, dim=1)


                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                correct += (pred == labels).sum().item()
                total += labels.size(0)

            acc = correct / total if total > 0 else 0.0
            if log_callback:
                # log_callback({"message": f"[Epoch {epoch+1}] Loss: {total_loss:.4f}, Acc: {acc:.4f}"})
                log_callback({
                    "message": f"[Dummy {dummy_id}] Epoch {epoch+1}: Loss={total_loss:.4f}, Acc={acc:.4f}"
                })
            else:
                print(f"[Epoch {epoch+1}] Loss: {total_loss:.4f}, Acc: {acc:.4f}")


    

    if load_weights:
        for part, weight_path in load_weights.items():
            if part in model_map and Path(weight_path).exists():
                if log_callback:
                    log_callback({"message": f"Loading weights for {part} from {weight_path}"})
                print(f"Loading weights for {part} from {weight_path}")
                state_dict = torch.load(weight_path, map_location="cpu")
                model_map[part].load_state_dict(state_dict)
            else:
                if log_callback:
                    log_callback({"message": f"Skipped loading weights for {part}"})
                print(f"Skipped loading weights for {part} (path not found or invalid)")

    loader, _ = load_medmnist_loader()

    results = []
    correct = 0
    total = 0

    for i, (images, labels) in enumerate(loader):
        if i >= sample_count:
            break
        

        inputs = images.view(images.size(0), -1)
        with torch.no_grad():
            qstate1 = encoder(inputs)
            qstate2 = pqc(qstate1)
            output = mea(qstate2)

            if output.ndim == 2:
                pred = torch.argmax(output, dim=1)
            elif output.ndim == 1:
                pred = (output > 0).long()
            elif output.ndim == 2 and output.shape[1] == 1:
                pred = (output > 0).long().squeeze(1)
            else:
                raise ValueError(f"Unsupported output shape: {output.shape}")

            if pred.ndim == 0:
                pred = pred.unsqueeze(0)
            if labels.ndim == 0:
                labels = labels.unsqueeze(0)

            pred = pred.view(-1)
            labels = labels.view(-1)

            # 2. 길이 맞추기
            min_len = min(len(pred), len(labels))

            for b in range(min_len):
                results.append({
                    "sample": i * len(pred) + b,
                    "predicted": int(pred[b].item()),
                    "ground_truth": int(labels[b].item())
                })

            correct += (pred[:min_len] == labels[:min_len]).sum().item()
            total += min_len

    acc = correct / total if total > 0 else 0.0

    if log_callback:
        log_callback({"message": f"Inference complete. Accuracy: {acc:.3f}"})

    # if log_callback:
    #     log_callback({"message": f"Sample {i+1}/{sample_count}"})
    #     print("[log_callback] sent log")


    if save_weights and target_parts:
        for part in target_parts:
            if part in {"encoder", "pqc", "mea"}:
                save_selected_weights(
                    part_name=part,
                    model=locals()[part],  # encoder, pqc, mea 중 해당 객체
                    save_dir=save_dir
                )
                if log_callback:
                    log_callback({"message": f"Saved weights for {part}."})



    return {
        "accuracy": acc,
        "samples_evaluated": total,
        "results": results
    }