"""Default application view: the fixture-driven custom decision workspace."""
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]


def projection_document():
    document = (ROOT / 'design/pitwall-concept.html').read_text(encoding='utf-8-sig')
    css = (ROOT / 'design/assets/pitwall.css').read_text(encoding='utf-8')
    js = (ROOT / 'design/assets/pitwall.js').read_text(encoding='utf-8')
    fixture = json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))
    payload = json.dumps(fixture, allow_nan=False).replace('<', chr(92) + 'u003c')
    document = document.replace('<link rel="stylesheet" href="assets/pitwall.css">', '<style>' + css + '</style>')
    document = document.replace('<script src="assets/pitwall.js"></script>',
        '<script id="projection-fixture" type="application/json">' + payload + '</script><script>' + js + '</script>')
    return document


def run_projection_dashboard():
    st.set_page_config(page_title='Formula · Decision fork', layout='wide', initial_sidebar_state='collapsed')
    st.markdown('<style>.stApp{background:#0d1e32}.block-container{padding:0;max-width:100%}header[data-testid="stHeader"]{background:transparent}</style>', unsafe_allow_html=True)
    with st.sidebar:
        st.link_button('Historical & legacy data tools', '?view=legacy')
        st.caption('The main workspace uses the saved synthetic projection fixture.')
    st.iframe(projection_document(), height='content')
