#!/usr/bin/env python3
"""Write the checked legal opinion as a Word document for the lawyer.

    python3 make_docx.py work/report.json --documents work/documents.json \
        --checks work/check_result.json --model "NAZIV MODELA" --out "Pravno mišljenje.docx"

It refuses a report whose check did not pass, unless --draft is given; the
document then says on its first page that it is an unchecked draft. The
first page always says who wrote it (the assistant and the model it names
itself), what kodeks.me checked and what it did not.

Uses only the Python standard library.
"""

import argparse
import datetime
import os
import sys
import zipfile
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kodeks_common import read_json  # noqa: E402

RANKS = {"main": "Glavni argument", "subsidiary": "Podredni argument"}
SUPPORT = {"strong": "jako potkrijepljen", "moderate": "srednje potkrijepljen", "weak": "slabo potkrijepljen"}
SECTIONS = [
    ("established_facts", "Utvrđene činjenice"),
    ("allegations", "Tvrdnje stranaka"),
    ("assumptions", "Analitičke pretpostavke"),
    ("authorities", "Pravni izvori"),
    ("analysis", "Analiza"),
    ("uncertainty", "Neizvjesnosti"),
    ("missing_information", "Nedostajuće informacije"),
]
KINDS = {"event": "Događaj", "deadline": "Rok", "action": "Radnja"}
STATUSES = {"established": "utvrđeno", "claimed": "tvrdnja stranke", "disputed": "sporno", "conditional": "uslovno"}


def date_me(value):
    try:
        return datetime.date.fromisoformat(value).strftime("%d.%m.%Y.")
    except (TypeError, ValueError):
        return value or ""


class Document:
    def __init__(self):
        self.body = []

    def run(self, value, bold=False, italic=False):
        props = ""
        if bold or italic:
            props = "<w:rPr>" + ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + "</w:rPr>"
        parts = str(value).split("\n")
        xml = []
        for i, part in enumerate(parts):
            if i:
                xml.append("<w:br/>")
            xml.append(f'<w:t xml:space="preserve">{escape(part)}</w:t>')
        return f"<w:r>{props}{''.join(xml)}</w:r>"

    def paragraph(self, runs, style=None, shaded=False):
        props = ""
        if style or shaded:
            props = "<w:pPr>"
            if style:
                props += f'<w:pStyle w:val="{style}"/>'
            if shaded:
                props += '<w:pBdr><w:top w:val="single" w:sz="8" w:space="4" w:color="8A3B2E"/><w:left w:val="single" w:sz="8" w:space="4" w:color="8A3B2E"/><w:bottom w:val="single" w:sz="8" w:space="4" w:color="8A3B2E"/><w:right w:val="single" w:sz="8" w:space="4" w:color="8A3B2E"/></w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="F7EDEA"/>'
            props += "</w:pPr>"
        self.body.append(f"<w:p>{props}{''.join(runs)}</w:p>")

    def heading(self, value, level=1):
        self.paragraph([self.run(value)], style=f"Heading{level}")

    def text(self, value, bold=False, italic=False):
        if str(value).strip():
            self.paragraph([self.run(value, bold, italic)])

    def field(self, label, value):
        if value is not None and str(value).strip():
            self.paragraph([self.run(label + ": ", bold=True), self.run(value)])

    def bullets(self, items):
        for item in items or []:
            if str(item).strip():
                self.paragraph([self.run("• " + str(item))], style="ListParagraph")

    def save(self, path, title):
        document = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
            + "".join(self.body)
            + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>'
        )
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        files = {
            "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>',
            "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>',
            "word/_rels/document.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
            "word/styles.xml": STYLES,
            "docProps/core.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{escape(title)}</dc:title><dc:creator>AI asistent uz kodeks.me</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created></cp:coreProperties>',
            "word/document.xml": document,
        }
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)


STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:lang w:val="sr-Latn-ME"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="240"/></w:pPr><w:rPr><w:b/><w:sz w:val="36"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="8A3B2E"/><w:sz w:val="28"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/></w:pPr></w:style>'
    "</w:styles>"
)


