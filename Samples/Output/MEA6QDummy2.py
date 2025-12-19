# Generated Measurement Dummy - MEA6QDummy2
import torch
import torch.nn as nn
import torchquantum as tq

class MEA6QDummy2(nn.Module):
    def __init__(self, n_qubits=6, num_classes=9):
        super().__init__()
        self.n_qubits = n_qubits
        self.fc = nn.Linear(n_qubits, num_classes)

    def forward(self, x: torch.Tensor):
        bsz = x.shape[0]
        qdev = tq.QuantumDevice(n_wires=self.n_qubits, bsz=bsz, device=x.device)  
        qdev.reset_states(bsz=bsz)
        qdev.set_states(x)

        measured = [
            tq.measurement.expval(qdev, wires=i, observables=tq.PauliZ())
            for i in range(self.n_qubits)
        ]
        measured_tensor = torch.stack(measured, dim=1).squeeze(-1)  
        return self.fc(measured_tensor)