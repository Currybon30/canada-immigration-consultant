import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import requests
import dotenv
import os
import time
from Home import session_manager

dotenv.load_dotenv()


def upload_pdf_page():
    x_api_key = os.getenv("ADMIN_API_KEY")
    initialize_session_state()
    st.title("Upload PDF")

    option, update_pdf_id, category, skip_tags, inline_txt_removed, uploaded_file = get_user_inputs()

    st.button("Upload", on_click=lambda: on_submit(option, update_pdf_id, category, skip_tags, inline_txt_removed, uploaded_file, x_api_key))

    handle_response()
    
def initialize_session_state():
    if 'processing_done' not in st.session_state:
        st.session_state.processing_done = False
    if 'backend_response' not in st.session_state:
        st.session_state.backend_response = None
    if 'error' not in st.session_state:
        st.session_state.error = False

def get_user_inputs():
    st.sidebar.button("⬅ Back", on_click=go_back)
    
    option = st.selectbox(
        "Select an option *",
        ("-- Please select one --", "Add a new PDF document", "Update an existing PDF document"),
        key="upload_pdf_option",
        on_change=on_option_select
    )
    
    if st.session_state.upload_pdf_option == "Update an existing PDF document":
        update_pdf_id = st.text_input(
            "Document ID needs to be updated*",
            value="",
            help="Type the ID of the document you want to update.",
            placeholder="e.g. study-permit-2025-01-01"
        )
    else:
        update_pdf_id = None
    
    category = st.text_input(
        "Categories *",
        value="",
        help="Type the categories of the document. Separate each category by comma.",
        placeholder="e.g. Study Permit, Work Permit"
    )

    skip_tags = st.text_input(
        "Skip headings", 
        value="",
        help="Type the sections/subsections you want to skip. Separate them by comma.",
        placeholder="e.g. Introduction, Conclusion"
    ) 

    inline_txt_removed = st.text_area(
        "Inline text removed",
        value="",
        help="Type the inline text you want to remove. Separate each text by comma.",
        placeholder="e.g. lorem ipsum, dolor sit amet"
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file *", 
        type=["pdf"], 
        accept_multiple_files=False,
        help="You can upload one PDF file at a time.",
    )

    return option, update_pdf_id, category, skip_tags, inline_txt_removed, uploaded_file



def on_submit(option, update_pdf_id, category, skip_tags, inline_txt_removed, uploaded_file, x_api_key):
    if option == "-- Please select one --":
        st.error("⚠ Please select an option.")
        
    if option != "-- Please select one --" and update_pdf_id == "":
        st.error("⚠ Please provide the document ID to delete.")
        return
    
    if category == "":
        st.error("⚠ Please provide the categories.")
        return
    
    if uploaded_file is None:
        st.error("⚠ Please upload a PDF file.")
        return
    
    if category and uploaded_file and option != "-- Please select one --":
        st.session_state.processing_done = False
        st.session_state.error = False
            
        
        category_send = category.split(',')
        category_send = [x.lower().strip() for x in category_send]
        skip_tags_send = skip_tags.split(',')
        skip_tags_send = [x.strip() for x in skip_tags_send]
        inline_txt_removed_send = inline_txt_removed.split(',')
        headers = {"x-api-key": x_api_key}
        file = {"pdf_file": uploaded_file}
        if update_pdf_id is not None:
            data = {
                "skip_tags": skip_tags_send,
                "category": category_send,
                "txt_removed": inline_txt_removed_send,
                "update_pdf_id": update_pdf_id
            }
        else:
            data = {
                "skip_tags": skip_tags_send,
                "category": category_send,
                "txt_removed": inline_txt_removed_send
            }
        
        with st.spinner("PDF is being processed..."):
            try:
                session = session_manager.get_session()
                response = session.post("http://localhost:8000/api/upload-pdf", headers=headers, files=file, data=data)
                st.session_state.backend_response = response.json()
                if response.status_code != 201:
                    st.session_state.error = True
            except requests.exceptions.RequestException:
                st.session_state.error = True
        
        st.session_state.processing_done = True


def handle_response():
    if st.session_state.processing_done and st.session_state.error == False:
        # Redirect to the edit extracted PDF page after successful upload
        st.session_state.page = "edit_extracted_pdf_page"
        st.rerun()
        
    elif st.session_state.processing_done and st.session_state.error:
        error_message = st.error("⚠ There was an error processing the PDF. Please try again.")
        time.sleep(5)
        error_message.empty()
    
def on_option_select():
    upload_pdf_option = st.session_state.upload_pdf_option
    if upload_pdf_option == "-- Please select one --":
        st.error("⚠ Please select an option.")
        
def go_back():
    st.session_state.page = "admin_dashboard"