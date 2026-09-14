# Web & Software Engineering Reactivation — Thinkful 2020 → HumanOS 2026

Status: **ACTIVE CANDIDATE CURRICULUM** on `feature/adaptive-learning-academy-v1`  
Purpose: reactivate Jon's prior full-stack web engineering knowledge, repair the rushed backend/authentication gaps from the 2020 Thinkful Engineering Flex experience, and convert refreshed skills into evidence through real HumanOS work.

This is **not** a restart-from-zero bootcamp and it is **not** a claim of prior mastery. Historical repositories establish exposure and practice provenance; present mastery must be demonstrated under the HumanOS Adaptive Mastery Engine.

## Course design rules

1. **Refresh-first, not beginner-first.** Start each previously studied topic with a compact diagnostic.
2. **One conceptual layer at a time.** Do not repeat the old pattern of teaching Node, Express, databases, JWT, DSA, job preparation, and a capstone simultaneously.
3. **Architecture before syntax.** Explain the system boundary and data flow before framework-specific code.
4. **Failure handling is first-class.** Every substantial module includes failures, recovery, logging, retries, and security implications.
5. **Real work when useful.** Prefer HumanOS implementation, debugging, documentation, tests, APIs, and browser/runtime work over disposable toy apps.
6. **Do not force a HumanOS feature just to teach a technology.** If the active HumanOS slice does not need React/Node/etc., use the historical repo as a diagnostic lab until a real product need appears.
7. **Old stack = literacy; modern stack = build target.** Read the 2020 code faithfully, then learn the current equivalent.
8. **No historical course completion percentage becomes mastery.** Repository evidence may justify `REFRESH` or a diagnostic starting point only.
9. **Every training session uses the HumanOS mastery format:** short oral interview, hands-on build/inspection, failure/debugging exercise, teach-back/evidence capture, grade, exactly one next action.

## Recovered 2020 curriculum trail

The following sequence is reconstructed from Jon's GitHub repositories plus Jon's recollection of the program. Forked/reference repositories are explicitly excluded from authored-work evidence.

| Phase | Surviving evidence | Skills evidenced | Evidence interpretation |
|---|---|---|---|
| Git/GitHub onboarding | `jhalicea/learn-github` | repo workflow, commits, GitHub basics | prior practice; refresh required |
| HTML/CSS foundations | `jhalicea/pizza`, `jhalicea/jhalicea.com` | semantic pages, CSS, responsive/personal site work, GitHub Pages | practiced; do not spend months reteaching |
| UI planning | `jhalicea/wireframe-fun-quiz-app` | multi-view wireframing before implementation | practiced project planning |
| JavaScript + jQuery + state/render thinking | `jhalicea/shopping-list`, `jhalicea/fun-quiz-app` | events, forms, DOM traversal/manipulation, delegated handlers, store/update/render pattern, accessibility/responsive requirements | practiced; use as bridge into React |
| Fetch + external APIs + errors | `jhalicea/dog-api-1` | `fetch`, Promises, JSON, validation, `.catch`, API error/fallback UI | practiced; refresh and modernize to async/await |
| npm + bundling | `jhalicea/webpack-template`, `jhalicea/bookmarks-app` | `package.json`, dependencies, npm scripts, Webpack dev/build workflow | practiced; modern build tooling differs |
| React foundations | `jhalicea/laptop-customizer`, `jhalicea/react-update-state-from-input-challenge` | components, state, `setState`, forms, Create React App, npm scripts | practiced; class-era material is historical literacy |
| React Router | `jhalicea/william-setstatespear`, `jhalicea/noteful` | BrowserRouter, Route, dynamic `:id` routes, Link, route props | practiced; modern Router APIs differ |
| React testing | `jhalicea/noteful`, `jhalicea/noteful-client` | Jest/CRA test runner, React Testing Library; Enzyme/adapter in older client | practiced/exposed; Enzyme is legacy |
| Node/Express APIs | `jhalicea/moviedex-api`, `jhalicea/pokedex-api`, `jhalicea/express-boilerplate` | Node, Express, routes, query params, middleware, env vars, CORS, Helmet, Morgan, nodemon | practiced; major reactivation target |
| API authorization + error middleware | `moviedex-api`, `pokedex-api` | Bearer token in `Authorization`, 401 responses, middleware chain, generic 500 handler | practiced; direct precursor to JWT/auth concepts |
| Backend testing | `jhalicea/express-boilerplate`, `jhalicea/bookmarks-server`, `jhalicea/noteful-api` | Mocha, Chai, Supertest | practiced/exposed; refresh through failure-first API tests |
| Logging / server hygiene | `jhalicea/bookmarks-server` | Winston, Helmet, Morgan, dotenv, UUIDs | prior exposure |
| SQL/PostgreSQL persistence | `jhalicea/noteful-api` | PostgreSQL, Knex, SQL migrations, Postgrator, router/service separation, XSS handling | practiced/exposed; deep refresh required |
| Deployment | GitHub Pages, CRA scripts, Heroku scripts across repos | builds, static deploy, server deploy/migrations | historical workflow; modernize |
| Capstone 1 | `jhalicea/jhalicea.com` | personal site | completed historical project |
| Capstone 2 | `jhalicea/plant-vault` | planned plant-identification/care application | repo shell only; do not treat as completed |
| DSA / recursion / Big-O transition | `jhalicea/DSA-Recursion` | course-stage evidence only | empty repo; no mastery claim |

