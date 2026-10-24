#!/usr/bin/env python3
"""
Convert Word DOCX documents in specification/word/ to clean, high-fidelity Markdown (.md) files.
Zero external dependencies (uses standard library zipfile and xml.etree.ElementTree).
"""

import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}

def get_style_map(zf):
    """Map style IDs to style names (case-insensitive) using word/styles.xml."""
    style_map = {}
    if 'word/styles.xml' not in zf.namelist():
        return style_map
    try:
        styles_xml = zf.read('word/styles.xml')
        root = ET.fromstring(styles_xml)
        for style in root.findall('w:style', NS):
            style_id = style.get(f'{{{NS["w"]}}}styleId')
            name_el = style.find('w:name', NS)
            if style_id and name_el is not None:
                style_map[style_id] = name_el.get(f'{{{NS["w"]}}}val', '')
    except Exception:
        pass
    return style_map


def get_num_map(zf):
    """Parse numbering definitions from word/numbering.xml to distinguish bullets vs ordered."""
    num_map = {}  # numId -> {ilvl -> is_bullet (bool)}
    if 'word/numbering.xml' not in zf.namelist():
        return num_map
    try:
        num_xml = zf.read('word/numbering.xml')
        root = ET.fromstring(num_xml)
        abstract_nums = {}  # abstractNumId -> {ilvl -> is_bullet}
        for ab in root.findall('w:abstractNum', NS):
            ab_id = ab.get(f'{{{NS["w"]}}}abstractNumId')
            lvl_map = {}
            for lvl in ab.findall('w:lvl', NS):
                ilvl = lvl.get(f'{{{NS["w"]}}}ilvl', '0')
                num_fmt = lvl.find('w:numFmt', NS)
                val = num_fmt.get(f'{{{NS["w"]}}}val', '') if num_fmt is not None else ''
                lvl_map[int(ilvl)] = (val == 'bullet')
            abstract_nums[ab_id] = lvl_map

        for num in root.findall('w:num', NS):
            num_id = num.get(f'{{{NS["w"]}}}numId')
            ab_ref = num.find('w:abstractNumId', NS)
            if ab_ref is not None:
                ab_id = ab_ref.get(f'{{{NS["w"]}}}val')
                if ab_id in abstract_nums:
                    num_map[num_id] = abstract_nums[ab_id]
    except Exception:
        pass
    return num_map


def extract_runs_text(element, in_cell=False, is_heading=False):
    """Extract formatted text from runs, hyperlinks, etc. inside a paragraph."""
    parts = []

    for child in element:
        tag = child.tag
        if tag == f'{{{NS["w"]}}}r':
            r_pr = child.find('w:rPr', NS)
            is_bold = False
            is_italic = False
            is_strike = False
            is_code = False

            if r_pr is not None and not is_heading:
                b = r_pr.find('w:b', NS)
                b_cs = r_pr.find('w:bCs', NS)
                if (b is not None and b.get(f'{{{NS["w"]}}}val', '1') not in ('0', 'false')) or \
                   (b_cs is not None and b_cs.get(f'{{{NS["w"]}}}val', '1') not in ('0', 'false')):
                    is_bold = True

                i = r_pr.find('w:i', NS)
                i_cs = r_pr.find('w:iCs', NS)
                if (i is not None and i.get(f'{{{NS["w"]}}}val', '1') not in ('0', 'false')) or \
                   (i_cs is not None and i_cs.get(f'{{{NS["w"]}}}val', '1') not in ('0', 'false')):
                    is_italic = True

                strike = r_pr.find('w:strike', NS)
                if strike is not None and strike.get(f'{{{NS["w"]}}}val', '1') not in ('0', 'false'):
                    is_strike = True

                r_style = r_pr.find('w:rStyle', NS)
                if r_style is not None:
                    style_val = r_style.get(f'{{{NS["w"]}}}val', '').lower()
                    if 'code' in style_val or 'verbatim' in style_val:
                        is_code = True

            # Text content
            run_text = ""
            for sub in child:
                if sub.tag == f'{{{NS["w"]}}}t':
                    if sub.text:
                        run_text += sub.text
                elif sub.tag == f'{{{NS["w"]}}}tab':
                    run_text += "\t"
                elif sub.tag == f'{{{NS["w"]}}}br':
                    run_text += "<br>" if in_cell else "\n"

            if run_text:
                if in_cell:
                    run_text = run_text.replace('|', r'\|').replace('\n', '<br>')

                if not is_heading:
                    # Apply markdown formatting while preserving leading/trailing spaces
                    match = re.match(r'^(\s*)(.*?)(\s*)$', run_text, re.DOTALL)
                    if match:
                        lead, core, trail = match.groups()
                        if core:
                            if is_code:
                                core = f"`{core}`"
                            if is_bold:
                                core = f"**{core}**"
                            if is_italic:
                                core = f"*{core}*"
                            if is_strike:
                                core = f"~~{core}~~"
                            run_text = f"{lead}{core}{trail}"
                parts.append(run_text)

        elif tag == f'{{{NS["w"]}}}hyperlink':
            link_text = extract_runs_text(child, in_cell=in_cell, is_heading=is_heading)
            parts.append(link_text)

        elif tag == f'{{{NS["w"]}}}sdt':
            sdt_content = child.find('w:sdtContent', NS)
            if sdt_content is not None:
                parts.append(extract_runs_text(sdt_content, in_cell=in_cell, is_heading=is_heading))

        elif tag == f'{{{NS["w"]}}}smartTag':
            parts.append(extract_runs_text(child, in_cell=in_cell, is_heading=is_heading))

    return "".join(parts)


