import torch
import torch.nn as nn
import torchquantum as tq

class PQC6QDummy0(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.n_qubits = n_qubits
        self.pqc = tq.QuantumModuleList([
            
            
            
                
                tq.RY(has_params=True,trainable=True, wires=0),
                
                tq.RY(has_params=True,trainable=True, wires=1),
                
                tq.RY(has_params=True,trainable=True, wires=2),
                
                tq.RY(has_params=True,trainable=True, wires=3),
                
                tq.RY(has_params=True,trainable=True, wires=4),
                
                tq.RY(has_params=True,trainable=True, wires=5),
                
            
            
            
                
                tq.RZ(has_params=True,trainable=True, wires=0),
                
                tq.RZ(has_params=True,trainable=True, wires=1),
                
                tq.RZ(has_params=True,trainable=True, wires=2),
                
                tq.RZ(has_params=True,trainable=True, wires=3),
                
                tq.RZ(has_params=True,trainable=True, wires=4),
                
                tq.RZ(has_params=True,trainable=True, wires=5),
                
            
            
            
                tq.CNOT(wires=[0, 1]),
            
            
            
            
            
                
                tq.RY(has_params=True,trainable=True, wires=0),
                
                tq.RY(has_params=True,trainable=True, wires=1),
                
                tq.RY(has_params=True,trainable=True, wires=2),
                
                tq.RY(has_params=True,trainable=True, wires=3),
                
                tq.RY(has_params=True,trainable=True, wires=4),
                
                tq.RY(has_params=True,trainable=True, wires=5),
                
            
            
            
                
                tq.RZ(has_params=True,trainable=True, wires=0),
                
                tq.RZ(has_params=True,trainable=True, wires=1),
                
                tq.RZ(has_params=True,trainable=True, wires=2),
                
                tq.RZ(has_params=True,trainable=True, wires=3),
                
                tq.RZ(has_params=True,trainable=True, wires=4),
                
                tq.RZ(has_params=True,trainable=True, wires=5),
                
            
            
            
                tq.CNOT(wires=[0, 1]),
            
            
             
        ])

    def forward(self, x: torch.Tensor):
        bsz = x.shape[0]
        qdev = tq.QuantumDevice(n_wires=self.n_qubits, bsz=bsz, device=x.device)  
        qdev.reset_states(bsz=bsz)
        qdev.set_states(x)  

        for op in self.pqc:
            op(qdev)

        return qdev.get_states_1d()