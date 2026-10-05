"""Strict UTF-8 and common UTF-8-as-Windows-1252 corruption in published text."""
from pathlib import Path
import re
import json
from src.ui.projection_dashboard import projection_document

ROOT=Path(__file__).resolve().parents[2]
# The leading bytes of misdecoded multibyte UTF-8, plus replacement characters.
MOJIBAKE=re.compile(r'\u00c3[\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013-\u203a\u20ac\u2122]|\u00c2[\u0080-\u00bf]|\u00e2[\u0080\u20ac]|\ufffd')

def check(text,path):
    assert not MOJIBAKE.search(text),f'Mojibake in {path}: {MOJIBAKE.search(text).group()}'

def test_docs_static_json_and_ui_are_utf8_without_double_encoding():
    paths=list((ROOT/'docs').rglob('*.md'))+[p for p in (ROOT/'static').rglob('*') if p.suffix in ('.json','.html','.md','.js','.css')]
    paths += [p for p in (ROOT/'design').rglob('*') if p.suffix in ('.html','.css','.js','.json')]
    paths += list((ROOT/'src/ui').rglob('*.py'))+[ROOT/'README.md']
    for path in paths:
        content=path.read_bytes().decode('utf-8-sig',errors='strict');check(content,path)
        if path.suffix=='.json':check(json.dumps(json.loads(content),ensure_ascii=False),path)
    check(projection_document(),'Streamlit document')

def test_detector_recognises_single_and_double_encoding():
    import pytest
    for value in ('\u00c2\u00b1','\u00c3\u201a\u00c2\u00b1','\u00e2\u20ac\u201c'):
        with pytest.raises(AssertionError):check(value,'example')
    check('Lap 5\u201314; \u00b11 lap; p10\u2013p90','good')
