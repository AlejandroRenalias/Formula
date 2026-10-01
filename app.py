"""Root entrypoint for Formula AI Pit Wall Strategy System."""
import streamlit as st
from src.ui.projection_dashboard import run_projection_dashboard

if __name__ == "__main__":
    if st.query_params.get('view') == 'legacy':
        from src.ui.dashboard import run_dashboard
        run_dashboard()
    else:
        run_projection_dashboard()
