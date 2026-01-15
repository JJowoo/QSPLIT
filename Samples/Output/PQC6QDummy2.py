# Generated PQC Dummy - PQC6QDummy2
import torch
import torch.nn as nn
import torchquantum as tq

try:
    import torchquantum.functional as tqf
except Exception:
    tqf = None

try:
    import torchquantum.operator as op
except Exception:
    op = None

class PQC6QDummy2(nn.Module):
    def __init__(self, n_qubits=6, depth=2):
        super().__init__()
        self.n_qubits = n_qubits
        self.depth = depth
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)

        # gate sequence (list[str])
        self.gates = ['U3', 'CCZ']

        # trainable params for parameterized gates (one scalar per step, broadcast to batch)
        self.theta = nn.Parameter(torch.zeros(len(self.gates), 4))

    def _pair(self, i: int):
        a = i % self.n_qubits
        b = (i + 1) % self.n_qubits
        return [a, b]

    def _triple(self, i: int):
        a = i % self.n_qubits
        b = (i + 1) % self.n_qubits
        c = (i + 2) % self.n_qubits
        return [a, b, c]

    def _apply_gate(self, gate: str, step: int, bsz: int):
        # choose wires deterministically
        if gate in {"CNOT","CZ","CY","CH","CHadamard","CS","CSDG","CSX","DCX","ECR","SWAP","SSWAP","ISWAP",
                    "RXX","RYY","RZZ","RZX","XXMINYY","XXPLUSYY","SingleExcitation",
                    "CRX","CRY","CRZ","CRot","CU","CU1","CU2","CU3","MultiRZ","MultiCNOT","MultiXCNOT"}:
            wires = self._pair(step)
        elif gate in {"Toffoli","CCZ","RCCX","CSWAP"}:
            wires = self._triple(step)
        elif gate in {"C3X","C3SX","RC3X"} and self.n_qubits >= 4:
            wires = [0,1,2,3]
        elif gate in {"C4X"} and self.n_qubits >= 5:
            wires = [0,1,2,3,4]
        else:
            wires = [step % self.n_qubits]

        param_dim = {
            "RX": 1, "RY": 1, "RZ": 1, "RXX": 1, "RYY": 1, "RZZ": 1, "RZX": 1,
            "XXPLUSYY": 1, "XXMINYY": 1,
            "CRX": 1, "CRY": 1, "CRZ": 1,
            "U1": 1, "CU1": 1,
            "PhaseShift": 1,
            "SingleExcitation": 1,
            "MultiRZ": 1,
            "U2": 2, "CU2": 2,
            "U3": 4, "CU3": 4,
            "U": 4, "CU": 4,
            "Rot": 4, "CRot": 4,
        }

        k = param_dim.get(gate, 0)
        params = None
        if k > 0:
            params = self.theta[step, :k].unsqueeze(0).repeat(bsz, 1)  # (bsz, k)

        # functional 우선
        if tqf is not None:
            fn = getattr(tqf, gate.lower(), None)
            if fn is not None:
                if k == 0:
                    fn(self.qdevice, wires=wires)
                elif k == 1:
                    try:
                        fn(self.qdevice, wires=wires, params=params[:, 0])
                    except Exception:
                        fn(self.qdevice, wires=wires, params=params)
                else:
                    fn(self.qdevice, wires=wires, params=params)
                return

        # 2) operator class fallback
        if op is None:
            raise RuntimeError(f"No functional/op backend for gate={gate}")

        cls = getattr(op, gate, None)
        if cls is None:
            raise RuntimeError(f"Unknown gate class: {gate}")

        try:
            g = cls(wires=wires, params=params) if params is not None else cls(wires=wires)
        except TypeError:
            # some ops expect params shape or different keyword; minimal fallback
            g = cls(wires=wires)

        # most torchquantum operators are callable on qdevice
        g(self.qdevice)

    def forward(self, x: torch.Tensor):
        bsz = x.shape[0]
        self.qdevice.reset_states(bsz=bsz)

        # apply gate sequence
        for step, gate in enumerate(self.gates):
            self._apply_gate(gate, step, bsz)

        return self.qdevice.get_states_1d()