def describe(citation, documents):
    quote = "„" + str(citation.get("quote", "")).strip() + "“"
    if "document" in citation:
        doc = documents.get(citation["document"], {})
        return f"{quote} — {doc.get('title', citation['document'])} ({citation['document']})"
    if citation.get("judgment") and not citation.get("law"):
        return f"{quote} — {citation.get('label') or 'presuda ' + citation['judgment']}"
    where = f"{citation.get('law', '')}, član {citation.get('article', '')}"
    if citation.get("date"):
        where += f", verzija na dan {date_me(citation['date'])}"
    return f"{quote} — {where}"


def notice(checks, model, draft):
    c = checks.get("counts", {})
    today = datetime.date.today().strftime("%d.%m.%Y.")
    lines = []
    if draft:
        lines.append(f"NEPROVJEREN NACRT: provjera nije prošla ({len(checks.get('problems', []))} problema). Ne koristiti prije nego što advokat provjeri svaki citat i zaključak.")
    else:
        lines.append("NACRT ZA PROVJERU ADVOKATA.")
    lines.append(f"Izradio AI asistent ({model}; naziv modela je izjava samog asistenta) uz kodeks.me konektor, {today}")
    legal = f"Citati propisa i presuda: {c.get('legalFound', 0)} od {c.get('legalQuotes', 0)} potvrđeno u korpusu kodeks.me"
    if c.get("legalUnreliable"):
        legal += f" ({c['legalUnreliable']} iz teksta koji još čeka reviziju)"
    lines.append(legal + ".")
    facts = f"Citati iz dokumenata predmeta: {c.get('factFound', 0)} od {c.get('factQuotes', 0)} pronađeno u dokumentima"
    if c.get("factUnverified"):
        facts += f", {c['factUnverified']} bez automatske provjere (dokumenti bez teksta)"
    lines.append(facts + ".")
    lines.append("Provjerena je doslovnost citata, ne pravno zaključivanje, ocjena dokaza niti potpunost istraživanja. Nezavisna kritika analize (drugi agent kao suprotna strana) nije rađena; na kodeks.me je dio paketa Kompletni.")
    return "\n".join(lines)


