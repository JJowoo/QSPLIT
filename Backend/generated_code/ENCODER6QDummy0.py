# Generated Encoder Dummy - ENCODER6QDummy0
import torch
import torch.nn as nn
import torchquantum as tq

class ENCODER6QDummy0(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)

    def forward(self, x: torch.Tensor):
        self.qdevice.reset_states(bsz=x.shape[0])
        for b in range(x.shape[0]):
            for i in range(6):
                tq.functional.rx(self.qdevice, wires=i, params=x[b][i])
        return self.qdevice.get_states_1d()