# Generated Measurement Dummy - MEA6QDummy3
import torch
import torch.nn as nn
import torchquantum as tq

class MEA6QDummy3(nn.Module):
    def __init__(self, n_qubits=6, num_classes=9):
        super().__init__()
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)
        self.fc = nn.Linear(n_qubits, num_classes)

    def forward(self, x=None):
        self.qdevice.reset_states(bsz=x.shape[0])
        self.qdevice.set_states(x)

        measured = [
            tq.measurement.expval(self.qdevice, wires=i, observables=tq.PauliZ())
            for i in range(6)
        ]
        measured_tensor = torch.stack(measured, dim=1)  # shape: [bsz, n_qubits, 1]
        measured_tensor = measured_tensor.squeeze(-1)

        
        return self.fc(measured_tensor)