# TensorFlow Forecasting Practice (2023)

Learning repository documenting my TensorFlow certification journey. 
Contains reproduced official examples and experiments that formed the foundation for my time series forecasting work.
The official examples cover fundamental concepts and real-world applications of deep learning.

## 📁 Project Structure

### 🔧 Core TensorFlow Concepts
- [**Distributed Training**](./01_training_techniques/distributed_training_with_tensorflow.ipynb): TensorFlow API to distribute training across multiple GPUs, multiple machines, or TPUs.
- [**Accelerators (GPU/TPU)**](./01_training_techniques/): Basic setup and usage of hardware accelerators
  - [**GPU Usage**](./01_training_techniques/accelerators_use_a_gpu.ipynb): Multiple GPUs using
  - [**Tensor Processing Units**](./01_training_techniques/accelerators_use_tpu.ipynb): Collection of TPU devices connected by dedicated high-speed network interfaces
- [**Overfit and underfit**](./01_training_techniques/overfit_and_underfit.ipynb): Managing model capacity by several common regularization techniques, and use them to improve on a classification model.
- [**Model Persistence**](./02_model_management/save_and_load.ipynb): Complete examples of saving/loading models in different formats
  - Contains: checkpoints, H5 models, SavedModel format
- [**TensorBoard Integration**](./03_optimization/tensorboard/get_started_with_tensorboard.ipynb): Visualization and metrics tracking
  - Contains fit and gradient tape training and validation logs
- [**Hyperparameter Tuning**](./03_optimization/hparams_tuning/hyperparameter_tuning_with_hparams.ipynb): Systematic parameter optimization with logging
  - Contains: training logs and parameter experiments
- [**Keras Tuner**](./03_optimization/keras_tuner_image_classification.ipynb): Hypertuning or hyperparameter tuning. The Keras Tuner is a library that helps you pick the optimal set of hyperparameters for your TensorFlow program.
- [**TensorFlow Hub Example**](./06_nlp/text_classification_with_hub_movie_reviews.ipynb): Demonstrates the basic application of transfer learning with TensorFlow Hub and Keras.

### 📊 Basic Regression & Forecasting
- [**Predict fuel efficiency**](./04_basic_regression/regression.ipynb): Basic regression: Predict fuel efficiency. The tutorial uses the classic Auto MPG dataset and demonstrates how to build models to predict the fuel efficiency of the late-1970s and early 1980s automobiles. 
  - Contains: trained model artifacts (SavedModel format)

### 🖼️ Computer Vision
- **Image Classification**:
  - [**Fashion MNIST**](./05_computer_vision/classify_clothing_images.ipynb): This guide trains a neural network model to classify images of clothing, like sneakers and shirts.
  - [**CIFAR-10**](./05_computer_vision/keras_tuner_cifar10_multiclasses_hyperparameter_tuning.ipynb): Creates a simple tunable model and shows how to train it on CIFAR-10

### 📝 Natural Language Processing
- [**Binary Text Classification with TensorFlow Hub**](./06_nlp/text_classification_sentiment_analysis.ipynb): Trains a sentiment analysis model to classify movie reviews as positive or negative, based on the text of the review. This is an example of binary—or two-class—classification.
- [**Multi-class Classification on Stack Overflow Questions**](./06_nlp/text_classification_multiclass_classification_on_stackoverflow_questions.ipynb): Shows how to train a multi-class classifier to predict the tag of a programming question on Stack Overflow.
- [**Text Classification with TensorFlow Hub**](./06_nlp/text_classification_with_hub_movie_reviews.ipynb): Classifies movie reviews as positive or negative using the text of the review with TensorFlow Hub.

## 🚀 Getting Started

### Environment
- **Primary**: Google Colab

## Original Sources

Based on [TensorFlow Official Tutorials](hhttps://www.tensorflow.org/guide)

---

**Note:** This code was transferred from my main [forecasting repository](https://github.com/galkinc/deep-learning-forecasting/) where these techniques were actively applied to real problems. You can find more application tasks related to time series forecasting there.