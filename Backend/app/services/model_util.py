from pathlib import Path
import torch
import os

def save_selected_weights(part_name: str, model: torch.nn.Module, save_dir: str = "./trained_weights"):
    os.makedirs(save_dir, exist_ok=True)
    save_path = Path(save_dir) / f"{part_name}_only.pt"
    torch.save(model.state_dict(), save_path)
    print(f"Saved weights for {part_name} at: {save_path}")