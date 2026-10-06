# Content for the two HLD slides

Flow 1: CMS data into the database, then suggestions to the policy owner.
Flow 2: a selected policy becomes approved rules and key facts.

---

## Label changes
- Billing codes box subtitle: "most articles it is found in" (was "most agreed first").
- Unstructured detail box: "Uses a partitioner to parse the document and extract elements: title, text, page number. Output is JSON."
- Validator box subtitle: "text matching and rule checks" (was "plain code, no AI").

---

## API endpoints

### Flow 1: data in, then suggestions
Outside calls, made by the weekly job (`scripts/refresh_cms_index.py`). Base: `https://api.coverage.cms.gov/v1`

| Call | What for |
|---|---|
| `GET /metadata/license-agreement` | Get the short-lived token |
| `GET /reports/local-coverage-articles/` | List every article |
| `GET /data/article/hcpc-code/?articleid=&ver=` | The billing codes on one article |
| `GET /reports/national-coverage-ncd/` | List every NCD |
| `GET /reports/local-coverage-final-lcds/` | List every LCD |
| `GET /data/ncd/?ncdid=&ncdver=` | One NCD's coverage text |
| `GET /data/lcd/?lcdid=&ver=` | One LCD's coverage text |

App endpoints, called by the owner screens (`app/policy_admin.py`). Prefix: `/api/policies`

| Endpoint | What for |
|---|---|
| `POST /services` | Create the service: name, one-sentence scope |
| `GET /services/{key}` | Open a service: codes, policies, key facts, activity |
| `GET /services/{key}/code-suggestions` | Articles that match the service name |
| `GET /services/{key}/code-consensus` | Billing codes, ranked by how many articles list them |
| `GET /services/{key}/code-article` | The codes on one chosen article |
| `POST /services/{key}/codes/from-cms` | Save the ticked codes, each with its CMS article as source |
| `POST /services/{key}/codes` | Add a code CMS did not list, with a typed source |
| `GET /services/{key}/suggestions` | Policies that match: library first, then CMS |
| `POST /services/{key}/policies` | Add an approved policy to the service |

### Flow 2: build, validate, approve
Outside calls:

| Call | What for |
|---|---|
| CMS Coverage API (`/data/ncd`, `/data/lcd`) or eCFR | Fetch the full policy text |
| Unstructured Transform API (`parse.run`, output = elements) | Read the document into JSON elements |
| Anthropic Messages API (`messages.create`, forced tool `record_policy`) | Claude Sonnet drafts rules and key facts |

App endpoints. Prefix: `/api/policies`

| Endpoint | What for |
|---|---|
| `POST /builds` | Start a build: type (NCD, LCD, CFR), id, service |
| `POST /builds/upload` | Start a build from a policy PDF |
| `GET /builds/{id}` | Poll progress, then read the draft with its checks |
| `POST /builds/{id}/criteria/{cid}` | Approve, reject or edit one rule |
| `POST /builds/{id}/publish` | Approve for the service. Saves rules and key facts as a new library version |
| `GET /audit` | Every action, and the version list |
| `POST /revert` | Go back to an earlier library version |
| `POST /{policy_id}/check-update` | Has the CMS source changed since the saved copy |

---

## Talking points: Flow 1
1. **Fetch.** A weekly job calls the CMS Coverage API for three things: the billing articles, the codes on each article, and the national and local policies.
2. **Save.** It saves them in our database. It compares versions and only fetches what is new or changed, so a weekly run is small.
3. **Why a database.** The owner never waits on the CMS website, and it works if CMS is down. We can also ask which articles list a code.
4. **The owner creates a service.** A name and one sentence on what it covers.
5. **Billing codes.** The app matches the service name to article titles and reads their codes from the database. We rank each code by how many articles it is found in. The owner ticks the ones to use, and each keeps its CMS article as its source.
6. **Policies.** The app suggests policies that match the service, from our library first and then from CMS. If a policy is already approved, the owner adds it in one click. Nothing is read or reviewed again.
7. **A new policy** goes to the build flow.

---

## Talking points: Flow 2

