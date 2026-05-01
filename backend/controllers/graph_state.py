import os
from typing import TypedDict, List, Optional
from controllers.data_processing import extract_keys_hyperlinks_pinecone
import logging
from utils.llm_extraction_helper import clean_generation
import warnings
warnings.filterwarnings("ignore")

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

memory = None
langsmith_client = None
conv_agent = None
document_search_agent = None
faq_agent = None
cross_check_agent = None
dec_agent = None
crs_links_agent = None
translator = None
_graph = None
_initialized = False
logging.basicConfig(level=logging.CRITICAL, format="%(message)s", handlers=[logging.StreamHandler()])


def _initialize_runtime():
    global _initialized
    global memory, langsmith_client, conv_agent, document_search_agent
    global faq_agent, cross_check_agent, dec_agent, crs_links_agent, translator, _graph

    from langgraph.checkpoint.memory import MemorySaver
    import googletrans

    from controllers.agents.document_search_agent import DocumentSearchAgent
    from controllers.agents.conversation_agent import ConversationAgent
    from controllers.agents.faq_agent import FAQAgent
    from controllers.agents.cross_check_agent import CrossCheckAgent
    from controllers.agents.decision_agent import DecisionAgent
    from controllers.agents.crs_links_agent import CRSLinksAgent

    if _initialized:
        return

    if USE_LOCAL_MODEL:
        print("Loading local LLM...")
        ConversationAgent.load_local_model()
        print("Local LLM loaded successfully")
    else:
        print("Skipping local LLM (using API)")

    memory = MemorySaver()
    # Optional dependency in some deployments; keep startup resilient.
    try:
        import langsmith as ls
        langsmith_client = ls.Client(api_url=LANGSMITH_ENDPOINT, api_key=LANGSMITH_API_KEY)
    except Exception:
        langsmith_client = None
    conv_agent = ConversationAgent()
    document_search_agent = DocumentSearchAgent()
    faq_agent = FAQAgent()
    cross_check_agent = CrossCheckAgent()
    dec_agent = DecisionAgent()
    crs_links_agent = CRSLinksAgent()
    translator = googletrans.Translator()
    _graph = _build_graph()
    _initialized = True


def get_graph():
    _initialize_runtime()
    return _graph

class GraphState(TypedDict):
    sender: Optional[str]
    receiver: Optional[str]
    question: str
    generation: Optional[str]
    documents: Optional[dict]
    crs_links: Optional[List[str]]
    cross_check_needed: Optional[bool]
    time_cross_check: Optional[int]
    revised_message: Optional[str]
    request_user: Optional[str]
    category: Optional[str]
    detected_lang: Optional[str]
    
    
