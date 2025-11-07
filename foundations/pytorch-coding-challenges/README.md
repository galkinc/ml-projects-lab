# Foundations

PyTorch practice problems, ranging from basic to hard, designed to enhance skills in deep learning and PyTorch.

The tasks was taken from: [TorchLeet / easy](https://github.com/Exorust/TorchLeet/tree/main/torch/easy) and [basic](https://github.com/Exorust/TorchLeet/tree/main/torch/basic)
The goal is not just to solve, but to **understand**, **explain** and **prepare for live-coding**. 

## 📚 Question Set

### Structure
- [`./basic_tasks/basic_tasks.ipynb`](./basic_tasks/basic_tasks.ipynb)
- [`./easy_tasks/easy_tasks.ipynb`](./easy_tasks/easy_tasks.ipynb)

### [Basic](./basic_tasks/basic_tasks.ipynb)
Mostly for beginners to get started with PyTorch.

- Implement linear regression (Solution)
- Write a custom Dataset and Dataloader to load from a CSV file (Solution)
- Write a custom activation function (Simple) (Solution)
- Implement Custom Loss Function (Huber Loss) (Solution)
- Implement a Deep Neural Network (Solution)
- Visualize Training Progress with TensorBoard in PyTorch (Solution)
- Save and Load Your PyTorch Model (Solution)

### [Easy](./easy_tasks/easy_tasks.ipynb)
Recommended for those who have a basic understanding of PyTorch and want to practice their skills.

- Implement a CNN on CIFAR-10 (Solution)
- Implement an RNN from Scratch (Solution)
- Use torchvision.transforms to apply data augmentation (Solution)
- Add a benchmark to your PyTorch code (Solution)
- Train an autoencoder for anomaly detection (Solution)
- Quantize your language model (Solution)
- Implement Mixed Precision Training using torch.cuda.amp (Solution)

## 🎯 Implementation Features

Some tasks have been adapted to modern practices and errors encountered in real code:

| Task | Update / Comment |
|-------|---------------------------|
| **Quantize your language model** | Used `torchao` instead of the deprecated `torch.quantization`. More details: [PyTorch deprecation](https://github.com/pytorch/ao/issues/2259). |
| **Mixed Precision Training** | Added support for CPU emulation via `torch.autocast(device_type="cpu", dtype=torch.bfloat16)` and clarification of why AMP is GPU-only. |
| **Linear Regression with Custom Activation** | Note: nonlinear activation in linear regression violates the problem's assumptions → it is important to distinguish between "model" and "specifications." |
| **RNN Training Loop** | Fixed: `super().__init__()` (not `super()`), `self.rnn(x)` (not `self.run(x)`), and optimized the loop (batch vs. sample-wise). |
| **Autoencoder for MNIST** | Added `nn.Flatten()` — critical for compatibility of the shapes `(B, 1, 28, 28) → (B, 784)`. |

> 💡 All solutions have been tested for functionality and are accompanied by an explanation if it requires.