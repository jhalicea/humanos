-- HumanOS Capture Fabric — least-privilege PostgreSQL role templates
--
-- These NOLOGIN roles define capability bundles. Production deployments should
-- create separate LOGIN/service identities and grant one template role to each.
-- Do not reuse an administrative provider-created role as a runtime identity.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'humanos_capture_writer_limited') THEN
        CREATE ROLE humanos_capture_writer_limited NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'humanos_capture_reader_limited') THEN
        CREATE ROLE humanos_capture_reader_limited NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'humanos_capture_encrypted_writer_limited') THEN
        CREATE ROLE humanos_capture_encrypted_writer_limited NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'humanos_capture_encrypted_reader_limited') THEN
        CREATE ROLE humanos_capture_encrypted_reader_limited NOLOGIN NOINHERIT;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO humanos_capture_writer_limited;
GRANT USAGE ON SCHEMA public TO humanos_capture_reader_limited;
GRANT USAGE ON SCHEMA public TO humanos_capture_encrypted_writer_limited;
GRANT USAGE ON SCHEMA public TO humanos_capture_encrypted_reader_limited;

-- Plaintext roles remain for synthetic bakeoff comparison only.
REVOKE ALL ON humanos_capture_events FROM humanos_capture_writer_limited;
REVOKE ALL ON humanos_capture_events FROM humanos_capture_reader_limited;
REVOKE ALL ON FUNCTION humanos_append_capture_event(jsonb) FROM humanos_capture_writer_limited;
REVOKE ALL ON FUNCTION humanos_capture_after(bigint, integer) FROM humanos_capture_writer_limited;
REVOKE ALL ON FUNCTION humanos_append_capture_event(jsonb) FROM humanos_capture_reader_limited;
REVOKE ALL ON FUNCTION humanos_capture_after(bigint, integer) FROM humanos_capture_reader_limited;
GRANT EXECUTE ON FUNCTION humanos_append_capture_event(jsonb)
    TO humanos_capture_writer_limited;
GRANT EXECUTE ON FUNCTION humanos_capture_after(bigint, integer)
    TO humanos_capture_reader_limited;

-- Production encrypted roles can touch only their single-purpose RPC function.
REVOKE ALL ON humanos_capture_envelopes FROM humanos_capture_encrypted_writer_limited;
REVOKE ALL ON humanos_capture_envelopes FROM humanos_capture_encrypted_reader_limited;
REVOKE ALL ON FUNCTION humanos_append_capture_envelope(jsonb)
    FROM humanos_capture_encrypted_writer_limited;
REVOKE ALL ON FUNCTION humanos_capture_envelopes_after(bigint, integer)
    FROM humanos_capture_encrypted_writer_limited;
REVOKE ALL ON FUNCTION humanos_append_capture_envelope(jsonb)
    FROM humanos_capture_encrypted_reader_limited;
REVOKE ALL ON FUNCTION humanos_capture_envelopes_after(bigint, integer)
    FROM humanos_capture_encrypted_reader_limited;
GRANT EXECUTE ON FUNCTION humanos_append_capture_envelope(jsonb)
    TO humanos_capture_encrypted_writer_limited;
GRANT EXECUTE ON FUNCTION humanos_capture_envelopes_after(bigint, integer)
    TO humanos_capture_encrypted_reader_limited;

COMMIT;

-- Production example (create through a secret manager / deployment system):
-- CREATE ROLE humanos_capture_writer_runtime LOGIN PASSWORD '<generated-secret>' NOINHERIT;
-- GRANT humanos_capture_encrypted_writer_limited TO humanos_capture_writer_runtime;
--
-- CREATE ROLE humanos_capture_reader_runtime LOGIN PASSWORD '<generated-secret>' NOINHERIT;
-- GRANT humanos_capture_encrypted_reader_limited TO humanos_capture_reader_runtime;
--
-- Runtime services should SET ROLE to the granted NOLOGIN capability role before
-- invoking the function, or deployment may grant the same exact function/schema
-- privileges directly to the LOGIN identity. Never commit the generated password.
