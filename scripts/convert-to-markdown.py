#!/usr/bin/env python3
"""Convert the handbook's main TeX sources to a self-contained Hexo page.

Requires Pandoc. Run from any directory; generated files live in md/.
This is a format conversion, not a factual revision of the source material.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "md"
SOURCES = ["frontmatter.tex", "Aachen及周边.tex", "初来乍到.tex",
           "在亚琛学习和生活.tex", "后记与致谢.tex"]


def pandoc(text, source="latex", target="json"):
    result = subprocess.run(
        ["pandoc", "-f", source, "-t", target, "--wrap=none"],
        input=text, text=True, capture_output=True, check=True, cwd=ROOT)
    if result.stderr.strip():
        raise RuntimeError(result.stderr)
    return result.stdout


def raw(text, block=True):
    return {"t": "RawBlock" if block else "RawInline", "c": ["html", text]}


def plain(value):
    if isinstance(value, list):
        return "".join(plain(x) for x in value)
    if isinstance(value, dict):
        if value["t"] == "Str":
            return value["c"]
        if value["t"] in ("Space", "SoftBreak", "LineBreak"):
            return " "
        if value["t"] in ("Link", "Image"):
            return plain(value["c"][1])
        return plain(value.get("c", []))
    return ""


def clean(text):
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    text = text.replace(r"\textsbf", r"\textbf")
    text = re.sub(r"\\rightline\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\LaTeX\s*", "LaTeX ", text)
    text = re.sub(r"\\qquad\s*", " / ", text)
    text = re.sub(r"\\quad\s*", " ", text)
    text = re.sub(r"\\MVRightarrow(?:\{\})?\s*", " → ", text)
    text = re.sub(r"\\textasciitilde\s*", "～", text)
    text = text.replace(r"$\in$", "∈")
    text = re.sub(r"\\vskip[^\n]*", "", text)
    text = re.sub(r"\\vspace\{[^}]*\}", "", text)
    text = text.replace(r"\newpage", "")
    text = text.replace(r"\noindent\fbox{", r"\begin{quote}")
    text = re.sub(r"(\\end\{minipage\})\s*\}", r"\1\n\\end{quote}", text)
    return text


OUT.mkdir(exist_ok=True)
(OUT / "assets").mkdir(exist_ok=True)
assets = {}


def image(path, caption=""):
    source = ROOT / path
    assert source.is_file(), path
    name = hashlib.sha256(path.encode()).hexdigest()[:12] + source.suffix.lower()
    target = "assets/" + name
    shutil.copy2(source, OUT / target)
    assets[target] = path
    return {"t": "Para", "c": [{"t": "Image", "c": [
        ["", [], []], [{"t": "Str", "c": caption or source.stem}], [target, ""]]}]}


text = "\n\n".join(clean((ROOT / name).read_text()) for name in SOURCES)
replacements = {}
labels = {}
figure_count = 0
table_count = 0


def replace_float(match):
    global figure_count, table_count
    kind, body = match.group(1), match.group(2)
    is_table = kind == "table"
    if is_table:
        table_count += 1
    else:
        figure_count += 1
    anchor = f"{'table' if is_table else 'figure'}-{table_count if is_table else figure_count}"
    caption = re.search(r"\\caption\{", body)
    caption_text = ""
    if caption:
        start = end = caption.end()
        depth = 1
        while depth:
            if body[end] == "{" and body[end - 1] != "\\":
                depth += 1
            elif body[end] == "}" and body[end - 1] != "\\":
                depth -= 1
            end += 1
        caption_text = body[start:end - 1]
    caption_blocks = json.loads(pandoc(caption_text))["blocks"] if caption_text else []
    blocks = [raw(f'<a id="{anchor}"></a>')]
    for label in re.findall(r"\\label\{([^}]*)\}", body):
        labels[label] = (anchor, plain(caption_blocks))
    if is_table:
        # Preserve the two merged cells as colspan, which pipe tables cannot express.
        blocks.append(raw('<table>\n<thead><tr><th>银行</th><th>Sperrkonto</th><th>Girokonto</th></tr></thead>\n<tbody>\n<tr><td>德银</td><td colspan="2">同一个IBAN</td></tr>\n<tr><td>Sparkasse</td><td>IBAN for Sperrkonto</td><td>IBAN for Girokonto</td></tr>\n<tr><td>N26</td><td colspan="2">同一个IBAN</td></tr>\n</tbody>\n</table>'))
    else:
        paths = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", body)
        assert paths
        blocks.extend(image(path) for path in paths)
    if caption_text:
        blocks.extend(json.loads(pandoc("图：" + caption_text if not is_table else "表：" + caption_text))["blocks"])
    token = f"HCWSAFLOAT{len(replacements):03d}"
    replacements[token] = blocks
    return "\n\n" + token + "\n\n"


text = re.sub(r"\\begin\{(figure|wrapfigure|table)\}(.*?)\\end\{\1\}", replace_float, text, flags=re.S)
doc = json.loads(pandoc(text))
headings = []
for block in doc["blocks"]:
    if block["t"] == "Header":
        level, attr, title = block["c"]
        anchor = f"section-{len(headings) + 1:03d}"
        labels[attr[0]] = (anchor, plain(title))
        headings.append((level, anchor, plain(title)))

notes = []
references = []


def walk(node):
    if isinstance(node, list):
        return [walk(item) for item in node]
    if not isinstance(node, dict):
        return node
    kind = node.get("t")
    if kind == "Note":
        number = len(notes) + 1
        notes.append(node["c"])
        return raw(f'<sup id="note-ref-{number}"><a href="#note-{number}">[{number}]</a></sup>', False)
    if kind == "Link" and dict(node["c"][0][2]).get("reference-type") == "ref":
        label = dict(node["c"][0][2])["reference"]
        anchor, title = labels[label]
        references.append(label)
        return {"t": "Link", "c": [["", [], []], [{"t": "Str", "c": title}], ["#" + anchor, ""]]}
    if kind == "RawInline" or kind == "RawBlock":
        assert node["c"][0] != "latex", node
    if kind == "Superscript":
        return raw("<sup>" + plain(node["c"]) + "</sup>", False)
    return {key: walk(value) for key, value in node.items()}


blocks = [image("Bilder/FrontCover.png", "亚琛新生手册 2023 封面")]
toc = "## 目录\n\n" + "\n".join(
    f'{"  " * (level - 1)}- [{title}](#{anchor})'
    for level, anchor, title in headings if level <= 2)
blocks.extend(json.loads(pandoc(toc, "markdown"))["blocks"])
for block in doc["blocks"]:
    if block["t"] == "Header":
        anchor, _ = labels[block["c"][1][0]]
        blocks.append(raw(f'<a id="{anchor}"></a>'))
        block["c"][0] += 1
        block["c"][1] = ["", [], []]
    if block["t"] == "Para" and plain(block["c"]) in replacements:
        blocks.extend(replacements[plain(block["c"])])
    else:
        blocks.append(walk(block))
blocks.append({"t": "Header", "c": [2, ["", [], []], [{"t": "Str", "c": "注释"}]]})
for number, note in enumerate(notes, 1):
    blocks.append(raw(f'<a id="note-{number}"></a>'))
    blocks.append({"t": "Para", "c": [{"t": "Strong", "c": [{"t": "Str", "c": f"[{number}]"}]}]})
    blocks.extend(walk(note))
    blocks.append({"t": "Para", "c": [{"t": "Link", "c": [["", [], []], [{"t": "Str", "c": "↩ 返回正文"}], [f"#note-ref-{number}", ""]]}]})
blocks.append(image("Bilder/BackCover.jpg", "亚琛新生手册 2023 封底"))
doc["blocks"] = blocks
body = pandoc(json.dumps(doc), "json", "gfm")
# Replace print-oriented reference prefixes with natural web link wording.
body = re.sub(r"\b(?:Sec|Fig|Table)\s+(?=\[)", "", body)
# Preserve successfully uploaded URLs when regenerating from the same assets.
uploads = OUT / "image-uploads.json"
if uploads.exists():
    for entry in json.loads(uploads.read_text())["images"]:
        local = OUT / entry["local_path"]
        if (entry["status"] == "uploaded" and local.is_file()
                and hashlib.sha256(local.read_bytes()).hexdigest() == entry["sha256"]):
            body = body.replace("](" + entry["local_path"] + ")", "](" + entry["url"] + ")")
frontmatter = '''---
title: 亚琛新生手册（2023 版）
subtitle: Aachen 及周边、初来乍到、在亚琛学习和生活
layout: page
lang: zh-CN
keywords: 亚琛新生手册, RWTH, Aachen, VCWSA, 德国留学
description: 亚琛新生手册 2023 版的 Markdown 转录，涵盖入境准备、入学注册及亚琛学习生活。
aside: true
toc: true
---

> 版本说明：本文由 2023 版手册的 TeX 源文档转换而来，保留原稿内容。文中的政策、金额、联系方式及链接未作时效性核验；本次转换不代表内容已更新。

'''
(OUT / "index.md").write_text(frontmatter + body)
(OUT / "assets-map.json").write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n")
print(f"Converted {len(SOURCES)} sources: {len(headings)} headings, {len(assets)} images, "
      f"{len(references)} references, {len(notes)} notes, {table_count} table.")
