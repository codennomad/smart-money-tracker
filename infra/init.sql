-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert time-series tables to hypertables after SQLAlchemy creates them
-- (run after alembic migrations)
-- SELECT create_hypertable('insider_trades', 'filed_at', if_not_exists => TRUE);
-- SELECT create_hypertable('options_flow', 'detected_at', if_not_exists => TRUE);
-- SELECT create_hypertable('darkpool_prints', 'report_date', if_not_exists => TRUE);
