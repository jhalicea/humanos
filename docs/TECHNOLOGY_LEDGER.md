# HumanOS Technology Encounter Ledger — v1

Status: **ACTIVE CANDIDATE ARTIFACT** on `feature/adaptive-learning-academy-v1`  
Purpose: record technologies Jon encounters so HumanOS can refresh, teach, test, and revisit them without pretending that exposure equals mastery.

## Ledger semantics

- **REFRESH** — previously studied or used; present competence is not assumed.
- **SEEN** — encountered and worth recognizing; no competence claim.
- **ACTIVE** — currently used in a real project/lab; evidence should still be graded separately.
- **CORE** — high-value for the current HumanOS / AI systems / cybersecurity / DFIR path.
- **SUPPORTING** — useful systems literacy or prerequisite knowledge.
- **ELECTIVE** — understand the concept first; specialize only if future work justifies it.

No row below is a mastery claim. Mastery remains evidence-derived through the Adaptive Mastery Engine.

## 2026-09-13 intake — networking refresh + scarce enterprise technologies

| Technology / concept | Domain | State | Learning priority | Course skill | Why it is in the ledger |
|---|---|---:|---:|---|---|
| OSI / TCP-IP models | Networking | REFRESH | CORE | `networking` | Mental model for DFIR, cloud, identity and troubleshooting |
| Ethernet / MAC / ARP | Networking | REFRESH | CORE | `networking` | Layer-2 traffic and host communication fundamentals |
| IPv4 / IPv6 | Networking | REFRESH | CORE | `networking` | Addressing, routing and investigation fundamentals |
| Subnetting | Networking | REFRESH | CORE | `networking` | Required to reason about network boundaries and routing |
| TCP / UDP | Networking | REFRESH | CORE | `networking` | Transport behavior, ports and packet analysis |
| DNS | Networking | REFRESH | CORE | `networking`, `networking.services` | Essential for normal operations and incident investigation |
| HTTP / HTTPS / TLS | Networking / Web | REFRESH | CORE | `networking`, `engineering.systems` | APIs, browsers, agents, security and web investigations |
| VLANs / 802.1Q trunks | Switching | REFRESH | CORE | `networking.switching` | Segmentation and enterprise switching literacy |
| STP / RSTP | Switching | REFRESH | SUPPORTING | `networking.switching` | Loop prevention and switched-network troubleshooting |
| EtherChannel | Switching | REFRESH | SUPPORTING | `networking.switching` | Link aggregation and switching literacy |
| Static/default routing | Routing | REFRESH | CORE | `networking.routing` | Basic routing-table reasoning |
| OSPF | Routing | REFRESH | SUPPORTING | `networking.routing` | Dynamic-routing literacy and troubleshooting |
| NAT / PAT | Routing / Security | REFRESH | CORE | `networking.routing` | Common boundary behavior relevant to IR and cloud |
| ACLs | Networking / Security | REFRESH | CORE | `networking.routing` | Traffic-policy and segmentation reasoning |
| DHCP | Network services | REFRESH | CORE | `networking.services` | Host configuration and investigation context |
| NTP | Network services | REFRESH | CORE | `networking.services` | Time integrity matters directly to DFIR timelines |
| SNMP / syslog | Operations | REFRESH | SUPPORTING | `networking.services` | Monitoring, telemetry and incident evidence |
| SSH | Secure administration | REFRESH | CORE | `networking.services`, `transfer.mft` | Remote administration and secure transport |
| AAA / RADIUS / TACACS+ | Identity / Networking | SEEN | CORE | `networking.services`, `identity.iam` | Authentication and authorization for infrastructure |
| Cisco IOS / IOS XE | Networking | REFRESH | SUPPORTING | `networking.switching`, `networking.routing` | Practical Cisco lab environment; vendor-specific details are secondary to concepts |
| Wireshark / PCAP analysis | DFIR / Networking | REFRESH | CORE | `dfir.network` | Directly supports network forensics and incident response |
| REST APIs | Engineering | ACTIVE | CORE | `networking.automation`, `engineering.systems` | HumanOS integrations, automation and modern network management |
| JSON / YAML | Engineering | ACTIVE | CORE | `networking.automation`, `engineering.systems` | Common configuration and API data formats |
| Ansible | Automation | SEEN | SUPPORTING | `networking.automation` | Configuration automation and repeatable operations |
| Terraform | Infrastructure as code | SEEN | SUPPORTING | `networking.automation`, `cloud.foundation` | Infrastructure provisioning and reproducibility |
| Agentic AI for network operations | AI / Networking | SEEN | SUPPORTING | `networking.automation` | Current network-operations direction; useful crossover with HumanOS |
| IAM | Identity / Security | SEEN | CORE | `identity.iam` | Central control plane for modern enterprise security |
| IDaaS | Identity / Cloud | SEEN | CORE | `identity.iam` | Cloud-delivered identity services |
| IGA | Identity governance | SEEN | CORE | `identity.iam` | Identity lifecycle, access reviews and governance |
| SSO / MFA | Identity | SEEN | CORE | `identity.iam` | Common authentication architecture and attack surface |
| RBAC / ABAC | Authorization | SEEN | CORE | `identity.iam` | Permission modeling for cloud, enterprise and HumanOS |
| PAM | Identity / Security | SEEN | CORE | `identity.iam` | High-value privileged-access control |
| OAuth 2.0 | Identity protocols | SEEN | CORE | `identity.federation` | API authorization and delegated access |
| OpenID Connect (OIDC) | Identity protocols | SEEN | CORE | `identity.federation` | Modern authentication layer built on OAuth 2.0 |
| SAML | Identity federation | SEEN | CORE | `identity.federation` | Enterprise SSO and federation literacy |
| Tokens / sessions / service identities | Identity / APIs | SEEN | CORE | `identity.federation`, `identity.iam` | Critical to cloud incidents, APIs and agent security |
| Okta | Identity platform | SEEN | CORE | `identity.platforms` | Major identity platform; learn concepts and basic administration/investigation |
| Microsoft Entra ID | Identity platform | SEEN | CORE | `identity.platforms` | Common enterprise/cloud identity control plane |
| Active Directory | Identity platform | REFRESH | CORE | `identity.platforms` | Foundational Windows enterprise identity and lateral-movement context |
| SailPoint | Identity governance platform | SEEN | SUPPORTING | `identity.platforms` | Representative enterprise IGA platform |
| Managed File Transfer (MFT) | Enterprise integration | SEEN | SUPPORTING | `transfer.mft` | Business-critical transfer workflows and auditability |
| SFTP / SCP | Secure file transfer | SEEN | CORE | `transfer.mft` | Secure transport; now explicitly present in current CCNA objectives |
| FTPS | Secure file transfer | SEEN | SUPPORTING | `transfer.mft` | Legacy/enterprise secure transfer literacy |
| SSH keys / certificates | Security | SEEN | CORE | `transfer.mft`, `identity.iam` | Machine identity and secure automation |
| Cloud compute/storage/network/IAM | Cloud | SEEN | CORE | `cloud.foundation` | Common environment for DFIR, AI systems and identity |
| Containers | Engineering | ACTIVE | CORE | `engineering.systems` | Deployment and local/server portability |
| Observability: logs/metrics/traces/alerts | Reliability / IR | ACTIVE | CORE | `engineering.systems` | HumanOS reliability plus security detection and diagnosis |
| IBM Netcool | Enterprise monitoring | SEEN | ELECTIVE | `enterprise.netcool` | Recognize enterprise event-management/operations tooling; do not specialize yet |
| SAFe | Delivery | SEEN | ELECTIVE | `delivery.safe` | Recognize large-enterprise delivery vocabulary |
| Release Train Engineer (RTE) | Delivery / Leadership | SEEN | ELECTIVE | `delivery.safe` | Understand role and coordination model; not a current specialization target |
| Front-office trading systems | Finance / Engineering | SEEN | ELECTIVE | `finance.frontoffice` | Systems literacy for market-data/execution environments |
| Market data / low-latency systems | Finance / Engineering | SEEN | ELECTIVE | `finance.frontoffice` | Explains why specialized financial engineering can command high compensation |
| kdb+ | Time-series databases | SEEN | ELECTIVE | `data.kdbq` | Specialized high-volume time-series platform used in finance |
| q | Programming / Data | SEEN | ELECTIVE | `data.kdbq` | kdb+ query/programming language |
| C++ | Systems programming | SEEN | ELECTIVE | `programming.cpp` | Useful in low-latency and performance-sensitive systems; not a current priority |
| FPGA | Hardware | SEEN | ELECTIVE | `hardware.fpga` | Hardware acceleration and low-latency systems literacy |
| RTL | Digital hardware | SEEN | ELECTIVE | `hardware.fpga` | Core abstraction for FPGA design |
| Verilog / SystemVerilog / VHDL | Hardware description languages | SEEN | ELECTIVE | `hardware.fpga` | Languages used to describe digital hardware |

## Learning rule for Jon's networking refresh

Do **not** restart networking as if it were new. Use a short diagnostic first, then targeted refresh labs. Previously studied topics can move quickly; rusty or weak areas get deeper practice. The books Jon already owns are allowed as concept references, but current Cisco objectives determine what is current for certification.

## Provenance

- Jon's prior study: CCENT/CCNA ICND1 100-105 and CCNA Routing & Switching ICND2 200-105 Official Cert Guides by Wendell Odom; Jon reports studying roughly half of one guide and being rusty now.
- Video intake: YouTube `lb_TQqeTq-k`, discussed 2026-09-13. Technologies from the video were treated as encounters, not mastery or career commitments.
- Cisco retired ICND1 100-105 and ICND2 200-105 on 2020-02-23 and replaced that certification path with 200-301 CCNA.
- Current Cisco source used for curriculum refresh: 200-301 CCNA v2.0 Exam Topics, Cisco Systems, 2026: https://learningcontent.cisco.com/documents/marketing/exam-topics/200-301_CCNA_v2.0_Exam_Topics_PDF.pdf

## Next implementation slice

Connect this version-controlled ledger to the Adaptive Mastery Engine so `SEEN` / `REFRESH` encounters can be recorded programmatically without being converted into mastery evidence.
