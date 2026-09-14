-- HumanOS Capture Fabric — PostgreSQL relay schema
--
-- This database is a durable synchronization mailbox, not the canonical Life
-- Notebook. Writers should receive EXECUTE on the append function only; they
-- should not receive UPDATE/DELETE/SELECT privileges on the underlying table.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS humanos_capture_events (
    seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    idempotency_key text NOT NULL UNIQUE,
    payload jsonb NOT NULL,
    payload_digest text NOT NULL,
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (jsonb_typeof(payload) = 'object'),
    CHECK (payload_digest ~ '^[0-9a-f]{64}$')
);

CREATE OR REPLACE FUNCTION humanos_capture_digest_part(p_value text)
RETURNS bytea
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    raw bytea;
BEGIN
    IF p_value IS NULL THEN
        RETURN convert_to('-1:', 'UTF8');
    END IF;
    raw := convert_to(p_value, 'UTF8');
    RETURN convert_to(octet_length(raw)::text || ':', 'UTF8') || raw;
END;
$$;

CREATE OR REPLACE FUNCTION humanos_capture_payload_digest(p_event jsonb)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT encode(
        digest(
            convert_to('HumanOS Capture Event v1|', 'UTF8')
            || humanos_capture_digest_part(p_event->>'version')
            || humanos_capture_digest_part(p_event->>'source')
            || humanos_capture_digest_part(p_event->>'conversation_id')
            || humanos_capture_digest_part(p_event->>'turn_id')
            || humanos_capture_digest_part(p_event->>'event_type')
            || humanos_capture_digest_part(p_event->>'role')
            || humanos_capture_digest_part(p_event->>'text')
            || humanos_capture_digest_part(p_event->>'idempotency_key')
            || humanos_capture_digest_part(p_event->>'variant_id')
            || humanos_capture_digest_part(p_event->>'source_created_at'),
            'sha256'
        ),
        'hex'
    );
$$;

CREATE OR REPLACE FUNCTION humanos_capture_events_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'HumanOS capture events are append-only';
END;
$$;

DROP TRIGGER IF EXISTS humanos_capture_events_no_update ON humanos_capture_events;
CREATE TRIGGER humanos_capture_events_no_update
BEFORE UPDATE ON humanos_capture_events
FOR EACH ROW EXECUTE FUNCTION humanos_capture_events_immutable();

DROP TRIGGER IF EXISTS humanos_capture_events_no_delete ON humanos_capture_events;
CREATE TRIGGER humanos_capture_events_no_delete
BEFORE DELETE ON humanos_capture_events
FOR EACH ROW EXECUTE FUNCTION humanos_capture_events_immutable();