def clean_markdown_artifacts(text: str) -> str:
    """Clean up adjacent formatting markers like **** or ** **."""
    text = re.sub(r'\*\*\s*\*\*', ' ', text)
    text = re.sub(r'\*\s*\* ', ' ', text)
    return text


def process_paragraph(p_elem, style_map, num_map, list_state, is_first_p=False):
    """Convert a <w:p> element to markdown text with state-aware list numbering."""
    p_pr = p_elem.find('w:pPr', NS)
    p_style_id = ""
    p_style_name = ""
    num_pr = None

    if p_pr is not None:
        p_style = p_pr.find('w:pStyle', NS)
        if p_style is not None:
            p_style_id = p_style.get(f'{{{NS["w"]}}}val', '')
            p_style_name = style_map.get(p_style_id, p_style_id).lower()
        num_pr = p_pr.find('w:numPr', NS)

    # First check raw plain text without styling to accurately identify structure
    plain_text = extract_runs_text(p_elem, is_heading=True).strip()
    if not plain_text:
        list_state.clear()
        return ""

    # Heading level determination
    heading_level = 0
    if 'heading 1' in p_style_name or p_style_id == 'Heading1' or p_style_name == 'title':
        heading_level = 1
    elif 'heading 2' in p_style_name or p_style_id == 'Heading2' or p_style_name == 'subtitle':
        heading_level = 2
    elif 'heading 3' in p_style_name or p_style_id == 'Heading3':
        heading_level = 3
    elif 'heading 4' in p_style_name or p_style_id == 'Heading4':
        heading_level = 4
    elif 'heading 5' in p_style_name or p_style_id == 'Heading5':
        heading_level = 5
    elif 'heading 6' in p_style_name or p_style_id == 'Heading6':
        heading_level = 6

    # Section numbering heuristic if style wasn't explicitly a Heading
    if heading_level == 0:
        if is_first_p and len(plain_text) < 100 and not plain_text.startswith(('1.', '-', '•')):
            heading_level = 1
        elif re.match(r'^(Section\s+\d+|[0-9]{1,2}\.[0-9]+(\.[0-9]+)*(\s*[-—:]|\s+[A-Z]))', plain_text):
            # Check depth of numbering (e.g. 1.2 -> h2, 03.10.1 -> h2, 03.10.1.1 -> h3)
            dots = plain_text.split()[0].count('.')
            if dots <= 1:
                heading_level = 2
            elif dots == 2:
                heading_level = 2 if plain_text.startswith(('0', '1', '2', '3')) else 3
            else:
                heading_level = 3
        elif re.match(r'^[A-Z]\.\s+[`\*\w]', plain_text):  # e.g. "A. users", "B. devices"
            heading_level = 3

    if heading_level > 0:
        list_state.clear()
        prefix = '#' * heading_level
        # Heading text should be clean and un-bolded
        clean_text = re.sub(r'[*_~`]', '', plain_text).strip()
        return f"\n{prefix} {clean_text}\n"

    # List item handling
    if num_pr is not None:
        ilvl = 0
        ilvl_el = num_pr.find('w:ilvl', NS)
        if ilvl_el is not None:
            ilvl = int(ilvl_el.get(f'{{{NS["w"]}}}val', '0'))

        num_id = ""
        num_id_el = num_pr.find('w:numId', NS)
        if num_id_el is not None:
            num_id = num_id_el.get(f'{{{NS["w"]}}}val', '')

        is_bullet = True
        if num_id in num_map and ilvl in num_map[num_id]:
            is_bullet = num_map[num_id][ilvl]

        indent = "  " * ilvl
        formatted_content = clean_markdown_artifacts(extract_runs_text(p_elem)).strip()

        if is_bullet:
            list_state.pop((num_id, ilvl), None)
            return f"{indent}- {formatted_content}"
        else:
            current_num = list_state.get((num_id, ilvl), 0) + 1
            list_state[(num_id, ilvl)] = current_num
            return f"{indent}{current_num}. {formatted_content}"

    # Reset list state if not in a list
    list_state.clear()

    # Formatted normal paragraph
    formatted_text = clean_markdown_artifacts(extract_runs_text(p_elem)).strip()

    # Bullet symbol fallback at start of paragraph (e.g. • or · or -)
    if formatted_text.startswith('• ') or formatted_text.startswith('· '):
        return f"- {formatted_text[2:].strip()}"
    if formatted_text.startswith('•') or formatted_text.startswith('·'):
        return f"- {formatted_text[1:].strip()}"

    return formatted_text


