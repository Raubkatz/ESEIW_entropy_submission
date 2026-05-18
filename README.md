# Commit Entropy Defect Prediction Pipeline

## Scope

This repository contains the Python scripts used to prepare data, train classifiers, evaluate results, and analyze feature relationships for the commit entropy defect prediction study.

The main goal is to compare two entropy-based process metrics:

- `180fileHcpf`: code-change entropy across files
- `180commitHcpf`: commit entropy across commits

The pipeline predicts:

- `isSZZBugIntroducer`

This means the model predicts whether a commit is classified as defect-inducing.

---

# Python Version

Recommended Python version:

```text
Python 3.11
```

Tested/recommended package versions:

```text
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.5.1
catboost==1.2.5
imbalanced-learn==0.12.3
matplotlib==3.9.1
seaborn==0.13.2
scipy==1.14.0
scikit-optimize==0.10.2
```

Install with:

```bash
pip install pandas==2.2.2 numpy==1.26.4 scikit-learn==1.5.1 catboost==1.2.5 imbalanced-learn==0.12.3 matplotlib==3.9.1 seaborn==0.13.2 scipy==1.14.0 scikit-optimize==0.10.2
```

Recommended Conda setup:

```bash
conda create -n commit_entropy python=3.11
conda activate commit_entropy

pip install pandas==2.2.2 numpy==1.26.4 scikit-learn==1.5.1 catboost==1.2.5 imbalanced-learn==0.12.3 matplotlib==3.9.1 seaborn==0.13.2 scipy==1.14.0 scikit-optimize==0.10.2
```

---

# Repository Scripts

```text
00a_data_analysis_merge_projects.py
01a_clean_data_Classifier.py
02a_train_test_split.py
03a_train_CatBoost_Classifier.py
04a_post_hoc_classifier.py
05_pairwise_correlation_analysis.py
```

The pre-cleaning script is not part of this README.

---

# Full Run Order

Run the scripts in this order:

```bash
python 00a_data_analysis_merge_projects.py
python 01a_clean_data_Classifier.py
python 02a_train_test_split.py
python 03a_train_CatBoost_Classifier.py
python 04a_post_hoc_classifier.py
python 05_pairwise_correlation_analysis.py
```

---

# 1. Merge Project CSV Files

## Script

```bash
python 00a_data_analysis_merge_projects.py
```

## What it does

This script reads all project CSV files from the input folder and combines them into one merged dataset.

It also checks that all project files follow the same expected column structure.

## Input

```text
DATA_ESEIW_final/
```

This folder should contain the project-level CSV files.

## Output

```text
DATA_ESEIW_merged_csv/merged_dataset_2026.csv
DATA_ESEIW_merged_csv/merge_report.json
```

## Main settings inside the script

```python
INPUT_DIR = "DATA_ESEIW_final"
OUT_DIR = "DATA_ESEIW_merged_csv"
OUTPUT_NAME = "merged_dataset_2026.csv"
PATTERN = "*.csv"
```

## Kept columns

The script keeps only the columns listed in `EXPECTED_COLUMNS`.

Current study columns:

```text
isSZZBugIntroducer
age
revision
nrOfFunctions
dok0.004Sum
dok0.004AuthorPreCommit
totalLoc
relativeModified
dok0.004AuthorPostCommit
modified
totalAuthors
dok0.004Avg
totalRefactors
authors
isRefactor
180fileHcpf
180commitHcpf
```

---

# 2. Clean Dataset

## Script

```bash
python 01a_clean_data_Classifier.py
```

## What it does

This script prepares the merged dataset for machine learning.

It:

- selects the target column,
- selects the feature columns,
- checks missing values,
- checks negative values,
- handles negative values,
- creates the cleaned dataset,
- writes basic statistics.

## Input

```text
DATA_ESEIW_merged_csv/merged_dataset_2026.csv
```

## Output

```text
data_isSZZBugIntroducer_classification/cleaned_dataset.csv
data_isSZZBugIntroducer_classification/sanity_report.txt
data_isSZZBugIntroducer_classification/sanity_report.json
data_isSZZBugIntroducer_classification/stats_tables/
```

## Main settings inside the script

```python
TARGET = "isSZZBugIntroducer"
NEGATIVE_HANDLING = "replace_with_nan"
DROP_MISSING_TARGET = True
DROP_ALL_FEATURES_MISSING = True
```

## Selected features

```text
age
revision
nrOfFunctions
dok0.004Sum
dok0.004AuthorPreCommit
totalLoc
relativeModified
dok0.004AuthorPostCommit
modified
totalAuthors
dok0.004Avg
totalRefactors
authors
isRefactor
180fileHcpf
180commitHcpf
```

## Negative value handling

Current setting:

```python
NEGATIVE_HANDLING = "replace_with_nan"
```

This means negative numeric feature values are replaced with missing values.

---

# 3. Create Train/Test Split

## Script

```bash
python 02a_train_test_split.py
```

## What it does

This script splits the cleaned dataset into training and test data.

By default, it uses a stratified split.  
This keeps the target-class distribution similar in train and test data.

## Input

```text
data_isSZZBugIntroducer_classification/cleaned_dataset.csv
```

## Output

```text
data_isSZZBugIntroducer_classification/splits_42/train.csv
data_isSZZBugIntroducer_classification/splits_42/test.csv
data_isSZZBugIntroducer_classification/splits_42/split_report.json
```