### Reference/fork repositories — not authored-work evidence

Examples include `jhalicea/dinero.js`, `jhalicea/javascript-questions`, `jhalicea/hiring-without-whiteboards`, and `jhalicea/react-coding-challenges`. These may document what Jon was reading or preparing for, but forked contents do **not** count as evidence that Jon wrote or mastered the material.

### Authentication/JWT evidence boundary

Jon reports that Thinkful introduced JWT after the initial login/authentication work and that token lifecycle/auth recovery was a major unresolved area. The surviving authored backend repositories clearly show Bearer-token middleware, `Authorization` headers, `401 Unauthorized`, and server error middleware. In the inspected repository manifests/source, no surviving `jsonwebtoken` dependency or JWT implementation has yet been located.

Therefore HumanOS records:

- API/Bearer-token authorization: **historically practiced; refresh**.
- JWT/token lifecycle: **user-reported prior course exposure; refresh from fundamentals**.
- Refresh tokens, expiration/revocation, OAuth/OIDC, secure browser storage and modern session design: **modern extension; mastery must be demonstrated**.

## 2026 modernization baseline

Verified against official project documentation in September 2026:

- React: current major/minor baseline is React 19.3 (`https://react.dev/versions`).
- Create React App: deprecated for new applications; React recommends frameworks or a modern build tool when appropriate (`https://react.dev/blog/2025/02/14/sunsetting-create-react-app`).
- React Router: current line is v8.x (`https://reactrouter.com/changelog`).
- Node.js: Node 24 is LTS; production labs should prefer an LTS release (`https://nodejs.org/en/about/previous-releases`).
- Express: learn Express 5 behavior and migration differences (`https://expressjs.com/en/guide/migrating-5/`).
- TypeScript: TypeScript 7 is current and should be introduced after the JavaScript/React reactivation rather than before the old mental model returns (`https://www.typescriptlang.org/`).
- Vite: modern build-tool option; useful for a lightweight React lab when a framework is not required (`https://vite.dev/`).

### Historical → modern mapping

| 2020-era item | 2026 treatment |
|---|---|
| Create React App / `react-scripts` | read old projects; do not use as default for new work |
| React class components / `setState` | recognize and refactor; primary work uses modern function components/hooks |
| React Router 4/5 | understand old syntax, then learn current Router data/framework APIs |
| Enzyme | legacy recognition only |
| Jest / React Testing Library | retain concepts; use current testing stack chosen per project |
| Webpack 4 handoff | understand bundling; use modern tooling unless project requires Webpack |
| Node 10-era exercises | rebuild against supported Node LTS |
| Express 4 | read old code; new instruction targets Express 5 |
| Heroku scripts | historical deployment literacy; choose deployment target based on current HumanOS need |
| JavaScript only | reactivate first, then add TypeScript gradually |
| simple Bearer API token | expand into sessions, JWT, OAuth 2.0/OIDC, service identities, secure secret handling |

## Skill graph and mastery gates

### WE-01 — Git, GitHub, VS Code, terminal reactivation

