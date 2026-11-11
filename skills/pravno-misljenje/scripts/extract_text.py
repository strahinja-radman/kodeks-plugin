#!/usr/bin/env python3
"""Extract the text of the case documents, exactly, so facts can be quoted
and checked word for word.

    python3 extract_text.py --out work FILE_OR_FOLDER [...]

Writes work/documents.json: one entry per document with an id (D1, D2, …),
the file name, the extracted text and how it was read. Nothing leaves the
machine: the documents are read here and never sent to kodeks.me.

Reads .docx (Word), .pdf with a text layer, .txt and .md. A scanned PDF has
no text layer: it is listed with a warning, and facts from it cannot be
checked automatically.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from xml.etree import ElementTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kodeks_common import write_json  # noqa: E402

SUPPORTED = (".docx", ".pdf", ".txt", ".md")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(path):
    """Paragraph text of the body, footnotes and endnotes, in order."""
    parts = []
    with zipfile.ZipFile(path) as archive:
        names = [n for n in ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml") if n in archive.namelist()]
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            for paragraph in root.iter(W + "p"):
                pieces = []
                for node in paragraph.iter():
                    if node.tag == W + "t" and node.text:
                        pieces.append(node.text)
                    elif node.tag == W + "tab":
                        pieces.append("\t")
                    elif node.tag in (W + "br", W + "cr"):
                        pieces.append("\n")
                    elif node.tag == W + "noBreakHyphen":
                        pieces.append("-")
                parts.append("".join(pieces))
    return "\n".join(parts), "docx"


def pdf_text(path):
    """The PDF's text layer, by the first reader available."""
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(path)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages), "pypdf"
    except ImportError:
        pass
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            return "\n\n".join((page.extract_text() or "") for page in pdf.pages), "pdfplumber"
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        result = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", path, "-"], capture_output=True, check=True)
        return result.stdout.decode("utf-8", "replace"), "pdftotext"
    raise RuntimeError("no PDF reader is installed (pypdf, pdfplumber or pdftotext)")


def plain_text(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    for encoding in ("utf-8-sig", "cp1250", "latin-1"):
        try:
            return raw.decode(encoding), "text/" + encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace"), "text/utf-8-replace"


def collect(paths):
    files = []
    for path in paths:
        if os.path.isdir(path):
            for folder, _, names in sorted(os.walk(path)):
                for name in sorted(names):
                    if name.lower().endswith(SUPPORTED) and not name.startswith((".", "~$")):
                        files.append(os.path.join(folder, name))
        elif os.path.isfile(path):
            files.append(path)
        else:
            print(f"Nije pronađeno: {path}", file=sys.stderr)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="files or folders of the case")
    parser.add_argument("--out", default="work", help="folder for documents.json (default: work)")
    args = parser.parse_args()
    documents = []
    for index, path in enumerate(collect(args.paths), start=1):
        name = os.path.basename(path)
        entry = {"id": f"D{index}", "title": name, "path": os.path.abspath(path), "text": "", "method": "", "warning": ""}
        lower = name.lower()
        try:
            if lower.endswith(".docx"):
                entry["text"], entry["method"] = docx_text(path)
            elif lower.endswith(".pdf"):
                entry["text"], entry["method"] = pdf_text(path)
            elif lower.endswith((".txt", ".md")):
                entry["text"], entry["method"] = plain_text(path)
            else:
                entry["warning"] = "Format nije podržan; sačuvajte dokument kao DOCX, PDF ili TXT."
        except Exception as error:  # noqa: BLE001 - every file is reported, none stops the others
            entry["warning"] = f"Tekst nije izvučen: {error}"
        if not entry["warning"] and len(re.sub(r"\s", "", entry["text"])) < 20:
            entry["warning"] = "Dokument nema tekstualni sloj (vjerovatno skeniran). Činjenice iz njega ne mogu se automatski provjeriti; navedite to u izvještaju."
        entry["characters"] = len(entry["text"])
        documents.append(entry)
    output = os.path.join(args.out, "documents.json")
    write_json(output, {"documents": documents})
    for doc in documents:
        status = doc["warning"] or f"{doc['characters']} znakova ({doc['method']})"
        print(f"{doc['id']}\t{doc['title']}\t{status}")
    print(f"\nSačuvano: {output}")
    return 0 if documents else 1


if __name__ == "__main__":
    sys.exit(main())
