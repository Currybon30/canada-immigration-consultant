import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import streamlit as st
from screens import *
from streamlit_session_browser_storage import SessionStorage
from Home import session_manager
import jwt

def on_logout():
    ssbs = SessionStorage()
    session = session_manager.get_session()
    response = session.post("http://localhost:8000/auth/logout")
    if response.status_code == 200:
        ssbs.deleteItem("saved_session_data")
        st.session_state.page = LOGIN_PAGE
    else:
        st.error("Error: Unable to logout. Please try again.")
        
def decode_jwt(token):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.ExpiredSignatureError:
        return "Signature expired. Please log in again."
    except jwt.InvalidTokenError:
        return "Invalid token. Please log in again."
    except Exception as e:
        return "An error occurred. Please log in again."
    
def is_super_admin():
    ssbs = SessionStorage()
    session_data = ssbs.getItem("saved_session_data")
    if session_data is None:
        return False
    if session_data.get("is_super_admin") is None or session_data.get("is_super_admin") == False:
        return False
    return True