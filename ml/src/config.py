"""ML hyperparameters and configuration for Guard-IA."""

# Model
MODEL_NAME = "distilbert-base-uncased"
NUM_LABELS = 2  # phishing vs legitimate

# Training
EPOCHS = 3
BATCH_SIZE = 8
LEARNING_RATE = 5e-5
MAX_SEQ_LENGTH = 256
WEIGHT_DECAY = 0.01
WARMUP_STEPS = 100

# Data
TRAIN_SPLIT = 0.8
VAL_SPLIT = 0.1
TEST_SPLIT = 0.1
RANDOM_SEED = 42

# Paths
DATA_RAW_DIR = "../data/raw"
DATA_PROCESSED_DIR = "../data/processed"
DATA_SPLITS_DIR = "../data/splits"
MODEL_OUTPUT_DIR = "../models/distilbert-guardia"

# MLflow
MLFLOW_EXPERIMENT_NAME = "guardia-distilbert"
