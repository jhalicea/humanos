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
| DNS | Network services | REFRESH | CORE | `networking`, `networking.services` | Essential for normal operations and incident investigation |
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

## 2026-09-14 intake — Thinkful 2020 web engineering recovery

These rows are derived from Jon's surviving 2020–early-2021 repositories and his stated Thinkful experience. `REFRESH` means prior study/use only; it does not imply current competence. Forked/reference repositories are not counted as authored-work evidence.

| Technology / concept | Domain | State | Learning priority | Course skill | Why it is in the ledger |
|---|---|---:|---:|---|---|
| Git / GitHub | Engineering workflow | REFRESH | CORE | `web.git` | `learn-github` and the historical project trail show prior use; essential to current HumanOS work |
| VS Code + integrated terminal workflow | Development environment | REFRESH | CORE | `web.git`, `engineering.systems` | User-reported primary 2020 workflow; supports current implementation/debugging |
| HTML5 / semantic HTML | Web frontend | REFRESH | SUPPORTING | `web.frontend` | Historical Thinkful projects; refresh rather than restart |
| CSS / responsive design | Web frontend | REFRESH | SUPPORTING | `web.frontend` | Extensive early-course exposure; maintain practical literacy |
| Accessibility / keyboard-first forms | Web frontend | REFRESH | CORE | `web.frontend.a11y` | Explicit requirement in the quiz project; important to usable HumanOS interfaces |
| Wireframing / view planning | Product / UI | REFRESH | SUPPORTING | `web.design` | Separate quiz wireframe repo shows prior planning practice |
| JavaScript | Programming | REFRESH | CORE | `web.javascript` | Central language across the recovered course and current web/automation work |
| jQuery | Web / DOM | REFRESH | ELECTIVE | `web.dom.legacy` | Useful to read old code and recall DOM/event concepts; not a modern specialization target |
| DOM events / delegation / traversal | Web / JavaScript | REFRESH | CORE | `web.javascript`, `web.dom` | Shopping List demonstrates submit/click events, `currentTarget`, delegated handlers and DOM updates |
| Browser `fetch` / Promises | HTTP / JavaScript | REFRESH | CORE | `web.http` | Dog API demonstrates external API requests, Promise chains and error catches |
| Async/await | JavaScript / HTTP | REFRESH | CORE | `web.http` | Modern expression of concepts previously practiced with Promise chains; diagnostic required |
| JSON / API response handling | Web / APIs | REFRESH | CORE | `web.http`, `engineering.systems` | Repeated throughout external API and backend exercises |
| npm | Node tooling | REFRESH | CORE | `web.node.tooling` | Historical React/Node projects rely on npm commands and dependency installation |
| `package.json` / npm scripts | Node tooling | REFRESH | CORE | `web.node.tooling` | Historical repos contain start/build/test/deploy scripts; key mental model for current tooling |
| `package-lock.json` / dependency locking | Supply chain / Tooling | REFRESH | CORE | `web.node.tooling`, `engineering.security` | Historical lockfiles exist; modern refresh should include integrity/version risk |
| Webpack 4 | Build tooling | REFRESH | ELECTIVE | `web.build.legacy` | Historical Bookmarks/template build system; recognize but do not default to it |
| Create React App / `react-scripts` | React tooling | REFRESH | ELECTIVE | `web.react.legacy` | Historical React bootstrapping; officially deprecated for new apps |
| React / JSX / components / props / state | Web frontend | REFRESH | CORE | `web.react` | Repeated authored project evidence; major reactivation target |
| Class components / `setState` | React legacy patterns | REFRESH | SUPPORTING | `web.react.legacy` | Explicit old exercise and Noteful-era code; needed to read old apps |
| React Hooks | React | REFRESH | CORE | `web.react.hooks` | User reports prior use; modern React baseline uses function components/hooks |
| React Router / dynamic route params / Link | React routing | REFRESH | CORE | `web.react.routing` | William Setstatespear and Noteful preserve direct routing evidence |
| Jest | Testing | REFRESH | CORE | `web.testing.frontend` | CRA/Noteful testing exposure; refresh current patterns |
| React Testing Library | Testing | REFRESH | CORE | `web.testing.frontend` | Present in Noteful dependencies; aligned with behavior-focused testing |
| Enzyme | Testing | REFRESH | ELECTIVE | `web.testing.legacy` | Present in older `noteful-client`; legacy recognition only |
| Node.js | Backend / Runtime | REFRESH | CORE | `web.node` | Multiple Express exercises; rebuild on supported Node LTS |
| Express | Backend / HTTP | REFRESH | CORE | `web.express` | Express 4 authored exercises; modern instruction targets Express 5 semantics |
| Express middleware ordering | Backend / HTTP | REFRESH | CORE | `web.express.middleware` | Auth, CORS, Helmet, Morgan and error middleware appear in authored APIs |
| CORS | Web security / HTTP | REFRESH | CORE | `web.http.security` | Present across backend exercises; important for browser/API boundaries |
| Helmet / HTTP security headers | Web security | REFRESH | CORE | `web.http.security` | Present across Express exercises |
| Morgan / Winston logging | Observability | REFRESH | CORE | `web.observability` | Historical request/application logging; connects directly to HumanOS reliability |
| dotenv / environment variables | Configuration / Security | REFRESH | CORE | `web.config` | Historical server configuration and API-token handling |
| REST routes / query parameters | API engineering | REFRESH | CORE | `web.api` | Moviedex/Pokedex/Noteful server evidence |
| HTTP status handling: 401 / 4xx / 5xx | API / Reliability | REFRESH | CORE | `web.http.failure` | Surviving code explicitly returns 401 and 500; deepen into recovery policy |
| Bearer token / `Authorization` header | Authentication / APIs | REFRESH | CORE | `web.auth` | Moviedex and Pokedex have direct authored middleware evidence |
| JWT | Authentication | REFRESH | CORE | `web.auth.jwt` | User-reported Thinkful exposure; no surviving JWT implementation located in inspected repos |
| Sessions / access-refresh lifecycle / revocation | Authentication | SEEN | CORE | `web.auth.session` | Modern extension needed to repair the old token-lifecycle gap |
| Password hashing | Authentication | SEEN | CORE | `web.auth.passwords` | Necessary foundation for modern login/auth understanding |
| OAuth 2.0 / OIDC for web apps | Identity / APIs | SEEN | CORE | `web.auth.federation`, `identity.federation` | Modern extension linking web engineering to HumanOS identity work |
| Mocha | Backend testing | REFRESH | CORE | `web.testing.backend` | Present in Express/Bookmarks/Noteful API dev dependencies |
| Chai | Backend testing | REFRESH | SUPPORTING | `web.testing.backend` | Historical assertion library exposure |
| Supertest | API integration testing | REFRESH | CORE | `web.testing.backend` | Directly useful for testing Express request/response and auth failures |
| SQL / PostgreSQL | Data / Backend | REFRESH | CORE | `web.data.sql` | Noteful API persistence and migrations; deep refresh required |
| Knex | Database tooling | REFRESH | SUPPORTING | `web.data.sql` | Historical query-builder exposure; learn concepts before choosing current library |
| Database migrations / Postgrator | Data lifecycle | REFRESH | CORE | `web.data.migrations` | Noteful API contains do/undo migrations and production migration scripts |
| Router/service separation | Backend architecture | REFRESH | CORE | `web.architecture` | Noteful API separates routers and services; foundation for maintainable systems |
| XSS handling / output sanitization | Web security | REFRESH | CORE | `web.security` | `xss` dependency in Noteful API; deepen into context-aware browser/server security |
| GitHub Pages | Deployment | REFRESH | SUPPORTING | `web.deploy` | Historical frontend deployment workflow |
| Heroku deployment scripts | Deployment | REFRESH | ELECTIVE | `web.deploy.legacy` | Historical server deployment literacy; do not use as default solely for nostalgia |
| Vercel | Deployment | REFRESH | SUPPORTING | `web.deploy` | User reports prior account/use; current competence not assumed |
| TypeScript | Programming | SEEN | CORE | `web.typescript` | Major modern extension; introduce after JavaScript/React reactivation |
| Vite | Build tooling | SEEN | SUPPORTING | `web.build` | Modern lightweight React/build option; CRA is deprecated |
| Data structures / Big-O / recursion | CS fundamentals | REFRESH | SUPPORTING | `web.dsa` | Course-stage evidence and user recollection; DSA repo is empty, so diagnostic starts low-confidence |
| Full-stack failure handling / recovery | Reliability | REFRESH | CORE | `web.reliability` | Central unresolved interest: network vs server failure, retries, auth expiry, UI state, logging |

