import streamlit as st
from screens import *
from Home import session_manager

def security_page():
    st.title("Change Password")
    if st.session_state.error:
        st.error("Please fill in all the required fields.")
    get_user_inputs()


def get_user_inputs():
    st.sidebar.button("⬅ Back", on_click=go_back)
    st.session_state.error = False
    
    current_password = st.text_input(
        "Current Password *",
        value="",
        help="Type your current password.",
        type="password"
    )
    
    new_password = st.text_input(
        "New Password *",
        value="",
        help="Type your new password.",
        type="password"
    )
    
    confirm_new_password = st.text_input(
        "Confirm New Password *",
        value="",
        help="Type your new password again.",
        type="password"
    )
    
    st.button("Submit", on_click=lambda: change_password(current_password, new_password, confirm_new_password))
    
    
def change_password(current_password, new_password, confirm_new_password):
    if not current_password or not new_password or not confirm_new_password:
        st.session_state.error = True
        return
    
    if new_password != confirm_new_password:
        st.error("New password and confirm new password do not match.")
        return
    
    session = session_manager.get_session()
    token = session.cookies.get_dict().get("access_token")
    response = session.put("https://canada-immigration-consultant.onrender.com/api/users/update-password", json={"new_password": new_password, "current_password": current_password}, headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code == 200:
        st.success("Password updated successfully.")
    elif response.status_code == 400:
        st.error("Incorrect current password.")
    else:
        st.error("An error occurred. Please try again.")
        
    st.session_state.error = False
    
    
def go_back():
    if 'prev_page' in st.session_state:
        prev_page = st.session_state.prev_page
        st.session_state.__delitem__('prev_page')
        st.session_state.page = prev_page
        
    else:
        st.session_state.page = ADMIN_DASHBOARD
    
if __name__ == "__main__":
    security_page()