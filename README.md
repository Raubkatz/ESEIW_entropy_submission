# Commit Entropy Defect Prediction Pipeline

## Overview

This repository implements the experimental pipeline for studying commit entropy as a predictor of defect-inducing commits.

The workflow covers:

- merging repository-level CSV files,
- selecting study features,
- cleaning target-specific datasets,
- generating train/test splits,
- training CatBoost classifiers,
- evaluating trained models,
- analyzing feature relationships.

The central comparison is between:

- `180fileHcpf` → code-change entropy,
- `180commitHcpf` → commit entropy.

The pipeline is intentionally configuration-driven.  
All parameters are configured directly inside the Python scripts.

No command-line argument parsing is used.

---

# Repository Structure

```text
├── 00a_data_analysis_merge_projects.py
├── 01a_clean_data_Classifier.py
├── 02a_train_test_split.py
├── 03a_train_CatBoost_Classifier.py
├── 04a_post_hoc_classifier.py
├── 05_pairwise_correlation_analysis.py
│
├── DATA_ESEIW_final/
├── DATA_ESEIW_merged_csv/
├── data_isSZZBugIntroducer_classification/
├── correlation_analysis_results_*/
└── README.md
```

---

# Full Pipeline Order

Run the scripts in the following order:

```bash
python 00a_data_analysis_merge_projects.py
python 01a_clean_data_Classifier.py
python 02a_train_test_split.py
python 03a_train_CatBoost_Classifier.py
python 04a_post_hoc_classifier.py
python 05_pairwise_correlation_analysis.py
```

---

# 1. Merge Per-Project CSV Files

## Script

```bash
python 00a_data_analysis_merge_projects.py
```

## Purpose

This script merges all per-project CSV files into one unified dataset.

Each input CSV represents one software repository or software project.

The script:

- reads all project CSV files,
- detects delimiters automatically,
- aligns schemas,
- inserts missing expected columns,
- removes unexpected columns,
- concatenates all project tables,
- writes one merged dataset.

The script also inserts provenance metadata:

```text
source_file
source_project
```

before merging.

---

## Main Configuration

```python
INPUT_DIR = "DATA_ESEIW_final"
OUT_DIR = "DATA_ESEIW_merged_csv"
OUTPUT_NAME = "merged_dataset_2026.csv"
PATTERN = "*.csv"

SCHEMA_CHECK = True
KEEP_EXTRA_COLS = False
WRITE_PARQUET = False
```

---

## Expected Columns

The merge script keeps only columns defined in:

```python
EXPECTED_COLUMNS
```

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

## Outputs

```text
DATA_ESEIW_merged_csv/
├── merged_dataset_2026.csv
└── merge_report.json
```

---

## Merge Report

The generated report documents:

- number of rows per file,
- missing expected columns,
- extra columns,
- original column count,
- final column count.

---

# 2. Clean Dataset and Select Features

## Script

```bash
python 01a_clean_data_Classifier.py
```

## Purpose

This script constructs the cleaned target-specific machine-learning dataset.

The script performs:

1. target selection,
2. feature selection,
3. datatype normalization,
4. missing-value handling,
5. negative-value handling,
6. descriptive-statistics generation,
7. LaTeX table export.

---

## Main Configuration

```python
INPUT_CSV = Path("DATA_ESEIW_merged_csv") / "merged_dataset_2026.csv"

TARGET = "isSZZBugIntroducer"

NEGATIVE_HANDLING = "replace_with_nan"

DROP_MISSING_TARGET = True
DROP_ALL_FEATURES_MISSING = True

PROJECT_COL = "source_project"
```

---

## Supported Targets

```text
isBugPresent
isBugfix
isSZZBugIntroducer
```

---

## Current Target

```text
isSZZBugIntroducer
```

This target marks commits identified as defect-inducing by the SZZ-based labeling process.

---

## Selected Features

The current study uses:

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

## Negative Value Handling

Current setting:

```python
NEGATIVE_HANDLING = "replace_with_nan"
```

Supported modes:

```text
discard
replace_with_nan
none
```

Meaning:

- `discard`
  → remove rows containing negative numeric feature values.

- `replace_with_nan`
  → convert negative numeric values into missing values.

- `none`
  → perform no negative-value processing.

---

## Statistics Generation

The script computes:

- feature missingness,
- feature distributions,
- target distributions,
- descriptive statistics,
- per-project statistics.

---

## Outputs

```text
data_isSZZBugIntroducer_classification/
├── cleaned_dataset.csv
├── sanity_report.txt
├── sanity_report.json
└── stats_tables/
    ├── stats_overall.tex
    ├── stats_by_source_project.tex
    └── stats_by_source_project.zip
```

---

# 3. Train/Test Split

## Script

```bash
python 02a_train_test_split.py
```

## Purpose

This script creates train/test splits from the cleaned dataset.

The script reads:

```text
data_isSZZBugIntroducer_classification/cleaned_dataset.csv
```

and writes train/test CSV files.

---

## Main Configuration

```python
TARGET = "isSZZBugIntroducer"

TEST_SIZE = 0.2
RANDOM_STATE = 42

STRATIFY = True

GROUP_COL = None
REQUIRE_GROUP_HOLDOUT = False
```

---

## Split Logic

By default, the script performs a stratified random split.

This preserves the class distribution approximately between:

- training data,
- test data.

---

## Optional Group-Aware Split

The script also supports group-aware splitting through:

```python
GROUP_COL
```

using:

```python
GroupShuffleSplit
```

This can be used for repository-aware evaluation.

---

## Outputs

```text
data_isSZZBugIntroducer_classification/
└── splits_42/
    ├── train.csv
    ├── test.csv
    └── split_report.json
```

---

## Split Report

The split report contains:

- row counts,
- selected features,
- target distributions,
- split mode,
- train/test row counts.

---

# 4. Train CatBoost Classifier

## Script

```bash
python 03a_train_CatBoost_Classifier.py
```

## Purpose

This script trains and selects CatBoost-based defect prediction models.

The workflow compares:

1. an out-of-the-box CatBoost model,
2. a Bayesian-optimized CatBoost model.

The better model is selected and saved.

---

## Main Configuration

```python
TARGET = "isSZZBugIntroducer"

RANDOM_STATE = 42

VAL_SIZE = 0.2
STRATIFY = True

N_REPEATS = 1

TRAIN_MINORITY_FRACTION = 0.9

N_VAL_EXCERPTS = 100
VAL_MINORITY_FRACTION = 0.9

SELECTION_METRIC = "val_balanced_f1"

SKIP_BAYES_OPTIMIZATION = False

BAYES_N_ITER = 20
BAYES_CV = 3
BAYES_SCORING = "f1"
```

---

## Workflow

The script performs:

1. internal train/validation splitting,
2. balanced undersampling,
3. optional Bayesian optimization,
4. validation evaluation,
5. candidate comparison,
6. final model selection.

---

## Balanced Undersampling

Training uses balanced undersampling.

The configuration:

```python
TRAIN_MINORITY_FRACTION = 0.9
```

means:

- keep 90% of the minority-class samples,
- sample the same number from the majority class.

This creates balanced training subsets.

---

## Validation Strategy

Validation uses repeated balanced excerpts:

```python
N_VAL_EXCERPTS = 100
VAL_MINORITY_FRACTION = 0.9
```

This reduces bias caused by strong class imbalance.

---

## Bayesian Optimization

Optional hyperparameter optimization uses:

```python
BayesSearchCV
```

The search space includes:

```python
depth
iterations
learning_rate
l2_leaf_reg
border_count
```

---

## CatBoost Handling

Categorical columns are detected automatically.

Object/string/category columns are:

- converted to string,
- passed through `cat_features`.

---

## Outputs

```text
data_isSZZBugIntroducer_classification/
└── models_42/
    ├── best_model.cbm
    ├── features.json
    ├── training_report.txt
    └── training_report.json
```

---

## Saved Artifacts

### `best_model.cbm`

Saved CatBoost model.

### `features.json`

Stores:

- selected feature list,
- target column.

This is required by the post-hoc evaluation script.

---

# 5. Post-Hoc Model Evaluation

## Script

```bash
python 04a_post_hoc_classifier.py
```

## Purpose

This script evaluates the saved CatBoost model.

It does not retrain the model.

The script loads:

```text
best_model.cbm
features.json
test.csv
```

and generates evaluation reports and plots.

---

## Main Configuration

```python
TARGET = "isSZZBugIntroducer"

RANDOM_STATE = 42

MODEL_PATH = "./data_isSZZBugIntroducer_classification/models_42/best_model.cbm"

FEATURES_JSON_PATH = "./data_isSZZBugIntroducer_classification/models_42/features.json"

TEST_DATA_PATH = "./data_isSZZBugIntroducer_classification/splits_42/test.csv"
```

---

## Evaluation Modes

### Raw Evaluation

Uses the test set directly.

This reflects the natural class imbalance.

---

### Balanced Evaluation

Uses repeated balanced undersampling of the test set.

This estimates model behavior when both classes occur equally often.

---

## Generated Outputs

The script produces:

- raw confusion matrices,
- balanced confusion matrices,
- normalized confusion matrices,
- classification reports,
- feature-importance plots,
- feature boxplots grouped by predicted class.

---

## Outputs

```text
data_isSZZBugIntroducer_classification/
└── models_42/
    └── Results_CatBoost_Classifier/
        ├── confusion_matrices/
        ├── feature_importance/
        ├── result_txts/
        └── boxplots/
```

---

# 6. Pairwise Correlation Analysis

## Script

```bash
python 05_pairwise_correlation_analysis.py
```

