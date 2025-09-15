import torch
import torch.nn as nn
import torchquantum as tq

class PQC6QDummy1(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)
        self.pqc = tq.QuantumModuleList([
            
            
                
                tq.U3(has_params=True,trainable=True, wires=0),
                
                tq.U3(has_params=True,trainable=True, wires=1),
                
                tq.U3(has_params=True,trainable=True, wires=2),
                
                tq.U3(has_params=True,trainable=True, wires=3),
                
                tq.U3(has_params=True,trainable=True, wires=4),
                
                tq.U3(has_params=True,trainable=True, wires=5),
                
            
            
            
                
                tq.RX(has_params=True,trainable=True, wires=0),
                
                tq.RX(has_params=True,trainable=True, wires=1),
                
                tq.RX(has_params=True,trainable=True, wires=2),
                
                tq.RX(has_params=True,trainable=True, wires=3),
                
                tq.RX(has_params=True,trainable=True, wires=4),
                
                tq.RX(has_params=True,trainable=True, wires=5),
                
            
            
            
                tq.CNOT(wires=[0, 1]),
            
            
        ])

    def forward(self, x=None):
        self.qdevice.reset_states(bsz=1)
        for op in self.pqc:
            op(self.qdevice)
        return self.qdevice.get_states_1d()