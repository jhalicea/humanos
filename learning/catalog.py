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
    Skill("networking", "Networking foundations and CCNA refresh: OSI/TCP-IP, Ethernet, IPv4/IPv6, subnetting, DNS, HTTP/S and packet analysis", ["cybersecurity", "ai", "networking"], priority=.95),
    Skill("networking.switching", "Switching: MAC learning, VLANs, 802.1Q trunks, STP/RSTP, EtherChannel and wireless access fundamentals", ["cybersecurity", "networking"], prerequisites=["networking"], priority=.80),
    Skill("networking.routing", "Routing: routing tables, static/default routes, OSPF, NAT/PAT, ACLs and IPv4/IPv6 forwarding", ["cybersecurity", "networking"], prerequisites=["networking"], priority=.85),
    Skill("networking.services", "Network services and management: DHCP, DNS, NTP, SNMP, syslog, SSH, AAA, RADIUS/TACACS+ and VPN basics", ["cybersecurity", "networking"], prerequisites=["networking"], priority=.75),
    Skill("networking.automation", "Network automation and operations: REST APIs, JSON/YAML, controllers, Ansible, Terraform and AI-assisted network operations", ["cybersecurity", "ai", "networking", "engineering"], prerequisites=["networking"], priority=.65),
    Skill("identity.iam", "IAM/IDaaS/IGA: authentication vs authorization, identity lifecycle, SSO, MFA, RBAC/ABAC, PAM and service identities", ["cybersecurity", "ai", "humanos", "identity"], priority=.95),
    Skill("identity.federation", "Identity federation and authorization protocols: OAuth 2.0, OpenID Connect, SAML, tokens, sessions and trust boundaries", ["cybersecurity", "ai", "humanos", "identity"], prerequisites=["identity.iam"], priority=.90),
    Skill("identity.platforms", "Identity platforms: Okta, Microsoft Entra ID, Active Directory and SailPoint fundamentals", ["cybersecurity", "ai", "humanos", "identity"], prerequisites=["identity.iam"], priority=.80),
    Skill("transfer.mft", "Managed and secure file transfer: SFTP, SCP, FTPS, SSH keys, TLS, integrity verification, automation and audit trails", ["cybersecurity", "engineering"], prerequisites=["networking"], priority=.60),
    Skill("cloud.foundation", "Cloud foundations: compute, storage, IAM, virtual networks, secrets, logging, serverless and shared-responsibility boundaries", ["cybersecurity", "ai", "engineering"], priority=.75),
    Skill("windows.telemetry", "Windows telemetry, Event Logs, Sysmon and PowerShell", ["cybersecurity", "dfir"], priority=1.0),
    Skill("dfir.evidence", "Evidence preservation, hashing, acquisition and chain of custody", ["cybersecurity", "dfir"], priority=.8),
    Skill("dfir.artifacts", "Windows forensic artifacts and timelines", ["cybersecurity", "dfir"], priority=1.0),
    Skill("dfir.memory", "Memory forensics", ["cybersecurity", "dfir"], priority=.9),
    Skill("dfir.network", "Network forensics and PCAP investigation", ["cybersecurity", "dfir"], priority=.95),
    Skill("ir", "Incident response, scoping, containment, recovery and communication", ["cybersecurity", "dfir"], priority=.9),
    Skill("intel.tradecraft", "OSINT verification, ACH, source grading, GEOINT, SOCMINT and reporting", ["cybersecurity", "atlas", "ai"], priority=.75),
    Skill("programming.python", "Python, data structures, packages, environments, testing and debugging", ["ai", "engineering"], priority=.7),
    Skill("programming.cpp", "C++ foundations for systems, performance-sensitive and low-latency computing", ["engineering", "finance", "hardware"], priority=.30),
    Skill("ai.ml", "ML foundations: data, loss, optimization, neural networks and backpropagation", ["ai"], priority=.75),
    Skill("ai.transformers", "Transformers: tokens, embeddings, Q/K/V, attention, MLP, logits and inference", ["ai"], priority=1.0),
    Skill("ai.adaptation", "Prompt/context engineering, RAG, embeddings, fine-tuning and LoRA", ["ai"], priority=.8),
    Skill("ai.systems", "Local models, Ollama, APIs, tools, agents, orchestration and memory", ["ai", "humanos"], priority=.9),
    Skill("ai.evaluation", "Model evaluation, benchmarking, disagreement and naturalization", ["ai", "humanos"], priority=.85),
    Skill("ai.security", "AI security, privacy, permissions, provenance and bounded agency", ["ai", "cybersecurity", "humanos"], priority=.9),
    Skill("engineering.systems", "APIs, databases, servers, containers, observability and reliability", ["ai", "humanos"], priority=.7),
    Skill("enterprise.netcool", "IBM Netcool and enterprise event-management concepts: ingestion, correlation, alerting and operations", ["enterprise", "observability"], priority=.20),
    Skill("delivery.safe", "SAFe and Release Train Engineer concepts: planning cadence, dependencies, release coordination and delivery flow", ["delivery", "leadership"], priority=.20),
    Skill("finance.frontoffice", "Front-office and trading-system concepts: market data, order/execution flow, production support and latency", ["finance", "engineering"], priority=.25),
    Skill("data.kdbq", "kdb+/q and high-volume time-series data concepts used in financial and low-latency systems", ["finance", "data", "engineering"], prerequisites=["programming.python"], priority=.20),
    Skill("hardware.fpga", "FPGA foundations: digital logic, RTL, Verilog/SystemVerilog/VHDL, timing, pipelining and hardware/software boundaries", ["hardware", "electronics", "engineering"], prerequisites=["computing.hardware"], priority=.30),
    Skill("plc.controls", "PLC, sensors, motors, industrial controls, SCADA and ICS foundations", ["plc", "electronics", "cybersecurity"], priority=.35),
]

