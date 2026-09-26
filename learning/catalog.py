"""Seed catalogs for the first HumanOS adaptive courses.

These are broad skill maps, not claims that every item has been taught.
Overlap is intentional: evidence may advance several courses.
"""
from copy import deepcopy

from .mastery_engine import Course, Skill

SKILLS = [
    Skill("computing.hardware", "Computer hardware, electricity, digital logic and microprocessors", ["cybersecurity", "ai", "electronics"], priority=.55),
    Skill("cli.shell", "Terminal, shell, Bash and command-line fluency", ["cybersecurity", "ai", "engineering"], priority=.65),
    Skill("git", "Git and GitHub: commits, branches, diffs, merges, recovery", ["cybersecurity", "ai", "engineering"], priority=.55),
    Skill("networking", "Networking: TCP/IP, DNS, HTTP/S, routing and packet analysis", ["cybersecurity", "ai"], priority=.9),
    Skill("windows.telemetry", "Windows telemetry, Event Logs, Sysmon and PowerShell", ["cybersecurity", "dfir"], priority=1.0),
    Skill("dfir.evidence", "Evidence preservation, hashing, acquisition and chain of custody", ["cybersecurity", "dfir"], priority=.8),
    Skill("dfir.artifacts", "Windows forensic artifacts and timelines", ["cybersecurity", "dfir"], priority=1.0),
    Skill("dfir.memory", "Memory forensics", ["cybersecurity", "dfir"], priority=.9),
    Skill("dfir.network", "Network forensics and PCAP investigation", ["cybersecurity", "dfir"], priority=.95),
    Skill("ir", "Incident response, scoping, containment, recovery and communication", ["cybersecurity", "dfir"], priority=.9),
    Skill("intel.tradecraft", "OSINT verification, ACH, source grading, GEOINT, SOCMINT and reporting", ["cybersecurity", "atlas", "ai"], priority=.75),
    Skill("programming.python", "Python, data structures, packages, environments, testing and debugging", ["ai", "engineering", "data"], priority=.7),
    Skill("data.sql_analytics", "SQL for data analysis: SELECT, filtering, joins, grouping, aggregation, quality checks and trend analysis", ["data", "engineering", "career"], priority=.9),
    Skill("data.quality", "Data quality and delivery validation: completeness, timeliness, consistency, duplicate/error detection, reconciliation and escalation", ["data", "career"], priority=.95),
    Skill("data.business_intelligence", "Business intelligence and analytical reasoning: metrics, trends, gaps, segmentation, dashboards and product/content improvement", ["data", "business", "career"], priority=.9),
    Skill("data.content_dissemination", "Content dissemination and provider data flows: source systems, ingestion, transformation, validation, delivery, downstream consumption and failure points", ["data", "engineering", "career"], priority=1.0),
    Skill("workflow.automation", "Workflow automation: identify repetitive work, map triggers/data/actions, design reliable automations, handle errors and measure improvement", ["engineering", "business", "career"], priority=.9),
    Skill("finance.market_structure", "Financial-market foundations: buy side, sell side, brokers, exchanges, research providers, equities, market participants and information flows", ["finance", "career"], priority=.95),
    Skill("finance.research_ecosystem", "Research-data ecosystem: sell-side research, contributors/providers, distribution, entitlements, discoverability, timeliness and client value", ["finance", "data", "career"], priority=1.0),
    Skill("client.customer_service", "High-quality customer service: clarify the request, own the issue, communicate progress, resolve or escalate, and close the loop", ["client", "career"], priority=1.0),
    Skill("client.relationship_management", "Relationship management: trust, discovery, expectation-setting, difficult conversations, follow-through and long-term account health", ["client", "business", "career"], priority=1.0),
    Skill("client.technical_account_management", "Technical account management: understand client architecture and goals, translate business needs into technical action, coordinate implementation/support and advise on improvements", ["client", "engineering", "career"], priority=1.0),
    Skill("support.ticket_sla", "Support operations: ticket hygiene, prioritization, SLA awareness, triage, ownership, escalation, status updates and closure quality", ["support", "client", "career"], priority=1.0),
    Skill("account.portfolio_strategy", "Account and portfolio strategy: segment accounts, define goals, use metrics, plan proactive client touches, identify growth/value opportunities and track outcomes", ["client", "business", "career"], priority=.95),
    Skill("project.prioritization", "Multi-project prioritization: urgency vs impact, dependencies, time-boxing, queue management, stakeholder alignment and reliable follow-through", ["business", "career"], priority=.95),
    Skill("process.continuous_improvement", "Continuous improvement: identify friction, challenge the status quo constructively, test changes, document results and scale better practices", ["business", "engineering", "career"], priority=.9),
    Skill("communication.stakeholder", "Stakeholder communication: concise technical explanation, executive/client updates, expectation management, active listening and negotiation", ["client", "business", "career"], priority=1.0),
    Skill("collaboration.cross_functional", "Cross-functional and global collaboration across account management, product, content, engineering and operations teams", ["business", "career"], priority=.9),
    Skill("ai.ml", "ML foundations: data, loss, optimization, neural networks and backpropagation", ["ai"], priority=.75),
    Skill("ai.transformers", "Transformers: tokens, embeddings, Q/K/V, attention, MLP, logits and inference", ["ai"], priority=1.0),
    Skill("ai.adaptation", "Prompt/context engineering, fine-tuning and LoRA", ["ai"], priority=.8),
    Skill("ai.rag", "RAG and knowledge systems: embeddings, chunking, vector databases, retrieval, reranking, provenance, permissions and evaluation", ["ai", "humanos", "engineering"], priority=.9),
    Skill("ai.systems", "Local models, Ollama, APIs, tools, agents, orchestration and memory", ["ai", "humanos"], priority=.9),
    Skill("ai.evaluation", "Model and agent evaluation, benchmarking, disagreement, naturalization and regression testing", ["ai", "humanos"], priority=.9),
    Skill("ai.observability", "AI observability: traces, logs, metrics, token/cost usage, latency, model/tool failures and agent execution history", ["ai", "humanos", "engineering"], priority=.85),
    Skill("ai.platform_architecture", "AI platform and reference architecture: model gateways, APIs, workers, queues, storage, identity, secrets and service boundaries", ["ai", "humanos", "engineering"], priority=.9),
    Skill("ai.governance", "Enterprise AI governance and risk: model/agent registries, approval boundaries, auditability, data classification, retention and evaluation gates", ["ai", "humanos", "cybersecurity"], priority=.9),
    Skill("ai.cost_performance", "AI cost/performance engineering: routing, caching, batching, context reduction, local/remote placement, latency, capacity and cost attribution", ["ai", "humanos", "engineering"], priority=.85),
    Skill("ai.security", "AI security, privacy, permissions, provenance and bounded agency", ["ai", "cybersecurity", "humanos"], priority=.9),
    Skill("architecture.documentation", "Architecture documentation: ADRs, C4 views, deployment/data-flow diagrams, threat models, runbooks and failure-mode documentation", ["ai", "humanos", "engineering"], priority=.8),
    Skill("deployment.portability", "Portable production deployment across local, private server, VPS/dedicated server, hybrid and cloud environments using containers, networking, TLS, secrets, backups and CI/CD", ["ai", "humanos", "engineering"], priority=.9),
    Skill("cloud.azure_foundry", "Azure and Azure AI Foundry as an enterprise implementation environment for AI services, identity, deployment, evaluation and operations without making HumanOS Azure-dependent", ["ai", "humanos", "engineering"], priority=.7),
    Skill("engineering.systems", "APIs, databases, servers, containers, observability and reliability", ["ai", "humanos", "engineering", "data"], priority=.7),
    Skill("plc.controls", "PLC, sensors, motors, industrial controls, SCADA and ICS foundations", ["plc", "electronics", "cybersecurity"], priority=.35),
]

