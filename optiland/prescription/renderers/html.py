"""HtmlRenderer — self-contained HTML output for Jupyter and files.

Kramer Harrison, 2026
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

from optiland.prescription.renderers.base import BaseRenderer

if TYPE_CHECKING:
    import os

    from optiland.prescription.document import (
        Block,
        Document,
        KeyValueBlock,
        Section,
        TableBlock,
    )

# Inline styles only (no external assets).  Colours are inherited and borders
# use a translucent grey so the output reads well on light and dark themes.
_BORDER = "1px solid rgba(128, 128, 128, 0.4)"
_STYLE_ROOT = "font-family: sans-serif; line-height: 1.4;"
_STYLE_TABLE = "border-collapse: collapse; margin: 0.25em 0 0.75em 0;"
_STYLE_TH = f"border-bottom: {_BORDER}; padding: 2px 10px; text-align: right;"
_STYLE_TD = "padding: 2px 10px; text-align: right;"
_STYLE_KEY = "padding: 2px 10px; text-align: left; font-weight: bold;"
_STYLE_VALUE = "padding: 2px 10px; text-align: left;"
_STYLE_BLOCK_TITLE = "margin: 0.5em 0 0.1em 0; font-weight: bold;"
_STYLE_HR = f"border: 0; border-top: {_BORDER}; margin: 0.5em 0;"


class HtmlRenderer(BaseRenderer):
    """Renders a Document to an HTML string.

    The output is a single ``<div>`` with inline styles, so it can be returned
    from ``_repr_html_`` or embedded in a page.  All text taken from the
    document is escaped with :func:`html.escape`.
    """

    def render(self, document: Document) -> str:
        """Return the document as an HTML fragment.

        Args:
            document: The document model to render.

        Returns:
            An HTML string with inline styles.
        """
        parts = [
            f'<div style="{_STYLE_ROOT}">',
            f"<h3>{escape(document.title)}</h3>",
            f"<p><small>Generated: {escape(document.generated_at)}</small></p>",
        ]
        for section in document.sections:
            parts.append(self._render_section(section))
        parts.append("</div>")
        return "".join(parts)

    def write(self, document: Document, path: str | os.PathLike) -> None:
        """Render the document and write it to a standalone HTML file.

        Args:
            document: The document model to render.
            path: Output file path.
        """
        page = (
            "<!DOCTYPE html>"
            '<html><head><meta charset="utf-8">'
            f"<title>{escape(document.title)}</title></head>"
            f"<body>{self.render(document)}</body></html>"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)

    def _render_section(self, section: Section) -> str:
        parts = [f"<h4>{escape(section.title)}</h4>"]
        parts.extend(self._render_block(block) for block in section.blocks)
        return "".join(parts)

    def _render_block(self, block: Block) -> str:
        from optiland.prescription.document import (
            KeyValueBlock,
            SeparatorBlock,
            TableBlock,
            TextBlock,
        )

        if isinstance(block, KeyValueBlock):
            return self._render_kv(block)
        if isinstance(block, TableBlock):
            return self._render_table(block)
        if isinstance(block, TextBlock):
            return f"<p>{escape(block.text)}</p>"
        if isinstance(block, SeparatorBlock):
            return f'<hr style="{_STYLE_HR}">'
        return ""

    @staticmethod
    def _block_title(title: str | None) -> str:
        if not title:
            return ""
        return f'<div style="{_STYLE_BLOCK_TITLE}">{escape(title)}</div>'

    def _render_kv(self, block: KeyValueBlock) -> str:
        if not block.rows:
            return ""
        rows = "".join(
            f'<tr><td style="{_STYLE_KEY}">{escape(key)}</td>'
            f'<td style="{_STYLE_VALUE}">{escape(value)}</td></tr>'
            for key, value in block.rows
        )
        return (
            self._block_title(block.title)
            + f'<table style="{_STYLE_TABLE}"><tbody>{rows}</tbody></table>'
        )

    def _render_table(self, block: TableBlock) -> str:
        header = "".join(
            f'<th style="{_STYLE_TH}">{escape(h)}</th>' for h in block.headers
        )
        rows = "".join(
            "<tr>"
            + "".join(f'<td style="{_STYLE_TD}">{escape(cell)}</td>' for cell in row)
            + "</tr>"
            for row in block.rows
        )
        return (
            self._block_title(block.title)
            + f'<table style="{_STYLE_TABLE}">'
            + f"<thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"
        )
