import os
from .ingest import _ingest_local, ingest
from .extract import extract_facts as extract_facts_rule_based
from .engine import analyze


def extract(elements, local=False):
    """Uses the LLM extractor when ANTHROPIC_API_KEY is set and local isn't forced; falls back
    to the rule-based extractor on any failure so the pipeline never hard-fails on this step."""
    if not local and os.getenv("ANTHROPIC_API_KEY"):
        try:
            from .extract_llm import extract_facts as extract_facts_llm
            return extract_facts_llm(elements)
        except Exception as e:
            print(f"[extract] LLM extraction failed ({type(e).__name__}: {str(e)[:150]}); using rule-based")
    return extract_facts_rule_based(elements)


def process(path, local=False, progress=None):
    """progress, if given, is called as progress(stage, **info) at the start of each stage:
    reading, facts, policy. The upload screen polls these to show what is happening."""
    say = progress or (lambda *a, **k: None)
    say("reading")
    elements, engine = (_ingest_local(path), "local") if local else ingest(path)
    say("facts", pages=len({e.page for e in elements}))
    facts = extract(elements, local=local)
    say("policy")
    return elements, engine, facts, analyze(facts)
