import streamlit as st
import requests
from screens import *
from auth.user_authentication import decode_jwt
from streamlit_session_browser_storage import SessionStorage
from Home import session_manager
import extra_streamlit_components as stx



def login_page():
    st.title("Admin Login")
    get_user_inputs()
    
        
def get_user_inputs():
    st.session_state.error = False
    
    username = st.text_input(
        "Username",
        value="",
        help="Type your username."
    )
    
    password = st.text_input(
        "Password",
        value="",
        help="Type your password.",
        type="password"
    )
    
    st.button("Login", on_click=lambda: on_submit(username, password))


def on_submit(username, password):
    if username == "" or password == "":
        st.error("Error: Username and password cannot be empty.")
        return
    form_data = {
        "username": username,
        "password": password
    }
    session = session_manager.get_session()
    response = session.post("https://l7f99zws-8000.use.devtunnels.ms/auth/login", data=form_data)
    if response.status_code == 200:
        cookies = session.cookies.get_dict()
        token = cookies.get("access_token")
        ssbs = SessionStorage()
        payload = decode_jwt(token)
        saved_data = {
            "admin_logged_in": True,
            "username": payload["username"],
            "is_super_admin": payload["is_super_admin"],
            "expiry": payload["exp"]
        }
        
        ssbs.setItem("saved_session_data", saved_data)
        st.session_state.page = ADMIN_DASHBOARD
    else:
        st.session_state.error = True
        st.error("Error: Incorrect username or password. Please try again.")
 
if __name__ == "__main__":
    login_page()