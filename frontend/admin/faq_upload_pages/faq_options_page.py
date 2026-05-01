import streamlit as st
from screens import *
from Home import session_manager
import time
import os
from functools import partial
from dotenv import load_dotenv
from streamlit_card import card
load_dotenv()

def faq_options_page():
    st.title("FAQ Options")
    st.sidebar.button("⬅ Back", on_click=go_back)
    get_user_inputs()
    
def on_card_click(page_name):
    st.session_state.page = page_name
    
def get_user_inputs():
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            card(
                title="Upload FAQs from IRCC",
                text="",
                on_click=partial(on_card_click, UPLOAD_FAQ_PAGE),
            )
        
        with col2:
            card(
                title="Upload FAQs from Database",
                text="",
                on_click=partial(on_card_click, FAQ_CLUSTER_PAGE),
            )
    
def go_back():
    st.session_state.page = ADMIN_DASHBOARD