async def conversation_agent(state, **kwargs):
    question = state['question']
    sender = state['sender']
    category = state.get('category', None)
    detected_lang = state.get("detected_lang")
    if sender not in ['document_search_agent', 'faq_agent', 'cross_check_agent', 'crs_links_agent']:
        response = await conv_agent.handle_user_request(question)
        if response[1] != "general" or response[1].lower() != "none":
            detected_lang = response[0]
            if response[0] == "fr" and response[3] == None:
                question = response[2]
            elif response[0] == "fr" and response[3] != None:
                question = response[3]
            elif response[0] == "en" and response[3] != None:
                question = response[3]
        
        if response[0] not in ["en", "fr"]:
            return {
                'question': question,
                'generation': response[1], 
                'detected_lang': detected_lang,
                'sender': 'conversation_agent',
                'receiver': '_end_',
            }
        elif response[1].lower() == "none":
            return {
                'question': question, 
                'generation': "Sorry, I am not able to answer this question. I can help you with questions related to international students in Canada about study permit, PGWP, and visa.",
                'detected_lang': detected_lang,
                'sender': 'conversation_agent',
                'receiver': '_end_',
            }
        elif response[1] == "general":
            prompt = f"""
            Your name is IRIS
            Greet back the user and tell them that you are here to help them with their questions related to international students in Canada about study permit, PGWP, and visa.
            
            Example: 
            User: Hi!
            Agent: Hello! I am IRIS. I am here to help you with your questions related to international students in Canada about study permit, PGWP, and visa. How can I help you today?
            
            # Strict Rules:
            - Do not talk about any other topics, ONLY talk about international students in Canada about study permit, PGWP, and visa.
            - Do not ask for any personal information.
            - Do not ask for any sensitive information.
            - Do not ask for any financial information.
            
            
            ** User's question: **
            {question}
            
            """
            from langchain.schema import HumanMessage
            import asyncio
            agent_response = await asyncio.to_thread(
                conv_agent.chat.invoke,
                [HumanMessage(content=prompt)])
            return {
                'question': question, 
                'generation': agent_response.content,
                'detected_lang': detected_lang,
                'sender': 'conversation_agent',
                'receiver': '_end_',
            }
        elif response[1] == "decision_agent":
            return {
                'question': question, 
                'detected_lang': detected_lang,
                'sender': 'conversation_agent',
                'receiver': 'decision_agent',
            }
    elif sender == 'document_search_agent':
        cross_check_needed = state['cross_check_needed']
        #! Implement text generation in this line
        documents = state['documents']
        if 'time_cross_check' not in state.keys():
            state['time_cross_check'] = 0
        if cross_check_needed:
            generation = conv_agent.handle_document_search_request(document_response=documents, question=question)
            if generation == "Sorry, I am unable to answer this question right now, please ask another question.":
                return {
                    'question': question, 
                    'generation': generation,
                    'category': category,
                    'detected_lang': detected_lang,
                    'sender': 'conversation_agent',
                    'receiver': '_end_',
                }
            return {
                'question': question, 
                'generation': generation,
                'documents': documents,
                'time_cross_check': state['time_cross_check'],
                'category': category,
                'detected_lang': detected_lang,
                'sender': 'conversation_agent',
                'receiver': 'cross_check_agent'
            }
        else:
            request_user = state['request_user']
            generation = conv_agent.handle_document_search_request(request_user, question = question)
            return {
                'question': question, 
                'generation': generation,
                'category': category,
                'detected_lang': detected_lang,
                'sender': 'conversation_agent',
                'receiver': '_end_',
            }
    elif sender == 'cross_check_agent':
        revised_message = state['revised_message']
        documents = state['documents']
        generation = conv_agent.handle_cross_agent_request(revised_message, document=documents, question=question)
        return {
            'question': question, 
            'generation': generation,
            'documents': documents,
            'time_cross_check': state['time_cross_check'],
            'category': category,
            'detected_lang': detected_lang,
            'sender': 'conversation_agent',
            'receiver': 'cross_check_agent'
        }
        
    elif sender == 'faq_agent':
        faq_docs = state['documents']
        generation = conv_agent.handle_faq_request(faq_docs)
        return {
            'question': question, 
            'generation': generation,
            'category': category,
            'detected_lang': detected_lang,
            'sender': 'conversation_agent',
            'receiver': '_end_',
        }
    
    elif sender == "crs_links_agent":
        crs_links = state['crs_links']
        generation = conv_agent.handle_crs_request(question=question, crs_links=crs_links)
        return {
            'question': question,
            'generation': generation,
            'category': category,
            'detected_lang': detected_lang,
            'sender': 'conversation_agent',
            'receiver': '_end_',
        }

def decision_agent(state, **kwargs):
    question = state['question']
    category = dec_agent.classify_question(question)
    detected_lang = state.get("detected_lang")
    is_sp_pgwp_visa = dec_agent.is_the_query_related_to_study_permit_pgwp_or_visa(question)
    if is_sp_pgwp_visa:
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'sender': 'decision_agent',
            'receiver': 'faq_agent'
        }
    else:
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'sender': 'decision_agent',
            'receiver': 'crs_links_agent'
        }

