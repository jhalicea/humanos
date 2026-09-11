"""Seed catalogs for the first HumanOS adaptive courses.

These are broad skill maps, not claims that every item has been taught.
Overlap is intentional: evidence may advance several courses.
"""
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
    Skill("programming.python", "Python, data structures, packages, environments, testing and debugging", ["ai", "engineering"], priority=.7),
    Skill("ai.ml", "ML foundations: data, loss, optimization, neural networks and backpropagation", ["ai"], priority=.75),
    Skill("ai.transformers", "Transformers: tokens, embeddings, Q/K/V, attention, MLP, logits and inference", ["ai"], priority=1.0),
    Skill("ai.adaptation", "Prompt/context engineering, RAG, embeddings, fine-tuning and LoRA", ["ai"], priority=.8),
    Skill("ai.systems", "Local models, Ollama, APIs, tools, agents, orchestration and memory", ["ai", "humanos"], priority=.9),
    Skill("ai.evaluation", "Model evaluation, benchmarking, disagreement and naturalization", ["ai", "humanos"], priority=.85),
    Skill("ai.security", "AI security, privacy, permissions, provenance and bounded agency", ["ai", "cybersecurity", "humanos"], priority=.9),
    Skill("engineering.systems", "APIs, databases, servers, containers, observability and reliability", ["ai", "humanos"], priority=.7),
    Skill("plc.controls", "PLC, sensors, motors, industrial controls, SCADA and ICS foundations", ["plc", "electronics", "cybersecurity"], priority=.35),
]

CYBER = Course("cybersecurity-dfir", "Cybersecurity, DFIR & Incident Response", [
    "computing.hardware", "cli.shell", "git", "networking", "windows.telemetry", "dfir.evidence",
    "dfir.artifacts", "dfir.memory", "dfir.network", "ir", "intel.tradecraft", "ai.security", "plc.controls"
], career_readiness_percent=47.0)

AI = Course("ai-systems", "AI Systems Engineering & HumanOS", [
    "computing.hardware", "cli.shell", "git", "networking", "programming.python", "ai.ml", "ai.transformers",
    "ai.adaptation", "ai.systems", "ai.evaluation", "ai.security", "engineering.systems", "intel.tradecraft"
])

def seed(engine):
    for skill in SKILLS:
        engine.add_skill(skill)
    engine.add_course(CYBER)
    engine.add_course(AI)
    # Preserve known continuation points without fabricating mastery scores.
    engine.skills["dfir.evidence"].stage = "demonstrated"
    engine.skills["windows.telemetry"].stage = "practiced"
    engine.skills["ai.transformers"].stage = "introduced"
    return engine
