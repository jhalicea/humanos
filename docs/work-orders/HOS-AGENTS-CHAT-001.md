# HOS-AGENTS-CHAT-001 — ChatGPT workers, dedicated Architect and HINE eval

Status: **DRAFT / CANDIDATE / NO EXECUTION AUTHORITY**  
Workspace: `WS-HUMANOS`  
Classification: `CREATE_SEPARATE` for ChatGPT worker bridge; `EXTEND HOS-ARCH-001` for Architect responsibilities and existing HINE/model governance for qualification.  
Baseline: `runtime-0.1` @ `0fe4ea5751bb17be30656a5c95809b79d6718636`  
Authority: human owner; role/model scores never confer capability.

## Objective
Activate a reusable, **manual** ChatGPT QA role protocol and a distinct Architect role; specify how existing execution contracts and HINE/Model Registry bind to chat/local workers; make local-model comparison repeatable and budget-capped without touching canonical policy, Notebook, or model permissions.

## Existing components reused
`execution_contracts.py`, `work_order_compiler.py`, `AGENTS.md`, issue #67 routing, `docs/work-orders/HOS-ARCH-001.md`, `docs/architecture/HUMANOS_ARCHITECTURE_BASELINE_PLAN.md`, `hine.py`, `naturalization.py`, `model_registry.py`, `swarm_models.py`, draft QA PR #136 and frozen Life Notebook #137. **No duplicate dispatcher, permission broker, HINE runtime or canonical architecture registry.**

## Delivery
- `docs/agents/QA-CHAT-001.md`: role, current chat operating mode, tool/release limits, QA lifecycle and output contract.
- `docs/agents/ARCH-CHAT-001.md`: architect as separate proposal role, Mirror distinct.
- `docs/agents/CHATGPT_EXECUTION_V01.md`: manual FRIEND handoff/receipt and clear implementation-vs-spec boundary.
- `docs/agents/HINE_ROLE_QUALIFICATION_V01.md`: identity/role admission ladder and low-cost local model matrix.
- `config/agent_roles.candidate.json`: descriptive candidate registry; **all automatic_authority=false**.
- `examples/qa-chat-001-friend-packet.example.json`: strictly valid existing FRIEND packet for a read-only role.
- `tests/test_chat_agent_protocol.py`: standard-library regression that rejects role/packet drift and auto-authority claims.

## Risk / consent
Read-only role/contract design is GREEN/AMBER depending on future connected tool use. **New external connector privileges, cross-workspace data flows, HINE auto-admission, autonomous dispatch, arbitrary model code execution, user data ingestion, and release authority are RED candidates requiring independent review and explicit human owner approval**. Nothing in this DRAFT authorizes operations.

## Acceptance
1. GitHub exact SHA identified; candidate branch/draft PR only.
2. No changes to Mirror runtime, permission system, Work Order validator, HINE engine, Life Notebook or BodyFixOS.
3. Test FRIEND packet parses with existing `validate_friend_packet`; role registry has no auto-authority, no executable grants, and Mirror architect flag false.
4. QA-CHAT-001 first role-run uses actual GitHub read-only evidence and reports self-review status and no code execution if true. Only an independently rerun analysis may claim independent audit.
5. Local model inventory is **not available from connected GitHub**; owner Mac runs explicit `ollama list`; trial matrix must be capped and record exact installed names/profile hashes. Never invent tests or remotely assume Ollama installed models.
6. HINE exam / benchmark / owner review are distinct; never allow score to grant permission.
7. No merge, deploy or production data access; independent high-risk review and owner approval remain outstanding.

## Rollback
Close draft PR without merge. No runtime migration or state changes.