## Purpose

This script performs pairwise statistical analysis between two selected dataset columns.

The script supports:

- feature-feature analysis,
- feature-target analysis,
- entropy-entropy analysis,
- arbitrary column comparisons.

---

## Main Configuration

```python
TARGET = "isSZZBugIntroducer"

CLEANED_DATA_KIND = "classification"

USE_OBJ_PREFIX = False

FEATURE_1 = "180fileHcpf"
FEATURE_2 = "180commitHcpf"
```

---

## Default Entropy Analysis

The default analysis compares:

```text
180fileHcpf
180commitHcpf
```

These correspond to:

- file-level code-change entropy,
- commit-level churn entropy.

---

## Statistical Methods

The script computes:

- Pearson correlation,
- Spearman correlation,
- Kendall correlation,
- linear regression,
- R²,
- adjusted R²,
- RMSE,
- MAE,
- residual standard error,
- bootstrap confidence intervals.

---

## Plot Outputs

The script saves:

- scatter plots,
- scatter plots with binned means,
- residual plots,
- residual histograms,
- Q-Q plots,
- observed-vs-fitted plots,
- hexbin density plots,
- rank-rank scatter plots.

---

## Outputs

```text
correlation_analysis_results_isSZZBugIntroducer_classification/
└── 180fileHcpf_vs_180commitHcpf_correlation_analysis/
    ├── samplewise_all_rows.csv
    ├── samplewise_pairwise_complete_sorted.csv
    ├── correlation_report.txt
    ├── correlation_summary.json
    ├── *.png
    └── *.eps
```

---

# Main Study Features

The current study uses:

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

This target represents defect-inducing commits identified using the SZZ-based labeling process.

---

# Entropy Variables

## `180fileHcpf`

File-side code-change entropy.

Measures how recent churn is distributed across files.

---

## `180commitHcpf`

Commit-side churn entropy.

Measures how recent churn is distributed across commits.

---

# Main Research Question

The central research question is whether commit entropy provides predictive information beyond traditional code-change entropy for defect-inducing commit prediction.

The study compares four classifier configurations:

1. no entropy features,
2. file entropy only,
3. commit entropy only,
4. both entropy metrics together.

---

# Main Output Folders

## Merged Dataset

```text
DATA_ESEIW_merged_csv/
```

Contains:

- merged dataset,
- merge report.

---

## Cleaned Dataset

```text
data_isSZZBugIntroducer_classification/
```

Contains:

- cleaned dataset,
- sanity reports,
- statistics tables,
- train/test splits,
- trained models,
- evaluation outputs.

---

## Statistics Tables

```text
data_isSZZBugIntroducer_classification/stats_tables/
```

Contains LaTeX-ready descriptive statistics.

---

## Train/Test Splits

```text
data_isSZZBugIntroducer_classification/splits_42/
```

Contains:

- train.csv,
- test.csv,
- split reports.

---

## Trained Models

```text
data_isSZZBugIntroducer_classification/models_42/
```

Contains:

- CatBoost model,
- training reports,
- feature definitions.

---

## Evaluation Outputs

```text
data_isSZZBugIntroducer_classification/models_42/Results_CatBoost_Classifier/
```

Contains:

- confusion matrices,
- feature importance,
- classification reports,
- boxplots.

---

## Correlation Analysis Outputs

```text
correlation_analysis_results_isSZZBugIntroducer_classification/
```

Contains pairwise statistical analysis outputs.

---

# Dependencies

Install required packages:

```bash
pip install pandas numpy scikit-learn catboost imbalanced-learn matplotlib seaborn scipy scikit-optimize
```

---

# Recommended Environment

A Conda environment is recommended.

Example:

```bash
conda create -n commit_entropy python=3.11
conda activate commit_entropy

pip install pandas numpy scikit-learn catboost imbalanced-learn matplotlib seaborn scipy scikit-optimize
```

---

# Reproducibility Notes

Most scripts use:

```python
RANDOM_STATE = 42
```

This affects:

- train/test splitting,
- undersampling,
- validation excerpts,
- model selection.

Because repeated undersampling and Bayesian optimization are used, exact results may still vary slightly depending on:

- package versions,
- operating system,
- hardware,
- CatBoost backend.

---

# Important Notes

- All configuration happens directly inside the Python scripts.
- No CLI argument parsing is used.
- Missing expected columns are automatically inserted during merging.
- Extra columns are removed during merging.
- The post-hoc evaluation script requires:
  - `best_model.cbm`
  - `features.json`
  - `test.csv`
- The correlation-analysis script operates on the cleaned target-specific dataset.
- The preclean script is intentionally not documented in this README.
- The workflow is designed for reproducible software-engineering experiments using heterogeneous repository datasets.
- CatBoost is used because it naturally supports:
  - missing values,
  - categorical variables,
  - feature importance analysis.