CREATE OR REPLACE FUNCTION humanos_append_capture_event(p_event jsonb)
RETURNS TABLE (
    seq bigint,
    event_id uuid,
    payload_digest text,
    received_at timestamptz,
    state text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    required_keys text[] := ARRAY[
        'version','source','conversation_id','turn_id','event_type','role',
        'text','idempotency_key','variant_id','source_created_at'
    ];
    actual_keys text[];
    required_keys_sorted text[];
    v_idempotency text;
    v_digest text;
    inserted humanos_capture_events%ROWTYPE;
    existing humanos_capture_events%ROWTYPE;
BEGIN
    IF p_event IS NULL OR jsonb_typeof(p_event) <> 'object' THEN
        RAISE EXCEPTION 'capture event must be a JSON object';
    END IF;

    SELECT array_agg(t.key ORDER BY t.key)
      INTO actual_keys
      FROM jsonb_object_keys(p_event) AS t(key);

    SELECT array_agg(t.key ORDER BY t.key)
      INTO required_keys_sorted
      FROM unnest(required_keys) AS t(key);

    IF actual_keys IS DISTINCT FROM required_keys_sorted THEN
        RAISE EXCEPTION 'unexpected or missing capture event fields';
    END IF;

    IF jsonb_typeof(p_event->'version') <> 'number' OR (p_event->>'version')::integer <> 1 THEN
        RAISE EXCEPTION 'unsupported capture event version';
    END IF;
    IF p_event->>'source' IS NULL OR p_event->>'source' = '' THEN
        RAISE EXCEPTION 'source is required';
    END IF;
    IF p_event->>'conversation_id' IS NULL OR p_event->>'conversation_id' = '' THEN
        RAISE EXCEPTION 'conversation_id is required';
    END IF;
    IF p_event->>'turn_id' IS NULL OR p_event->>'turn_id' = '' THEN
        RAISE EXCEPTION 'turn_id is required';
    END IF;
    IF p_event->>'variant_id' IS NULL OR p_event->>'variant_id' = '' THEN
        RAISE EXCEPTION 'variant_id is required';
    END IF;
    IF p_event->>'event_type' NOT IN (
        'human_message','assistant_message','human_edit','assistant_regeneration'
    ) THEN
        RAISE EXCEPTION 'unsupported event_type';
    END IF;
    IF p_event->>'role' NOT IN ('human','assistant') THEN
        RAISE EXCEPTION 'unsupported role';
    END IF;
    IF (p_event->>'event_type' LIKE 'human%' AND p_event->>'role' <> 'human')
       OR (p_event->>'event_type' LIKE 'assistant%' AND p_event->>'role' <> 'assistant') THEN
        RAISE EXCEPTION 'event_type and role disagree';
    END IF;
    IF p_event->>'text' IS NULL OR p_event->>'text' = '' THEN
        RAISE EXCEPTION 'text is required';
    END IF;
    IF octet_length(convert_to(p_event->>'text', 'UTF8')) > 1000000 THEN
        RAISE EXCEPTION 'text is too large';
    END IF;

    v_idempotency := p_event->>'idempotency_key';
    IF v_idempotency IS NULL OR v_idempotency = '' THEN
        RAISE EXCEPTION 'idempotency_key is required';
    END IF;

    -- Cross-platform transport digest. This is not a replacement for the local
    -- Life Notebook's vault-keyed record integrity.
    v_digest := humanos_capture_payload_digest(p_event);

    INSERT INTO humanos_capture_events(idempotency_key, payload, payload_digest)
    VALUES (v_idempotency, p_event, v_digest)
    ON CONFLICT (idempotency_key) DO NOTHING
    RETURNING * INTO inserted;

    IF inserted.seq IS NOT NULL THEN
        RETURN QUERY SELECT inserted.seq, inserted.event_id, inserted.payload_digest,
                            inserted.received_at, 'REMOTE_CAPTURED'::text;
        RETURN;
    END IF;

    SELECT * INTO existing
      FROM humanos_capture_events
     WHERE idempotency_key = v_idempotency;

    IF existing.seq IS NULL THEN
        RAISE EXCEPTION 'idempotency reconciliation failed';
    END IF;
    IF existing.payload IS DISTINCT FROM p_event THEN
        RAISE EXCEPTION 'conflicting retry for idempotency_key';
    END IF;
    IF existing.payload_digest IS DISTINCT FROM v_digest THEN
        RAISE EXCEPTION 'existing payload digest differs from protocol digest';
    END IF;

    RETURN QUERY SELECT existing.seq, existing.event_id, existing.payload_digest,
                        existing.received_at, 'REMOTE_CAPTURED'::text;
END;
$$;

CREATE OR REPLACE FUNCTION humanos_capture_after(p_seq bigint, p_limit integer DEFAULT 100)
RETURNS TABLE (
    seq bigint,
    event_id uuid,
    payload jsonb,
    payload_digest text,
    received_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF p_seq < 0 THEN
        RAISE EXCEPTION 'p_seq must be nonnegative';
    END IF;
    IF p_limit < 1 OR p_limit > 1000 THEN
        RAISE EXCEPTION 'p_limit must be from 1 to 1000';
    END IF;

    RETURN QUERY
    SELECT e.seq, e.event_id, e.payload, e.payload_digest, e.received_at
      FROM humanos_capture_events e
     WHERE e.seq > p_seq
     ORDER BY e.seq
     LIMIT p_limit;
END;
$$;

-- Fail closed by default. Deployment creates provider-specific NOLOGIN/login
-- roles and grants only the functions each route needs.
REVOKE ALL ON humanos_capture_events FROM PUBLIC;
REVOKE ALL ON FUNCTION humanos_capture_digest_part(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION humanos_capture_payload_digest(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION humanos_append_capture_event(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION humanos_capture_after(bigint, integer) FROM PUBLIC;

-- Example deployment grants (do not run until those roles exist):
-- GRANT EXECUTE ON FUNCTION humanos_append_capture_event(jsonb) TO humanos_capture_writer;
-- GRANT EXECUTE ON FUNCTION humanos_capture_after(bigint, integer) TO humanos_capture_reader;

COMMIT;
