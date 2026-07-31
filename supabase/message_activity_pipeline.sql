-- Message activity pipeline for Supabase/Postgres
-- Goal:
-- 1) user_stats.total_messages is the source of truth
-- 2) hourly/daily/weekly are rollups for graphing
-- 3) daily cleanup by retention policy

-- =========================
-- 0) Safety constraints
-- =========================

-- Create constraints only if missing.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'user_stats_user_guild_unique'
    ) THEN
        ALTER TABLE user_stats
            ADD CONSTRAINT user_stats_user_guild_unique UNIQUE (user_id, guild_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'hourly_activity_user_guild_bucket_unique'
    ) THEN
        ALTER TABLE hourly_activity
            ADD CONSTRAINT hourly_activity_user_guild_bucket_unique UNIQUE (user_id, guild_id, bucket_time);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'daily_activity_user_guild_day_unique'
    ) THEN
        ALTER TABLE daily_activity
            ADD CONSTRAINT daily_activity_user_guild_day_unique UNIQUE (user_id, guild_id, day_bucket);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'weekly_activity_user_guild_week_unique'
    ) THEN
        ALTER TABLE weekly_activity
            ADD CONSTRAINT weekly_activity_user_guild_week_unique UNIQUE (user_id, guild_id, week_bucket);
    END IF;
END;
$$;

-- Remove older function signatures so they do not remain in the schema as overloads.
DROP TRIGGER IF EXISTS trg_sync_totals ON hourly_activity;
DROP TRIGGER IF EXISTS trg_sync_user_totals ON hourly_activity;
DROP FUNCTION IF EXISTS increment_message_activity(bigint, bigint, bigint, text, integer);
DROP FUNCTION IF EXISTS increment_message_activity(bigint, bigint, bigint, bigint, bigint, text, integer);
DROP FUNCTION IF EXISTS sync_user_totals();
DROP FUNCTION IF EXISTS trg_sync_user_totals();
DROP TABLE IF EXISTS processed_messages;


-- =========================
-- 1) Main increment function
-- =========================

-- Replace your current increment_message_activity function with this.
-- Notes:
-- - p_bucket_time is a unix epoch hour bucket in UTC
CREATE OR REPLACE FUNCTION increment_message_activity(
    p_user_id bigint,
    p_guild_id bigint,
    p_bucket_time bigint,
    p_user_name text,
    p_inc integer DEFAULT 1
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_day_bucket bigint;
    v_week_bucket bigint;
BEGIN
    IF p_inc IS NULL OR p_inc <= 0 THEN
        RAISE EXCEPTION 'p_inc must be > 0';
    END IF;

    -- Normalize day/week from the supplied hour bucket.
    v_day_bucket := (p_bucket_time / 86400) * 86400;

    -- Week bucket aligned to ISO week start (Monday 00:00 UTC)
    v_week_bucket := EXTRACT(EPOCH FROM date_trunc('week', timezone('UTC', to_timestamp(p_bucket_time))))::bigint;

    -- 1) Canonical total
    INSERT INTO user_stats (user_id, guild_id, user_name, total_messages)
    VALUES (p_user_id, p_guild_id, p_user_name, p_inc)
    ON CONFLICT (user_id, guild_id)
    DO UPDATE SET
        total_messages = user_stats.total_messages + EXCLUDED.total_messages,
        user_name = COALESCE(EXCLUDED.user_name, user_stats.user_name);

    -- 2) Hourly rollup
    INSERT INTO hourly_activity (user_id, guild_id, bucket_time, user_name, message_count)
    VALUES (p_user_id, p_guild_id, p_bucket_time, p_user_name, p_inc)
    ON CONFLICT (user_id, guild_id, bucket_time)
    DO UPDATE SET
        message_count = hourly_activity.message_count + EXCLUDED.message_count,
        user_name = COALESCE(EXCLUDED.user_name, hourly_activity.user_name);

    -- 3) Daily rollup
    INSERT INTO daily_activity (user_id, guild_id, day_bucket, message_count)
    VALUES (p_user_id, p_guild_id, v_day_bucket, p_inc)
    ON CONFLICT (user_id, guild_id, day_bucket)
    DO UPDATE SET
        message_count = daily_activity.message_count + EXCLUDED.message_count;

    -- 4) Weekly rollup
    INSERT INTO weekly_activity (user_id, guild_id, week_bucket, message_count)
    VALUES (p_user_id, p_guild_id, v_week_bucket, p_inc)
    ON CONFLICT (user_id, guild_id, week_bucket)
    DO UPDATE SET
        message_count = weekly_activity.message_count + EXCLUDED.message_count;
END;
$$;


-- =========================
-- 2) Disable old trigger path
-- =========================

-- Your old sync_user_totals trigger logic can cause overcounting if NEW.message_count is cumulative.
-- Disable/drop old trigger if it exists. Adjust trigger name if yours differs.
DROP TRIGGER IF EXISTS trg_sync_totals ON hourly_activity;
DROP TRIGGER IF EXISTS trg_sync_user_totals ON hourly_activity;


-- =========================
-- 3) Retention cleanup
-- =========================

-- Retention target:
-- - Keep hourly for 7 days
-- - Keep daily for 365 days
-- - Keep weekly forever

CREATE OR REPLACE FUNCTION purge_activity_rollups()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM hourly_activity
    WHERE bucket_time < EXTRACT(EPOCH FROM (timezone('UTC', now()) - INTERVAL '7 days'))::bigint;

    DELETE FROM daily_activity
    WHERE day_bucket < EXTRACT(EPOCH FROM (timezone('UTC', now()) - INTERVAL '365 days'))::bigint;
END;
$$;

-- Schedule daily purge with pg_cron (00:15 UTC).
-- If pg_cron is not enabled in your project, enable extension first.
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Remove old job if it exists, then recreate.
DO $$
DECLARE
    v_job_id integer;
BEGIN
    SELECT jobid INTO v_job_id
    FROM cron.job
    WHERE jobname = 'purge_activity_rollups_daily';

    IF v_job_id IS NOT NULL THEN
        PERFORM cron.unschedule(v_job_id);
    END IF;

    PERFORM cron.schedule(
        'purge_activity_rollups_daily',
        '15 0 * * *',
        'SELECT purge_activity_rollups();'
    );
END;
$$;


-- =========================
-- 4) One-time repair helpers
-- =========================

-- Rebuild totals from rollups if you choose to trust hourly as baseline.
-- If hourly is known-bad, skip this and use admin update command/user recounts.
CREATE OR REPLACE FUNCTION rebuild_user_stats_from_hourly()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE user_stats;

    INSERT INTO user_stats (user_id, guild_id, user_name, total_messages)
    SELECT
        h.user_id,
        h.guild_id,
        MAX(h.user_name) AS user_name,
        SUM(h.message_count)::bigint AS total_messages
    FROM hourly_activity h
    GROUP BY h.user_id, h.guild_id;
END;
$$;
