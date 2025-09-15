import torch
import torch.nn as nn
import torchquantum as tq

class PQC6QDummy3(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)
        self.pqc = tq.QuantumModuleList([
            
            
                tq.FarhiLayer0(arch={"n_wires": 6, "n_blocks": 2}),
            
            
        ])

    def forward(self, x=None):
        self.qdevice.reset_states(bsz=1)
        for op in self.pqc:
            op(self.qdevice)
        return self.qdevice.get_states_1d()