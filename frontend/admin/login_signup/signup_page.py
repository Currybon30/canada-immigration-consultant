import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import requests
import dotenv
from auth.user_authentication import is_super_admin
from Home import session_manager
import time
from screens import *
dotenv.load_dotenv()


def signup_page():
    if not is_super_admin():
        st.error("You are not authorized to access this page. Please go back.")
        st.sidebar.button("⬅ Back", on_click=go_back)
        return
    
    st.title("Create a new admin account")
    get_user_inputs()
    
def get_user_inputs():
    st.sidebar.button("⬅ Back", on_click=go_back)
    st.session_state.error = False
    
    username = st.text_input(
        "Username *",
        value="",
        help="Type your username."
    )
    
    password = st.text_input(
        "Password *",
        value="",
        help="Type your password."
    )
    
    confirm_password = st.text_input(
        "Confirm Password *",
        value="",
        help="Type your password again."
    )
    
    first_name = st.text_input(
        "First Name *",
        value="",
        help="Type your first name."
    )
    
    last_name = st.text_input(
        "Last Name *",
        value="",
        help="Type your last name."
    )
    
    middle_name = st.text_input(
        "Middle Name",
        value="",
        help="Type your middle name."
    )
    
    email = st.text_input(
        "Email *",
        value="",
        help="Type your email."
    )
    
    phone_number = st.text_input(
        "Phone Number",
        value="",
        help="Type your phone number."
    )
    
    is_super_admin = st.checkbox(
        "Is super admin?",
        value=False,
        help="False by default."
    )
    
    st.button(
        "Create Account",
        on_click=lambda: on_submit(
            username, 
            password, 
            confirm_password, 
            first_name, 
            last_name, 
            middle_name, 
            email, 
            phone_number, 
            is_super_admin
        )
    )
    
    

def on_submit(username, password, confirm_password, first_name, last_name, middle_name, email, phone_number, is_super_admin):
    if username == "":
        st.error("Username cannot be empty.")
        return
    
    if password == "":
        st.error("Password cannot be empty.")
        return
    
    if confirm_password == "":
        st.error("Please confirm your password.")
        return
    
    if first_name == "":
        st.error("First name cannot be empty.")
        return
    
    if last_name == "":
        st.error("Last name cannot be empty.")
        return
    
    if email == "":
        st.error("Email cannot be empty.")
        return
    
    if password != confirm_password:
        st.error("Passwords do not match. Please try again.")
        return
    
    user = {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name if middle_name != "" else None,
        "email": email,
        "phone_number": phone_number if phone_number != "" else None,
        "is_super_admin": is_super_admin
    }
    
    x_api_key = os.getenv("ADMIN_API_KEY")
    session = session_manager.get_session()
    token = session.cookies.get_dict().get("access_token")
    headers = {
        "x-api-key": x_api_key
    }
    
    response = session.post("http://localhost:8000/auth/signup", json=user, headers=headers, cookies={"access_token": token})
    
    if response.status_code == 201:
        success_msg = st.success("User created successfully.")
        time.sleep(2)
        success_msg.empty()
        st.session_state.error = False
        st.session_state.page = ACCOUNT_MGNT_PAGE
    else:
        st.error("An error occurred. Please try again.")
        
def go_back():
    st.session_state.page = ACCOUNT_MGNT_PAGE
    
if __name__ == "__main__":
    signup_page()