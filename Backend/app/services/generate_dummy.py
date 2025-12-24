from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
import json
import random

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

from itertools import combinations, product

def build_pauli_observable_pool(n_qubits: int,
                               max_locality: int = 2,
                               paulis: tuple[str, ...] = ("X", "Y", "Z")) -> list[str]:
    
   
    pool: list[str] = []
    for loc in range(1, max_locality + 1):
        for idxs in combinations(range(n_qubits), loc):
            for ops in product(paulis, repeat=loc):
                s = ["I"] * n_qubits
                for i, o in zip(idxs, ops):
                    s[i] = o
                pool.append("".join(s))
    return pool

def mea_variant_single(n_qubits: int, variant: int, max_locality: int = 2) -> list[str]:
    pool = build_pauli_observable_pool(n_qubits, max_locality=max_locality)
    return [pool[variant % len(pool)]]

def build_pqc_gate_pool(n_qubits: int, include_advanced: bool = False) -> list[str]:
    exclude = {
        "Operator", "Operation", "Observable",
        "DiagonalOperation",            # diag 값 필요
        "QubitUnitary", "QubitUnitaryFast",  # unitary matrix 필요
        "TrainableUnitary", "TrainableUnitaryStrict",  # 초기화/행렬 필요 
        "GlobalPhase",                  # phase 파라미터 필요
        "Reset", 
        'XXPLUSYY', 'CU', 'CU1', 'CU2', 'CU3','U2','XXMINYY'                    # 시뮬레이터 설정에 따라 불안정
    }

    all_names = [
        'C3SX', 'C3X', 'C4X', 'CCZ', 'CH', 'CHadamard', 'CNOT', 'CRX', 'CRY', 'CRZ', 'CRot', 'CS', 'CSDG', 'CSWAP', 'CSX',
        'CY', 'CZ', 'DCX', 'ECR', 'Hadamard', 'I', 'ISWAP',
        'MultiCNOT', 'MultiRZ', 'MultiXCNOT',
        'PauliX', 'PauliY', 'PauliZ',
        'PhaseShift', 'QFT', 'R', 'RC3X', 'RCCX', 'RX', 'RXX', 'RY', 'RYY', 'RZ', 'RZX', 'RZZ',
        'Rot', 'S', 'SDG', 'SHadamard', 'SSWAP', 'SWAP', 'SX', 'SXDG',
        'SingleExcitation', 'T', 'TDG', 'Toffoli',
        'U', 'U1', 'U3'
    ]

    pool = [g for g in all_names if g not in exclude]


    def ok(g: str) -> bool:
        if g in ("Toffoli", "CCZ", "RCCX"):
            return n_qubits >= 3
        if g in ("C3X", "C3SX", "RC3X"):
            return n_qubits >= 4
        if g in ("C4X",):
            return n_qubits >= 5
        if g in ("CSWAP",):
            return n_qubits >= 3
       
        twoq = {"CNOT","CZ","CY","CH","CHadamard","CS","CSDG","CSX","DCX","ECR","SWAP","SSWAP","ISWAP",
                "RXX","RYY","RZZ","RZX","XXMINYY","XXPLUSYY","SingleExcitation",
                "CRX","CRY","CRZ","CRot","CU","CU1","CU2","CU3","MultiRZ"}  # MultiRZ는 보통 2+ wires
        if g in twoq:
            return n_qubits >= 2
        return True

    pool = [g for g in pool if ok(g)]

    
    if include_advanced:
        pool += ["GlobalPhase", "QubitUnitary", "QubitUnitaryFast", "DiagonalOperation", "TrainableUnitary", "TrainableUnitaryStrict"]

    return pool

def pqc_variant_sample(n_qubits: int, variant: int, depth: int, include_advanced: bool = False) -> list[str]:
    pool = build_pqc_gate_pool(n_qubits, include_advanced=include_advanced)
    rnd = random.Random(variant)
    # depth만큼 gate name을 뽑아 시퀀스 구성
    return [rnd.choice(pool) for _ in range(depth)]

def get_layer_variant(part: str, variant: int, n_qubits: int, depth: int) -> list[str]:
    pqc_variants = [
        ["RY", "RZ", "CNOT"],
        ["U3", "RX", "CNOT"],
        ["RXYZCXLayer0"],
        ["FarhiLayer0"]
    ]
    encoder_variants = [
        ["AmplitudeEncoder"],
        ["MagnitudeEncoder"],
        ["MultiPhaseEncoder"],
        ["StateEncoder"],
        ["GeneralEncoder"],
    ]
    
    if part == "pqc":
        return pqc_variant_sample(n_qubits, variant, depth, include_advanced=False)
    elif part == "mea":
        return mea_variant_single(n_qubits, variant, max_locality=2)
    elif part == "encoder":
        return encoder_variants[variant % len(encoder_variants)]
    else:
        return []
    
def extract_metadata(part: str, layers: list[str], n_qubits: int) -> dict:
    if part == "encoder":
        encoder_type = layers[0] if layers else "StateEncoder"
        input_dim = (2 ** n_qubits) if encoder_type in ("AmplitudeEncoder", "StateEncoder") else n_qubits
        return {
            "encoding_type": encoder_type,
            "input_dim": input_dim,
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



def generate_dummy_code(part: str,class_name: str, n_qubits: int, layers: list[str], save_path: Path= Path("generated_code"), depth: int = 2) -> Path:
    if part not in TEMPLATE_MAP:
        raise ValueError(f"Unsupported part type: {part}")
    
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    try:
        tpl = env.get_template(TEMPLATE_MAP[part])
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Template not found: {TEMPLATE_MAP[part]}") from e

    code = tpl.render(
        class_name=class_name,
        n_qubits=n_qubits,
        layers=layers or [],  # MEA 일 때 빈거 요청
        num_classes=9,
        depth=depth, 
    )
    out_file = save_path / f"{class_name}.py"
    out_file.write_text(code, encoding="utf-8")

    metadata = extract_metadata(part, layers, n_qubits)
    metadata["depth"] = depth 
    meta_file = save_path / f"{class_name}_info.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return out_file

def generate_dummy_variants(part: str, base_class_name: str, n_qubits: int, count: int, save_path: Path = Path("generated_code"), depth: int = 2) -> list[Path]:
    variant_paths = []
    for i in range(count):
        layers = get_layer_variant(part, i, n_qubits, depth)
        class_name = f"{base_class_name}{i}"
        path = generate_dummy_code(
            part=part,
            class_name=class_name,
            n_qubits=n_qubits,
            layers=layers,
            save_path=save_path,
            depth=depth
        )
        variant_paths.append(path)
    return variant_paths
