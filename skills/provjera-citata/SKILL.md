---
name: provjera-citata
description: Provjera citata crnogorskih propisa i sudskih odluka u podnesku, mišljenju ili nacrtu, na korpusu kodeks.me — da li citirani član zaista tako glasi u verziji koja važi na dan, i da li presuda sadrži citirane riječi. Use when a lawyer asks to check, verify or proofread the legal quotations or article references in a text.
---

# Provjera citata uz kodeks.me

You check every quotation of Montenegrin legislation and court decisions in a text the lawyer gives you (a submission, an opinion, a draft), against kodeks.me. Answer in Montenegrin.

You need the kodeks tools (`check_quotes`, `get_law`, `search_legislation`, `search_case_law`, `get_judgment`). If they are missing, tell the lawyer to add the connector (address `https://kodeks.me/mcp`) and stop.

## Steps

1. **Read the text.** For an attached Word or PDF file you may use `../pravno-misljenje/scripts/extract_text.py --out work <file>` and read `work/documents.json`.
2. **Find every legal quotation**: words in quotation marks attributed to an act and article, or to a court decision. Also note article references without a quotation.
3. **Identify each source.** For legislation you need the act's full title as kodeks.me knows it (use `search_legislation` when the text uses a short name or abbreviation), the article, and the date on which the quoted version must apply (the date of the event, or the date of the submission when the text speaks of the law in force). For a judgment you need its kodeks.me id: find it with `search_case_law` by court, number and date, using only legal terms and the case number, never the parties' names.
4. **Check** with `check_quotes`, at most 30 quotations per call, each with exactly the words of the text.
5. **For every quotation that is not found**, load the source (`get_law` for the article on that date, `get_judgment`) and show the lawyer the correct wording, or explain that the article was amended, renumbered or not in force on that date.
6. **For article references without a quotation**, load the article on the relevant date and say whether it says what the text claims.

## The answer

A table, one row per quotation: where it is in the text, the source (act, article, date or the decision), the result (potvrđeno / ne poklapa se / izvor nije pronađen / tekst čeka reviziju) and, where it does not match, the correct wording. Then the article references that do not support what the text claims. End with one line on what was checked (the wording of legal quotations on kodeks.me) and what was not (the legal reasoning and facts).

Never send the parties' names or other details of the case to kodeks.me: only legal text and legal terms.
