import streamlit as st
from screens import *
from Home import session_manager
import time
import os
from functools import partial
from dotenv import load_dotenv
load_dotenv()

def upload_faq_page():
    st.title("Upload FAQs")
    st.sidebar.button("⬅ Back", on_click=go_back)
    initialize_session_state()
    get_user_inputs()
    
def get_user_inputs():
    faq_docs = []
    if 'clustered_query' in st.session_state and st.session_state.clustered_query:
        st.session_state.num_questions = len(st.session_state.faq_kmeans_docs[0]["questions"])
    for i in range(st.session_state.num_questions):
        faq_doc = {}
        with st.expander(f"Question {i + 1}", expanded=True):
            faq_doc_key = f"faq_{i}"
            
            if faq_doc_key not in st.session_state:
                if st.session_state.clustered_query == False:
                    st.session_state[faq_doc_key] = {
                        "categories": "",
                        "faq_id": "",
                        "question": "",
                        "answer": "",
                        "hyperlinks": []
                    }
                else:
                    st.session_state[faq_doc_key] = {
                        "categories": str(st.session_state.faq_kmeans_docs[0]["category"]).strip(),
                        "faq_id": "",
                        "question": str(st.session_state.faq_kmeans_docs[0]["questions"][i]).strip(),
                        "answer": "",
                        "hyperlinks": []
                    }
            if st.session_state.clustered_query == True:
                st.button(
                    "🗑️Remove",
                    on_click=partial(on_remove_doc, faq_doc_key, i),
                    key=f"remove_doc_faq_{i}"
                )
            
            st.session_state[faq_doc_key]["categories"] = st.text_input("Categories *:", st.session_state[faq_doc_key]["categories"], key=f"categories_{i}")
            st.session_state[faq_doc_key]["faq_id"] = st.text_input("Faq ID *:", st.session_state[faq_doc_key]["faq_id"], key=f"faq_id_{i}")
            st.session_state[faq_doc_key]["question"] = st.text_area("Question *:", st.session_state[faq_doc_key]["question"], key=f"question_{i}")
            st.session_state[faq_doc_key]["answer"] = st.text_area("Answer *:", st.session_state[faq_doc_key]["answer"], key=f"answer_{i}")
                
            if 'num_hyperlinks' not in st.session_state[faq_doc_key]:
                st.session_state[faq_doc_key]["num_hyperlinks"] = 1
            
            st.write("Hyperlink:")
            c1, c2 = st.columns([1, 15]) # Adjust the width of the columns as needed
            c1.button("Add", on_click=partial(handle_add_hyperlink_click, faq_doc_key), key=f"add_hyperlink_{i}")
            if st.session_state[faq_doc_key]["num_hyperlinks"] > 1:
                c2.button("Remove", on_click=partial(handle_remove_hyperlink_click, faq_doc_key), key=f"remove_hyperlink_{i}")
            hyperlink_col, text_col = st.columns(2)
            for j in range(st.session_state[faq_doc_key]["num_hyperlinks"]):
                with hyperlink_col:
                    edited_hyperlink = st.text_area(f"Hyperlink:", key=f"hyperlink_q{i}_{j}", label_visibility="collapsed", placeholder="https://www.example.com")
                with text_col:
                    edited_hyperlink_text = st.text_area(f"Hyperlink Text:", key=f"hyperlink_text_q{i}_{j}", label_visibility="collapsed", placeholder="Example")

                if edited_hyperlink != "" and edited_hyperlink_text != "":
                    edited_hyperlink = edited_hyperlink.strip()
                    edited_hyperlink_text = edited_hyperlink_text.strip()
                    combined_hyperlink = f"{edited_hyperlink}: {edited_hyperlink_text}"
                    st.session_state[faq_doc_key]["hyperlinks"].append(combined_hyperlink)
                
        # Add the faq doc to faq_docs
        faq_doc["tags"] = st.session_state[faq_doc_key]["categories"].lower().split(", ")
        faq_doc["tags"] = [tag.strip() for tag in faq_doc["tags"]]
        faq_doc["faq_id"] = st.session_state[faq_doc_key]["faq_id"]
        faq_doc["question"] = st.session_state[faq_doc_key]["question"]
        faq_doc["answer"] = st.session_state[faq_doc_key]["answer"]
        faq_doc["hyperlinks"] = st.session_state[faq_doc_key]["hyperlinks"]
        faq_docs.append(faq_doc)
        
    if st.session_state.clustered_query == False:
        col1, col2 = st.columns([1, 7]) # Adjust the width of the columns as needed
        col1.button("Add question", on_click=handle_add_question_click)
        if st.session_state.num_questions > 1:
            col2.button("Remove question", on_click=handle_remove_question_click)
        
    st.button("Submit", on_click=lambda: on_submit(faq_docs))
