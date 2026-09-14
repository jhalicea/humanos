\set ON_ERROR_STOP on

DO $$
DECLARE
    writer_append boolean;
    writer_read boolean;
    writer_select boolean;
    writer_update boolean;
    writer_delete boolean;
    reader_append boolean;
    reader_read boolean;
    reader_select boolean;
BEGIN
    SELECT has_function_privilege(
        'humanos_capture_writer_limited',
        'humanos_append_capture_event(jsonb)', 'EXECUTE')
      INTO writer_append;
    SELECT has_function_privilege(
        'humanos_capture_writer_limited',
        'humanos_capture_after(bigint,integer)', 'EXECUTE')
      INTO writer_read;
    SELECT has_table_privilege(
        'humanos_capture_writer_limited', 'humanos_capture_events', 'SELECT')
      INTO writer_select;
    SELECT has_table_privilege(
        'humanos_capture_writer_limited', 'humanos_capture_events', 'UPDATE')
      INTO writer_update;
    SELECT has_table_privilege(
        'humanos_capture_writer_limited', 'humanos_capture_events', 'DELETE')
      INTO writer_delete;

    IF NOT writer_append OR writer_read OR writer_select OR writer_update OR writer_delete THEN
        RAISE EXCEPTION 'writer role exceeds or lacks expected authority';
    END IF;

    SELECT has_function_privilege(
        'humanos_capture_reader_limited',
        'humanos_append_capture_event(jsonb)', 'EXECUTE')
      INTO reader_append;
    SELECT has_function_privilege(
        'humanos_capture_reader_limited',
        'humanos_capture_after(bigint,integer)', 'EXECUTE')
      INTO reader_read;
    SELECT has_table_privilege(
        'humanos_capture_reader_limited', 'humanos_capture_events', 'SELECT')
      INTO reader_select;

    IF reader_append OR NOT reader_read OR reader_select THEN
        RAISE EXCEPTION 'reader role exceeds or lacks expected authority';
    END IF;
END
$$;
