import streamlit as st
from screens import SECURITY_PAGE, ACCOUNT_MGNT_PAGE


def reset_password_button(username: str, disable = False, key = None):
    st.button("Reset Password", on_click=lambda: reset_password(username), disabled=disable, key=key)
    
def reset_password(username: str):
    pass

def delete_account_button(username: str, disable = False, key = None):
    st.button("Delete Account", on_click=lambda: delete_account(username), disabled=disable, key=key)
    
def delete_account(username: str):
    pass

def change_password_button(disable = False, key = None):
    st.button("Change Password", on_click=redirect_to_change_password_page, disabled=disable, key=key)
    
def redirect_to_change_password_page():
    if 'prev_page' not in st.session_state:
        st.session_state.prev_page = st.session_state.page
    st.session_state.page = SECURITY_PAGE