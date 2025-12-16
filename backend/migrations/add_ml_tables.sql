-- Migration: Add ML/Data Science Tables
-- Purpose: Store training data, predictions, and model metrics

-- Table 1: Model Training Data
-- Stores preprocessed features and labels for model training
CREATE TABLE IF NOT EXISTS model_training_data (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    features JSONB NOT NULL,
    labels JSONB,
    source_table TEXT,
    source_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT model_training_data_model_name_check CHECK (char_length(model_name) > 0)
);

CREATE INDEX IF NOT EXISTS idx_model_training_data_model_name ON model_training_data(model_name);
CREATE INDEX IF NOT EXISTS idx_model_training_data_created_at ON model_training_data(created_at DESC);

-- Table 2: Model Predictions
-- Stores all model predictions for audit and analysis
CREATE TABLE IF NOT EXISTS model_predictions (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT DEFAULT '1.0',
    input_data JSONB NOT NULL,
    output JSONB NOT NULL,
    confidence FLOAT,
    latency_ms FLOAT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT model_predictions_model_name_check CHECK (char_length(model_name) > 0),
    CONSTRAINT model_predictions_confidence_check CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX IF NOT EXISTS idx_model_predictions_model_name ON model_predictions(model_name);
CREATE INDEX IF NOT EXISTS idx_model_predictions_created_at ON model_predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_predictions_model_version ON model_predictions(model_name, model_version);

-- Table 3: Model Metrics
-- Tracks model performance over time
CREATE TABLE IF NOT EXISTS model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT DEFAULT '1.0',
    metric_name TEXT NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_metadata JSONB,
    evaluation_date TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT model_metrics_model_name_check CHECK (char_length(model_name) > 0),
    CONSTRAINT model_metrics_metric_name_check CHECK (char_length(metric_name) > 0)
);

CREATE INDEX IF NOT EXISTS idx_model_metrics_model_name ON model_metrics(model_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_metric_name ON model_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_evaluation_date ON model_metrics(evaluation_date DESC);

-- Table 4: Model Logs (already exists in core.py but formalize schema)
-- Comprehensive logging of all model invocations
CREATE TABLE IF NOT EXISTS model_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    model_name TEXT NOT NULL,
    inputs JSONB NOT NULL,
    output JSONB NOT NULL,
    latency_ms FLOAT NOT NULL,
    
    CONSTRAINT model_logs_model_name_check CHECK (char_length(model_name) > 0),
    CONSTRAINT model_logs_latency_check CHECK (latency_ms >= 0)
);

CREATE INDEX IF NOT EXISTS idx_model_logs_model_name ON model_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_model_logs_timestamp ON model_logs(timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE model_training_data IS 'Preprocessed training data for ML models';
COMMENT ON TABLE model_predictions IS 'All model predictions with metadata for audit trail';
COMMENT ON TABLE model_metrics IS 'Model performance metrics tracked over time';
COMMENT ON TABLE model_logs IS 'Comprehensive logs of all model invocations';

COMMENT ON COLUMN model_predictions.confidence IS 'Prediction confidence score (0-1)';
COMMENT ON COLUMN model_predictions.latency_ms IS 'Inference latency in milliseconds';
COMMENT ON COLUMN model_metrics.metric_name IS 'Metric name (e.g., accuracy, precision, recall, f1_score)';
