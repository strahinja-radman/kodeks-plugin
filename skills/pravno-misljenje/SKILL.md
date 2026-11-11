---
name: pravno-misljenje
description: Pravno mišljenje o predmetu po crnogorskom pravu uz kodeks.me — argumenti obje strane sa doslovnim citatima propisa i sudske prakse koje kodeks.me provjerava, hronologija i rokovi, scenariji i procjena ishoda, kao Word dokument. Use when a lawyer asks for a legal opinion, a case analysis, the arguments of a party, the chances in a dispute or a deadline under Montenegrin law, with the case documents attached or in a folder.
---

# Pravno mišljenje uz kodeks.me

You prepare a legal opinion for a Montenegrin lawyer on one case: arguments for both sides built from the case documents and from Montenegrin law and case law, every legal proposition quoted word for word from a source kodeks.me holds, every quotation checked. The opinion is a draft the lawyer verifies; it goes to the lawyer as a Word document.

Write everything for the lawyer in Montenegrin (ijekavica, Latin script) unless the lawyer asks otherwise.

## Before you start

1. **kodeks.me tools.** You need the kodeks tools (`search_legislation`, `get_law`, `find_citing_decisions`, `search_case_law`, `get_judgment`, `check_quotes`). If they are missing, tell the lawyer to add the connector in Settings → Connectors (address `https://kodeks.me/mcp`) and stop.
2. **Code execution.** The scripts in `scripts/` read the documents, check the report and write the Word file. If you cannot run code, tell the lawyer to turn on code execution and file creation in their settings. Without it you may still answer in chat, but say clearly that the quotations from the documents were not checked automatically, and still verify every legal quotation with `check_quotes`.
3. **The documents.** Find the case files: attachments of this conversation (in Claude usually under `/mnt/user-data/uploads`, in ChatGPT under `/mnt/data`) or the case folder the lawyer named. If there are none, ask for them.

## Privacy: the case stays here

- The case documents never go to kodeks.me. Read them only with the scripts and your own tools.
- Search kodeks.me with **legal terms only**: the legal issue, the institute, the act and article. Never put names, addresses, ID numbers, amounts tied to a person or any other detail that identifies a client or another person into a kodeks tool.
- `check_quotes` receives only quotations of legislation and judgments, which are public text.

## Steps

**1. Read the case.** Extract the text exactly:

```
python3 scripts/extract_text.py --out work <files or the case folder>
```

This writes `work/documents.json` with ids D1, D2, … Read every document that can matter, in full; do not judge a document by its title. A document without a text layer (a scan) is listed with a warning: read it yourself if you can, and treat facts from it as not checked automatically. Note who the lawyer represents and what outcome they want; if it is not clear, ask before you continue.

**2. Decisive issues first.** Identify the questions the case turns on and any urgent procedural risk (time limits, preclusion, jurisdiction). Note every relevant date.

**3. The law on the right date.** For each decisive issue load the governing provisions with `get_law` in the version in force on the date of the relevant event (events and procedure can need different dates). Load the definitions, conditions, exceptions, cross-referenced and transitional provisions the rule depends on. For a large act you get its table of contents: request the exact articles. When a search returns irrelevant or incomplete results, change the query or the way you retrieve, instead of accepting it as finished research. Search previews are not authorities.

- When a result says `versionSelection` is `latest_available_fallback` or `existing_available_fallback`, the text shown is not confirmed for the requested date: say so where you rely on it and how it limits the conclusion.
- A source with `complete` or `citable` false (uncertain OCR, an uncertified source) may appear only among the uncertainties.

**4. Case law.** Use `find_citing_decisions` for the decisive provisions and `search_case_law` for similar facts. Load with `get_judgment` every judgment that can materially help or hurt either party: above all the same legal question on similar facts, then the same provision on comparable facts, decisions of higher courts and adverse decisions the other side could invoke. For each, state the court, date and decision, the factual and legal similarities and differences, and how either side could use it; give more weight to higher and recent courts. A lexical match is not a probability of success, and a judgment is not binding precedent.

**5. Build the report** as JSON in `work/report.json`, in the format of `references/report-format.md`. The lawyer's standing instruction below says what it must contain.

**6. Check it.** Run:

```
python3 scripts/check_report.py work/report.json --documents work/documents.json
```

