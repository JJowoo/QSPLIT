# QSPLIT: Quantum Split Learning Testing Toolkit

**QSPLIT** is a GUI-based framework designed for automated testing and development of Quantum Neural Network (QNN) architectures. By combining user-provided **Target Code** with automatically generated **Dummy Code**, QSPLIT facilitates efficient Split Learning experiments.

[![Demo Video](https://img.shields.io/badge/Demo-Video-red?style=for-the-badge&logo=youtube)](https://github.com/user-attachments/assets/3a013af0-2cd1-43a7-b4a8-30ccf24d3538)
[![Web Inference](https://img.shields.io/badge/Web-Inference-blue?style=for-the-badge&logo=googlechrome)](https://eb355abb2a59.ngrok-free.app/)

---

## 🛠 Tool Components

<p align="center">
  <img width="1000" alt="QSPLIT Components" src="https://github.com/user-attachments/assets/0bbca86b-b062-4290-a472-d12387a05518" />
</p>

### **A. Part Selection**
Define which components of the QNN (SE, PQC, MEA) are provided by the user and which are generated.
- **Target Code**: User-uploaded core logic.
- **Dummy Code**: Components automatically generated to ensure structural compatibility.

### **B. Target Code Hyperparameters**
- **Quantum Device**: Configures the number of qubits, batch size, and circuit depth.
- **Training**: Defines epochs, optimizer, and learning rate for the split learning process.

### **C. Dummy Code Generation**
- Automatically generates variations of dummy codes (e.g., PQC layers or MEA observables).
- The Dummy List allows users to inspect the internal gate operations of each generated code.

### **D. Split Learning Execution**
- Powered by the TorchQuantum framework.
- Executes parallel training across multiple target-dummy combinations with real-time log streaming.

### **E. Result Visualization & Export**
- Displays performance metrics (Accuracy/Loss) for all combinations.
- Validated components can be exported as executable `.py` files for seamless integration into production.
---

# 🚀 HOW TO USE

## 1. Getting Started

### 🌐 Web Inference (Quick Start)
Access the live interface without installation: [QSPLIT Web](https://eb355abb2a59.ngrok-free.app/)

### 💻 Local Setup
**Prerequisites:**
- **Python** ≥ 3.12 | **Flutter** 3.32.8
- **PyTorch** 2.8.0 | **TorchQuantum** 0.1.8

**Step 1: Environment Setup**
```bash
# Clone the repository and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 2. Dataset Setup**
Before running the backend, you must download and place the dataset.
- Download Link: [Dataset](https://drive.google.com/file/d/15N7R2SZJHxJIPPBmwAB-JeUCUhvHmNR-/view?usp=sharing)
- Path: Place the downloaded images into the following directory: Backend/dataset/medmnist/AbdomenCT

**Step 3. Run Application**
```bash
# run backend
cd Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
```bash
# run frontend
cd Frontend
flutter run -d chrome
```

## 2. Configure Components
- **Upload Target Code**: In *Part Selection*, click **Upload** to provide any subset of SE / PQC / MEA as target code.  
- **Component Selection**: Select each component as **Target Code** or **Dummy Code** (radio buttons; mutually exclusive).  
- **Parameter Input**: In *Target Code Hyperparameter*  
  - *Quantum Device*: number of qubits, batch size, circuit depths  
  - *Training*: epochs, optimizer, learning rate  
  - *Dataset*: choose from datasets uploaded to QSPLIT (e.g., MedNIST)  

## 3. Generate Dummy Code

1. Configure parameters in *Target Code Hyperparameter*  
2. Click **Generate** to create dummy code  
3. Inspect in *Dummy Code Generation → Dummy List*  
   - Example: PQC = RY/RZ/CNOT gate stack, MEA = Z observable  

## 4. Execute Split Learning

- In *Dummy Code Generation*, click **Run** to start split learning across all combinations  
- Training uses *TorchQuantum*; per-epoch loss/accuracy are streamed in real time to the GUI  

## 5. Compare Results

- *Results* section lists accuracy and training time per combination  
- Easily identify stable or high-performing combinations  

## 6. Export Code

- In *Results*, select a dummy code and click **Export**  
- Outputs an executable `.py` file compatible with *TorchQuantum*  
- Enables reuse, extension, and integration into follow-up experiments or deployment

# Supplementary Examples
##Target Code: MEA, Dummy Code: SE, PQC
[https://github.com/user-attachments/assets/24fb7965-2d18-42cd-9492-faf29ad299a7](https://github.com/user-attachments/assets/24fb7965-2d18-42cd-9492-faf29ad299a7)



## Software Version
v1.0.0  
