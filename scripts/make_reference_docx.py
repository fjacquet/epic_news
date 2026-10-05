"""Build ``reference.docx``: the Word template Pandoc applies to every DOCX report.

Starts from Pandoc's own default reference document (so every style Pandoc relies on
exists), then replaces ``styles.xml`` wholesale, switches the theme fonts, and sets an
A4 page with a "Page X / Y" footer. The palette is defined below.

Usage: ``uv run python scripts/make_reference_docx.py``  (needs ``pandoc`` on PATH)
"""

import re
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "src/epic_news/utils/docx_report/reference.docx"

BODY_FONT = "Segoe UI Light"
CODE_FONT = "Consolas"

# Palette, hex without '#'
TEXT = "343A40"
H1 = "0056B3"
H2 = "2980B9"
H3 = "2C3E50"
MUTED = "6C757D"
BORDER = "DEE2E6"
PANEL = "F8F9FA"
LINK = "007BFF"

# A4 portrait, 2.5 cm margins (twips)
PAGE_W, PAGE_H, MARGIN, FOOTER_DIST = 11906, 16838, 1417, 708
TEXT_W = PAGE_W - 2 * MARGIN

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
FOOTER_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
FOOTER_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"


def _fonts(name: str) -> str:
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:eastAsia="{name}" w:cs="{name}"/>'


def _rpr(
    *,
    size: int | None = None,
    color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    font: str | None = None,
    extra: str = "",
) -> str:
    parts = []
    if font:
        parts.append(_fonts(font))
    if bold:
        parts.append("<w:b/><w:bCs/>")
    if italic:
        parts.append("<w:i/><w:iCs/>")
    if color:
        parts.append(f'<w:color w:val="{color}"/>')
    if size:
        parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    parts.append(extra)
    return f"<w:rPr>{''.join(parts)}</w:rPr>" if any(parts) else ""


def _spacing(before: int = 0, after: int = 0, line: int | None = None) -> str:
    line_attr = f' w:line="{line}" w:lineRule="auto"' if line else ""
    return f'<w:spacing w:before="{before}" w:after="{after}"{line_attr}/>'


def _para(
    style_id: str,
    name: str,
    *,
    based: str | None = "Normal",
    nxt: str | None = None,
    ppr: str = "",
    rpr: str = "",
    default: bool = False,
) -> str:
    attrs = ' w:default="1"' if default else ""
    based_xml = f'<w:basedOn w:val="{based}"/>' if based else ""
    next_xml = f'<w:next w:val="{nxt}"/>' if nxt else ""
    ppr_xml = f"<w:pPr>{ppr}</w:pPr>" if ppr else ""
    return (
        f'<w:style w:type="paragraph"{attrs} w:styleId="{style_id}"><w:name w:val="{name}"/>'
        f"{based_xml}{next_xml}<w:qFormat/>{ppr_xml}{rpr}</w:style>"
    )


def _char(style_id: str, name: str, rpr: str) -> str:
    return (
        f'<w:style w:type="character" w:styleId="{style_id}"><w:name w:val="{name}"/>'
        f'<w:basedOn w:val="DefaultParagraphFont"/><w:uiPriority w:val="1"/>{rpr}</w:style>'
    )


def _border(side: str, color: str, size: int = 4, space: int = 0) -> str:
    return f'<w:{side} w:val="single" w:sz="{size}" w:space="{space}" w:color="{color}"/>'


def _heading(
    level: int,
    size: int,
    color: str,
    *,
    before: int,
    after: int,
    bold: bool = False,
    italic: bool = False,
    rule: bool = False,
) -> str:
    ppr = "<w:keepNext/><w:keepLines/>"
    if rule:
        ppr += f"<w:pBdr>{_border('bottom', H2, 6, 4)}</w:pBdr>"
    ppr += _spacing(before, after) + f'<w:outlineLvl w:val="{level - 1}"/>'
    return _para(
        f"Heading{level}",
        f"heading {level}",
        nxt="BodyText",
        ppr=ppr,
        rpr=_rpr(size=size, color=color, bold=bold, italic=italic),
    )


