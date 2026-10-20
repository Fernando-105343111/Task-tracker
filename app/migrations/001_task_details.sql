-- Additive, rerunnable upgrade for databases created by the original backend.
ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS priority VARCHAR(6) NOT NULL DEFAULT 'Medium'
        CHECK (priority IN ('Low', 'Medium', 'High')),
    ADD COLUMN IF NOT EXISTS due_date DATE;
