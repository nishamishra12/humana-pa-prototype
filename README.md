# Prior Authorization Decision Support

Humana take-home, Use Case 1: Utilization Management.

- `docs/ARCHITECTURE.md` — the production system design
- `docs/NOTES.md` — decision log and research
- `prototype/pa-console.html` — interactive demo (open directly in a browser)
- `deck/Humana_PA_Deck.pptx` — presentation

## Run the prototype

```
pip install fastapi "uvicorn[standard]" python-multipart python-dotenv fpdf2 unstructured-transform-client httpx
python scripts/make_packets.py
python -m uvicorn app.main:app --port 8000
```

Open http://localhost:8000 and pick a demo account on the sign-in screen (password `demo1234`).
Optional: put `UNSTRUCTURED_API_KEY` in a local `.env` (never commit it). Without it, ingestion
falls back to local `pdftotext`. All data is made up.
