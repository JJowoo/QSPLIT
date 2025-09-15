from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import json

# -----------------테스트용 실행 코드-------------
# template_dir = Path(".")  
# env = Environment(loader=FileSystemLoader(template_dir))

# template = env.get_template("pqc_template.j2")

# template_vars = {
#     "class_name": "PQC6QDummy",
#     "n_qubits": 6,
#     "layers": ["RXYZCXLayer", "U3CU3Layer"]
# }

# rendered_code = template.render(template_vars)

# output_path = Path("./pqc_dummy_6q.py")
# output_path.write_text(rendered_code, encoding="utf-8")

# print(f"Dummy PQC 코드가 생성되었습니다: {output_path}")

#------------------실제 부르는 함수---------------------------
env = Environment(loader=FileSystemLoader("app/templates"))

TEMPLATE_MAP = {
    "pqc": "pqc_template.j2",
    "mea": "mea_template.j2",
    "encoder": "encoder_template.j2"  
}

def get_layer_variant(part: str, variant: int) -> list[str]:
    pqc_variants = [
        ["RY", "RZ", "CNOT"],
        ["U3", "RX", "CNOT"],
        ["RXYZCXLayer0"],
        ["FarhiLayer0"]
    ]
    mea_variants = [
        ["Z"],
        ["X"],
        ["Z", "X"]
    ]
    if part == "pqc":
        return pqc_variants[variant % len(pqc_variants)]
    elif part == "mea":
        return mea_variants[variant % len(mea_variants)]
    else:
        return []
    
def extract_metadata(part: str, layers: list[str], n_qubits: int) -> dict:
    if part == "encoder":
        return {
            "encoding_type": "angle-encoding",  # 현재 템플릿 기준으로 고정 가능
            "input_dim": n_qubits,
            "output_qubits": n_qubits
        }
    elif part == "pqc":
        return {
            "layer_list": layers,
            "entanglement_type": "CNOT" if any("CNOT" in l or "CX" in l for l in layers) else "none"
        }
    elif part == "mea":
        return {
            "observables": layers,
            "measurement_type": "projective"
        }
    else:
        return {}



def generate_dummy_code(part: str,class_name: str, n_qubits: int, layers: list[str], save_path: Path= Path("generated_code")) -> Path:
    if part not in TEMPLATE_MAP:
        raise ValueError(f"Unsupported part type: {part}")
    
    try:
        tpl = env.get_template(TEMPLATE_MAP[part])
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Template not found: {TEMPLATE_MAP[part]}") from e

    code = tpl.render(
        class_name=class_name,
        n_qubits=n_qubits,
        layers=layers or [],  # MEA 일 때 빈거 요청
        num_classes=9
    )
    out_file = save_path / f"{class_name}.py"
    out_file.write_text(code, encoding="utf-8")

    metadata = extract_metadata(part, layers, n_qubits)
    meta_file = save_path / f"{class_name}_info.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return out_file

def generate_dummy_variants(part: str, base_class_name: str, n_qubits: int, count: int, save_path: Path = Path("generated_code")) -> list[Path]:
    variant_paths = []
    for i in range(count):
        layers = get_layer_variant(part, i)
        class_name = f"{base_class_name}{i}"
        path = generate_dummy_code(
            part=part,
            class_name=class_name,
            n_qubits=n_qubits,
            layers=layers,
            save_path=save_path
        )
        variant_paths.append(path)
    return variant_paths