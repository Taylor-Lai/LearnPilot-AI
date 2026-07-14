-- =============================================================================
-- LearnPilot PostgreSQL sequence repair after MySQL -> PostgreSQL data import
-- =============================================================================
-- Symptom:
--   duplicate key value violates unique constraint "<table>_pkey"
--
-- Cause:
--   INSERT with explicit id values during import does not advance SERIAL/IDENTITY
--   sequences. The next ORM insert may reuse an existing id.
--
-- Scope (from backend/app/models/entities.py):
--   All tables with Integer primary key column "id".
--
-- Safety:
--   - Does NOT delete data
--   - Does NOT alter table structure
--   - Only calls setval() on existing sequences
--   - Skips tables/sequences that do not exist
--
-- Usage (PostgreSQL):
--   psql "$DATABASE_URL" -f backend/scripts/fix_postgres_sequences.sql
-- =============================================================================

BEGIN;

DO $$
DECLARE
  tbl text;
  seq text;
  max_id bigint;
  next_id bigint;
  -- Ordered list mirrors entities.py __tablename__ values.
  tables text[] := ARRAY[
    'user',
    'course',
    'knowledge_point',
    'course_resource',
    'resource_center',
    'student_profile',
    'profile_builder_session',
    'profile_builder_message',
    'ml_profile_answer',
    'producer_task',
    'producer_artifact',
    'producer_chat_message',
    'student_weakness',
    'learning_resource',
    'learning_path',
    'learning_path_node',
    'path_node_progress',
    'path_feedback',
    'evaluation_result',
    'import_job',
    'resource_chunk',
    'question',
    'student_answer',
    'feedback_event',
    'chat_message'
  ];
BEGIN
  FOREACH tbl IN ARRAY tables
  LOOP
    IF to_regclass(format('public.%I', tbl)) IS NULL THEN
      RAISE NOTICE '[SKIP] table public.% does not exist', tbl;
      CONTINUE;
    END IF;

    seq := pg_get_serial_sequence(format('public.%I', tbl), 'id');
    IF seq IS NULL THEN
      RAISE NOTICE '[SKIP] table public.% has no serial/identity sequence on id', tbl;
      CONTINUE;
    END IF;

    EXECUTE format('SELECT COALESCE(MAX(id), 0) FROM public.%I', tbl)
      INTO max_id;

    next_id := max_id + 1;
    PERFORM setval(seq::regclass, next_id, false);

    RAISE NOTICE '[OK] public.% sequence % -> next id = % (current max id = %)',
      tbl, seq, next_id, max_id;
  END LOOP;
END $$;
COMMIT;

-- -----------------------------------------------------------------------------
-- Verification report (read-only)
-- Expected: sequence_ok = true for every existing table with a serial sequence
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  tbl text;
  seq text;
  max_id bigint;
  last_val bigint;
  is_called boolean;
  tables text[] := ARRAY[
    'user',
    'course',
    'knowledge_point',
    'course_resource',
    'resource_center',
    'student_profile',
    'profile_builder_session',
    'profile_builder_message',
    'ml_profile_answer',
    'producer_task',
    'producer_artifact',
    'producer_chat_message',
    'student_weakness',
    'learning_resource',
    'learning_path',
    'learning_path_node',
    'path_node_progress',
    'path_feedback',
    'evaluation_result',
    'import_job',
    'resource_chunk',
    'question',
    'student_answer',
    'feedback_event',
    'chat_message'
  ];
BEGIN
  RAISE NOTICE 'table_name | sequence_name | max_id | last_value | is_called | sequence_ok';
  RAISE NOTICE '-----------+---------------+--------+------------+-----------+------------';

  FOREACH tbl IN ARRAY tables
  LOOP
    IF to_regclass(format('public.%I', tbl)) IS NULL THEN
      CONTINUE;
    END IF;

    seq := pg_get_serial_sequence(format('public.%I', tbl), 'id');
    IF seq IS NULL THEN
      CONTINUE;
    END IF;

    EXECUTE format('SELECT COALESCE(MAX(id), 0) FROM public.%I', tbl)
      INTO max_id;

    SELECT s.last_value, s.is_called
      INTO last_val, is_called
    FROM pg_sequences AS s
    WHERE s.schemaname || '.' || s.sequencename = seq;

    RAISE NOTICE '% | % | % | % | % | %',
      rpad(tbl, 25, ' '),
      rpad(seq, 30, ' '),
      max_id,
      last_val,
      is_called,
      (last_val = max_id + 1 AND is_called = false);
  END LOOP;
END $$;
