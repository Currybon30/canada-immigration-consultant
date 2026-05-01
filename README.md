# Canadian Immigration Consultant Chatbot 🍁🤖

## Table of Contents
- [Canadian Immigration Consultant Chatbot 🍁🤖](#canadian-immigration-consultant-chatbot-)
  - [Table of Contents](#table-of-contents)
    - [Project Description](#project-description)
    - [Demo](#demo)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Contributors](#contributors)
    - [License](#license)


### Project Description

<p align="center">
  <img src="https://github.com/user-attachments/assets/def87a39-ee15-4681-8d68-2c6a364823b4" alt="Image description" width="250"/>
</p>

**IRIS (Immigration Resources for International Students)** is a full-stack AI chatbot that delivers real-time immigration guidance using a Retrieval-Augmented Generation (RAG) system. It enables users to navigate complex IRCC (Immigration, Refugees and Citizenship Canada) policies through a conversational interface backed by a dynamic, searchable knowledge base.

International students often struggle to navigate legal documents, frequent policy updates, and long support wait times. IRIS addresses this gap by offering a reliable, user-friendly solution available 24/7.

**🔍 Key Features**
- **Large Language Model Integration (LLMs):** Delivers conversational, human-like responses to help users understand complex immigration terms and scenarios.
- **Retrieval-Augmented Generation (RAG):** Ensures answers are grounded in the most up-to-date IRCC policy documents stored in a custom, searchable vector database.
- **Multi-Agent System with LangGraph:** Applies agentic AI principles to autonomously manage tasks such as document retrieval, question answering, and dialogue flow—minimizing human intervention.
- **Dynamic Admin Panel:** Enables authorized staff to update policies and documentation in real time, ensuring accuracy and compliance as IRCC guidelines evolve.

**🛠️ Tech Stack**
- 🖥️ Streamlit – Frontend interface for chatbot and admin panel
- ⚡ FastAPI – High-performance backend API framework
- 🧲 Pinecone – Vector similarity search for document retrieval (RAG)
- 🍃 MongoDB – NoSQL database for storing user queries, sessions, and logs
- 🤗 Hugging Face – Pretrained LLMs for natural language understanding and response generation

### Demo

Live Demo: https://iris-canada.streamlit.app/

<img width="1919" height="1012" alt="Screenshot 2026-05-01 152054" src="https://github.com/user-attachments/assets/651950ca-7e32-4adf-ac23-0f103e6e9836" />


**Note:** 
- Designed for demonstration purposes; usage may be rate-limited
- Hosted on a free-tier cloud service  
- May experience cold starts after periods of inactivity 

### Installation
<b><i>1. Clone the repository: </i></b>

```
git clone https://github.com/Curry091104/immigration-consultant-capstone.git
```

<b><i>2. Install dependencies: </i></b>

> - Python version must be 3.11.
> - To prevent dependency conflicts, it's recommended that separate virtual environment folders for both the front end and back end be created.
> - To leverage GPU, after running ```pip install -r requirements.txt```, please run a command to reinstall PyTorch. Check this [link](https://pytorch.org/get-started/locally/) for the installation command.

Frontend
```
cd frontend
pip install -r requirements.txt
```

Backend
```
cd backend
pip install -r requirements.txt
```

### Usage
To run the project, use the following command: </br></br>

> - Ensure that your environment is activated before running the command.
> - Verify that you have a .env file with all required keys.
> - Run the backend (server) first and let it finish loading, then run the frontend (client).

Backend
```
cd backend
uvicorn main:app
```
Frontend
```
cd frontend
streamlit run Home.py
```

### Contributors
- Tuong Nguyen Pham - [@Curry091104](https://github.com/Curry091104)
- Ngoc Quynh Nhu Nguyen - [@NhuNhuNguyen](https://github.com/NhuNhuNguyen)
- Kwok Wing Tang - [@Patrickccca](https://github.com/Patrickccca)
- Joan Suaverdez - [@jsuaverd](https://github.com/jsuaverd)
- Huaye Zhan - [@howardzhan12](https://github.com/howardzhan12)
- Dongheun Yang - [@DongheunDanielYang](https://github.com/DongheunDanielYang)

### License
This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](LICENSE)
