"""Tests for HtmlRenderer and Optic._repr_html_."""

from __future__ import annotations

import pytest

from optiland.optic import Optic
from optiland.prescription import Prescription
from optiland.prescription.document import (
    Document,
    KeyValueBlock,
    Section,
    SeparatorBlock,
    TableBlock,
    TextBlock,
)
from optiland.prescription.renderers.html import HtmlRenderer


def _document(*blocks) -> Document:
    return Document(
        title="Title",
        generated_at="2026-01-01 00:00 UTC",
        sections=[Section(title="Section", blocks=list(blocks))],
    )


def test_blocks_map_to_html_elements():
    doc = _document(
        KeyValueBlock(rows=[("EFL", "50.0")], title="Overview"),
        TableBlock(headers=["S#", "Radius"], rows=[["1", "10.0"]], title="Surfaces"),
        TextBlock(text="A note."),
        SeparatorBlock(),
    )
    html = HtmlRenderer().render(doc)
    assert html.count("<table") == 2
    assert "<td" in html and "EFL" in html and "50.0" in html
    assert "<th" in html and "Radius" in html
    assert "<p>A note.</p>" in html
    assert "<hr" in html
    assert "Overview" in html and "Surfaces" in html


def test_text_is_escaped():
    doc = _document(
        KeyValueBlock(rows=[("a<b", "x & y")], title="<t>"),
        TableBlock(headers=["<h>"], rows=[["N-BK7 <glass> & more"]]),
        TextBlock(text="<script>alert(1)</script>"),
    )
    doc.title = "A & B <C>"
    html = HtmlRenderer().render(doc)
    assert "<script>" not in html
    assert "<glass>" not in html
    assert "a&lt;b" in html
    assert "x &amp; y" in html
    assert "N-BK7 &lt;glass&gt; &amp; more" in html
    assert "&lt;script&gt;" in html
    assert "A &amp; B &lt;C&gt;" in html


def test_empty_key_value_block_renders_nothing():
    html = HtmlRenderer().render(_document(KeyValueBlock(rows=[])))
    assert "<table" not in html


def test_write_creates_standalone_page(tmp_path):
    out = tmp_path / "report.html"
    HtmlRenderer().write(_document(TextBlock(text="hello")), out)
    content = out.read_text(encoding="utf-8")
    assert content.startswith("<!DOCTYPE html>")
    assert 'charset="utf-8"' in content
    assert "hello" in content


def test_renders_real_prescription(cooke_triplet):
    html = HtmlRenderer().render(Prescription(cooke_triplet).build())
    assert "<table" in html
    assert "Surface Data" in html


def test_optic_repr_html_contains_surface_table(cooke_triplet):
    html = cooke_triplet._repr_html_()
    assert isinstance(html, str)
    assert "<table" in html
    assert "Surface Data" in html
    assert "Cooke Triplet" in html


def test_optic_repr_html_escapes_comments(cooke_triplet):
    cooke_triplet.surfaces.surfaces[1].comment = "<b>&"
    html = cooke_triplet._repr_html_()
    assert "<b>&" not in html
    assert "&lt;b&gt;&amp;" in html


@pytest.mark.parametrize("state", ["empty", "no_fields", "no_wavelengths"])
def test_optic_repr_html_never_raises_on_incomplete_optic(cooke_triplet, state):
    if state == "empty":
        optic = Optic()
    elif state == "no_fields":
        optic = cooke_triplet
        optic.fields.fields.clear()
    else:
        optic = cooke_triplet
        optic.wavelengths.wavelengths.clear()
    result = optic._repr_html_()
    assert result is None or isinstance(result, str)


def test_optic_repr_html_returns_none_on_any_error(cooke_triplet, monkeypatch):
    def boom(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(Prescription, "build", boom)
    assert cooke_triplet._repr_html_() is None


@pytest.mark.parametrize("backend_name", ["numpy"])
def test_optic_repr_html_does_not_trace_rays(cooke_triplet, monkeypatch, backend_name):
    def fail(*args, **kwargs):
        raise AssertionError("real ray trace requested")

    monkeypatch.setattr(type(cooke_triplet), "trace", fail, raising=False)
    monkeypatch.setattr(type(cooke_triplet), "trace_generic", fail, raising=False)
    assert cooke_triplet._repr_html_() is not None