def build_styles_xml() -> str:
    doc_defaults = (
        "<w:docDefaults><w:rPrDefault><w:rPr>"
        f"{_fonts(BODY_FONT)}"
        f'<w:color w:val="{TEXT}"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
        '<w:lang w:val="fr-CH" w:eastAsia="fr-CH" w:bidi="ar-SA"/>'
        "</w:rPr></w:rPrDefault>"
        f"<w:pPrDefault><w:pPr>{_spacing(0, 120, 276)}</w:pPr></w:pPrDefault></w:docDefaults>"
    )

    toc_tab = f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{TEXT_W}"/></w:tabs>'
    code_shading = f'<w:shd w:val="clear" w:color="auto" w:fill="{PANEL}"/>'

    styles = [
        # --- defaults ---
        '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">'
        '<w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/></w:style>',
        '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/>'
        '<w:uiPriority w:val="99"/><w:semiHidden/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/>'
        '<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
        '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>',
        '<w:style w:type="numbering" w:default="1" w:styleId="NoList"><w:name w:val="No List"/>'
        '<w:uiPriority w:val="99"/><w:semiHidden/></w:style>',
        _para("Normal", "Normal", based=None, default=True),
        # --- body ---
        _para("BodyText", "Body Text", ppr=_spacing(60, 120)),
        _para("FirstParagraph", "First Paragraph", based="BodyText", nxt="BodyText"),
        _para("Compact", "Compact", based="BodyText", ppr=_spacing(20, 20)),
        # --- title block ---
        _para(
            "Title",
            "Title",
            nxt="BodyText",
            ppr="<w:keepNext/>" + _spacing(0, 120),
            rpr=_rpr(size=52, color=H1),
        ),
        _para(
            "Subtitle",
            "Subtitle",
            nxt="BodyText",
            ppr="<w:keepNext/>" + _spacing(0, 240),
            rpr=_rpr(size=28, color=MUTED),
        ),
        _para(
            "Author",
            "Author",
            nxt="BodyText",
            ppr="<w:keepNext/>" + _spacing(0, 40),
            rpr=_rpr(size=22, color=MUTED),
        ),
        _para(
            "Date",
            "Date",
            nxt="BodyText",
            ppr="<w:keepNext/>" + _spacing(0, 360),
            rpr=_rpr(size=22, color=MUTED),
        ),
        _para(
            "AbstractTitle",
            "Abstract Title",
            nxt="Abstract",
            ppr="<w:keepNext/>" + _spacing(240, 60),
            rpr=_rpr(size=22, color=H2),
        ),
        _para("Abstract", "Abstract", nxt="BodyText", ppr=_spacing(0, 240), rpr=_rpr(italic=True)),
        _para(
            "TOCHeading",
            "TOC Heading",
            nxt="BodyText",
            ppr="<w:keepNext/>" + _spacing(240, 160),
            rpr=_rpr(size=36, color=H1),
        ),
        # --- headings ---
        _heading(1, 36, H1, before=480, after=160, rule=True),
        _heading(2, 28, H2, before=320, after=100),
        _heading(3, 24, H3, before=240, after=80),
        _heading(4, 20, H3, before=200, after=60, bold=True),
        _heading(5, 20, MUTED, before=160, after=40, bold=True),
        _heading(6, 20, MUTED, before=160, after=40, italic=True),
        _heading(7, 20, MUTED, before=120, after=40, italic=True),
        _heading(8, 20, MUTED, before=120, after=40, italic=True),
        _heading(9, 20, MUTED, before=120, after=40, italic=True),
        # --- TOC entries ---
        _para("TOC1", "toc 1", nxt="BodyText", ppr=toc_tab + _spacing(80, 40), rpr=_rpr(bold=True)),
        _para("TOC2", "toc 2", nxt="BodyText", ppr=toc_tab + _spacing(0, 20) + '<w:ind w:left="220"/>'),
        _para(
            "TOC3",
            "toc 3",
            nxt="BodyText",
            ppr=toc_tab + _spacing(0, 20) + '<w:ind w:left="440"/>',
            rpr=_rpr(size=18, color=MUTED),
        ),
        # --- quotes, definitions, bibliography ---
        _para(
            "BlockText",
            "Block Text",
            based="BodyText",
            ppr=f"<w:pBdr>{_border('left', H2, 18, 8)}</w:pBdr>{code_shading}"
            + _spacing(60, 120)
            + '<w:ind w:left="284" w:right="284"/>',
            rpr=_rpr(color=MUTED, italic=True),
        ),
        _para(
            "DefinitionTerm",
            "Definition Term",
            based="BodyText",
            nxt="Definition",
            ppr="<w:keepNext/>" + _spacing(60, 0),
            rpr=_rpr(bold=True),
        ),
        _para("Definition", "Definition", based="BodyText", ppr='<w:ind w:left="360"/>'),
        _para("Bibliography", "Bibliography", based="BodyText"),
        # --- captions, figures, footnotes ---
        _para("Caption", "Caption", ppr=_spacing(60, 120), rpr=_rpr(size=18, color=MUTED, italic=True)),
        _para("TableCaption", "Table Caption", based="Caption", nxt="BodyText", ppr="<w:keepNext/>"),
        _para("ImageCaption", "Image Caption", based="Caption", nxt="BodyText"),
        _para("Figure", "Figure", ppr='<w:jc w:val="center"/>'),
        _para("CaptionedFigure", "Captioned Figure", based="Figure", nxt="BodyText", ppr="<w:keepNext/>"),
        _para("FootnoteText", "footnote text", ppr=_spacing(0, 40), rpr=_rpr(size=16, color=MUTED)),
        _para("Header", "header", ppr=_spacing(0, 0), rpr=_rpr(size=16, color=MUTED)),
        _para(
            "Footer", "footer", ppr=_spacing(0, 0) + '<w:jc w:val="center"/>', rpr=_rpr(size=16, color=MUTED)
        ),
        # --- code ---
        _para(
            "SourceCode",
            "Source Code",
            based="Normal",
            ppr=f"<w:pBdr>{_border('left', BORDER, 12, 6)}</w:pBdr>{code_shading}"
            + _spacing(60, 120, 240)
            + '<w:ind w:left="120"/>',
            rpr=_rpr(size=18, font=CODE_FONT),
        ),
        # Inline `code` (LLMs backtick transport names, brands...) keeps the body font; only
        # SourceCode blocks get the monospace font, inherited through the paragraph style.
        _char("VerbatimChar", "Verbatim Char", _rpr(color=H2)),
        # --- inline ---
        _char("Hyperlink", "Hyperlink", _rpr(color=LINK, extra='<w:u w:val="single"/>')),
        _char("FootnoteReference", "footnote reference", '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'),
        _char("SectionNumber", "Section Number", ""),
        # --- tables ---
        (
            '<w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/>'
            '<w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/><w:qFormat/>'
            '<w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
            '<w:tblPr><w:tblStyleRowBandSize w:val="1"/><w:tblInd w:w="0" w:type="dxa"/>'
            f"<w:tblBorders>{_border('top', BORDER)}{_border('bottom', BORDER)}"
            f"{_border('insideH', BORDER)}</w:tblBorders>"
            '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
            '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:bCs/><w:color w:val="FFFFFF"/></w:rPr>'
            f"<w:tcPr><w:tcBorders>{_border('bottom', H1)}</w:tcBorders>"
            f'<w:shd w:val="clear" w:color="auto" w:fill="{H1}"/></w:tcPr></w:tblStylePr>'
            f'<w:tblStylePr w:type="band2Horz"><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{PANEL}"/>'
            "</w:tcPr></w:tblStylePr></w:style>"
        ),
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{W_NS}">{doc_defaults}{"".join(styles)}</w:styles>'
    )


