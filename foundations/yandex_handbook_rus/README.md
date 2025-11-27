# Yandex ML Handbook Labs (RU)

Solutions to laboratory assignments from the [Yandex ML Handbook](https://ml-handbook.ru/) — a structured curriculum by the School of Data Analysis (ShAD).

Tasks fro ShAD are in Russian. 
All code is written in English, with clear variable names and production-oriented patterns were it's possible (e.g., `sklearn` pipelines, proper validation).

Shad requires validation when submitting tasks. 
The verification system is not always correct, so there may be several implementations, 
for example, the way I implemented it, the way the validator expects (usually through torture), and a mixed version.

---

## 📚 Labs Completed

### [Lab 2: Linear Models](./2_1_Lab_Linear_models/autohw_linear_models_dabd6b0378.ipynb)
- Basic & advanced preprocessing (handling missing values, scaling)
- **RMSLE** as a business-relevant metric for price prediction
- Log-transforming target → `ExponentialLinearRegression`
- Cross-validation and hyperparameter tuning
- Implementing linear regression **from scratch**
- Working with categorical features (one-hot, target encoding)
- Building robust `sklearn` pipelines

### [Lab 1: Introduction to Machine Learning](./1_Lab_Introduction_to_ML/autohw_intro_ML_92e1d33a4d_1_3.ipynb)
- Exploratory Data Analysis (EDA) with `pandas`/`numpy`
- Task framing: regression vs classification
- Metric selection and interpretation (why MAE ≠ MSE ≠ accuracy)
- Training simple models and observing overfitting
- Understanding the role of data quality and quantity