def initialize_session_state():
    if 'num_questions' not in st.session_state:
        st.session_state.num_questions = 1
    if 'clustered_query' not in st.session_state:
        st.session_state.clustered_query = False
    if 'faq_kmeans_docs' not in st.session_state:
        st.session_state.faq_kmeans_docs = []
    if 'num_unclustered_queries' not in st.session_state:
        st.session_state.num_unclustered_queries = 0
    if 'category' not in st.session_state:
        st.session_state.category = ""
    
    
def on_submit(faq_docs):
    for faq_doc in faq_docs:
        if faq_doc["tags"] == "" or faq_doc["faq_id"] == "" or faq_doc["question"] == "" or faq_doc["answer"] == "":
            st.error("Please fill in all the required fields")
            return
        
    if not isinstance(faq_docs, list):
        faq_docs = [faq_docs]
    session = session_manager.get_session()
    token = session.cookies.get_dict().get("access_token")
    x_api_key = os.getenv("ADMIN_API_KEY")
    if st.session_state.clustered_query == False:
        response = session.post("https://canada-immigration-consultant.onrender.com//api/create-faq", json={"faq_docs": faq_docs}, headers={"x-api-key": x_api_key}, cookies={"access_token": token})
    else:
        response = session.post("https://canada-immigration-consultant.onrender.com//api/create-faq", json={"faq_docs": faq_docs, "mongo_db_faq_ids": st.session_state.faq_kmeans_docs[0]["ids"]}, headers={"x-api-key": x_api_key}, cookies={"access_token": token})
    if response.status_code == 201:
        success_msg = st.success("FAQs uploaded successfully")
        time.sleep(2)
        success_msg.empty()
        st.session_state.num_questions = 1
        for i in st.session_state.keys():
            if i.startswith("faq_"):
                st.session_state.pop(i)
        st.session_state.page = ADMIN_DASHBOARD
        
    else:
        st.error("An error occurred while uploading FAQs")

def handle_add_question_click():
    st.session_state.num_questions += 1
    
def handle_remove_question_click():
    if st.session_state.num_questions > 1:
        st.session_state.num_questions -= 1
                
def handle_add_hyperlink_click(faq_index):
    st.session_state[faq_index]["num_hyperlinks"] += 1
    
def handle_remove_hyperlink_click(faq_index):
    if st.session_state[faq_index]["num_hyperlinks"] > 1:
        st.session_state[faq_index]["num_hyperlinks"] -= 1
    
def on_remove_doc(doc_key, index_in_faq_kmeans_docs):
    if doc_key not in st.session_state:
        st.warning("Document not found in session state.")
        return
    
    del st.session_state[doc_key]
    
    if 'faq_kmeans_docs' in st.session_state and len(st.session_state.faq_kmeans_docs) > 0:
        if index_in_faq_kmeans_docs < len(st.session_state.faq_kmeans_docs[0]["questions"]):
            st.session_state.faq_kmeans_docs[0]["questions"].pop(index_in_faq_kmeans_docs)
                
    if st.session_state.faq_kmeans_docs[0]["questions"] == []:
        st.session_state.num_questions = 1
        st.session_state.clustered_query = False
        st.session_state.faq_kmeans_docs = []
        st.session_state.category = ""
        st.session_state.num_unclustered_queries = 0
        st.session_state.page = FAQ_CLUSTER_PAGE
        
def go_back():
    st.session_state.num_questions = 1
    for i in st.session_state.keys():
        if i.startswith("faq_"):
            st.session_state.pop(i)
            
    st.session_state.page = FAQ_OPTIONS_PAGE