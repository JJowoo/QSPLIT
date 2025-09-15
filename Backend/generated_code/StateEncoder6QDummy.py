from torchvision import datasets, transforms
from PIL import Image
import os

def save_cifar_images(path="./shared-data/cifar-10", num_images=10):
    os.makedirs(path, exist_ok=True)
    transform = transforms.ToPILImage()
    dataset = datasets.CIFAR10(root="./client-side/data", train=False, download=True)
    
    for i in range(min(num_images, len(dataset))):
        img, _ = dataset[i]
        img = transform(img)
        img.save(os.path.join(path, f"{i:04d}.png"))
