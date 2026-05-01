import streamlit as st
import requests
import json
import asyncio
import aiohttp
import time
import re



st.set_page_config(
        page_title="IRIS",
        page_icon="🍁",
        layout="wide"
)
st.logo(
    "frontend/static/iris-side.png",
    size="large"
)

st.sidebar.title("IRIS Disclaimer")
st.sidebar.write("""
    <p style="font-size: 0.8rem;">
        Please be aware that IRIS chatbot is an automated system, and it may not always
        provide 100% accurate information. While we strive to provide accurate information,
        we cannot guarantee the accuracy, completeness, or timeliness of the information provided by IRIS chatbot.
    </p>
""", unsafe_allow_html=True)

st.sidebar.title("Avis de non-responsabilité d'IRIS")
st.sidebar.write("""
    <p style="font-size: 0.8rem;">
        Veuillez noter que le chatbot IRIS est un système automatisé et qu'il peut ne pas toujours fournir des informations exactes à 100 %. 
        Bien que nous nous efforcions de fournir des informations exactes, 
        nous ne pouvons garantir leur exactitude, leur exhaustivité ni leur actualité.
    </p>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    [data-testid="stChatMessageContent"] p{
        font-size: 1.3rem;
    }
    
    .ea2tk8x2 {
        width: 60px;
        height: 60px; 
        font-size: 2rem;
    }
    </style>
    """, unsafe_allow_html=True
)

def get_consultation_page():
    get_iris_id()
        
    if st.session_state.error_chat:
        st.session_state.disabled_chat = True
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message["avatar"]):
            st.markdown(message["text"])
        
    if not any(message["text"] == "Hello! I am IRIS, your virtual assistant. I am here to help you with your queries. Before starting, I suggest you read the IRIS Disclaimer in the left sidebar to understand the terms, conditions, and limitations associated with its use.\n\nBonjour ! Je suis IRIS, votre assistante virtuelle. Je suis là pour répondre à vos questions. Avant de commencer, je vous suggère de lire l'avis de non-responsabilité d'IRIS dans la barre latérale gauche pour comprendre les conditions d'utilisation et les limitations liées à son utilisation." for message in st.session_state.messages):
        
        time.sleep(1.5)
        
        waiting_message = st.empty()
        waiting_message.markdown("IRIS is typing...")
        
        time.sleep(2)
        
        waiting_message.empty()
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("Hello! I am IRIS, your virtual assistant. I am here to help you with your queries. Before starting, I suggest you read the IRIS Disclaimer in the left sidebar to understand the terms, conditions, and limitations associated with its use.\n\nBonjour ! Je suis IRIS, votre assistante virtuelle. Je suis là pour répondre à vos questions. Avant de commencer, je vous suggère de lire l'avis de non-responsabilité d'IRIS dans la barre latérale gauche pour comprendre les conditions d'utilisation et les limitations liées à son utilisation.")
        st.session_state.messages.append({"role": "assistant", "text": "Hello! I am IRIS, your virtual assistant. I am here to help you with your queries. Before starting, I suggest you read the IRIS Disclaimer in the left sidebar to understand the terms, conditions, and limitations associated with its use.\n\nBonjour ! Je suis IRIS, votre assistante virtuelle. Je suis là pour répondre à vos questions. Avant de commencer, je vous suggère de lire l'avis de non-responsabilité d'IRIS dans la barre latérale gauche pour comprendre les conditions d'utilisation et les limitations liées à son utilisation.", "avatar": "🤖"})
    
    if prompt := st.chat_input("Type your message here...", disabled=st.session_state.disabled_chat):
        try:
            if any(word in prompt.lower() for word in ["bye", "goodbye", "exit", "quit", "thank", "thanks"]):
                with st.chat_message("human", avatar="🧑‍🎓"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "human", "text": prompt, "avatar": "🧑‍🎓"})
                
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown("Please don’t hesitate to use our live chat service again in future – we’re always here to help. I hope to hear from you soon. Take care!")
                st.session_state.messages.append({"role": "assistant", "text": "Please don’t hesitate to use our live chat service again in future – we’re always here to help. I hope to hear from you soon. Take care!", "avatar": "🤖"})
                
                st.session_state.disabled_chat = True
                return
            
            with st.chat_message("human", avatar="🧑‍🎓"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "human", "text": prompt, "avatar": "🧑‍🎓"})
            
            waiting_message = st.empty()
            waiting_message.markdown("IRIS is typing...")
            
            response = asyncio.run(get_iris_response(prompt))
            
            
            with st.chat_message("assistant", avatar="🤖"):
                waiting_message.empty()
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "text": response, "avatar": "🤖"})
            
            
        except Exception as e:
            st.session_state.error_chat = True
            st.session_state.disabled_chat = True
            st.error(f"An error occurred: {e}")
            st.write("Please refresh the page and try again.")
            return

    
def get_iris_id():
    if 'connection_error' in st.session_state and st.session_state.connection_error is not None:
        st.session_state.connection_error.empty()
        del st.session_state.connection_error
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    if 'error_chat' not in st.session_state:
        st.session_state.error_chat = False
    
    if 'disabled_chat' not in st.session_state:
        st.session_state.disabled_chat = False
    
    if 'connection_error' not in st.session_state:
        st.session_state.connection_error = None
        
    try:
        response = requests.get(
            "https://l7f99zws-8000.use.devtunnels.ms/api/iris-id",
            timeout=5
        )
        
        st.write("Content-Type:", response.headers.get("content-type"))
        st.write("Raw response text:")
        st.code(response.text)

        # 🔥 ADD THIS CHECK
        if response.status_code != 200:
            st.error(f"Backend error: {response.status_code}")
            st.write(response.text)
            return

        # 🔥 SAFE JSON PARSE
        data = response.json()

        if "iris_id" not in data:
            st.error("Invalid response format")
            st.write(data)
            return

        st.session_state.iris_id = data["iris_id"]
    except requests.exceptions.ConnectionError:
        st.session_state.connection_error = st.error("Trying to connect to server.\n\nTentative de connexion au serveur.")
        time.sleep(15)
        return
    if 'iris_id' not in st.session_state:
        st.session_state.iris_id = response.json()["iris_id"]
        

async def get_iris_response(input):
    if st.session_state.iris_id is None:
        st.error("Error: Could not connect to IRIS")
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://l7f99zws-8000.use.devtunnels.ms/iris/{st.session_state.iris_id}?user_input={input}") as response:
            response = await response.json()
            response = response["agent_response"]
            # Clean up response
            response = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', response)
            response = re.sub(r'(?<!\\n)\\n(?!\\n)', '\\n\\n', response)
            
            # Remove unintended spaces before line breaks
            response = re.sub(r'\s*\n\s*', '\n', response)
            response = re.sub(r'\s*\\n\s*', '\\n', response)

            # Remove surrounding quotes if present
            response = response.strip('"')
            
            # Remove context after ```, if present
            response = re.sub(r'```.*?$', '', response, flags=re.DOTALL)

            # Remove triple backticks (```), often used in code blocks
            response = re.sub(r"\s*```+\s*", " ", response).strip()
            
            # Ensure that "Reference:" is followed by a newline
            response = re.sub(r'(\n)(Reference:)', r'\1\n\2', response)
            return response
        


get_consultation_page()