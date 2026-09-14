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
    enc_writer_append boolean;
    enc_writer_read boolean;
    enc_writer_select boolean;
    enc_writer_plaintext boolean;
    enc_reader_append boolean;
    enc_reader_read boolean;
    enc_reader_select boolean;
    enc_reader_plaintext boolean;
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
        RAISE EXCEPTION 'plaintext writer role exceeds or lacks expected authority';
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
        RAISE EXCEPTION 'plaintext reader role exceeds or lacks expected authority';
    END IF;

    SELECT has_function_privilege(
        'humanos_capture_encrypted_writer_limited',
        'humanos_append_capture_envelope(jsonb)', 'EXECUTE')
      INTO enc_writer_append;
    SELECT has_function_privilege(
        'humanos_capture_encrypted_writer_limited',
        'humanos_capture_envelopes_after(bigint,integer)', 'EXECUTE')
      INTO enc_writer_read;
    SELECT has_table_privilege(
        'humanos_capture_encrypted_writer_limited', 'humanos_capture_envelopes', 'SELECT')
      INTO enc_writer_select;
    SELECT has_function_privilege(
        'humanos_capture_encrypted_writer_limited',
        'humanos_append_capture_event(jsonb)', 'EXECUTE')
      INTO enc_writer_plaintext;

    IF NOT enc_writer_append OR enc_writer_read OR enc_writer_select OR enc_writer_plaintext THEN
        RAISE EXCEPTION 'encrypted writer role exceeds or lacks expected authority';
    END IF;

    SELECT has_function_privilege(
        'humanos_capture_encrypted_reader_limited',
        'humanos_append_capture_envelope(jsonb)', 'EXECUTE')
      INTO enc_reader_append;
    SELECT has_function_privilege(
        'humanos_capture_encrypted_reader_limited',
        'humanos_capture_envelopes_after(bigint,integer)', 'EXECUTE')
      INTO enc_reader_read;
    SELECT has_table_privilege(
        'humanos_capture_encrypted_reader_limited', 'humanos_capture_envelopes', 'SELECT')
      INTO enc_reader_select;
    SELECT has_function_privilege(
        'humanos_capture_encrypted_reader_limited',
        'humanos_capture_after(bigint,integer)', 'EXECUTE')
      INTO enc_reader_plaintext;

    IF enc_reader_append OR NOT enc_reader_read OR enc_reader_select OR enc_reader_plaintext THEN
        RAISE EXCEPTION 'encrypted reader role exceeds or lacks expected authority';
    END IF;
END
$$;