**Refresh:** clone/pull/status/diff/add/commit/branch/merge/rebase concepts, `.gitignore`, remotes, recovery, reading history.  
**HumanOS lab:** inspect a real HumanOS branch, explain the diff, make a reversible documentation change on a bounded branch when needed.  
**Failure drill:** detached/dirty state, merge conflict, accidental staged file, wrong branch.  
**Gate:** can diagnose repository state before changing it and explain rollback.

### WE-02 — JavaScript + DOM + jQuery bridge

**Refresh:** functions, scope, arrays/objects, callbacks, events, forms, DOM, event delegation; read the old jQuery code without making jQuery a 2026 specialization.  
**Historical lab:** `shopping-list` and `fun-quiz-app`.  
**HumanOS link:** browser-extension/service-worker and browser-boundary JavaScript when relevant.  
**Failure drill:** wrong selector, event target/currentTarget confusion, stale/missing DOM node.

### WE-03 — npm, package manifests, modules and build tooling

**Refresh:** Node vs npm, `package.json`, `package-lock.json`, dependencies/devDependencies, scripts, semver, `node_modules`, module imports, build/dev/test commands.  
**Historical lab:** `bookmarks-app`, `noteful`.  
**Modern extension:** supported Node LTS, Vite/framework tooling, lockfile integrity and dependency risk.  
**Failure drill:** incompatible dependency, missing script, wrong Node version, vulnerable/stale package.

### WE-04 — React mental model

**Refresh:** JSX, components, props, state, render cycle, controlled forms, composition, function components, hooks, state ownership.  
**Historical lab:** `laptop-customizer`, `noteful`.  
**Depth questions:** why rendering occurs, stale closures/state, effect dependencies, where state belongs.  
**Failure drill:** infinite effect/render loop, stale state, invalid update, loading/error state.

### WE-05 — Routing and application state

**Refresh:** BrowserRouter, routes, dynamic params, links/navigation, nested UI, URL as state.  
**Historical lab:** `william-setstatespear`, `noteful`.  
**Modern extension:** current React Router patterns, loaders/actions/error boundaries where appropriate.  
**Failure drill:** invalid route/param, aborted navigation, 404, data-loader failure.

### WE-06 — HTTP, APIs and failure handling

**Refresh deeply:** request/response lifecycle, methods, headers, JSON, status codes, fetch/async/await, timeouts, network vs server vs application failure, idempotency, retries/backoff.  
**Historical lab:** `dog-api-1`, `moviedex-api`, `pokedex-api`.  
**HumanOS lab:** real connector/API contract or browser-bridge failure path when a current slice requires it.  
**Gate:** can distinguish no-response/network failure, 401, 403, 404, 409, 429, and 5xx and choose an appropriate recovery policy.

### WE-07 — Node + Express backend architecture

**Refresh deeply:** Node runtime, Express app/server split, route handlers, middleware ordering, environment configuration, CORS, security headers, logging, error middleware, service boundaries.  
**Historical lab:** `express-boilerplate`, `bookmarks-server`, `noteful-api`.  
**Modern extension:** Express 5 async/error semantics.  
**Failure drill:** thrown async error, malformed input, missing env var, middleware order bug, server restart.

### WE-08 — Testing and debugging

**Refresh:** assertions, unit vs integration vs end-to-end, Jest/React Testing Library concepts, Mocha/Chai/Supertest, mocks only when justified.  
**Legacy recognition:** Enzyme.  
**HumanOS standard:** normal path + failures + restart/recovery + duplication/idempotency + security + regression.  
**Gate:** a green test suite is not enough; explain what failure class each test protects against.

### WE-09 — SQL, PostgreSQL and persistence

**Refresh deeply:** relational model, primary/foreign keys, CRUD, joins, constraints, transactions, indexes, migrations, query boundaries, Knex/history vs modern options.  
**Historical lab:** `noteful-api` migrations and router/service split.  
**HumanOS link:** only touch canonical HumanOS storage when a real approved slice needs it; otherwise use synthetic/local lab data.  
**Failure drill:** migration failure, duplicate record, broken constraint, transaction rollback, connection failure.

### WE-10 — Authentication, authorization and identity

**Priority repair module.**  
**Start conceptually:** identity → authentication → session/credential → authorization → protected resource.  
**Refresh:** Bearer headers, 401 vs 403, API keys/tokens.  
**Deep rebuild:** password hashing, sessions/cookies, access tokens, JWT structure/signature/claims/expiration, refresh/revocation, secure storage, CSRF/XSS, service identities, OAuth 2.0 and OpenID Connect.  
**Failure drill:** expired access token, failed refresh, revoked credential, offline client, 401 loop, 403 permission denial, server failure.  
**Security rule:** use synthetic credentials in training; never expose real secrets.

