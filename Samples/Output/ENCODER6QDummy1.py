# Generated Encoder Dummy - ENCODER6QDummy1
import torch
import torch.nn as nn
import torchquantum as tq

class ENCODER6QDummy1(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.n_qubits = n_qubits
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)

    def forward(self, x: torch.Tensor):
        bsz = x.shape[0]
        self.qdevice.reset_states(bsz=bsz)

        angles = x[:, :self.n_qubits]

        for i in range(self.n_qubits):
            tq.functional.rx(self.qdevice, wires=i, params=angles[:, i])
        return self.qdevice.get_states_1d()