def build_footer_xml() -> str:
    def run(inner: str) -> str:
        return f"<w:r>{inner}</w:r>"

    def field(instr: str) -> str:
        return f'<w:fldSimple w:instr=" {instr} "><w:r><w:t>1</w:t></w:r></w:fldSimple>'

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W_NS}"><w:p><w:pPr><w:pStyle w:val="Footer"/></w:pPr>'
        + run('<w:t xml:space="preserve">Page </w:t>')
        + field("PAGE")
        + run('<w:t xml:space="preserve"> / </w:t>')
        + field("NUMPAGES")
        + "</w:p></w:ftr>"
    )


def build_sect_pr() -> str:
    return (
        '<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter1"/>'
        '<w:footnotePr><w:numRestart w:val="eachSect"/></w:footnotePr>'
        f'<w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>'
        f'<w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" w:bottom="{MARGIN}" w:left="{MARGIN}" '
        f'w:header="{FOOTER_DIST}" w:footer="{FOOTER_DIST}" w:gutter="0"/></w:sectPr>'
    )


def patch_parts(parts: dict[str, bytes]) -> dict[str, bytes]:
    """Return ``parts`` with styles, theme fonts, A4 section and footer swapped in."""
    patched = dict(parts)
    patched["word/styles.xml"] = build_styles_xml().encode()

    theme = patched["word/theme/theme1.xml"].decode()
    theme = re.sub(r'(<a:latin typeface=")[^"]*(")', rf"\g<1>{BODY_FONT}\g<2>", theme)
    patched["word/theme/theme1.xml"] = theme.encode()

    document = patched["word/document.xml"].decode()
    document, count = re.subn(r"<w:sectPr>.*?</w:sectPr>", build_sect_pr(), document, flags=re.S)
    if count != 1:
        raise RuntimeError(f"expected exactly one sectPr in default reference.docx, found {count}")
    patched["word/document.xml"] = document.encode()

    patched["word/footer1.xml"] = build_footer_xml().encode()
    rels = patched["word/_rels/document.xml.rels"].decode()
    rels = rels.replace(
        "</Relationships>",
        f'<Relationship Type="{FOOTER_REL_TYPE}" Id="rIdFooter1" Target="footer1.xml"/></Relationships>',
    )
    patched["word/_rels/document.xml.rels"] = rels.encode()
    content_types = patched["[Content_Types].xml"].decode()
    content_types = content_types.replace(
        "</Types>", f'<Override PartName="/word/footer1.xml" ContentType="{FOOTER_CT}"/></Types>'
    )
    patched["[Content_Types].xml"] = content_types.encode()
    return patched


def main() -> None:
    default_ref = subprocess.run(
        ["pandoc", "--print-default-data-file", "reference.docx"], check=True, capture_output=True
    ).stdout
    with zipfile.ZipFile(BytesIO(default_ref)) as zf:
        parts = {name: zf.read(name) for name in zf.namelist()}
    patched = patch_parts(parts)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in patched.items():
            zf.writestr(name, data)
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
