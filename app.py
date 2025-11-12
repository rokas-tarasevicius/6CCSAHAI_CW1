"""Main Streamlit application entry point."""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Adaptive Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import the home page
from src.ui.pages.home import render_home_page

# Render home page
render_home_page()