## Learning rule for Jon's networking refresh

Do **not** restart networking as if it were new. Use a short diagnostic first, then targeted refresh labs. Previously studied topics can move quickly; rusty or weak areas get deeper practice. The books Jon already owns are allowed as concept references, but current Cisco objectives determine what is current for certification.

## Learning rule for Jon's web engineering reactivation

Do **not** restart from beginner HTML/CSS. Begin with Git/GitHub + JavaScript/jQuery recognition diagnostics, then reactivate npm/React/Router and spend disproportionate depth on HTTP failures, Node/Express, backend testing, PostgreSQL and authentication/token lifecycle. Historical repos establish `REFRESH` provenance only. New `DEMONSTRATED` or `MASTERED` status requires current hands-on evidence, debugging and explanation. Prefer real HumanOS work when the selected implementation slice genuinely needs the skill; otherwise use the historical repository read-only as the diagnostic lab.

## Provenance

- Jon's prior study: CCENT/CCNA ICND1 100-105 and CCNA Routing & Switching ICND2 200-105 Official Cert Guides by Wendell Odom; Jon reports studying roughly half of one guide and being rusty now.
- Video intake: YouTube `lb_TQqeTq-k`, discussed 2026-09-13. Technologies from the video were treated as encounters, not mastery or career commitments.
- Cisco retired ICND1 100-105 and ICND2 200-105 on 2020-02-23 and replaced that certification path with 200-301 CCNA.
- Current Cisco source used for curriculum refresh: 200-301 CCNA v2.0 Exam Topics, Cisco Systems, 2026: https://learningcontent.cisco.com/documents/marketing/exam-topics/200-301_CCNA_v2.0_Exam_Topics_PDF.pdf
- Web engineering recovery intake, 2026-09-14: Jon's surviving GitHub repositories from the 2020–early-2021 Thinkful period were inspected for authored source, package manifests, tests, database migrations and deployment scripts. Forked/reference repositories were excluded from authored-work evidence. The detailed evidence map is `docs/WEB_ENGINEERING_REACTIVATION.md`.
- Current web modernization sources, checked 2026-09-14: React 19.3 / React docs and Create React App deprecation (`react.dev`), React Router v8 changelog (`reactrouter.com`), Node release/LTS table (`nodejs.org`), Express 5 migration guide (`expressjs.com`), TypeScript 7 (`typescriptlang.org`), and Vite 8 (`vite.dev`).

## Next implementation slice

Connect this version-controlled ledger to the Adaptive Mastery Engine so `SEEN` / `REFRESH` encounters can be recorded programmatically without being converted into mastery evidence.
