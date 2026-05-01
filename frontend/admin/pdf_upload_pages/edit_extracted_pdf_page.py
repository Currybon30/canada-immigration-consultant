import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import requests
import time
import dotenv
from Home import session_manager
from screens import *
import os
from functools import partial

dotenv.load_dotenv()


def edit_extracted_pdf_page():
    st.title("Edit Extracted a PDF Document")
      
    if "backend_response" in st.session_state:
        if "docs" not in st.session_state or st.session_state.docs is None:
            st.session_state.docs = st.session_state.backend_response.get("docs", [])
            

        get_user_input()
    else:
        st.write("Error: No data found.")
        st.stop()
    
def get_user_input():
    st.sidebar.button("⬅ Back", on_click=go_back)
    ofc_doc_id = st.text_input(
        "Enter document ID *",
        value="",
        help="Type the document ID. Should be title of the document and the modified date of the document.",
        placeholder="e.g., study-permit-2025-01-01"
    )
    
    st.subheader("Documents")
    st.write("Please review the text carefully")
    updated_docs = []
    for doc in st.session_state.docs:
        with st.expander(f"Document ID: {doc['id'] + 1}"):
            st.button(
                "🗑️Remove",
                on_click=partial(on_remove_doc, doc),
                key=f"remove_doc_{doc['id']}"
            )
            doc_key = "doc_" + str(doc['id'])
            
            if doc_key not in st.session_state:
                st.session_state[doc_key] = {
                    "tags": ", ".join(tag.lower() for tag in doc['tags']),
                    "content": doc['content'],
                    "hyperlinks": doc['hyperlinks'],
                    "ref_link": doc['ref_link']
                }
                
            st.session_state[doc_key]["tags"] = st.text_input("Tags:", st.session_state[doc_key]["tags"], key=f"tags_{doc['id']}")
            st.session_state[doc_key]["content"] = st.text_area("Content:", st.session_state[doc_key]["content"], key=f"content_{doc['id']}")
            
            st.write("Hyperlinks:")
            st.write("If you don't want to include a hyperlink, leave the fields empty.")
            updated_hyperlinks = []
            for i, hyperlink in enumerate(doc['hyperlinks']):
                hyperlink_parts = hyperlink.split(": ")
                original_hyperlink = hyperlink_parts[0]
                original_text = hyperlink_parts[1]
                hyperlink_col, text_col = st.columns(2)
                with hyperlink_col:
                    edited_hyperlink = st.text_area(f"Hyperlink:", original_hyperlink, key=f"hyperlink_{doc['id']}_{i}", label_visibility="collapsed")
                with text_col:
                    edited_hyperlink_text = st.text_area(f"Hyperlink Text:", original_text, key=f"hyperlink_text_{doc['id']}_{i}", label_visibility="collapsed")
                    
                if edited_hyperlink != original_hyperlink or edited_hyperlink_text != original_text:
                    updated_hyperlinks.append(f"{edited_hyperlink}: {edited_hyperlink_text}")
                elif edited_hyperlink is None or edited_hyperlink == "" or edited_hyperlink_text is None or edited_hyperlink_text == "":
                    continue
                else:
                    updated_hyperlinks.append(original_hyperlink + ": " + original_text)
                
            st.session_state[doc_key]["hyperlinks"] = updated_hyperlinks
            st.session_state[doc_key]["ref_link"] = st.text_input("Reference Link:", st.session_state[doc_key]["ref_link"], key=f"ref_link_{doc['id']}") 

            
            updated_docs.append({
                "id": doc['id'],
                "tags": st.session_state[doc_key]["tags"].lower().split(", "),
                "content": st.session_state[doc_key]["content"],
                "hyperlinks": st.session_state[doc_key]["hyperlinks"],
                "ref_link": st.session_state[doc_key]["ref_link"]
            })
            
    st.session_state.docs = updated_docs
    st.button(
        "Save Changes",
        on_click=lambda: on_save_changes(ofc_doc_id, st.session_state.docs)
    )
    
def on_save_changes(ofc_doc_id, docs):
    if not ofc_doc_id:
        st.error("Error: Document ID is required.")
        return
    data = {
        "docs": docs,
        "ofc_doc_id": ofc_doc_id
    }
    headers = {
        "x-api-key": os.getenv("ADMIN_API_KEY")
    }
    with st.spinner("Please wait..."):
        st.session_state.error = False
        try:
            session = session_manager.get_session()
            response = session.post("https://canada-immigration-consultant.onrender.com//api/save-pdf-to-pinecone", headers=headers, json=data)
            st.session_state.backend_response = response.json()
            if response.status_code != 201:
                st.session_state.error = True
        except requests.exceptions.RequestException:
            st.session_state.error = True
    
    if st.session_state.error:
        st.error("Error: Something went wrong. Please try again.")
    else:
        success_message = st.success("Changes saved successfully. Redirecting to the upload page...")
        time.sleep(1.5)
        success_message.empty()
        st.session_state.__delitem__("docs")
        st.session_state.pop("ofc_doc_id", None)
        for key in list(st.session_state.keys()):
            if key.startswith("doc_") or key.startswith("tags_") or key.startswith("content_") or key.startswith("hyperlink_") or key.startswith("ref_link_"):
                st.session_state.pop(key, None)
        st.session_state.processing_done = False
        st.session_state.page = UPLOAD_PDF_PAGE
   
def on_remove_doc(doc):
    if doc not in st.session_state.docs:
        return
    st.session_state.docs.remove(doc)
    if len(st.session_state.docs) == 0:
        st.session_state.__delitem__("docs")
        st.session_state.pop("ofc_doc_id", None)
        for key in list(st.session_state.keys()):
            if key.startswith("doc_") or key.startswith("tags_") or key.startswith("content_") or key.startswith("hyperlink_") or key.startswith("ref_link_"):
                st.session_state.pop(key, None)
        msg = st.warning("No documents left. Redirecting to the upload page...")
        time.sleep(2)
        msg.empty()
        st.session_state.processing_done = False
        st.session_state.page = UPLOAD_PDF_PAGE

def go_back():
    st.session_state.__delitem__("docs")
    st.session_state.pop("ofc_doc_id", None)
    for key in list(st.session_state.keys()):
        if key.startswith("doc_") or key.startswith("tags_") or key.startswith("content_") or key.startswith("hyperlink_") or key.startswith("ref_link_"):
            st.session_state.pop(key, None)
    st.session_state.processing_done = False
    st.session_state.page = UPLOAD_PDF_PAGE
            