def rag_retrieval(state, **kwargs):
    question = state['question']
    category = state['category']
    detected_lang = state.get("detected_lang")
    filter_pinecone_search = {"tags": {"$in": [category.lower()]}}
    documents = None
    answer = document_search_agent.get_answers(question, filter=filter_pinecone_search)
    if answer == "Answer not found":
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'cross_check_needed': False,
            'sender': 'document_search_agent',
            'receiver': 'conversation_agent',
            'request_user': "Answer not found. Please ask user for more details."
        }
    else:
        documents = [
            {
            "page_content": answer.get('text', ''),
            "metadata": {
                'hyperlinks': answer.get('hyperlinks', []),
                'ref_link': answer.get('ref_link', None)
                }
            }
        ]
        extracted_hyperlinks = extract_keys_hyperlinks_pinecone(docs=documents)
        documents = {
            "page_content": answer.get('text', ''),
            "metadata": {
                'hyperlinks': extracted_hyperlinks,
                'ref_link': answer.get('ref_link', None)
            }
        }
        return {
            'question': question, 
            'category': category,
            'detected_lang': detected_lang,
            'documents': documents, 
            'sender': 'document_search_agent', 
            'receiver': 'conversation_agent',
            'cross_check_needed': True
        }

async def faq_retrieval(state, **kwargs):
    question = state['question']
    category = state['category']
    detected_lang = state.get("detected_lang")
    filter_pinecone_search = {"tags": {"$in": [category.lower()]}}
    answer = await faq_agent.get_answer(question, category = category, filter=filter_pinecone_search)
    if answer == "Not found":
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'documents': [], 
            'sender': 'faq_agent',
            'receiver': 'document_search_agent',
        }
    else:
        documents = [
            {
            "page_content": answer.get('answer', ''),
            "metadata": {
                'hyperlinks': answer.get('hyperlinks', [])
                }
            }
        ]
        extracted_hyperlinks = extract_keys_hyperlinks_pinecone(docs=documents)
        documents = {
            "page_content": answer.get('answer', ''),
            "metadata": {
                'hyperlinks': extracted_hyperlinks
            }
        }
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'documents': documents, 
            'sender': 'faq_agent',
            'receiver': 'conversation_agent',
        }
    
def cross_check(state, **kwargs):
    question = state['question']
    detected_lang = state.get("detected_lang")
    state['time_cross_check'] = state.get('time_cross_check', 0) + 1
    time_cross_check = state['time_cross_check']
    category = state['category']
    generation = state['generation']
    documents = state['documents']
    refined_doc = documents['page_content']
    similarity_score = cross_check_agent.cross_check(generation, refined_doc)
    if time_cross_check <= 2:
        if similarity_score > 0.75:
            return {
                'question': question,
                'generation': generation,
                'category': category,
                'detected_lang': detected_lang,
                'revise_message': None,
                'sender': 'cross_check_agent',
                'receiver': '_end_',
            }
        else:
            revised_message = "The generated answer is not similar to the retrieved documents. Please revise the answer that matches the retrieved documents closely."
            return {
                'question': question, 
                'documents': documents,
                'category': category,
                'detected_lang': detected_lang,
                'time_cross_check': time_cross_check,
                'revised_message': revised_message,
                'sender': 'cross_check_agent',
                'receiver': 'conversation_agent'
            } 
    else:
        generation = "Sorry, I am unable to answer this question right now, please ask another question."
        return {
            'question': question,
            'generation': generation,
            'category': category,
            'detected_lang': detected_lang,
            'sender': 'cross_check_agent',
            'receiver': '_end_',
        }
        
def crs_agent(state, **kwargs):
    question = state['question']
    category = state['category']
    detected_lang = state.get("detected_lang")
    crs_links = crs_links_agent.get_recommendations(question)
    if crs_links == "No recommendations found":
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'request_user': "No recommendations found. Please ask user for more details.",
            'sender': 'crs_links_agent',
            'receiver': 'conversation_agent'
        }
    else:
        return {
            'question': question,
            'category': category,
            'detected_lang': detected_lang,
            'crs_links': crs_links,
            'sender': 'crs_links_agent',
            'receiver': 'conversation_agent'
        }
    
