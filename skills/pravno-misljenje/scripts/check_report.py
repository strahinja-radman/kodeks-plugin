#!/usr/bin/env python3
"""Check a legal opinion before it goes to the lawyer, by the rules
kodeks.me checks its own reports by.

1. Structure and completeness, and every quotation of a case document:

       python3 check_report.py work/report.json --documents work/documents.json

   This also writes work/legal_requests.json: the quotations of legislation
   and judgments in batches of at most 30, exactly as kodeks.me's check_quotes
   tool takes them.

2. Call check_quotes once per batch and save each answer, unchanged, as
   work/legal_checks/batch-N.json (N is the batch number). Then:

       python3 check_report.py work/report.json --documents work/documents.json --legal-results work/legal_checks

The result is printed and saved as work/check_result.json; make_docx.py reads
it. Status pass means: the report is complete, every quotation of a case
document is in that document, and kodeks.me found every quotation of
legislation and judgments in its corpus. It does not check the reasoning.
"""

import argparse
import datetime
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kodeks_common import matched_prefix, quote_found, read_json, write_json  # noqa: E402

RANKS = {"main", "subsidiary"}
SUPPORT = {"strong", "moderate", "weak"}
SECTION_KINDS = ["established_facts", "allegations", "assumptions", "authorities", "analysis", "uncertainty", "missing_information"]
TIMELINE_KINDS = {"event", "deadline", "action"}
TIMELINE_STATUSES = {"established", "claimed", "disputed", "conditional"}
BATCH_SIZE = 30
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def valid_date(value):
    if not isinstance(value, str) or not DATE.match(value):
        return False
    try:
        datetime.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def text(value):
    return value.strip() if isinstance(value, str) else ""


