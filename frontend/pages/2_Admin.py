import streamlit as st
from admin.pdf_upload_pages.upload_pdf_page import upload_pdf_page
from admin.login_signup.login_page import login_page
from admin.login_signup.signup_page import signup_page
from admin.pdf_upload_pages.edit_extracted_pdf_page import edit_extracted_pdf_page
from admin.account_mgnt_page.acc_mgnt_page import account_mgnt_page
from admin.security_pages.change_password_page import security_page
from admin.faq_upload_pages.faq_upload import upload_faq_page
from admin.faq_upload_pages.faq_options_page import faq_options_page
from admin.faq_upload_pages.faq_cluster_page import faq_cluster_page
from auth.user_authentication import on_logout
from streamlit_session_browser_storage import SessionStorage
from screens import *
from streamlit_card import card


def admin_run():
    initialize_session_state()
    if st.session_state.page == LOGIN_PAGE:
        st.set_page_config(page_title="Admin", page_icon="🔒", layout="centered")
        login_page()
        
    else:
        st.set_page_config(page_title="Admin", page_icon="🔓", layout="wide")
        if st.session_state.page == ADMIN_DASHBOARD:
            admin_dashboard()
        elif st.session_state.page == UPLOAD_PDF_PAGE:
            upload_pdf_page()
        elif st.session_state.page == EDIT_EXTRACTED_PDF_PAGE:
            edit_extracted_pdf_page()
        elif st.session_state.page == UPLOAD_FAQ_PAGE:
            upload_faq_page()
        elif st.session_state.page == ACCOUNT_MGNT_PAGE:
            account_mgnt_page()
        elif st.session_state.page == SECURITY_PAGE:
            security_page()
        elif st.session_state.page == SIGNUP_PAGE:
            signup_page()
        elif st.session_state.page == FAQ_OPTIONS_PAGE:
            faq_options_page()
        elif st.session_state.page == FAQ_CLUSTER_PAGE:
            faq_cluster_page()
        st.sidebar.button(
            "🚪Logout", 
            on_click=on_logout
        )
    
        
def initialize_session_state():
    ssbs = SessionStorage()
    session_data = ssbs.getItem("saved_session_data")
    if 'page' not in st.session_state:
        if session_data is None or session_data == None:
            st.session_state.page = LOGIN_PAGE
        else:
            st.session_state.page = ADMIN_DASHBOARD
    if 'error' not in st.session_state:
        st.session_state.error = False
        
def on_card_click(page_name):
    st.session_state.page = page_name
    
def admin_dashboard():
    with st.container():
        
        # Custom CSS to center the title
        st.markdown(
            """
            <style>
            .title {
                text-align: center;
                font-size: 36px;
                font-weight: bold;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Display the centered title
        st.markdown('<h1 class="title">Admin Dashboard</h1>', unsafe_allow_html=True)
        
        p1, p2 = st.columns(2)
        
        with p1:
            card(
                title="Upload PDF Document",
                text="",
                on_click=lambda: on_card_click(UPLOAD_PDF_PAGE),
            )
            
        with p2:
            card(
                title = "Upload FAQ",
                text = "",
                on_click = lambda: on_card_click(FAQ_OPTIONS_PAGE),
            )
            
        p3, p4 = st.columns(2)
        
        with p3:
            card(
                title = "Manage Accounts",
                text = "",
                on_click = lambda: on_card_click(ACCOUNT_MGNT_PAGE),
            )
            
        with p4:
            card(
                title = "Security Settings",
                text = "",
                on_click = lambda: on_card_click(SECURITY_PAGE),
            )
    
if __name__ == "__main__":
    admin_run()