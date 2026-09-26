from .ingest import _ingest_local, ingest
from .extract import extract_facts
from .engine import analyze


def process(path, local=False):
    elements, engine = (_ingest_local(path), "local") if local else ingest(path)
    facts = extract_facts(elements)
    return elements, engine, facts, analyze(facts)