class Checker:
    def __init__(self, report, documents):
        self.report = report
        self.documents = {doc["id"]: doc for doc in documents}
        self.problems = []
        self.warnings = []
        self.legal = []  # unique legal quotations, in order of first use
        self.legal_index = {}
        self.legal_uses = []  # (path, key)
        self.counts = {"factQuotes": 0, "factFound": 0, "factUnverified": 0, "legalQuotes": 0, "legalFound": 0, "legalUnreliable": 0}

    def problem(self, path, code, message, **extra):
        self.problems.append({"path": path, "code": code, "message": message, **extra})

    def warning(self, path, code, message):
        self.warnings.append({"path": path, "code": code, "message": message})

    # ---- citations ----

    def citations(self, path, items, allow_fact=True, allow_legal=True, require=False):
        if items is None:
            items = []
        if not isinstance(items, list):
            self.problem(path, "invalid", "citations must be a list")
            return
        if require and not items:
            self.problem(path, "missing_citation", "Add at least one exact quotation.")
        for i, item in enumerate(items):
            at = f"{path}[{i}]"
            if not isinstance(item, dict):
                self.problem(at, "invalid", "a citation is an object")
                continue
            quote = item.get("quote")
            if not text(quote):
                self.problem(at, "empty_quote", "The quotation is empty.")
                continue
            if "document" in item:
                if not allow_fact:
                    self.problem(at, "fact_as_authority", "A case document is not a legal authority here; quote legislation or a judgment.")
                    continue
                self.fact(at, item)
            elif "law" in item or "judgment" in item:
                if not allow_legal:
                    self.problem(at, "authority_as_fact", "Facts are quoted from the case documents (document D1, D2, …).")
                    continue
                self.legal_citation(at, item)
            else:
                self.problem(at, "invalid", "A citation names a document (D1, D2, …), a law with article, or a judgment id.")

    def fact(self, path, item):
        self.counts["factQuotes"] += 1
        doc = self.documents.get(item.get("document"))
        if doc is None:
            self.problem(path, "unknown_document", f"No case document has the id {item.get('document')!r}.")
            return
        if doc.get("warning") or not doc.get("text"):
            self.counts["factUnverified"] += 1
            self.warning(path, "fact_unverified", f"{doc['id']} ({doc['title']}) has no readable text; this quotation is not checked automatically.")
            return
        if quote_found(doc["text"], item["quote"]):
            self.counts["factFound"] += 1
            return
        self.problem(path, "quote_not_found", f"The quotation is not in {doc['id']} ({doc['title']}). Copy it exactly; whitespace, letter case and typographic quotes do not matter.", matchedPrefix=matched_prefix(doc["text"], item["quote"]))

    def legal_citation(self, path, item):
        self.counts["legalQuotes"] += 1
        if text(item.get("judgment")) and not text(item.get("law")):
            key = ("judgment", text(item["judgment"]), "", "", item["quote"].strip())
            request = {"judgment": key[1], "quote": key[4]}
        elif text(item.get("law")) and text(item.get("article")) and not text(item.get("judgment")):
            date = text(item.get("date"))
            if date and not valid_date(date):
                self.problem(path, "invalid_date", "date must be YYYY-MM-DD.")
                return
            key = ("law", text(item["law"]), text(item["article"]), date, item["quote"].strip())
            request = {"law": key[1], "article": key[2], "quote": key[4]}
            if date:
                request["date"] = date
        else:
            self.problem(path, "invalid", "A legal citation names a law with one article (and the date), or a judgment id.")
            return
        if key not in self.legal_index:
            self.legal_index[key] = len(self.legal)
            self.legal.append(request)
        self.legal_uses.append((path, key))

    # ---- report ----

    def check(self):
        r = self.report
        if not isinstance(r, dict):
            self.problem("report", "invalid", "The report is a JSON object.")
            return
        if not text(r.get("title")) or not [x for x in r.get("decisiveIssues") or [] if text(x)]:
            self.problem("overview", "missing", "Set the title and the decisive issues.")
        arguments = r.get("arguments") or []
        parties = {text(a.get("party")) for a in arguments if isinstance(a, dict) and text(a.get("party"))}
        if len(parties) < 2:
            self.problem("arguments", "missing", "Add arguments for both parties.")
        for i, a in enumerate(arguments):
            at = f"arguments[{i}]"
            if not isinstance(a, dict):
                self.problem(at, "invalid", "an argument is an object")
                continue
            for field in ("party", "issue", "thesis", "rule", "application", "evidence", "counterargument", "response", "conclusion"):
                if not text(a.get(field)):
                    self.problem(f"{at}.{field}", "empty_field", f"{field} is empty.")
            if a.get("rank") not in RANKS:
                self.problem(f"{at}.rank", "invalid", "rank is main or subsidiary.")
            if a.get("support") not in SUPPORT:
                self.problem(f"{at}.support", "invalid", "support is strong, moderate or weak.")
            verified = a.get("ruleVerified") is True
            rules = a.get("ruleCitations") or []
            if verified:
                self.citations(f"{at}.ruleCitations", rules, allow_fact=False, require=True)
            elif rules:
                self.problem(f"{at}.ruleCitations", "invalid", "ruleVerified is false: the rule was not verified, so it has no citations; say so in rule.")
            self.citations(f"{at}.factCitations", a.get("factCitations"), allow_legal=False)
        for i, q in enumerate(r.get("qualifications") or []):
            at = f"qualifications[{i}]"
            for field in ("qualification", "conditions", "supports", "defeats"):
                if not text(q.get(field)):
                    self.problem(f"{at}.{field}", "empty_field", f"{field} is empty.")
            self.citations(f"{at}.citations", q.get("citations"))
        for i, s in enumerate(r.get("scenarios") or []):
            at = f"scenarios[{i}]"
            for field in ("condition", "outcome"):
                if not text(s.get(field)):
                    self.problem(f"{at}.{field}", "empty_field", f"{field} is empty.")
            self.citations(f"{at}.citations", s.get("citations"))
        sections = r.get("sections") or []
        if not sections:
            self.problem("sections", "missing", "Add the report sections (facts, analysis, uncertainty and the others that apply).")
        for i, s in enumerate(sections):
            at = f"sections[{i}]"
            if s.get("kind") not in SECTION_KINDS:
                self.problem(f"{at}.kind", "invalid", "kind is one of " + ", ".join(SECTION_KINDS) + ".")
            if not text(s.get("text")):
                self.problem(f"{at}.text", "empty_field", "The section text is empty.")
            if s.get("kind") == "established_facts":
                self.citations(f"{at}.citations", s.get("citations"), allow_legal=False, require=True)
            else:
                self.citations(f"{at}.citations", s.get("citations"))
        timeline = r.get("timeline") or []
        if not timeline:
            self.problem("timeline", "missing", "Add the timeline: the dated events, every deadline with its computation and the steps the client should take by a date.")
        for i, e in enumerate(timeline):
            at = f"timeline[{i}]"
            if not valid_date(e.get("date")):
                self.problem(f"{at}.date", "invalid_date", "date must be YYYY-MM-DD.")
            if not text(e.get("title")):
                self.problem(f"{at}.title", "empty_field", "title is empty.")
            if e.get("kind", "event") not in TIMELINE_KINDS:
                self.problem(f"{at}.kind", "invalid", "kind is event, deadline or action.")
            if e.get("status", "established") not in TIMELINE_STATUSES:
                self.problem(f"{at}.status", "invalid", "status is established, claimed, disputed or conditional.")
            if e.get("kind") == "deadline" and not text(e.get("computation")):
                self.problem(f"{at}.computation", "empty_field", "A deadline shows its computation: starting event, rule, length, counting, non-working-day shift.")
            if e.get("ruleVerified") is True:
                self.citations(f"{at}.ruleCitations", e.get("ruleCitations"), allow_fact=False, require=True)
            else:
                self.citations(f"{at}.ruleCitations", e.get("ruleCitations"), allow_fact=False)
            self.citations(f"{at}.factCitations", e.get("factCitations"), allow_legal=False)
        estimate = r.get("outcomeEstimate")
        valid = isinstance(estimate, dict) and text(estimate.get("party")) and text(estimate.get("basis")) and isinstance(estimate.get("low"), int) and isinstance(estimate.get("high"), int) and 0 <= estimate["low"] <= estimate["high"] <= 100
        if not valid:
            self.problem("assessment", "missing", "Set outcomeEstimate: the client's party, low and high whole percentages 0-100 (low ≤ high) and the basis.")
        for field in ("uncertainty", "missingInformation"):
            if not isinstance(r.get(field, []), list):
                self.problem(field, "invalid", f"{field} is a list.")

    # ---- legal results ----

    def batches(self):
        return [{"batch": n + 1, "quotes": self.legal[i : i + BATCH_SIZE]} for n, i in enumerate(range(0, len(self.legal), BATCH_SIZE))]

    def apply_legal_results(self, folder):
        statuses = {}
        missing = []
        for batch in self.batches():
            path = os.path.join(folder, f"batch-{batch['batch']}.json")
            if not os.path.exists(path):
                missing.append(path)
                continue
            answer = read_json(path)
            results = answer.get("results") if isinstance(answer, dict) else None
            if not isinstance(results, list) or len(results) != len(batch["quotes"]):
                self.problem(path, "legal_results_invalid", "Save check_quotes' answer for this batch unchanged.")
                continue
            offset = (batch["batch"] - 1) * BATCH_SIZE
            for i, result in enumerate(results):
                statuses[offset + i] = result
        if missing:
            self.problem("legal", "legal_unchecked", "Call check_quotes for these batches and save the answers: " + ", ".join(missing))
            return
        for path, key in self.legal_uses:
            result = statuses.get(self.legal_index[key], {})
            status = result.get("status")
            if status == "found":
                self.counts["legalFound"] += 1
            elif status == "unreliable_legal_source":
                self.counts["legalFound"] += 1
                self.counts["legalUnreliable"] += 1
                self.warning(path, "unreliable_legal_source", "kodeks.me found the words, but the source text still needs review; say so where it is relied on.")
            else:
                self.problem(path, status or "legal_unchecked", "kodeks.me did not confirm this quotation: " + (result.get("note") or status or "no result"), matchedPrefix=result.get("matchedPrefix", ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--documents", required=True, help="documents.json from extract_text.py")
    parser.add_argument("--legal-results", help="folder with check_quotes answers (batch-N.json)")
    args = parser.parse_args()
    work = os.path.dirname(os.path.abspath(args.report))
    checker = Checker(read_json(args.report), read_json(args.documents).get("documents", []))
    checker.check()
    batches = checker.batches()
    write_json(os.path.join(work, "legal_requests.json"), {"batches": batches})
    if batches and args.legal_results:
        checker.apply_legal_results(args.legal_results)
    elif batches:
        checker.problem("legal", "legal_unchecked", f"Call check_quotes for each of the {len(batches)} batch(es) in legal_requests.json, save the answers as batch-N.json, and run again with --legal-results.")
    status = "pass" if not checker.problems else "fail"
    result = {"status": status, "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "counts": checker.counts, "problems": checker.problems, "warnings": checker.warnings, "legalBatches": len(batches)}
    write_json(os.path.join(work, "check_result.json"), result)
    c = checker.counts
    print(f"Status: {status.upper()}")
    print(f"Citati iz dokumenata: {c['factFound']} od {c['factQuotes']} pronađeno, {c['factUnverified']} bez provjere (dokument bez teksta)")
    print(f"Citati propisa i presuda: {c['legalFound']} od {c['legalQuotes']} potvrđeno na kodeks.me ({c['legalUnreliable']} iz teksta koji čeka reviziju)")
    for item in checker.problems:
        line = f"PROBLEM {item['path']}: {item['code']} — {item['message']}"
        if item.get("matchedPrefix"):
            line += f" | poklapa se do: «{item['matchedPrefix']}»"
        print(line)
    for item in checker.warnings:
        print(f"NAPOMENA {item['path']}: {item['code']} — {item['message']}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
