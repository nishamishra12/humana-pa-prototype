"""Ingestion: packet PDF -> page-cited text elements.

Uses the Unstructured Transform API when UNSTRUCTURED_API_KEY is set; otherwise falls
back to local pdftotext so the demo always runs. Both return the same shape.
"""
import os, subprocess
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Element:
    page: int
    type: str
    text: str


def _ingest_unstructured(path: str) -> list[Element]:
    from unstructured_transform_client import TransformClient
    client = TransformClient(api_key=os.environ["UNSTRUCTURED_API_KEY"],
                             server_url="https://transform.unstructured.io")
    with open(path, "rb") as f:
        res = client.parse.run(input=f, output="elements")
    return [Element(page=e.metadata.page_number or 1, type=e.type, text=e.text)
            for e in res.elements if e.text and e.text.strip()]


def _ingest_local(path: str) -> list[Element]:
    out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True,
                         text=True, check=True).stdout
    out = out.replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    elems = []
    for i, page in enumerate(out.split("\f"), start=1):
        for para in [p.strip() for p in page.split("\n\n") if p.strip()]:
            elems.append(Element(page=i, type="NarrativeText", text=para))
    return elems


def ingest(path: str) -> tuple[list[Element], str]:
    """Returns (elements, engine) where engine is 'unstructured' or 'local'."""
    if os.getenv("UNSTRUCTURED_API_KEY"):
        try:
            return _ingest_unstructured(path), "unstructured"
        except Exception as e:  # network/quota: degrade, never hard-fail the demo
            print(f"[ingest] unstructured failed ({type(e).__name__}: {str(e)[:120]}); using local")
    return _ingest_local(path), "local"


if __name__ == "__main__":
    import sys, json
    els, engine = ingest(sys.argv[1])
    print("engine:", engine, "| elements:", len(els))
    print(json.dumps([asdict(e) for e in els[:6]], indent=1)[:1500])
