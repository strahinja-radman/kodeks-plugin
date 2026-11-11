# Report format (`work/report.json`)

One JSON object. Write every text in Montenegrin. `check_report.py` checks it; `make_docx.py` turns it into the Word document.

```json
{
  "title": "Naplata zajma — Tužilac (zajmodavac) protiv zajmoprimca",
  "decisiveIssues": ["Da li je zajam dospio prije podnošenja tužbe?"],
  "urgentRisks": ["Rok za odgovor na tužbu ističe 25.03.2024."],
  "timeline": [
    {
      "date": "2024-03-01",
      "time": "",
      "kind": "event",
      "status": "established",
      "title": "Rok za vraćanje zajma",
      "detail": "",
      "party": "",
      "computation": "",
      "ruleVerified": false,
      "ruleCitations": [],
      "factCitations": [{"document": "D2", "quote": "vrati do 1. marta 2024."}]
    }
  ],
  "arguments": [
    {
      "party": "Tužilac (zajmodavac)",
      "rank": "main",
      "support": "strong",
      "issue": "Dospjelost obaveze",
      "thesis": "…",
      "rule": "…",
      "ruleVerified": true,
      "ruleCitations": [{"law": "Zakon o obligacionim odnosima", "article": "269", "date": "2024-03-01", "quote": "…exact words of the article…"}],
      "application": "…",
      "factCitations": [{"document": "D2", "quote": "…exact words of the document…"}],
      "evidence": "Šta treba dokazati i ko snosi teret dokazivanja.",
      "counterargument": "Najjači protivargument.",
      "response": "Odgovor na njega.",
      "conclusion": "Uslovni zaključak.",
      "weaknesses": "Slabosti argumenta."
    }
  ],
  "qualifications": [
    {"qualification": "…", "conditions": "…", "supports": "…", "defeats": "…", "citations": []}
  ],
  "scenarios": [
    {"condition": "Ako se dokaže da …", "outcome": "…", "citations": []}
  ],
  "sections": [
    {"kind": "established_facts", "title": "Ugovor o zajmu", "text": "…", "citations": [{"document": "D2", "quote": "…"}]},
    {"kind": "analysis", "title": "…", "text": "…", "citations": []}
  ],
  "outcomeEstimate": {
    "party": "Tužilac (zajmodavac)",
    "low": 60,
    "high": 75,
    "basis": "Zašto ovaj raspon: odlučujuća pitanja, snaga obje strane, sudska praksa, dokazi, procesni rizici. Profesionalna procjena, ne izračunata vjerovatnoća.",
    "conditions": ["Šta bi podiglo ili spustilo procjenu."]
  },
  "changingFactors": ["Podaci koji bi promijenili procjenu."],
  "sourceDiagnostics": ["Tehnička ograničenja izvora (verzije, nedostajući tekstovi), svako jednom."],
  "uncertainty": ["…"],
  "missingInformation": ["…"]
}
```

## Citations

- **A case document:** `{"document": "D2", "quote": "…"}`, the id from `documents.json`.
- **Legislation:** `{"law": "<full title as kodeks.me returns it>", "article": "269", "date": "YYYY-MM-DD", "quote": "…"}`, one article per citation; the date is the version you loaded and rely on.
- **A judgment:** `{"judgment": "<id from kodeks.me>", "label": "Viši sud u Podgorici, Gž 123/2024 od 12.02.2024.", "quote": "…"}`.

A quotation is a contiguous run of the source's words, copied exactly. Whitespace, letter case and typographic quotes or dashes do not matter; every word, number and punctuation mark does. Quote the shortest passage that states what you rely on.

## Fields

- `arguments`: at least one for each side; two different `party` values. `rank` is `main` or `subsidiary`; `support` is `strong`, `moderate` or `weak`. With `ruleVerified: true` the rule has at least one legal citation; with `false` it has none and `rule` says it could not be verified.
- `sections[].kind`: `established_facts` (each with case-document citations), `allegations`, `assumptions`, `authorities`, `analysis`, `uncertainty`, `missing_information`. Do not repeat the arguments in sections.
- `timeline[].kind`: `event`, `deadline` (with `computation` and, when the rule was loaded, `ruleVerified: true` and its citations) or `action` (a step the client should take by the date). `status`: `established`, `claimed`, `disputed` or `conditional`. `time` is `HH:MM` with its zone, only when the timing matters.
- `outcomeEstimate`: the chances of the lawyer's client to obtain the desired outcome; `low` and `high` are whole percentages 0–100, their width shows the uncertainty.
