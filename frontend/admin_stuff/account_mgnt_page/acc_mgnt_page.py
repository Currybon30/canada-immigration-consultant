import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__)))

import streamlit as st
from screens import *
from streamlit_session_browser_storage import SessionStorage
from Home import session_manager
from operation_buttons import reset_password_button, delete_account_button, change_password_button
import dotenv
import os
from auth.user_authentication import is_super_admin


dotenv.load_dotenv()



def account_mgnt_page():
    st.title("Account Management")
    st.sidebar.button("⬅ Back", on_click=go_back)
    st.button("Create Account", on_click=on_click)
    display_accounts()
    

def display_accounts():
    x_api_key = os.getenv("ADMIN_API_KEY")
    session = session_manager.get_session()
    token = session.cookies.get_dict().get("access_token")
    response = session.get("http://localhost:8000/api/users", headers={"x-api-key": x_api_key, "Authorization": f"Bearer {token}"})
    
    if response.status_code == 403 or response.status_code == 401:
        st.error("Unauthorized access. Please login again.")
    elif response.status_code == 200:
        users = response.json()
        owner_account = find_owner_account(users)
        accounts = get_accounts_except_owner(users)
        st.html("""
        <style>
            .account-card {
                padding: 10px;
                margin: 10px 0;
            }
        </style>
        """)
        display_owner_account(owner_account)
        st.html("<hr>")
        display_other_accounts(accounts)
            
            
def display_owner_account(owner_account):
    with st.container():
        st.markdown("<h3>Your Account</h3>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"""
                <div class="account-card">
                    <b>Username:</b> {owner_account["username"]}<br>
                    <b>Name:</b> {owner_account["first_name"]} {owner_account["last_name"]}<br>
                </div>
                """,
                unsafe_allow_html=True
                )
            
        with p2:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                change_password_button(disable=False)
            with col2:
                reset_password_button(owner_account["username"], disable=True)
            with col3:
                delete_account_button(owner_account["username"], disable=True)
            

def display_other_accounts(accounts):
    with st.container():
        st.markdown("<h3>Other Accounts</h3>", unsafe_allow_html=True)
        if accounts is None:
            st.html("""<p class="account-card">No accounts found.</p>""")
        else:
            for account in accounts:
                p1, p2 = st.columns(2)
                with p1:
                    st.markdown(f"""
                    <div class="account-card">
                        <b>Username:</b> {account["username"]}<br>
                        <b>Name:</b> {account["first_name"]} {account["last_name"]}<br>
                    </div>
                    """,
                    unsafe_allow_html=True
                    )
                    
                with p2:
                    if is_super_admin(): 
                        disable = False 
                    else: 
                        disable = True
                        
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        change_password_button(disable=True, key=f'{account["username"]}_change_password')
                    with col2:
                        reset_password_button(account["username"], disable=disable, key=f'{account["username"]}_reset_password')
                    with col3:
                        delete_account_button(account["username"], disable=disable, key=f'{account["username"]}_delete_account')

    
    
def find_owner_account(users):
    ssbs = SessionStorage()
    session_data = ssbs.getItem("saved_session_data")
    if session_data is None:
        return None
    for user in users["users"]:
        if user["username"] == session_data["username"]:
            return user
    return None

def get_accounts_except_owner(users):
    ssbs = SessionStorage()
    session_data = ssbs.getItem("saved_session_data")
    if session_data is None:
        return None
    accounts = []
    for user in users["users"]:
        if user["username"] != session_data["username"]:
            accounts.append(user)
    if len(accounts) == 0:
        return None
    else:
        return accounts

def on_click():
    st.session_state.page = SIGNUP_PAGE
    
def go_back():
    st.session_state.page = ADMIN_DASHBOARD
    

if __name__ == "__main__":
    account_mgnt_page()