### The partitioner (Unstructured)
Unstructured uses a partitioner to parse the document. It extracts elements: the title, the text, the page number. It gives the output as JSON. We keep that structure, because a rule hangs on a section, and flat text would lose it. A real element looks like this:
```json
{ "type": "Title", "text": "NCD 30.3.3: Acupuncture for Chronic Lower Back Pain (cLBP)", "page": 1, "id": "e1" }
```

### The LLM (Claude Sonnet) and its prompt
The model gets a system prompt with 10 rules, the policy's elements, and a list of key facts we already know. It must answer through a fixed form, so the output is always structured. The rules, in plain words:
1. One condition, one key fact. Split compound rules.
2. Copy the exact sentence the rule comes from.
3. Use an existing key fact. If none fits, propose a new one.
4. Choose the test: at least, at most, one of, must be none, must be documented.
5. Any number in a test must appear in the quote.
6. If a rule applies to a subgroup, say which.
7. If a rule can't be modelled, list it and say why. A person decides.
8. For each rule, write the question to ask the provider if the fact is missing.
9. Give the section it came from.
10. Say how confident you are: high, medium or low.

Example of what goes in:
```
Policy: Acupuncture for Chronic Lower Back Pain (NCD-30.3.3)
KNOWN KEY FACTS
- clbp_duration_weeks (number): How many weeks has the patient's low back pain lasted?
POLICY TEXT
[e5] (NarrativeText) ... chronic low back pain lasting 12 weeks or longer ...
```
Example of what comes out:
```json
{ "id": "CLBP-DURATION",
  "text": "Chronic LBP must have lasted 12 weeks or longer.",
  "source_quote": "Lasting 12 weeks or longer",
  "required_fact": "clbp_duration_weeks",
  "test": { "type": "gte", "value": 12 },
  "if_missing": "How long has the patient's low back pain lasted (in weeks)?",
  "confidence": "high" }
```

### The validator
It is code with real algorithms: text matching and rule checks. It never trusts the model's quote. It re-finds it.

How the quote check works:
1. **Normalise both texts.** Lowercase, straighten curly quotes and dashes, rejoin words split across a line break, collapse spaces. Keep a map from each character back to the original text.
2. **Exact search.** Look for the quote in every page of the policy. If found, record the page and the exact span in the original.
3. **Fuzzy search, only if exact fails.** Slide the quote along the page and score the similarity. It needs at least 88 out of 100.
4. **A fuzzy match must carry the same numbers.** If the numbers differ, it is a different rule, so it is rejected.
5. **A quote with "..." in it** is accepted only if every piece is found.
6. **Not found means fail.** The rule is marked as failed and shown to the owner. It is never silently dropped.

The other checks:
- **Every number in the test must appear in the quote.** A threshold the policy never stated is rejected. A fraction written as a percent is flagged.
- **The key fact must exist,** or be declared as new.
- **"One of" tests may only use values the key fact can take.**
- **Coverage scan.** It looks for sentences that sound like requirements ("must", "at least", "within 30 days") that no rule and no note covers, and lists them as possible misses.
- **Low confidence** from the model is flagged for a closer look.

Each rule comes out as pass, check or fail.

In Part 2 the same matching runs on the nurse's packet. There, a second model also reads the quote in its page and judges whether it truly supports the fact. That is the semantic check.

### What a key fact is, and why it matters
A key fact is one thing a nurse must find in a packet to apply a rule. For a heart device, for example: the ejection fraction, how long the patient has been on medicine, whether a shared decision visit happened.

Each key fact has:
- a name and a type: a number, a choice, a list or text,
- the exact policy sentence behind it,
- the question to ask the provider if the packet doesn't have it.

Why it matters:
- **It makes a long policy checkable.** Thirty pages become a short list of facts.
- **It tells the AI reader exactly what to look for** in every packet, and nothing more.
- **It gives the nurse the question to send** when something is missing, so the provider gets one precise question.
- **It ties every check to the policy's own words,** which is the audit trail.

### Owner review and which key facts count
The owner sees each rule with its exact quote, its key fact and the question. They approve, edit or reject each rule.
- **Only approved rules are checked.** A rejected rule is never checked.
- **A key fact is kept only if an approved rule needs it.** If the owner rejects the only rule that uses a key fact, that key fact is not checked and not asked for.
- Today the choice is made at the rule level. There is no separate required or not-required switch on a key fact.
