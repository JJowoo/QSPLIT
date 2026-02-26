# Generated Encoder Dummy - ENCODER6QDummy0
import math
import inspect
import torch
import torch.nn as nn
import torchquantum as tq

class StateEncoder6QDummy(nn.Module):
    def __init__(self, n_qubits=6):
        super().__init__()
        self.n_qubits = n_qubits
        self.qdevice = tq.QuantumDevice(n_wires=n_qubits)

 
        self.encoder_type = "AmplitudeEncoder"

        enc_mod = getattr(tq, "encoding", None)
        if enc_mod is None:
            raise ImportError("torchquantum.encoding module not found")

        enc_cls = getattr(enc_mod, self.encoder_type, None)
        self.encoder = None
        if enc_cls is not None:
            self.encoder = self._init_encoder(enc_cls)

    def _init_encoder(self, enc_cls):
       
        sig = inspect.signature(enc_cls.__init__)
        params = sig.parameters
        kwargs = {}


        for key in ("n_wires", "n_qubits", "n_wire"):
            if key in params:
                kwargs[key] = self.n_qubits
                break

   
        dim = (2 ** self.n_qubits) if self.encoder_type in ("AmplitudeEncoder", "StateEncoder") else self.n_qubits
        for key in ("input_dim", "feature_dim", "n_features", "num_features"):
            if key in params and key not in kwargs:
                kwargs[key] = dim
                break

       
        if self.encoder_type == "PhaseEncoder":
            if "func" in params:
                kwargs["func"] = "rx"

        if self.encoder_type == "MultiPhaseEncoder":
            if "funcs" in params:
                kwargs["funcs"] = ["rx"] * self.n_qubits

        if self.encoder_type == "MagnitudeEncoder":
            
            if "func" in params:
                kwargs["func"] = "rx"
            if "funcs" in params:
                kwargs["funcs"] = ["rx"] * self.n_qubits

        
        if self.encoder_type == "GeneralEncoder":
            for key in ("encoder_config", "config", "encoding_config"):
                if key in params:
                    kwargs[key] = self._default_general_config()
                    break

        try:
            return enc_cls(**kwargs) if kwargs else enc_cls()
        except Exception:
            
            try:
                return enc_cls()
            except Exception:
                return None

    def _default_general_config(self):
        cfg = []
        for i in range(self.n_qubits):
            cfg.append({
                "input_idx": [i],
                "func": "rx",
                "wires": [i],
            })
        return cfg

    def _prepare_input(self, x: torch.Tensor) -> torch.Tensor:
        bsz = x.shape[0]

        if self.encoder_type in ("AmplitudeEncoder", "StateEncoder"):
            dim = 2 ** self.n_qubits
            if x.shape[1] < dim:
                pad = torch.zeros((bsz, dim - x.shape[1]), device=x.device, dtype=x.dtype)
                v = torch.cat([x, pad], dim=1)
            else:
                v = x[:, :dim]

            norm = torch.norm(v, dim=1, keepdim=True).clamp_min(1e-12)
            v = v / norm
            return v


        if x.shape[1] < self.n_qubits:
            pad = torch.zeros((bsz, self.n_qubits - x.shape[1]), device=x.device, dtype=x.dtype)
            v = torch.cat([x, pad], dim=1)
        else:
            v = x[:, :self.n_qubits]

        if self.encoder_type in ("PhaseEncoder", "MultiPhaseEncoder"):
            v = (v + math.pi) % (2 * math.pi) - math.pi
        if self.encoder_type == "MagnitudeEncoder":
            v = torch.abs(v)

        return v

    def _manual_fallback_encode(self, features: torch.Tensor):
      
        if self.encoder_type in ("PhaseEncoder", "MultiPhaseEncoder"):
            for i in range(self.n_qubits):
                tq.functional.rz(self.qdevice, wires=i, params=features[:, i])
        else:
            for i in range(self.n_qubits):
                tq.functional.rx(self.qdevice, wires=i, params=features[:, i])

    def forward(self, x: torch.Tensor):
        bsz = x.shape[0]
        self.qdevice.reset_states(bsz=bsz)

        features = self._prepare_input(x)

  
        if self.encoder is not None:
            try:
               
                try:
                    _ = self.encoder(self.qdevice, features)
                except TypeError:
                    try:
                        _ = self.encoder(features, self.qdevice)
                    except TypeError:
                        _ = self.encoder(features)

                return self.qdevice.get_states_1d()

            except (NotImplementedError, ValueError, TypeError):
                
                self._manual_fallback_encode(features)
                return self.qdevice.get_states_1d()

        
        self._manual_fallback_encode(features)
        return self.qdevice.get_states_1d()