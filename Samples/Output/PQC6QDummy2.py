import torch
import torch.nn as nn
import torchquantum as tq

class PQC6QDummy2(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.n_qubits = n_qubits
        self.pqc = tq.QuantumModuleList([
            
            
            
                tq.RXYZCXLayer0(arch={"n_wires": 6, "n_blocks": 2}),
            
            
            
            
            
                tq.RXYZCXLayer0(arch={"n_wires": 6, "n_blocks": 2}),
            
            
             
        ])

    def forward(self, x: torch.Tensor):
        bsz = x.shape[0]
        qdev = tq.QuantumDevice(n_wires=self.n_qubits, bsz=bsz, device=x.device)  
        qdev.reset_states(bsz=bsz)
        qdev.set_states(x)  

        for op in self.pqc:
            op(qdev)

        return qdev.get_states_1d()