import streamlit as st
from auth.SessionManager import SessionManager
import base64
from pathlib import Path

st.set_page_config(
        page_title="IRIS",
        page_icon="🍁",
        layout="wide",
        initial_sidebar_state="collapsed"
)
st.logo(
    "frontend/static/iris-side.png",
    size="large"
)

def home_page():
    configue()
    read_css()
    main_content()
    

def configue():
    pass
    
def read_css():
    css_path = Path(__file__).parent / "styles.css"
    with open(css_path, "r") as file:
        st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
def main_content():
    logo_path = "frontend/static/IRIS.png"
    logo = base64.b64encode(open(logo_path, 'rb').read()).decode()
    background_path = "frontend/static/bg.png"
    background = base64.b64encode(open(background_path, 'rb').read()).decode()
    st.markdown(f"""
        <style>
        div.stMainBlockContainer.block-container.st-emotion-cache-t1wise.eht7o1d4 {{
            background-image: url('data:image/png;base64,{background}');
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
            min-height: 100vh;
            height: 100vh;
        }}
        </style>
    """, unsafe_allow_html=True)
    html_code = f"""
        <!-- Logo Section -->
        <div style="display: flex; justify-content: center; align-items: center; flex-shrink: 0;">
            <img src="data:image/png;base64,{logo}" style="width: 300px; height: 300px; margin-top: 0px;">
        </div>
        <!-- Chat Now Button -->
        <div class="container">
            <form action="https://canada-immigration-consultant.streamlit.app/Get_Consultation_with_IRIS">
                <button class="chat-now-btn" type="submit">
                <p>CHAT NOW</p>
                <p>Discutons Maintenant</p>
                </button>
            </form>
        </div>
    """
    
    st.markdown(html_code, unsafe_allow_html=True)
    

        

session_manager = SessionManager()
home_page()
