import os
from .ingest import _ingest_local, ingest
from .extract import extract_facts as extract_facts_rule_based, extract_header, _fact
from .engine import analyze
from .procedures import procedure_for_cpt, library
from . import telemetry as tel


def _unsure_all(proc_key, header, why):
    """No reader available for this procedure. Say so for every fact, so a person reads the packet."""
    facts = dict(header)
    facts["_extractor"] = "none"
    facts["_procedure_key"] = proc_key
    for d in library()["procedures"][proc_key]["facts"]:
        facts[d["key"]] = _fact("unsure", note=why)
    return facts


def extract(elements, local=False, fast=False):
    """Picks the AI reader when a key is set. The rule-based reader only knows lumbar fusion, so for
    any other procedure with no AI reader every fact is marked 'not sure' instead of guessed.
    fast=True runs one read instead of three (used when a provider reply is added to a case)."""
    full = "\n".join(e.text for e in elements)
    header = extract_header(full)
    proc_key, _ = procedure_for_cpt(header.get("_cpt"))
    if proc_key and not local and os.getenv("ANTHROPIC_API_KEY"):
        try:
            from .extract_llm import extract_facts as extract_facts_llm
            return extract_facts_llm(elements, proc_key, n_votes=1 if fast else 3)
        except Exception as e:
            print(f"[extract] AI reading failed ({type(e).__name__}: {str(e)[:150]})")
            tel.event("extract.failed", error=True, **{"error.type": type(e).__name__})
    if proc_key in (None, "lumbar_fusion"):
        return extract_facts_rule_based(elements)
    return _unsure_all(proc_key, header, "The AI reader was not available for this packet. Read the packet and enter the facts.")


def process(path, local=False, progress=None):
    """progress, if given, is called as progress(stage, **info) at the start of each stage:
    reading, facts, policy. The upload screen polls these to show what is happening."""
    say = progress or (lambda *a, **k: None)
    with tel.span("pa.analyze_packet", **tel.packet_tags()) as root:
        say("reading")
        with tel.span("ingest.read_pages", local=local) as s:
            elements, engine = (_ingest_local(path), "local") if local else ingest(path)
            tel.add(engine=engine, pages=len({e.page for e in elements}), elements=len(elements))
        say("facts", pages=len({e.page for e in elements}))
        with tel.span("extract.facts"):
            facts = extract(elements, local=local)
            tel.add(extractor=facts.get("_extractor"), cpt=facts.get("_cpt"), procedure_key=facts.get("_procedure_key"))
        say("policy")
        with tel.span("rules.analyze"):
            res = analyze(facts)
            tel.add(action=res["action"], criteria=len(res.get("checklist", [])),
                    criteria_met=sum(1 for c in res.get("checklist", []) if c["status"] == "met"),
                    criteria_not_met=sum(1 for c in res.get("checklist", []) if c["status"] == "not_met"),
                    criteria_missing=sum(1 for c in res.get("checklist", []) if c["status"] == "missing"),
                    criteria_unsure=sum(1 for c in res.get("checklist", []) if c["status"] == "unsure"),
                    questions_for_provider=len(res.get("gate", {}).get("questions", [])))
        root.set_attribute("recommendation", res["action"])
        return elements, engine, facts, res