### WE-11 — Full-stack integration and reliability

Trace and explain one request end-to-end:

`UI → router/state → HTTP → server route → middleware/auth → service → database/external API → response → UI state`

Then test the same path under network loss, expired auth, invalid input, dependency outage, duplicate submission and restart.

**HumanOS application:** implement this only when a real HumanOS control-room/UI/API need is selected as the active slice.

### WE-12 — DSA, Big-O and problem solving

Teach after the application stack is stable—not concurrently with an unfinished backend capstone.  
Topics: Big-O intuition, recursion, arrays/lists, stacks/queues, maps/sets, trees, search/sort, practical tradeoffs.  
**HumanOS link:** analyze an actual algorithm/data-flow bottleneck where possible; otherwise use bounded exercises.

### WE-13 — Modern engineering extension

Introduce only after reactivation gates justify it:

- TypeScript
- modern React/Router patterns
- Vite or an appropriate React framework
- CI/CD and GitHub Actions
- containers/Docker
- cloud/runtime deployment
- webhooks and event-driven design
- queues/background work
- observability: logs, metrics, traces, alerts
- secrets/configuration management
- n8n/Make and workflow automation
- LLM APIs, structured output, tool calling, agents and AI failure modes

This module overlaps intentionally with **AI Systems Engineering & HumanOS** and should reuse evidence rather than duplicate it.

## Current practical sequencing

Historical diagnostics may run at any time without opening a second implementation project. New production-facing React/Node/DB/auth work must wait until it is useful to the selected HumanOS implementation slice.

Recommended reactivation order:

`Git/GitHub → JavaScript/jQuery bridge → npm/tooling → React → Router → HTTP/failure handling → Node/Express → testing → PostgreSQL → auth/JWT → full-stack reliability → DSA → modern extension`

## Session 1 — Noteful diagnostic

Use `jhalicea/noteful` read-only as the initial diagnostic.

1. Oral recall: npm, package.json, JSX, component, prop, state, BrowserRouter, Route, dynamic `:id`, Link.
2. Trace `index.js → <BrowserRouter> → <App> → <Main> → <Route> → component`.
3. Explain what `npm start` actually resolves from `package.json`.
4. Identify class-era code vs modern function/hook code.
5. Run/inspect only in a safe local copy; do not modernize the original historical repo during the diagnostic.
6. Intentionally diagnose one dependency/tooling failure rather than hiding it.
7. Grade Knowledge / Practical / Diagnostic / Communication separately.
8. Record one next action.

## Provenance summary

Primary historical evidence is Jon's GitHub repository set created during the 2020–early-2021 Thinkful period. The strongest authored-code evidence inspected includes:

- `jhalicea/shopping-list`
- `jhalicea/fun-quiz-app`
- `jhalicea/dog-api-1`
- `jhalicea/bookmarks-app`
- `jhalicea/laptop-customizer`
- `jhalicea/noteful`
- `jhalicea/noteful-client`
- `jhalicea/moviedex-api`
- `jhalicea/pokedex-api`
- `jhalicea/express-boilerplate`
- `jhalicea/bookmarks-server`
- `jhalicea/noteful-api`
- `jhalicea/jhalicea.com`

Course-stage/shell evidence includes `github-candidates-information`, `national-parks-api`, `plant-vault`, and `DSA-Recursion`.

User recollection is valuable provenance but remains distinct from repository-verified evidence. In particular, the JWT lesson and Plant Vault product concept are preserved as user-reported history unless/until additional source artifacts are recovered.

## Done criteria for the reactivation track

The track is not done when the old syllabus has been reread. It is done when Jon can, with decreasing assistance:

- inspect and safely change a real repository;
- explain frontend/server/database/auth boundaries;
- build and debug a modern client/API flow;
- design explicit failure/recovery behavior;
- write meaningful automated tests;
- reason about authorization and token/session lifecycle;
- make and migrate a relational data model;
- explain the architecture to another engineer;
- transfer these skills into unfamiliar HumanOS work.

Historical familiarity may accelerate the path, but only present evidence can produce `DEMONSTRATED` or `MASTERED` status.