def _build_graph():
    from langgraph.graph import StateGraph, END, START
    immigration_graph = StateGraph(GraphState)

    # Define the nodes
    immigration_graph.add_node("conversation_agent", conversation_agent)
    immigration_graph.add_node("document_search_agent", rag_retrieval)
    immigration_graph.add_node("faq_agent", faq_retrieval)
    immigration_graph.add_node("cross_check_agent", cross_check)
    immigration_graph.add_node("decision_agent", decision_agent)
    immigration_graph.add_node("crs_links_agent", crs_agent)

    # Build the graph
    immigration_graph.add_edge(START, "conversation_agent")
    immigration_graph.add_conditional_edges(
        "conversation_agent",
        lambda state: state['receiver'],
        {
            "decision_agent": "decision_agent",
            "cross_check_agent": "cross_check_agent",
            '_end_': END
        }
    )

    immigration_graph.add_conditional_edges(
        "decision_agent",
        lambda state: state['receiver'],
        {
            "faq_agent": "faq_agent",
            "crs_links_agent": "crs_links_agent"
        }
    )

    immigration_graph.add_conditional_edges(
        "faq_agent",
        lambda state: state['receiver'],
        {
            "document_search_agent": "document_search_agent",
            "conversation_agent": "conversation_agent"
        }
    )
    immigration_graph.add_conditional_edges(
        "cross_check_agent",
        lambda state: state['receiver'],
        {
            "conversation_agent": "conversation_agent",
            "_end_": END
        }
    )

    immigration_graph.add_edge("crs_links_agent", "conversation_agent")
    immigration_graph.add_edge("document_search_agent", "conversation_agent")
    return immigration_graph.compile(checkpointer=memory)

# #Get image bytes from the graph
# img_bytes = agents.get_graph().draw_mermaid_png()

# # Convert bytes to an image
# img = mpimg.imread(BytesIO(img_bytes), format="png")

# # Display the image
# plt.figure(figsize=(10, 6))
# plt.imshow(img)
# plt.title("Multi-agent collaboration graph", fontsize=20)
# plt.axis("off")  # Hide axes
# plt.show()

async def run_agent(user_input, iris_id = "1"):
    inputs = {
        'sender': "user",
        'question': user_input,
        'detected_lang': None,
    }
    config = {"configurable": {"thread_id": iris_id}}
    graph = get_graph()
    detected_lang = None
    try:
        async for output in graph.astream(inputs, config):
            try:
                logging.info("\nOutput from the agent: ")
                logging.critical(output)
                logging.info("\n")
                if 'conversation_agent' in output.keys():
                    if output['conversation_agent']['receiver'] == '_end_':
                        if 'generation' in output['conversation_agent'].keys():
                                detected_lang = output['conversation_agent'].get('detected_lang')
                                generation = output['conversation_agent']['generation']
                                generation = clean_generation(generation)
                                if detected_lang == "fr" and translator:
                                    output = await translator.translate(generation, src='en', dest='fr')
                                    yield output.text
                                else:
                                    yield generation
                    else:
                        continue
                elif 'cross_check_agent' in output.keys():
                    if output['cross_check_agent']['receiver'] != 'conversation_agent':
                        detected_lang = output['cross_check_agent'].get('detected_lang')
                        generation = output['cross_check_agent']['generation']
                        generation = clean_generation(generation)
                        if detected_lang == "fr" and translator:
                            output = await translator.translate(generation, src='en', dest='fr')
                            yield output.text
                        else:
                            yield generation
                    else:
                        continue
                else:
                    continue
            except GeneratorExit:
                logging.warning("GeneratorExit ignored")
                break

    except GeneratorExit:
        logging.warning("GeneratorExit ignored. Continuing execution.")
        yield "An error occurred: GeneratorExit. Please try again."
    except Exception as e:
        print(e)
        yield "An error occurred. Please try again."
        

###################### TEST GRAPH ##############################
# import asyncio

# graph = get_graph()
# config = {"configurable": {"thread_id": "test"}}

# async def main():
#     while True:
#         user_input = await asyncio.to_thread(input, "Enter your question: ")

#         if user_input == "q":
#             print("Goodbye!")
#             break

#         inputs = {
#             "question": user_input,
#             "sender": "user",
#             "detected_lang": None,
#         }

#         async for output in graph.astream(inputs, config):

#             if not output:
#                 continue

#             for node, data in output.items():

#                 if node == "conversation_agent" and "generation" in data:
#                     generation = data["generation"]

#                     if data.get("detected_lang") == "fr" and translator:
#                         translated = await translator.translate(generation, src="en", dest="fr")
#                         print(translated.text)
#                     else:
#                         print(generation)

#                 elif node == "decision_agent":
#                     print(data.get("category"))

#                 elif node == "faq_agent":
#                     docs = data.get("documents")
#                     print(docs.get("page_content") if docs else "No answer found")

# asyncio.run(main())