-- HumanOS Capture Fabric — encrypted PostgreSQL relay schema
--
-- Production remote capture stores ciphertext only. The gateway may receive
-- plaintext transiently from the provider/tool call, but the database does not
-- need transcript plaintext, source IDs, role, or message text.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS humanos_capture_envelopes (
    seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    idempotency_token text NOT NULL UNIQUE,
    conflict_token text NOT NULL,
    recipient_key_id text NOT NULL,
    envelope jsonb NOT NULL,
    ciphertext_digest text NOT NULL,
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (idempotency_token ~ '^[0-9a-f]{64}$'),
    CHECK (conflict_token ~ '^[0-9a-f]{64}$'),
    CHECK (recipient_key_id ~ '^[0-9a-f]{32}$'),
    CHECK (ciphertext_digest ~ '^[0-9a-f]{64}$'),
    CHECK (jsonb_typeof(envelope) = 'object')
);

CREATE OR REPLACE FUNCTION humanos_capture_envelopes_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'HumanOS encrypted capture envelopes are append-only';
END;
$$;

DROP TRIGGER IF EXISTS humanos_capture_envelopes_no_update ON humanos_capture_envelopes;
CREATE TRIGGER humanos_capture_envelopes_no_update
BEFORE UPDATE ON humanos_capture_envelopes
FOR EACH ROW EXECUTE FUNCTION humanos_capture_envelopes_immutable();

DROP TRIGGER IF EXISTS humanos_capture_envelopes_no_delete ON humanos_capture_envelopes;
CREATE TRIGGER humanos_capture_envelopes_no_delete
BEFORE DELETE ON humanos_capture_envelopes
FOR EACH ROW EXECUTE FUNCTION humanos_capture_envelopes_immutable();

CREATE OR REPLACE FUNCTION humanos_append_capture_envelope(p_envelope jsonb)
RETURNS TABLE (
    seq bigint,
    event_id uuid,
    ciphertext_digest text,
    received_at timestamptz,
    state text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    required_keys text[] := ARRAY[
        'format','version','recipient_key_id','idempotency_token',
        'conflict_token','ephemeral_public_key','nonce','ciphertext'
    ];
    actual_keys text[];
    required_keys_sorted text[];
    v_idempotency text;
    v_conflict text;
    v_recipient text;
    v_ciphertext bytea;
    v_digest text;
    inserted humanos_capture_envelopes%ROWTYPE;
    existing humanos_capture_envelopes%ROWTYPE;
BEGIN
    IF p_envelope IS NULL OR jsonb_typeof(p_envelope) <> 'object' THEN
        RAISE EXCEPTION 'capture envelope must be a JSON object';
    END IF;

    SELECT array_agg(t.key ORDER BY t.key)
      INTO actual_keys
      FROM jsonb_object_keys(p_envelope) AS t(key);
    SELECT array_agg(t.key ORDER BY t.key)
      INTO required_keys_sorted
      FROM unnest(required_keys) AS t(key);
    IF actual_keys IS DISTINCT FROM required_keys_sorted THEN
        RAISE EXCEPTION 'unexpected or missing encrypted envelope fields';
    END IF;

    IF p_envelope->>'format' <> 'humanos-capture-envelope' THEN
        RAISE EXCEPTION 'unsupported capture envelope format';
    END IF;
    IF jsonb_typeof(p_envelope->'version') <> 'number'
       OR (p_envelope->>'version')::integer <> 1 THEN
        RAISE EXCEPTION 'unsupported capture envelope version';
    END IF;

    v_idempotency := p_envelope->>'idempotency_token';
    v_conflict := p_envelope->>'conflict_token';
    v_recipient := p_envelope->>'recipient_key_id';
    IF v_idempotency !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'invalid idempotency token';
    END IF;
    IF v_conflict !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'invalid conflict token';
    END IF;
    IF v_recipient !~ '^[0-9a-f]{32}$' THEN
        RAISE EXCEPTION 'invalid recipient key id';
    END IF;

    BEGIN
        IF octet_length(decode(p_envelope->>'ephemeral_public_key', 'base64')) <> 32 THEN
            RAISE EXCEPTION 'invalid ephemeral public key length';
        END IF;
        IF octet_length(decode(p_envelope->>'nonce', 'base64')) <> 12 THEN
            RAISE EXCEPTION 'invalid nonce length';
        END IF;
        v_ciphertext := decode(p_envelope->>'ciphertext', 'base64');
    EXCEPTION WHEN others THEN
        RAISE EXCEPTION 'invalid encrypted envelope base64';
    END;
    IF octet_length(v_ciphertext) < 16 OR octet_length(v_ciphertext) > 1100000 THEN
        RAISE EXCEPTION 'invalid ciphertext size';
    END IF;
    v_digest := encode(digest(v_ciphertext, 'sha256'), 'hex');

    INSERT INTO humanos_capture_envelopes(
        idempotency_token, conflict_token, recipient_key_id, envelope, ciphertext_digest
    ) VALUES (
        v_idempotency, v_conflict, v_recipient, p_envelope, v_digest
    )
    ON CONFLICT (idempotency_token) DO NOTHING
    RETURNING * INTO inserted;

    IF inserted.seq IS NOT NULL THEN
        RETURN QUERY SELECT inserted.seq, inserted.event_id, inserted.ciphertext_digest,
                            inserted.received_at, 'REMOTE_CAPTURED_ENCRYPTED'::text;
        RETURN;
    END IF;

    SELECT * INTO existing
      FROM humanos_capture_envelopes
     WHERE idempotency_token = v_idempotency;

    IF existing.seq IS NULL THEN
        RAISE EXCEPTION 'encrypted idempotency reconciliation failed';
    END IF;
    -- Encryption is randomized, so an identical retry can have different
    -- ciphertext. The keyed conflict token proves whether the plaintext event
    -- was identical without storing a plaintext digest in the database.
    IF existing.conflict_token IS DISTINCT FROM v_conflict THEN
        RAISE EXCEPTION 'conflicting retry for encrypted idempotency token';
    END IF;
    IF existing.recipient_key_id IS DISTINCT FROM v_recipient THEN
        RAISE EXCEPTION 'encrypted retry changed recipient key';
    END IF;

    RETURN QUERY SELECT existing.seq, existing.event_id, existing.ciphertext_digest,
                        existing.received_at, 'REMOTE_CAPTURED_ENCRYPTED'::text;
END;
$$;

CREATE OR REPLACE FUNCTION humanos_capture_envelopes_after(
    p_seq bigint, p_limit integer DEFAULT 100
)
RETURNS TABLE (
    seq bigint,
    event_id uuid,
    envelope jsonb,
    ciphertext_digest text,
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
    SELECT e.seq, e.event_id, e.envelope, e.ciphertext_digest, e.received_at
      FROM humanos_capture_envelopes e
     WHERE e.seq > p_seq
     ORDER BY e.seq
     LIMIT p_limit;
END;
$$;

REVOKE ALL ON humanos_capture_envelopes FROM PUBLIC;
REVOKE ALL ON FUNCTION humanos_append_capture_envelope(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION humanos_capture_envelopes_after(bigint, integer) FROM PUBLIC;

COMMIT;