CYBER = Course("cybersecurity-dfir", "Cybersecurity, DFIR & Incident Response", [
    "computing.hardware", "cli.shell", "git", "networking", "windows.telemetry", "dfir.evidence",
    "dfir.artifacts", "dfir.memory", "dfir.network", "ir", "intel.tradecraft", "ai.security", "plc.controls"
], career_readiness_percent=47.0)

AI = Course("ai-systems", "AI Systems Engineering & HumanOS", [
    "computing.hardware", "cli.shell", "git", "networking", "programming.python", "ai.ml", "ai.transformers",
    "ai.adaptation", "ai.rag", "ai.systems", "ai.evaluation", "ai.observability", "ai.platform_architecture",
    "ai.governance", "ai.cost_performance", "ai.security", "architecture.documentation",
    "deployment.portability", "cloud.azure_foundry", "engineering.systems", "intel.tradecraft"
])

BLOOMBERG_RESEARCH_DATA_TAM = Course("bloomberg-research-data-tam", "Bloomberg Technical Account Manager - Research Data", [
    "finance.market_structure", "finance.research_ecosystem", "data.content_dissemination", "data.quality",
    "data.sql_analytics", "programming.python", "data.business_intelligence", "workflow.automation",
    "client.customer_service", "client.relationship_management", "client.technical_account_management",
    "support.ticket_sla", "account.portfolio_strategy", "project.prioritization",
    "process.continuous_improvement", "communication.stakeholder", "collaboration.cross_functional",
    "engineering.systems"
])

def seed(engine):
    # Module-level catalog entries are templates, not shared learner state.
    # Deep-copying prevents evidence/stage mutations in one engine instance from
    # leaking into later tests, sessions, or humans.
    for skill in SKILLS:
        engine.add_skill(deepcopy(skill))
    engine.add_course(deepcopy(CYBER))
    engine.add_course(deepcopy(AI))
    engine.add_course(deepcopy(BLOOMBERG_RESEARCH_DATA_TAM))
    # Preserve known continuation points without fabricating mastery scores.
    engine.skills["dfir.evidence"].stage = "demonstrated"
    engine.skills["windows.telemetry"].stage = "practiced"
    # Tabletop / first-response work supports an IR practice continuation point;
    # TTX-001 itself remains open and does not receive a fabricated final grade.
    engine.skills["ir"].stage = "practiced"
    engine.skills["ai.transformers"].stage = "introduced"
    return engine
