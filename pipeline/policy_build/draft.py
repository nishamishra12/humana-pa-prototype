"""Step 3 of the policy build: an AI drafts the criteria from the parsed policy, through a fixed form.

This is a program run, not a chat. The model gets the policy elements and a list of facts the packet reader can already find
(the vocabulary), and it must answer by filling the form below. Every rule has to carry the exact source sentence it came from, so
code can check it in the next step. The model never sees the existing hand-written rules, so a comparison against them is fair.

A person approves the result. Nothing here goes live.
"""
import json, os

DRAFT_MODEL = os.getenv("PA_DRAFT_MODEL", "claude-sonnet-5")

TEST_TYPES = ["gte", "lte", "in", "absent", "present", "informational"]

SYSTEM = """You turn one Medicare coverage policy into a checklist of testable criteria for a prior authorization tool.

A criterion is one condition that the policy says must be true (or must be absent) for coverage, in a form a program can check against
one fact found in a clinical packet. Work only from the policy text you are given. Never add a rule from your own medical knowledge.

1. ONE CONDITION, ONE FACT. Split compound rules. "LVEF 35% or less measured by echo" is two criteria: one for the number, one for the method.
2. SOURCE QUOTE. For every criterion, copy word for word the shortest sentence or clause from the policy that states it. It must exist in the text. You may skip words in the middle with "...", but every piece you keep must be copied exactly.
3. FACT. Use a fact key from the vocabulary when one fits. If none fits, propose a new fact in new_facts and use its key. Do not force-fit a rule onto a fact that does not mean the same thing.
4. TEST. gte or lte for a number (give the number). in for a list of allowed values (copy the values the fact can take). absent when the rule is MET only if the packet says there is none: "must not have", "no evidence of", "not within the last 40 days". present when the rule is MET only if the thing is documented: "has at least one comorbidity", "was previously unsuccessful with treatment", "a shared decision making visit occurred". Read the direction of the rule twice before choosing between present and absent. informational for a note or exception that cannot be tested.
5. NUMBERS. Any number in a test must appear in the source quote. Do not infer, round or convert.
6. SUBGROUPS. If a rule applies only to a subgroup ("for non-ischemic patients"), set applies_if to the fact and the value that defines the subgroup.
7. NOT MODELED. If a covered pathway or rule needs facts outside the vocabulary and you are not proposing a new fact, list it in not_modeled with its quote and why. A person decides those cases.
8. IF MISSING. For each criterion write one short plain question the plan would ask the provider if the fact is not in the packet.
9. CITE. Give the section label from the nearest heading, for example "B.3" or "(d)(1)".
10. CONFIDENCE. Say low when the wording is ambiguous or you mapped it to a fact that is a loose fit."""


def _tool(vocab_keys):
    return {
        "name": "record_policy",
        "description": "Record the draft criteria for this policy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "criteria": {"type": "array", "items": {"type": "object", "properties": {
                    "id": {"type": "string", "description": "Short id, like ICD-LVEF."},
                    "text": {"type": "string", "description": "The rule in one plain sentence."},
                    "source_quote": {"type": "string", "description": "Exact words from the policy."},
                    "cite": {"type": "string"},
                    "required_fact": {"type": ["string", "null"], "description": "A key from the vocabulary, or the key of a fact you propose in new_facts, or null for an informational note."},
                    "test": {"type": "object", "properties": {"type": {"type": "string", "enum": TEST_TYPES}, "value": {}}, "required": ["type"]},
                    "applies_if": {"type": ["object", "null"], "properties": {"fact": {"type": "string"}, "equals": {"type": "string"}}},
                    "if_missing": {"type": ["string", "null"]},
                    "short": {"type": "string", "description": "Short phrase for when the criterion is not met."},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]}},
                    "required": ["id", "text", "source_quote", "cite", "required_fact", "test", "if_missing", "short", "confidence"]}},
                "new_facts": {"type": "array", "items": {"type": "object", "properties": {
                    "key": {"type": "string"}, "label": {"type": "string"}, "kind": {"type": "string", "enum": ["number", "enum", "list", "text", "event"]},
                    "ask": {"type": "string", "description": "What the packet reader should look for."},
                    "statuses": {"type": "array", "items": {"type": "string"}}, "values": {"type": "array", "items": {"type": "string"}}},
                    "required": ["key", "label", "kind", "ask"]}},
                "not_modeled": {"type": "array", "items": {"type": "object", "properties": {"quote": {"type": "string"}, "why": {"type": "string"}}, "required": ["quote", "why"]}},
            },
            "required": ["criteria", "new_facts", "not_modeled"],
        },
    }


def _vocab_text(vocab):
    if not vocab:
        return "No facts exist yet for this service. Propose every fact you need in new_facts."
    lines = []
    for d in vocab:
        extra = f" Allowed values: {', '.join(d['values'])}." if d.get("values") else ""
        lines.append(f"- {d['key']} ({d['kind']}): {d['ask']}{extra}")
    return "\n".join(lines)


def draft(elements, meta, vocab, client=None):
    """elements: parsed elements. meta: policy meta (policy_id, title, level). vocab: list of fact definitions. Returns the draft dict."""
    import anthropic
    client = client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    policy_text = "\n".join(f"[{e['id']}] ({e['type']}) {e['text']}" for e in elements)
    user = (f"Policy: {meta['title']} ({meta['policy_id']}), level {meta['level']}.\n\nFACT VOCABULARY\n{_vocab_text(vocab)}\n\nPOLICY TEXT\n{policy_text}")
    last = None
    for attempt in (1, 2):
        resp = client.messages.create(model=DRAFT_MODEL, max_tokens=8000, system=SYSTEM, tools=[_tool([d["key"] for d in vocab])],
                                      tool_choice={"type": "tool", "name": "record_policy"}, messages=[{"role": "user", "content": user}])
        out = next(b for b in resp.content if b.type == "tool_use").input
        try:
            for k in ("criteria", "new_facts", "not_modeled"):
                if isinstance(out.get(k), str):
                    out[k] = json.loads(out[k])
            assert isinstance(out["criteria"], list)
            usage = getattr(resp, "usage", None)
            out["_usage"] = dict(input_tokens=getattr(usage, "input_tokens", None), output_tokens=getattr(usage, "output_tokens", None))
            out["_model"] = DRAFT_MODEL
            return out
        except Exception as e:
            last = e
    raise last
