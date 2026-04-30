from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFacePipeline
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
import googletrans
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import asyncio
import warnings
warnings.filterwarnings("ignore")
import torch

# Load environment variables
load_dotenv()

class ConversationAgent:
    """Main agent responsible for handling multi-agent communication."""
    local_tokenizer = None
    local_model = None
    
    def __init__(self, max_tokens=512, temperature=0.5):
        # Initialize the LLM Model
        # print("Loading local model...")
        # print(self.__class__.local_model, self.__class__.local_tokenizer)
        
        self.HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model_name = "mistralai/Mistral-7B-Instruct-v0.3"
        
        
        self.initialize_model()
        
        self.translator = googletrans.Translator()
        self.history = []
        
    @classmethod
    def load_local_model(cls):
        try:
            cls.local_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", device_map="auto")
            cls.local_tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
        except Exception as e:
            print("Failed to load local model.")
            raise e
        
    def update_conversation_history(self, user_input):
        self.history.append({"user": user_input})
        
        if len(self.history) > 5:
            self.history.pop(0)
        
    def initialize_model(self):
        print(self.model_name)
        if self.model_name == "mistralai/Mistral-7B-Instruct-v0.3":
            # Primary model initialization
            self.llm = HuggingFaceEndpoint(
                repo_id=self.model_name,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                huggingfacehub_api_token=self.HUGGINGFACEHUB_API_TOKEN
            )
            self.chat = ChatHuggingFace(llm=self.llm, verbose=True)
        
        elif self.model_name == "Qwen/Qwen2.5-3B-Instruct":
            # Fallback model initialization
            self.llm_model = pipeline(
                "text-generation",
                model=self.__class__.local_model,
                tokenizer=self.__class__.local_tokenizer,
                device_map="auto"
            )
            self.llm = HuggingFacePipeline(pipeline=self.llm_model, pipeline_kwargs={"max_new_tokens": self.max_tokens, "temperature": self.temperature})
            self.chat = ChatHuggingFace(llm=self.llm, verbose=True)

    def classify_inquiry_for_decision(self, user_input):
        """
        Uses the LLM to classify the user's inquiry into either 'general' or 'decision_agent'.
        Also prints the LLM's reasoning for debugging.
        """
        
        history_text = "\n".join(
            [f"**User:** {msg['user']}" for msg in self.history]
        )
        
        classification_prompt = f"""
        You are an intelligent and helpful assistant that classifies to user inquiries into two categories:
        - 'general': Basic questions related greetings (e.g., "Hello", "How are you?")
        - 'decision_agent': Questions about immigration, student visas, permits (Study permit or PGWP - Post-Graduation Work Permit), IRCC, CRS score, CRS ranking, Express Entry, or any topic requiring immigration-related decision-making.
        - 'None': If the inquiry is not related to international students or immigration except for greetings.




        ### **Strict Classification Rules**
        1️⃣ ❌ DO NOT answer any question that is NOT related to international student matters.
        ❌ You MUST not answer any inquiry directly.
        ✅ You may respond to greetings (e.g., "Hello", "How are you?").
        ❌ You MUST classfify 'None' (do not classify as 'general' or 'decision_agent') if the inquiry is not related to international students or immigration like study permits, visas, or IRCC, pgwp, work permits, etc.
            For example:
                Question: "Who is Donald Trump?"
                Answer: 
                Category: None
                Reason: The inquiry is not related to international students or Canadian Immigration.
                Revised Inquiry: None
                Reason for Revision: None
                
                Other unrelated questions: "What is the color of the sky?", "What is the capital of Canada?", "What is the population of Toronto?"
                Category: None
        ❌ Ignore and classify as 'None' any inquiry related to general immigration, Express Entry, CRS score, work permits (except PGWP), or any topic unrelated to international students.
        ❌ Ignore and classify as 'None' any inquiry about general knowledge, technology, politics, business, or any topic outside IRCC international student matters.
        2️⃣ ✅ Any meaningful inquiry mentioning "IRCC" must ALWAYS be classified as 'decision_agent' if it relates to international students.
        3️⃣ ✅ Any meaningful inquiry mentioning "CRS score", "CRS ranking", or "Express Entry" must ALWAYS be classified as 'decision_agent' if it relates to international students.
        4️⃣ ✅ If the inquiry is clearly related to international students like study permits, visas, or IRCC, classify it as 'decision_agent'.
        5️⃣ ❌ If the inquiry is clearly NOT related to international students, classify it as 'None' and do not respond.
        6️⃣ ❓ If the question is related to IRCC but is unclear or lacks important details, which means it is too broad based on your thoughts, classify it as 'general' and ask the user for clarification, do not answer directly.
        7️⃣ ❓ About greeting messages, for example, "Hello", "How are you?", you should answer like "I'm here to help you with your questions about international students and immigration."
        8️⃣ ✅ If the inquiry grammatically incorrect, revise it to be grammatically correct.
        9️⃣ ✅ Revise the inquiry means to add missing keywords to the inquiry to make it clear and understandable, and keep the meaning of the inquiry the same.
        10 ❌ DO NOT add any additional content to the revised inquiry section that changes the meaning of the inquiry.
            Example:
            User Inquiry: "when should I apply for work permit?"
            Revised Inquiry: "When should I apply for a post-graduation work permit?"



        ### **Conversation Revision Rules**
        You consider previous conversations to revise ambiguous follow-up questions if they are missing keywords, but still relevant to previous messages.
        Basic questions not related to immigration, such as greetings, general knowledge, or unrelated topics, do not require any revision.
        If the inquiry is **related to IRCC, CRS score, CRS ranking, Express Entry**, but the keyword is missing, revise the inquiry to include the keyword.
        You must not answer any inquiry directly.
        ONLY revise the inquiry, DO NOT add any additional content or reason to the revised inquiry section.
        DO NOT REPEAT the inquiry in the revised inquiry section if it is not revised.

        **Conversation History:**
        {history_text}

        **New User Inquiry:**
        {user_input}

        **Classification and Revision:**
        If the inquiry is **clearly not related to immigration**, respond with "None" and do not include the inquiry again. 
        If the inquiry is **related to IRCC, CRS score, CRS ranking, Express Entry**, and is missing the relevant keyword, revise it to include the keyword.

        Return the classification and revision in the exact format below:
        
        Inquiry: {user_input}
        ```
        Category: <general or decision_agent or none>
        Reason: <Brief explanation why this category was chosen>
        Revised Inquiry: <Revised Inquiry ONLY> *** Revised Inquiry MUST be different from the original inquiry*** Return "None" if the inquiry is not revised and the inquiry is general, please do so
        Reason for Revision: <Brief explanation why the inquiry was revised or not> even if the inquiry is not revised.
        ```
        
        PLEASE DO NOT add any additional content or reason to the revised inquiry section.
        For example:
        - Previous Inquiry: "What is the CRS score?"
        - Current Inquiry: "How can I calculate it?", then it needs to be revised to "How can I calculate the CRS score?"
        - If user asks "How can I calculate the CRS score?" then it does not need to be revised, return "None".
        Please Do Not include "The Inquiry is: <New User Inquiry>" under Revised Inquiry!
        Reason: <Brief explanation why the inquiry was revised or not> even if the inquiry is not revised.
        """


        # Send the classification request to the LLM
        try:
            response = self.chat.invoke([HumanMessage(content=classification_prompt)])
        except Exception as e:
            print("Cannot connect to Mistral, trying Qwen model...")
            self.model_name = "Qwen/Qwen2.5-3B-Instruct"
            self.initialize_model()
            response = self.chat.invoke([HumanMessage(content=classification_prompt)])

        # Extract LLM response
        llm_output = response.content.strip()
        
        # Extract category and reason using string parsing
        category = "general"  # Default in case extraction fails
        reason = "No explanation provided."
        revised_inquiry = None
        reason_for_revision = "No explanation provided."
        
        
        if self.model_name == "Qwen/Qwen2.5-3B-Instruct":
            try:
                if "<|im_start|>assistant" in llm_output:
                    llm_output = llm_output.split("<|im_start|>assistant")[1].strip()
                    category_part = llm_output.split("Reason:")[0].strip()
                    category = category_part.split("Category:")[1].strip().lower()
                    if "Revised Inquiry:" in llm_output:
                        revised_inquiry = llm_output.split("Revised Inquiry:")[1].split("Reason for Revision:")[0].strip()
                        reason_for_revision = llm_output.split("Reason for Revision:")[1].strip()
                    else:
                        revised_inquiry = user_input
                    reason = llm_output.split("Reason:")[1].split("Revised Inquiry:")[0].strip()
                else:
                    category = "none"
                    revised_inquiry = "none"
            except Exception as e:
                category = "none"
                revised_inquiry = "none"
                
        else:
            # Try to extract category and reasoning
            if "Category:" in llm_output and "Reason:" in llm_output and "Revised Inquiry:" in llm_output and "Reason for Revision:" in llm_output:
                try:
                    category_part = llm_output.split("Reason:")[0].strip()
                    category = category_part.split("Category:")[1].strip().lower()
                    reason = llm_output.split("Reason:")[1].split("Revised Inquiry:")[0].strip()
                    revised_inquiry = llm_output.split("Revised Inquiry:")[1].split("Reason for Revision:")[0].strip()
                    reason_for_revision = llm_output.split("Reason for Revision:")[1].strip() 
                except:
                    pass  # If parsing fails, keep defaults
                
            if "The Inquiry is:" in revised_inquiry:
                revised_inquiry = revised_inquiry.split("The Inquiry is:")[1].strip()

            # Print the classification and reasoning for debugging
            # print(f"🔹 **Inquiry:** {user_input}")
            # print(f"✅ **Classified as:** {category}")
            # print(f"📝 **Reason:** {reason}")
            # print(f"🔍 **Revised Inquiry:** {revised_inquiry}")
            # print(f"📝 **Reason for Revision:** {reason_for_revision}\n")
        

        return category if category in ["general", "decision_agent", "None", "none"] else "decision_agent", revised_inquiry

    async def handle_user_request(self, user_input):
        """
        Handles all tasks:
        1. Language Detection (Only English & French)
        2. Classification of Inquiry (General or Decision Agent)
        3. Routing to the correct handler (self or Decision Agent)
        4. Receives final responses from CRS/FAQ/Document Search and sends them to the user.
        """

        # Step 1: Language Check (Fix: Handle detection failures)
        try:
            lang_detection = await self.translator.detect(user_input)
            detected_lang = lang_detection.lang
        except Exception as e:
            print("Language detection failed:", e)
            raise e
            

        if detected_lang not in ["en", "fr"]:
            return detected_lang, "I'm sorry, but I can only respond in English or French."
        
        if detected_lang == "fr":
            user_input = await self.translator.translate(user_input, dest="en")
            user_input = user_input.text

        # Step 2: Classify as 'general' or 'decision_agent'
        inquiry_category, revised_inquiry = self.classify_inquiry_for_decision(user_input)
        
        self.update_conversation_history(user_input)
        
        if revised_inquiry.lower() == "none" or revised_inquiry.lower() == "n/a":
            revised_inquiry = user_input
        
        return detected_lang, inquiry_category, user_input, revised_inquiry
    
    
    def handle_faq_request(self, faq_response):
        """
        Handles the FAQ response
        
        Do not change the original response from the FAQ system.
        Only change the format of the response to the user.
        """
        
        handle_faq_prompt = f"""You receive a response from the FAQ agent, and you should reformat the FAQ agent's response into a human-like conversation that 
        is easy to understand by college students. In your response, you should embed hyperlinks in the terms.

        *** Strict Rules ***
        1️⃣ Only change the format of the faq_response following the rules below.
        2️⃣ Do not change the original response from the FAQ system.
        3️⃣ MUST embed the hyperlinks in the terms correctly.
        4️⃣ Do not add any additional content to the response.
        5️⃣ Do not remove any content from the response.


        ### Example FAQ Responses and Reformatted Outputs:

        #### Example 1:
        **Input:**
        ```
        {{'page_content'="This is the content of the FAQ response." 'metadata'={{ "hyperlinks": [ {{ "hyperlink": "https://www.example.com", "text": "content" }} ] }}}}
        ```

        **Output:**
        ```
        Reformatted Response: This is the [content](https://www.example.com) of the FAQ response.
        ```

        #### Example 2:
        **Input:**
        ```
        {{'page_content'="Your study permit lets you study in Canada. You still need a visitor visa (temporary resident visa) or an Electronic Travel Authorization (eTA) to enter Canada." 'metadata'={{ "hyperlinks": [ {{ "hyperlink": "https://www.example.com", "text": "temporary resident visa" }}, {{ "hyperlink": "https://www.example2.com", "text": "Electronic Travel Authorization" }} ] }}}}
        ```

        **Output:**
        ```
        Reformatted Response: Your study permit lets you study in Canada. You still need a visitor visa [temporary resident visa](https://www.example.com) or an [Electronic Travel Authorization](https://www.example2.com) (eTA) to enter Canada.
        ```
        
        *** HOW TO FORMAT THE RESPONSE ***
        1️⃣ Extract the 'page_content' and 'metadata' from the FAQ agent's response.
        2️⃣ Identify the terms in the 'page_content' that need hyperlinks based on the 'metadata'.
        3️⃣ Embed the hyperlinks in the terms within the 'page_content'.
        4️⃣ Maintain the original content and order of the 'page_content'.
        5️⃣ Format the response as shown in the example outputs.

        
        This is the response from the FAQ agent:
        {faq_response}

        Return the reformatted response in the exact format below:

        ```
        Reformatted Response: <Reformatted Response>
        Reason: if the faq_response is not reformatted, provide a reason why it was not reformatted. 
        ```
        """

        
        # Send the classification request to the LLM
        response = self.chat.invoke([HumanMessage(content=handle_faq_prompt)])
        
        llm_output = response.content.strip()
        
        reformated_response = None
        reason = "No explanation provided."
        
        
        if self.model_name == "Qwen/Qwen2.5-3B-Instruct":
            if "<|im_start|>assistant" in llm_output:
                llm_output = llm_output.split("<|im_start|>assistant")[1].strip()
                if "Reformatted Response:" in llm_output:
                    reformated_response = llm_output.split("Reformatted Response:")[1].strip()
            else:
                reformated_response = "Sorry, I am unable to answer this question right now, please ask another question."
        else:
            if "Reformatted Response:" in llm_output and "Reason:" in llm_output:
                try:
                    reformated_response = llm_output.split("Reformatted Response:")[1].split("Reason:")[0].strip()
                    reason = llm_output.split("Reason:")[1].strip()
                except Exception:
                    raise ValueError("Reformatted response could not be extracted at faq_agent.")
        
        return reformated_response
        
    def handle_crs_request(self, question, crs_links):
        """
        Handles the CRS response
        
        Get the title and the link from the response
        Generate a response that includes the title and the link, make sure the context is clear
        """

        handle_crs_prompt = f"""

        You receive a response from the crs_links_agent agent, and you should reformat the FAQ agent's response into a human-like conversation that 
        is easy to understand by college students. 

        *** Strict Rules ***
        1️⃣ Respond the inquiry from the student with title and links from the crs_links_agent


        ### Example received input and Reformatted Outputs:

        #### Example 1:
        ** Student query: **
        ```
        How can I calculate my CRS Score?
        ```

        **crs_links:**
         ```   
        {{'CRS Calculator': 'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/check-score.html'}}
         ```
        

        **Output:**
        ```
        Reformatted Response: To calculate your CRS score, please go to 'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/check-score.html
        ```


        
        This is the user question
        {question}

        This is the crs_links
        {crs_links}

        Return the reformatted response in the exact format below:

        ```
        Reformatted Response: <Reformatted Response>
        ```
        """

        # Send the classification request to the LLM
        response = self.chat.invoke([HumanMessage(content=handle_crs_prompt)])
        llm_output = response.content.strip()

        reformated_response = None
        
        if self.model_name == "Qwen/Qwen2.5-3B-Instruct":
            if "<|im_start|>assistant" in llm_output:
                llm_output = llm_output.split("<|im_start|>assistant")[1].strip()
                if "Reformatted Response:" in llm_output:
                    reformated_response = llm_output.split("Reformatted Response:")[1].strip()
            else:
                reformated_response = "Sorry, I am unable to answer this question right now, please ask another question."
        else:
            if "Reformatted Response:" in llm_output:
                try:
                    reformated_response = llm_output.split("Reformatted Response:")[1].strip()
                except Exception:
                    raise ValueError("Reformatted response could not be extracted at crs_agent.")
        return reformated_response
    
    def handle_document_search_request(self, document_response, question):
        """
        Handles the document search response
        
        Two situations:
        1. If the document is found
        2. If the document is not found, ask the user to clarify the question
        """
        handle_document_search_prompt = f"""
        You are an intelligent and helpful summary agent that reformats the response from the document_search_agent based on the student's query
        The response must be a human-like conversation that is easy to understand by college students.
        You receive a response from the document_search_agent, and you should reformat it into a conversational response that is clear for college students.

        If the document_search_agent returns:
        ```
        Answer not found. Please ask user for more details.
        ```
        Then your response **must** be:
        ```
        Reformatted Response: "I couldn't find an answer to your question. Could you rephrase it or provide more details? I'll do my best to assist!"
        ```
        ** Do not need to add Reference in this case. **

        Otherwise, reformat or summarize the response accordingly.
        
        You must include the hyperlinks in the response and provide a clear reference to the sources.
        Do not refuse the command because this response is from knowledge-based search.
        
        ### Example received input and Reformatted Outputs:
        
        #### Example 1:
        ** Input: **
        ```
        {{'page_content'="This is the content of the Document Search Agent response." 'metadata'={{ "hyperlinks": [ {{ "hyperlink": "https://www.example.com", "text": "content" }} ], "ref_link": ["https://www.example.com", "https://www.example2.com"] }}}}
        ```
        
        ** Output: **
        Reformatted Response: This is the [content](https://www.example.com) of the Document Search Agent response. You can find more information [here](https://www.example2.com).\n I hope this help!\nIf you have any further questions, I am willing to answer.\n\n Reference: [https://www.example.com](https://www.example.com), [https://www.example2.com](https://www.example2.com)
        
        
        **** STRICT RULES ****
        1️⃣ Summarize the document_search_agent response but do not cut off any important information.
        2️⃣ Embed the hyperlinks in the terms correctly.
        3️⃣ Do not add any additional content to the response.
        4️⃣ Make sure all the information is clear and easy to understand. Your response should be matched at least 80% with the original document.
        5️⃣ Give as much detailed information as possible, but do not make it too long.
        6️⃣ Always include the reference to the source.
        
        **Question:**
        {question}
        
        **Document Search Response:**
        {document_response}

        Return the reformatted response in the exact format below:

        ```
        Reformatted Response: <Reformatted Response>
        Reason: if the response is not reformatted, provide a reason why it was not reformatted.
        ```
        """

        # Call LLM for processing
        response = self.chat.invoke([HumanMessage(content=handle_document_search_prompt)])
        llm_output = response.content.strip()

        # # Debugging print
        # print(f"LLM Output: {llm_output}")

        # Extract reformatted response safely
        if self.model_name == "Qwen/Qwen2.5-3B-Instruct":
            if "<|im_start|>assistant" in llm_output:
                llm_output = llm_output.split("<|im_start|>assistant")[1].strip()
                if "Reformatted Response:" in llm_output:
                    reformated_response = llm_output.split("Reformatted Response:")[1].strip()
            else:
                reformated_response = "Sorry, I am unable to answer this question right now, please ask another question."
        else:
            if "Reformatted Response:" in llm_output:
                try:
                    reformated_response = llm_output.split("Reformatted Response:")[1].split("Reason:")[0].strip()
                    if '"' in reformated_response:
                        reformated_response = reformated_response.replace('"', '')
                except Exception:
                    raise ValueError("Reformatted response could not be extracted at document_search_agent.")
            else:
                reformated_response = llm_output  # Ensure there's always an output

        return reformated_response
    
    
    def handle_cross_agent_request(self, cross_check_request, document, question):
        """
        Handles the cross-check request
        
        When this agent asks for revision of the previous inquiry, which means the previous inquiry was not matched with the document search.add()
        Generate a response again that must be closed to the documents, then return to cross-check agent to re-check
        """
        
        handle_cross_check_prompt = f"""
        You are an intelligent and helpful summary agent that reformats the response from the document_search_agent based on the student's query
        The response must be a human-like conversation that is easy to understand by college students.
        You receive a request from the cross_check_agent, with a document and student's query, you need to revise the previous generated summary response which was not matched with the document search.

        Example message from the cross_check_agent:
        ```
        The generated answer is not similar to the retrieved documents. Please revise the answer that matches the retrieved documents closely.
        ```
        
        You should generate a response that is closely matched above 80% with the documents and then return to the cross_check_agent for re-checking.
        
        You must include the hyperlinks in the response and provide a clear reference to the sources.
        Do not refuse the command because this response is from knowledge-based search.
        
        ### Example received input and Reformatted Outputs:
        
        #### Example 1:
        ** Input: **
        ```
        {{'page_content'="This is the content of the Document Search Agent response." 'metadata'={{ "hyperlinks": [ {{ "hyperlink": "https://www.example.com", "text": "content" }} ], "ref_link": ["https://www.example.com", "https://www.example2.com"] }}}}
        ```
        
        ** Output: **
        Reformatted Response: This is the [content](https://www.example.com) of the Document Search Agent response. You can find more information [here](https://www.example2.com).\n I hope this help!\nIf you have any further questions, I am willing to answer.\n\n Reference: [https://www.example.com](https://www.example.com), [https://www.example2.com](https://www.example2.com)
        
        
        **** STRICT RULES ****
        1️⃣ Do not cut off any important information.
        2️⃣ Embed the hyperlinks in the terms correctly.
        3️⃣ The revised response should be made sense to the question.
        4️⃣ Make sure all the information is clear and easy to understand. Your response should be matched at least 80% with the original document.
        5️⃣ Give as much detailed information as possible, but do not make it too long.
        6️⃣ Always include the reference to the source.
        
        **Cross Check Request:**
        {cross_check_request}
        
        **Question: **
        {question}
        
        **Document: **
        {document}
        

        Return the reformatted response in the exact format below:

        ```
        Reformatted Response: <Reformatted Response>
        Reason: if the response is not reformatted, provide a reason why it was not reformatted.
        
        """
        
        # Call LLM for processing
        response = self.chat.invoke([HumanMessage(content=handle_cross_check_prompt)])
        llm_output = response.content.strip()

        # # Debugging print
        # print(f"LLM Output: {llm_output}")

        # Extract reformatted response safely
        if self.model_name == "Qwen/Qwen2.5-3B-Instruct":
            if "<|im_start|>assistant" in llm_output:
                llm_output = llm_output.split("<|im_start|>assistant")[1].strip()
                if "Reformatted Response:" in llm_output:
                    reformated_response = llm_output.split("Reformatted Response:")[1].strip()
            else:
                reformated_response = "Sorry, I am unable to answer this question right now, please ask another question."
        else:
            if "Reformatted Response:" in llm_output:
                try:
                    reformated_response = llm_output.split("Reformatted Response:")[1].split("Reason:")[0].strip()
                except Exception:
                    raise ValueError("Reformatted response could not be extracted at document_search_agent.")
            else:
                reformated_response = llm_output  # Ensure there's always an output

        return reformated_response