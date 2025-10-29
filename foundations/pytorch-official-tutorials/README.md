# PyTorch Official Tutorials

Implementation of PyTorch's official beginner tutorials covering core concepts and fundamentals.

## 📚 Notebooks Overview

| Notebook | Topics Covered | Key Concepts |
|----------|----------------|--------------|
| [Basics 0: Quickstart](Basics%200%20Quickstart.ipynb) | Quick introduction to PyTorch | Data, Model Creation, Model Evaluation, Model saving/loading |
| [Basics 1: Tensors](Basics%201%20Tensors.ipynb) | Tensors and Tensor operations | Creation, Attributes, Indexing, Slicing, Joining, Arithmetic, In-place operations, Bridge with NumPy |
| [Basics 2: Datasets and DataLoaders](Basics%202%20Datasets%20and%20DataLoaders.ipynb) | Data handling | `Dataset`, `DataLoader`, Iterating, Visualizing |
| [Basics 3: Transforms](Basics%203%20Transforms.ipynb) | Data preprocessing | ToTensor, Lambda Transforms |
| [Basics 4: Build the Neural Network](Basics%204%20Build%20the%20Neural%20Network.ipynb) | Model architecture and example of building a neural network to classify images in the FashionMNIST dataset. | device, forward, layers, params |
| [Basics 5: Automatic Differentiation](Basics%205%20Automatic%20Differentiation.ipynb) | Back propagation and gradients | gradients, gradient tracking, DAG, `autograd`, forward pass, backward pass, Jacobian Products |
| [Basics 6: Optimizing Model Parameters](Basics%206%20Optimizing%20Model%20Parameters.ipynb) | Training loop | Hyperparameterss, loss, optimizer, training steps |
| [Basics 7: Save and Load the Model](Basics%207%20Save%20and%20Load%20the%20Model.ipynb) | Model persistence | Shapes, saving/loading |

## 🚀 Getting Started

### Environment
- **Primary**: Google Colab

## Original Sources

Based on [PyTorch Official Tutorials](https://docs.pytorch.org/tutorials/intro.html)

## Learning Path

This series follows the natural progression of machine learning workflow:
1. Data Preparation (Notebooks 1-3) - Tensors, Datasets, Transforms
2. Model Building (Notebook 4) - Neural Network architecture
3. Training Fundamentals (Notebooks 5-6) - Autograd, Optimization
4. Model Management (Notebook 7) - Saving and loading

## Key Takeaways
- Understanding PyTorch tensor operations and automatic differentiation
- Building custom datasets and data loaders for real-world data
- Creating modular neural network architectures
- Implementing complete training loops with optimization
- Model persistence and deployment basics