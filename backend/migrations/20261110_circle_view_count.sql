-- Apply once after checking the target database. Existing views were not tracked.
ALTER TABLE circles ADD COLUMN view_count INT NOT NULL DEFAULT 0;
