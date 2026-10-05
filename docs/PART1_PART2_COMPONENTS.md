# Part 1 and Part 2: components and code files

For drawing the two Excalidraw diagrams. Each box below is a component, with the file that holds it. Arrows are listed under "Flow".

Part 1 builds the policy library, once per service, before go-live. Part 2 runs on every packet, using that library.

---

## Part 1: build the policy library (the policy owner)

### Flow
1. Owner describes a **service** (name, one-sentence scope).
2. Owner picks **billing codes** from a stored copy of CMS articles. Each code keeps its CMS article as its source.
3. Owner finds a **policy**: from the library, or from CMS by service name.
4. System **builds the policy**: fetch, read, AI draft, automatic checks, compare with the live version.
5. Owner **reviews every rule** beside its exact quote: approve, reject or edit.
6. Owner **approves for the service**. Key facts are saved on the policy. The service shows the combined list.
7. Service goes **pilot**, then **live**. Every change is a saved, revertible library version.

### Components

| Component | What it does | File |
|---|---|---|
| Owner screens | Services list, step-by-step setup (Describe, Billing codes, Policies, Key facts, Go live), draft review with quotes, Policies, Version history, Requests without a policy | `web/policy.js`, `web/app.js` (shell, sign-in, nav), `web/style.css` |
| Owner API | Services, codes, policy suggestions, builds, rule decisions, approve, status changes, revert, audit, check for CMS changes | `app/policy_admin.py` |
| CMS API client | Gets the token, calls the Coverage API, fetches NCD, LCD and CFR text, hashes the source | `pipeline/policy_build/sources.py` |
| Stored CMS copy | Billing articles and their codes in the database. The screens read only this | `pipeline/policy_build/cms_index.py`, tables `cms_articles`, `cms_article_codes`, `cms_meta` |
| Refresh job | Copies the CMS articles and codes into the database. Run on a schedule | `scripts/refresh_cms_index.py` |
| Code matching | Matches a service name to articles by word stems, reads an article's codes, ranks by how many articles agree | `pipeline/policy_build/codes.py` |
| Policy lists | NCD and LCD titles kept for policy suggestions | `policies/corpus/*.json`, built by `scripts/build_corpus.py` |
| Build pipeline | Runs fetch, parse, draft, check, compare for one policy and saves it | `pipeline/policy_build/build.py` |
| Read the policy | Turns the source into page-cited elements (Unstructured) | `pipeline/policy_build/parse.py` |
| AI draft | Claude writes rules and key facts through a fixed form, each with its exact quote | `pipeline/policy_build/draft.py` |
| Automatic checks | Plain code checks every quote and number against the source. No AI | `pipeline/policy_build/validate.py` |
| Compare | Compares a draft with the live rules | `pipeline/policy_build/compare.py` |
| Policy library | Services, policies, rules, key facts. Key facts live on the policy and are merged into each service when loaded | `pipeline/procedures.py`, `policies/policy_library.json`, live copy `app/policy_library.live.json` |
| Versions | Snapshot of every saved library version, for revert | `library_versions/` on the data disk |
| Build files | Elements, draft, report and codes for each build | `policies/work/<policy>/<version>/` |
| Audit | Every build, decision, approval and revert | table `policy_audit`; tables `policy_builds`, `policy_decisions`, `policy_versions` |
| Telemetry | Build and approval events | `pipeline/telemetry.py` |

### Outside Part 1
- CMS Coverage API (articles, codes, NCD and LCD text)
- eCFR API (federal regulations)
- Unstructured API (reads the policy)
- Anthropic API (the AI draft)

---

## Part 2: decide each packet (intake, nurse, medical director)

### Flow
1. **Intake coordinator** uploads or receives the packet and assigns a nurse.
2. System **reads the packet**: pages become text elements with page numbers.
3. System **finds the billing code** and the **service** that owns it. No service means "no policy" and the request is listed for the policy owner.
4. **AI reader** finds the service's key facts. Three reads must agree. A disagreement is "unsure".
5. **Evidence**: each fact keeps its page and exact quote. A second AI check confirms the quote means what the fact says.
6. **Rules engine** checks the facts against the service's rules. Missing means pend, unsure means verify, a rule not met means escalate, all met means approve. It never denies.
7. **Nurse** reviews the evidence and confirms: approve, send one question to the provider (pend), or escalate.
8. **Medical director** decides escalated cases. Only this role can deny, and must give a reason.
9. Every action is written to the audit trail and the live dashboard.

### Components

| Component | What it does | File |
|---|---|---|
| Case screens | Queue, assign, review with facts and evidence beside the packet, pend, escalate, decide, chat | `web/app.js`, `web/style.css`, `web/index.html` |
| Case API | Upload, assign, comments, actions, addendum from the provider, check again, correct a fact, notifications, sign-in and roles | `app/main.py` |
| Read the packet | PDF to page-cited elements (Unstructured, or a local fallback) | `pipeline/ingest.py` |
| Orchestrator | Runs read, extract, analyze for one packet | `pipeline/run.py` (`process`) |
| Billing code and service | Finds the procedure code in the packet text and looks up the service that owns it | `pipeline/extract.py`, `pipeline/procedures.py` (`procedure_for_cpt`) |
| AI reader | Builds its form from the service's key facts, reads the packet three times, keeps only what agrees | `pipeline/extract_llm.py` |
| Dates | Counts days and midnights in code. The AI only reads the dates | `pipeline/dates.py` |
| Evidence | Finds each quote on its page, and runs a second AI check on meaning | `pipeline/evidence.py` |
| Rules engine | Plain code. Checks facts against rules and picks the next action | `pipeline/engine.py` (`analyze`) |
| Policy library | The same library Part 1 publishes. The engine reloads it on every new version | `pipeline/procedures.py`, `app/policy_admin.py` (`_write_live`) |
| Policy lookup (not connected) | A bounded lookup for a code no service owns. It is built but not wired in. Today the product shows "no policy" and lists the request for the policy owner | `pipeline/policy_retrieval.py` |
| Case data | Cases, page elements, comments, audit, notifications, users, sessions | `app/db.py` (tables `cases`, `elements`, `comments`, `audit`, `notifications`, `users`, `sessions`) |
| Dashboard | Live numbers for intake and medical directors, updated every 4 seconds | `app/dashboard.py`, `web/ops.html`, route `/api/dashboard` |
| Telemetry | Case traces and eval events to Honeycomb | `pipeline/telemetry.py` |

### Outside Part 2
- Unstructured API (reads the packet)
- Anthropic API (the AI reader and the meaning check)
- Honeycomb (traces)

---

## Where the two parts meet
Part 1 writes one thing and Part 2 reads it: the **policy library** (`app/policy_library.live.json` on the data disk). Publishing a new version reloads it in Part 2 without a restart. Cases already decided keep their recommendation. New cases and re-checked cases use the new version.

## People
- Part 1: **Policy owner**
- Part 2: **Intake coordinator**, **UM nurse**, **Medical director**
- Not a role in the product: the **ML team** owns test packets and tuning of the AI reader
