\set ON_ERROR_STOP on

DO $$
DECLARE
    e1 jsonb := jsonb_build_object(
        'version', 1,
        'source', 'chatgpt',
        'conversation_id', 'conversation-1',
        'turn_id', 'turn-1',
        'event_type', 'human_message',
        'role', 'human',
        'text', E'  exact text 🧭\nline two  ',
        'idempotency_key', 'chatgpt/conversation-1/turn-1/human/primary',
        'variant_id', 'primary',
        'source_created_at', NULL
    );
    e2 jsonb := jsonb_build_object(
        'version', 1,
        'source', 'chatgpt',
        'conversation_id', 'conversation-1',
        'turn_id', 'turn-1',
        'event_type', 'assistant_message',
        'role', 'assistant',
        'text', 'assistant exact text',
        'idempotency_key', 'chatgpt/conversation-1/turn-1/assistant/primary',
        'variant_id', 'primary',
        'source_created_at', NULL
    );
    r1 bigint;
    r1_retry bigint;
    r2 bigint;
    c integer;
    protocol_digest text;
BEGIN
    protocol_digest := humanos_capture_payload_digest(e1);
    IF protocol_digest <> 'aca0fc36611bb56005f78fbbba919e773d391eb40e8c2e7a500e10138e79a50c' THEN
        RAISE EXCEPTION 'PostgreSQL digest differs from Capture Event v1 protocol: %', protocol_digest;
    END IF;

    SELECT x.seq INTO r1 FROM humanos_append_capture_event(e1) AS x;
    SELECT x.seq INTO r1_retry FROM humanos_append_capture_event(e1) AS x;
    IF r1 IS NULL OR r1_retry <> r1 THEN
        RAISE EXCEPTION 'idempotent retry did not return same sequence';
    END IF;

    IF (SELECT payload_digest FROM humanos_capture_events WHERE seq = r1) <> protocol_digest THEN
        RAISE EXCEPTION 'stored digest differs from protocol digest';
    END IF;

    BEGIN
        PERFORM * FROM humanos_append_capture_event(
            jsonb_set(e1, '{text}', to_jsonb('conflicting text'::text))
        );
        RAISE EXCEPTION 'conflicting retry was accepted';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'conflicting retry was accepted' THEN
                RAISE;
            END IF;
            IF position('conflicting retry' in SQLERRM) = 0 THEN
                RAISE;
            END IF;
    END;

    BEGIN
        UPDATE humanos_capture_events SET received_at = clock_timestamp() WHERE seq = r1;
        RAISE EXCEPTION 'append-only update was accepted';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'append-only update was accepted' THEN
                RAISE;
            END IF;
            IF position('append-only' in SQLERRM) = 0 THEN
                RAISE;
            END IF;
    END;

    BEGIN
        DELETE FROM humanos_capture_events WHERE seq = r1;
        RAISE EXCEPTION 'append-only delete was accepted';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'append-only delete was accepted' THEN
                RAISE;
            END IF;
            IF position('append-only' in SQLERRM) = 0 THEN
                RAISE;
            END IF;
    END;

    SELECT x.seq INTO r2 FROM humanos_append_capture_event(e2) AS x;
    IF r2 <= r1 THEN
        RAISE EXCEPTION 'sequence did not advance';
    END IF;

    SELECT count(*) INTO c FROM humanos_capture_after(r1, 100);
    IF c <> 1 THEN
        RAISE EXCEPTION 'cursor query returned % rows instead of 1', c;
    END IF;

    IF (SELECT payload->>'text' FROM humanos_capture_events WHERE seq = r1)
       IS DISTINCT FROM E'  exact text 🧭\nline two  ' THEN
        RAISE EXCEPTION 'exact text did not survive PostgreSQL round trip';
    END IF;
END;
$$;