## Main settings inside the script

```python
TARGET = "isSZZBugIntroducer"
TEST_SIZE = 0.2
RANDOM_STATE = 42
STRATIFY = True
```

---

# 4. Train CatBoost Classifier

## Script

```bash
python 03a_train_CatBoost_Classifier.py
```

## What it does

This script trains the defect prediction model.

It:

- reads the training and test data,
- creates an internal validation split,
- balances the training data by undersampling,
- trains CatBoost models,
- optionally runs Bayesian hyperparameter optimization,
- selects the best model,
- saves the final model and reports.

## Input

```text
data_isSZZBugIntroducer_classification/splits_42/train.csv
data_isSZZBugIntroducer_classification/splits_42/test.csv
```

## Output

```text
data_isSZZBugIntroducer_classification/models_42/best_model.cbm
data_isSZZBugIntroducer_classification/models_42/features.json
data_isSZZBugIntroducer_classification/models_42/training_report.txt
data_isSZZBugIntroducer_classification/models_42/training_report.json
```

## Main settings inside the script

```python
TARGET = "isSZZBugIntroducer"
RANDOM_STATE = 42
VAL_SIZE = 0.2
TRAIN_MINORITY_FRACTION = 0.9
N_VAL_EXCERPTS = 100
VAL_MINORITY_FRACTION = 0.9
SKIP_BAYES_OPTIMIZATION = False
```

## Important output files

```text
best_model.cbm
```

The trained CatBoost model.

```text
features.json
```

The exact feature list used during training.

---

# 5. Evaluate Trained Model

## Script

```bash
python 04a_post_hoc_classifier.py
```

## What it does

This script evaluates the trained model.

It does not train a new model.

It:

- loads `best_model.cbm`,
- loads `features.json`,
- loads the test data,
- computes classification reports,
- creates confusion matrices,
- creates feature-importance plots,
- creates boxplots for important features.

## Input

```text
data_isSZZBugIntroducer_classification/models_42/best_model.cbm
data_isSZZBugIntroducer_classification/models_42/features.json
data_isSZZBugIntroducer_classification/splits_42/test.csv
```

## Output

```text
data_isSZZBugIntroducer_classification/models_42/Results_CatBoost_Classifier/
```

This folder contains:

```text
confusion_matrices/
feature_importance/
result_txts/
boxplots/
```

## Evaluation types

The script reports:

- raw test-set performance,
- balanced test-set performance using repeated undersampling.

---

# 6. Pairwise Correlation Analysis

## Script

```bash
python 05_pairwise_correlation_analysis.py
```

## What it does

This script analyzes the relationship between two selected columns.

The default analysis compares:

```text
180fileHcpf
180commitHcpf
```

This is the main comparison between file entropy and commit entropy.

## Input

```text
data_isSZZBugIntroducer_classification/cleaned_dataset.csv
```

## Output

```text
correlation_analysis_results_isSZZBugIntroducer_classification/
```

## Main settings inside the script

```python
TARGET = "isSZZBugIntroducer"
FEATURE_1 = "180fileHcpf"
FEATURE_2 = "180commitHcpf"
```

## Statistics produced

The script computes:

- Pearson correlation,
- Spearman correlation,
- Kendall correlation,
- linear regression,
- R²,
- adjusted R²,
- RMSE,
- MAE,
- bootstrap confidence intervals.

## Plots produced

The script creates:

- scatter plot,
- scatter plot with binned means,
- residual plot,
- residual histogram,
- Q-Q plot,
- observed-vs-fitted plot,
- hexbin density plot,
- rank-rank plot.

---

# Main Feature List

```text
age
revision
nrOfFunctions
dok0.004Sum
dok0.004AuthorPreCommit
totalLoc
relativeModified
dok0.004AuthorPostCommit
modified
totalAuthors
dok0.004Avg
totalRefactors
authors
isRefactor
180fileHcpf
180commitHcpf
```

---

# Main Target

```text
isSZZBugIntroducer
```

This target is used for binary classification.

Class meaning:

```text
0 = not defect-inducing
1 = defect-inducing
```

---

# Entropy Variables

## `180fileHcpf`

This is the file-based entropy metric.

It describes how recent code churn is distributed across files.

## `180commitHcpf`

This is the commit-based entropy metric.

It describes how recent code churn is distributed across commits.

---

# Expected Output Folders

After running the full pipeline, the main folders are:

```text
DATA_ESEIW_merged_csv/
data_isSZZBugIntroducer_classification/
correlation_analysis_results_isSZZBugIntroducer_classification/
```

---

# Minimal Usage Summary

```bash
# 1. Merge all project CSV files
python 00a_data_analysis_merge_projects.py

# 2. Clean and select features
python 01a_clean_data_Classifier.py

# 3. Create train/test split
python 02a_train_test_split.py

# 4. Train CatBoost model
python 03a_train_CatBoost_Classifier.py

# 5. Evaluate trained model
python 04a_post_hoc_classifier.py

# 6. Analyze entropy correlation
python 05_pairwise_correlation_analysis.py
```

---

# Notes

- All settings are edited directly in the scripts.
- No command-line arguments are required.
- The scripts assume CSV input data.
- The pipeline uses `RANDOM_STATE = 42` where applicable.
- The model is saved as a native CatBoost `.cbm` file.
- The file `features.json` is required for evaluation.
- The preclean script is intentionally not included in this README.