def process_table(tbl_elem, style_map, num_map):
    """Convert a <w:tbl> element to a GitHub Flavored Markdown pipe table."""
    rows = tbl_elem.findall('w:tr', NS)
    if not rows:
        return ""

    table_matrix = []
    max_cols = 0

    for tr in rows:
        row_cells = []
        cells = tr.findall('w:tc', NS)
        for tc in cells:
            cell_paras = tc.findall('w:p', NS)
            cell_texts = []
            for p in cell_paras:
                p_text = clean_markdown_artifacts(extract_runs_text(p, in_cell=True)).strip()
                if p_text:
                    cell_texts.append(p_text)
            cell_content = "<br>".join(cell_texts) if cell_texts else " "
            row_cells.append(cell_content)
        if len(row_cells) > max_cols:
            max_cols = len(row_cells)
        table_matrix.append(row_cells)

    if max_cols == 0:
        return ""

    # Normalize row lengths
    for row in table_matrix:
        while len(row) < max_cols:
            row.append(" ")

    lines = []
    # Header row
    header_row = table_matrix[0]
    lines.append("| " + " | ".join(header_row) + " |")
    # Separator row
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    # Data rows
    for row in table_matrix[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n" + "\n".join(lines) + "\n"


def convert_docx_to_md(docx_path: Path) -> str:
    """Convert a single DOCX file to Markdown string."""
    with zipfile.ZipFile(docx_path) as zf:
        style_map = get_style_map(zf)
        num_map = get_num_map(zf)

        doc_xml = zf.read('word/document.xml')
        root = ET.fromstring(doc_xml)
        body = root.find('w:body', NS)
        if body is None:
            return ""

        output_blocks = []
        list_state = {}
        is_first_p = True

        for child in body:
            tag = child.tag
            if tag == f'{{{NS["w"]}}}p':
                md_p = process_paragraph(child, style_map, num_map, list_state, is_first_p=is_first_p)
                if md_p:
                    output_blocks.append(md_p)
                    is_first_p = False
            elif tag == f'{{{NS["w"]}}}tbl':
                list_state.clear()
                md_tbl = process_table(child, style_map, num_map)
                if md_tbl:
                    output_blocks.append(md_tbl)
            elif tag == f'{{{NS["w"]}}}sdt':
                sdt_content = child.find('w:sdtContent', NS)
                if sdt_content is not None:
                    for sub in sdt_content:
                        if sub.tag == f'{{{NS["w"]}}}p':
                            md_p = process_paragraph(sub, style_map, num_map, list_state, is_first_p=is_first_p)
                            if md_p:
                                output_blocks.append(md_p)
                                is_first_p = False
                        elif sub.tag == f'{{{NS["w"]}}}tbl':
                            list_state.clear()
                            md_tbl = process_table(sub, style_map, num_map)
                            if md_tbl:
                                output_blocks.append(md_tbl)

        # Assemble and format document text
        md_text = "\n\n".join(output_blocks)

        # Clean up excessive newlines
        md_text = re.sub(r'\n{3,}', '\n\n', md_text).strip() + "\n"
        return md_text


def main():
    workspace_dir = Path(__file__).resolve().parent.parent
    docs_dir = workspace_dir / "specification" / "word"
    out_dir = workspace_dir / "specification" / "markdown"
    out_dir.mkdir(exist_ok=True)

    if not docs_dir.exists():
        print(f"Error: Word documents directory not found at {docs_dir}", file=sys.stderr)
        sys.exit(1)

    docx_files = sorted(list(docs_dir.glob("*.docx")))
    print(f"Found {len(docx_files)} .docx files in {docs_dir}")

    success_count = 0
    for docx_path in docx_files:
        md_path = out_dir / (docx_path.stem + ".md")
        try:
            md_content = convert_docx_to_md(docx_path)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"✓ Converted: {docx_path.name} -> {md_path.name} ({len(md_content)} chars)")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed: {docx_path.name} - Error: {e}", file=sys.stderr)

    print(f"\nConversion complete: {success_count}/{len(docx_files)} files converted successfully.")


if __name__ == "__main__":
    main()