CYBER = Course("cybersecurity-dfir", "Cybersecurity, DFIR & Incident Response", [
    "computing.hardware", "cli.shell", "git", "networking", "networking.switching", "networking.routing",
    "networking.services", "networking.automation", "identity.iam", "identity.federation", "identity.platforms",
    "transfer.mft", "cloud.foundation", "windows.telemetry", "dfir.evidence", "dfir.artifacts", "dfir.memory",
    "dfir.network", "ir", "intel.tradecraft", "ai.security", "plc.controls"
], career_readiness_percent=47.0)

AI = Course("ai-systems", "AI Systems Engineering & HumanOS", [
    "computing.hardware", "cli.shell", "git", "networking", "networking.automation", "identity.iam",
    "identity.federation", "identity.platforms", "cloud.foundation", "programming.python", "ai.ml",
    "ai.transformers", "ai.adaptation", "ai.systems", "ai.evaluation", "ai.security", "engineering.systems",
    "intel.tradecraft"
])

SYSTEMS_LITERACY = Course("systems-literacy", "Technology Systems Literacy & Scarcity Niches", [
    "networking", "networking.switching", "networking.routing", "networking.services", "networking.automation",
    "identity.iam", "identity.federation", "identity.platforms", "transfer.mft", "cloud.foundation",
    "engineering.systems", "enterprise.netcool", "delivery.safe", "finance.frontoffice", "data.kdbq",
    "programming.cpp", "computing.hardware", "hardware.fpga"
])

def seed(engine):
    # Catalog constants are templates. Each engine receives independent mutable
    # learner state so evidence recorded in one engine/test/session cannot leak
    # into another through module-level Skill objects.
    for skill in SKILLS:
        engine.add_skill(deepcopy(skill))
    engine.add_course(deepcopy(CYBER))
    engine.add_course(deepcopy(AI))
    engine.add_course(deepcopy(SYSTEMS_LITERACY))
    # Preserve known continuation points without fabricating mastery scores.
    engine.skills["dfir.evidence"].stage = "demonstrated"
    engine.skills["windows.telemetry"].stage = "practiced"
    engine.skills["ai.transformers"].stage = "introduced"
    engine.skills["networking"].stage = "introduced"
    return engine
