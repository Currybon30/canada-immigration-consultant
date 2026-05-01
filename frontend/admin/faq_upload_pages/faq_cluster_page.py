import streamlit as st
from screens import *
from Home import session_manager
import time
import os
from functools import partial
from dotenv import load_dotenv
load_dotenv()

def faq_cluster_page():
    st.title("FAQ Clustering")
    st.sidebar.button("⬅ Back", on_click=go_back)
    initialize_session_state()
    get_user_inputs()
    
    
def initialize_session_state():
    if 'clustered_query' not in st.session_state:
        st.session_state.clustered_query = False
    if 'faq_kmeans_docs' not in st.session_state:
        st.session_state.faq_kmeans_docs = []
    if 'num_unclustered_queries' not in st.session_state:
        st.session_state.num_unclustered_queries = 0
    if 'category' not in st.session_state:
        st.session_state.category = ""

def get_user_inputs():
    category = st.selectbox(
        "Select Category *", 
        options=["","study permit", "pgwp", "visa"],
        on_change=on_change,
        key="category"
    )

    st.write(f"Total number of unprocessed queries: {st.session_state.num_unclustered_queries}")
    
    st.button(
        "Proceed",
        on_click=partial(on_submit, category),
    )
    
def on_change():
    category = st.session_state.category
    if category == "":
        st.session_state.num_unclustered_queries = 0
        st.session_state.faq_kmeans_docs = []
        st.session_state.clustered_query = False
        st.session_state.category = ""
        return

    st.session_state.category = category
    session = session_manager.get_session()
    token = session.cookies.get_dict().get("access_token")
    x_api_key = os.getenv("ADMIN_API_KEY")
    
    with st.spinner("Please wait..."):
        response = session.get(
            f'https://canada-immigration-consultant.onrender.com//api/faqs/total-number-unclustered-queries?category={category}',
            headers={"x-api-key": x_api_key}, cookies={"access_token": token}
        )
    if response.status_code == 200:
        data = response.json()
        st.session_state.num_unclustered_queries = data.get("total_unclustered_queries", 0)
    
def on_submit(category):
    if category == "":
        error_msg = st.error("Please select a category.")
        time.sleep(3)
        error_msg.empty()
        return
    if st.session_state.num_unclustered_queries == 0:
        error_msg = st.error("No unclustered queries available.")
        time.sleep(3)
        error_msg.empty()
        return
    if st.session_state.num_unclustered_queries < 2:
        error_msg = st.error("Not enough unclustered queries available.")
        time.sleep(3)
        error_msg.empty()
        return
    
    session = session_manager.get_session()
    token = session.cookies.get_dict().get("access_token")
    x_api_key = os.getenv("ADMIN_API_KEY")
    response = session.get(
        f'https://canada-immigration-consultant.onrender.com//api/faqs/kmeans-cluster?category={category}',
        headers={"x-api-key": x_api_key}, cookies={"access_token": token}
    )
    if response.status_code == 200:
        data = response.json()
        st.session_state.faq_kmeans_docs = data.get("pending_new_faqs", [])
        st.session_state.clustered_query = True
        st.session_state.num_unclustered_queries = 0
        sucess_msg = st.success("Clustering completed successfully. Redirecting to upload page...")
        time.sleep(3)
        sucess_msg.empty()
        st.session_state.page = UPLOAD_FAQ_PAGE
    else:
        error_msg = st.error("An error occurred while clustering FAQs.")
        time.sleep(3)
        error_msg.empty()
    
def go_back():
    st.session_state.num_questions = 1
    for i in st.session_state.keys():
        if i.startswith("faq_"):
            st.session_state.pop(i)
    st.session_state.faq_kmeans_docs = []
    st.session_state.clustered_query = False
    st.session_state.num_unclustered_queries = 0
    st.session_state.category = ""
    st.session_state.page = FAQ_OPTIONS_PAGE