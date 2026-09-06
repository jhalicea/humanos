HumanOS Runtime 0.1 local implementation context
Evidence: IMPLEMENTATION NOTE, not a canonical decision or constitutional amendment.

Mirror is the human-facing interface inside HumanOS. Models are replaceable resources.
Local session identity is issued by HumanOS. Prior session reuse requires its exact HCID.
Notebook transcript chronology is separate from selected current-state records in core.
The existing daily Markdown notebooks remain historical and unchanged. New transactions
use the runtime ledger and page projections beneath the configured existing vault.
Google Drive remains the designated canonical store for existing HumanOS records.
This local runtime is not yet synchronized with that store. Local checkpoint means
local write/readback only, never Drive reconciliation or proof of human receipt.

A model can request read_file, list_files, or create_file within workspace. Deterministic
policy checks govern execution. No shell, arbitrary Python, network tools, or overwrite.
File creation requires explicit human approval. The owner may stop the CLI with Ctrl-C.
