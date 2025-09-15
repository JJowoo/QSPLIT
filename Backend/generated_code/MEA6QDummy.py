# Generated Measurement Dummy - MEA6QDummy
import torch
import torch.nn as nn
import torchquantum as tq

class MEA6QDummy(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)

    def forward(self, x=None):
        self.qdevice.reset_states(bsz=x.shape[0])
        if x is not None:
            self.qdevice.set_states(x)
        measured = [
            tq.measurement.expval(self.qdevice, wires=i, observables=tq.PauliZ())
            for i in range(6)
        ]
        return torch.tensor(measured, dtype=torch.float32)