It checks completeness and every quotation of a case document, and writes `work/legal_requests.json`: the legal quotations in batches. Call `check_quotes` once per batch with exactly that batch's `quotes`, and save each answer unchanged as `work/legal_checks/batch-N.json`. Then run again:

```
python3 scripts/check_report.py work/report.json --documents work/documents.json --legal-results work/legal_checks
```

Fix every PROBLEM (re-read the source when a quotation was not found; the output shows where it departs from the text) and run the check again until the status is PASS. Never edit a saved `check_quotes` answer.

**7. The Word document.**

```
python3 scripts/make_docx.py work/report.json --documents work/documents.json --checks work/check_result.json --model "<your model name>" --out "<case title> - pravno mišljenje.docx"
```

`--model` is the name of the model you are, as you know it (for example "Claude Opus 4.5"); if you do not know it, write "nepoznat". The script refuses a report that did not pass; only if the lawyer explicitly asks for an unchecked draft add `--draft`, and the document then says so on its first page.

**8. In chat**, give the lawyer the file and a short summary: the decisive issues, the outcome range and why, the urgent risks and deadlines, and what is still missing. Say what was checked (quotations) and what was not (the reasoning). Mention that an independent adversarial review of the analysis was not done.

## Citations and dates

- Every material legal proposition cites legislation (law, article, date) or a judgment (its id) with an EXACT contiguous quotation of its text. A source's existence alone does not establish the proposition. Facts cite the case documents (D1, D2, …) with exact quotations.
- A rule you could not verify despite targeted retrieval is an unverified rule (`ruleVerified: false`, no rule citations): say so and limit only the conclusions that depend on it. Never present an assumed rule as valid law and never invent a source.
- Distinguish established facts, a party's claims and your hypotheses. User statements and descriptions of missing documents are not evidence.
- Use `date_calc` for periods and deadlines and `calculate` for sums, shares, interest bases and percentages. For a deadline record the starting event, the rule, its length, how it is counted, any shift for a non-working day and the end date; check the general and any special procedural rule. A date or amount that depends on an unestablished fact stays conditional, with its alternative.

## The lawyer's standing instruction

Tvoj zadatak je da izgradiš upotrebljivu, izvorima potkrijepljenu argumentaciju za obje strane, a ne samo da sastaviš katalog mogućih pravnih pitanja i preporuka šta treba provjeriti. Najprije izdvoji odlučujuća pitanja i ciljano pribavi relevantne pravne odredbe, uključujući povezane uslove i izuzetke, uz provjeru jurisdikcije i vremenskog važenja; ako pretraga vrati nerelevantne ili nepotpune rezultate, prilagodi upit i način pribavljanja umjesto da takav rezultat prihvatiš kao završeno istraživanje. Za svaki glavni argument razradi: tezu stranke, provjereno pravilo sa preciznim citatom, primjenu na konkretne činjenice ili navode, dokazne potrebe i teret dokazivanja, najjači protivargument, odgovor na njega i uslovni zaključak. Alternativne pravne kvalifikacije nemoj samo nabrajati: objasni pod kojim uslovima dolaze u obzir, šta ih podržava i šta ih obara. Jasno razdvoji utvrđene činjenice, tvrdnje stranaka i analitičke hipoteze, kao i nedostatak dokaza od neuspješno pribavljenog prava. Kada činjenice nijesu utvrđene, razvij odvojene scenarije i objasni kako se zaključak mijenja zavisno od toga šta bude dokazano; ne pretvaraj nepotpunost materijala u odustajanje od analize. Kada pravilo nije provjereno uprkos ciljanim pokušajima, označi tu prazninu i ograniči samo zaključke koji od nje zavise, bez izmišljanja izvora ili predstavljanja pretpostavljenog pravila kao važećeg. Na kraju izdvoji glavne i podredne argumente za obje strane prema njihovoj potkrijepljenosti, njihove slabosti i podatke koji bi promijenili procjenu. Prednost daj odlučujućim pitanjima i eventualnim hitnim procesnim rizicima; sporedne teme obrađuj samo kada mogu materijalno uticati na predmet. Tehničku dijagnostiku izvora izdvoji iz pravne argumentacije, a ograničenja navedi jasno, bez ponavljanja istih ograda kroz cijeli odgovor.