def build(report, documents, checks, model, draft):
    doc = Document()
    title = str(report.get("title") or "Pravno mišljenje").strip()
    doc.paragraph([doc.run(title)], style="Title")
    doc.paragraph([doc.run(notice(checks, model, draft))], shaded=True)

    estimate = report.get("outcomeEstimate") or {}
    if estimate:
        doc.heading("Procjena ishoda")
        doc.text(f"{estimate.get('party', '')}: {estimate.get('low', '')}–{estimate.get('high', '')} %", bold=True)
        doc.text(estimate.get("basis", ""))
        doc.bullets(estimate.get("conditions"))
    if report.get("decisiveIssues"):
        doc.heading("Odlučujuća pitanja")
        doc.bullets(report["decisiveIssues"])
    if report.get("urgentRisks"):
        doc.heading("Hitni procesni rizici")
        doc.bullets(report["urgentRisks"])

    timeline = sorted(report.get("timeline") or [], key=lambda e: (e.get("date", ""), e.get("time", "")))
    if timeline:
        doc.heading("Hronologija, rokovi i radnje")
        for event in timeline:
            head = f"{date_me(event.get('date'))}{' ' + event['time'] if event.get('time') else ''} — {event.get('title', '')}"
            tags = f"{KINDS.get(event.get('kind', 'event'), event.get('kind', ''))}, {STATUSES.get(event.get('status', 'established'), event.get('status', ''))}"
            doc.paragraph([doc.run(head, bold=True), doc.run(f" ({tags})", italic=True)])
            doc.text(event.get("detail", ""))
            doc.field("Izračun", event.get("computation"))
            if event.get("kind") == "deadline" and not event.get("ruleVerified"):
                doc.text("Pravilo za ovaj rok nije provjereno.", italic=True)
            doc.bullets([describe(c, documents) for c in (event.get("ruleCitations") or []) + (event.get("factCitations") or [])])

    arguments = report.get("arguments") or []
    parties = []
    for argument in arguments:
        if argument.get("party") not in parties:
            parties.append(argument.get("party"))
    if arguments:
        doc.heading("Argumenti stranaka")
    order = {"main": 0, "subsidiary": 1}
    strength = {"strong": 0, "moderate": 1, "weak": 2}
    for party in parties:
        doc.heading(str(party), 2)
        own = sorted((a for a in arguments if a.get("party") == party), key=lambda a: (order.get(a.get("rank"), 2), strength.get(a.get("support"), 3)))
        for argument in own:
            doc.paragraph([doc.run(f"{RANKS.get(argument.get('rank'), '')}, {SUPPORT.get(argument.get('support'), '')}: ", bold=True), doc.run(argument.get("issue", ""))])
            doc.field("Teza", argument.get("thesis"))
            doc.field("Pravilo", argument.get("rule"))
            if not argument.get("ruleVerified"):
                doc.text("Pravilo nije provjereno uprkos ciljanoj pretrazi; zaključci koji od njega zavise su ograničeni.", italic=True)
            doc.bullets([describe(c, documents) for c in argument.get("ruleCitations") or []])
            doc.field("Primjena na činjenice", argument.get("application"))
            doc.bullets([describe(c, documents) for c in argument.get("factCitations") or []])
            doc.field("Dokazi i teret dokazivanja", argument.get("evidence"))
            doc.field("Najjači protivargument", argument.get("counterargument"))
            doc.field("Odgovor", argument.get("response"))
            doc.field("Uslovni zaključak", argument.get("conclusion"))
            doc.field("Slabosti", argument.get("weaknesses"))

    if report.get("qualifications"):
        doc.heading("Alternativne pravne kvalifikacije")
        for item in report["qualifications"]:
            doc.text(item.get("qualification", ""), bold=True)
            doc.field("Kada dolazi u obzir", item.get("conditions"))
            doc.field("Šta je podržava", item.get("supports"))
            doc.field("Šta je obara", item.get("defeats"))
            doc.bullets([describe(c, documents) for c in item.get("citations") or []])
    if report.get("scenarios"):
        doc.heading("Scenariji prema činjenicama koje još nijesu utvrđene")
        for item in report["scenarios"]:
            doc.field("Ako", item.get("condition"))
            doc.field("Onda", item.get("outcome"))
            doc.bullets([describe(c, documents) for c in item.get("citations") or []])

    sections = report.get("sections") or []
    for kind, label in SECTIONS:
        own = [s for s in sections if s.get("kind") == kind]
        if not own:
            continue
        doc.heading(label)
        for section in own:
            if section.get("title"):
                doc.heading(section["title"], 2)
            doc.text(section.get("text", ""))
            doc.bullets([describe(c, documents) for c in section.get("citations") or []])

    for field, label in (("changingFactors", "Podaci koji bi promijenili procjenu"), ("uncertainty", "Neizvjesnosti"), ("missingInformation", "Nedostajuće informacije"), ("sourceDiagnostics", "Ograničenja izvora")):
        if report.get(field):
            doc.heading(label)
            doc.bullets(report[field])

    doc.heading("Prilog: provjera citata")
    doc.text(notice(checks, model, draft))
    for item in checks.get("warnings", []):
        doc.bullets([f"{item.get('path')}: {item.get('message')}"])
    for item in checks.get("problems", []):
        doc.bullets([f"PROBLEM {item.get('path')}: {item.get('message')}"])
    return doc, title


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--documents", required=True)
    parser.add_argument("--checks", required=True, help="check_result.json from check_report.py")
    parser.add_argument("--model", required=True, help="the model you are, as you know it")
    parser.add_argument("--out", required=True)
    parser.add_argument("--draft", action="store_true", help="write an unchecked draft although the check failed")
    args = parser.parse_args()
    checks = read_json(args.checks)
    if checks.get("status") != "pass" and not args.draft:
        print("Provjera nije prošla: ispravite probleme iz check_result.json i pokrenite check_report.py ponovo. Samo ako advokat izričito traži nacrt, dodajte --draft.", file=sys.stderr)
        return 1
    if os.path.getmtime(args.report) > os.path.getmtime(args.checks):
        print("Izvještaj je izmijenjen posle provjere: pokrenite check_report.py ponovo.", file=sys.stderr)
        return 1
    documents = {d["id"]: d for d in read_json(args.documents).get("documents", [])}
    doc, title = build(read_json(args.report), documents, checks, args.model.strip() or "model nije naveden", checks.get("status") != "pass")
    doc.save(args.out, title)
    print(f"Sačuvano: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
