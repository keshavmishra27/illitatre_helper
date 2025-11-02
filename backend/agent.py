from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI # For Gemini fallback
from langdetect import detect
import re 
from flask import current_app # To access the Gemini API key from Flask config
# Import database helpers and model from the models file
from .models import UserDetail, get_db_user_details, store_db_user_details 

# --- LLM Initialization (Primary) ---

# Ollama is the fast, primary model. Initialize globally once.
try:
    llm_primary = OllamaLLM(model='mistral:latest')
    print("INFO: Ollama Mistral model initialized successfully.")
except Exception as e:
    # This block executes if Ollama is NOT running when Flask starts.
    print(f"WARNING: Ollama Mistral initialization failed. Error: {e}. Preparing Gemini fallback.")
    llm_primary = None 

# --- Global Resources ---

CHAT_HISTORY = ChatMessageHistory()

PROMPT = PromptTemplate(
    input_variables=["system_instructions", "chat_history", "current_user_data", "user_query"],
    template="{system_instructions}\n\nUser Data Status:\n{current_user_data}\n\nPrevious Conversation:\n{chat_history}\nUser: {user_query}\nAI:",
)

# --- State-Driven Agent Logic ---

def get_gemini_llm_client():
    """Initializes and returns the ChatGoogleGenerativeAI client."""
    gemini_api_key = current_app.config.get('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("FATAL: GOOGLE_API_KEY is missing. Gemini client cannot be created.")
        return None
        
    try:
        # We initialize the client on demand using the key from Flask config
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", # Fast model for chat/extraction
            google_api_key=gemini_api_key 
        )
        return llm
    except Exception as e:
        print(f"FATAL: Gemini client initialization failed. Error: {e}")
        return None


def process_agent_query(user_query: str, user_id: int = 1) -> tuple[str, bool]:
    """
    Chooses the appropriate LLM (Ollama or Gemini), processes the query, 
    manages the conversation state, and performs data extraction/storage.
    """
    
    # 1. LLM SELECTION (HYBRID LOGIC)
    llm_to_use = None
    
    # Check PRIMARY (Ollama) FIRST
    if llm_primary is not None:
        llm_to_use = llm_primary
    
    else:
        # FALLBACK PATH: Ollama is None. Attempt to use Gemini.
        gemini_api_key = current_app.config.get('GEMINI_API_KEY')
        
        if gemini_api_key:
            print("INFO: Ollama is down. Falling back to Gemini 2.5 Flash.")
            try:
                llm_to_use = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=gemini_api_key 
                )
            except Exception as e:
                print(f"FATAL: Gemini fallback failed. Error: {e}")
                llm_to_use = None
        
    if llm_to_use is None:
        # Failsafe: Both Ollama and Gemini failed
        return "AI service is unavailable. Check Gemini API key and network.", True
    
    # 2. GET STATE AND INITIALIZE VARIABLES
    current_details = get_db_user_details(user_id) or UserDetail(id=user_id).to_dict() 
    name, age, language = current_details['name'], current_details['age'], current_details['language']
    
    system_goal = ""
    contextual_query = user_query 
    is_setup_complete = (name != 'N/A' and age != 0) 

    # 3. DETERMINE CONVERSATION STATE AND GOAL
    
    if language == 'en' and name == 'N/A' and age == 0:
        # State A: Initial Greeting & Language Detection
        try:
            detected_lang = detect(user_query)
        except:
            detected_lang = 'en'
        
        # Store the detected language immediately
        store_db_user_details({'name': name, 'age': age, 'language': detected_lang}, user_id)
        language = detected_lang
        
        # Forces the LLM to reply immediately and ask the first question
        system_goal = (
            f"Goal: The user has initiated contact. You **MUST** reply immediately with a "
            f"warm greeting in the {language} language, and then ask for the user's **full name** "
            f"to begin the profile setup. Your response must be generated solely in {language}."
        )
        # Use a generic prompt to force the LLM to execute the system goal
        contextual_query = f"User initiated contact. Execute the defined System Goal."
        
    elif name == 'N/A':
        # State B: Collecting Name
        system_goal = (
            f"Goal: You must **extract the user's full name** from their last response. Once extracted, "
            f"confirm the name (e.g., 'Thank you, [Name]'), and immediately ask for their **age** in {language}."
        )
    
    elif age == 0:
        # State C: Collecting Age
        system_goal = (
            f"Goal: You must **extract the user's age (a number)** from their last response. Once extracted, "
            f"confirm the setup is complete in {language} and transition to normal conversation by asking how you can help."
        )
    
    else:
        # State D: Complete - Normal Chat
        system_goal = (
            f"Goal: Setup is complete. Respond naturally to the user's query in {language}. "
            f"Use the context (Name: {name}, Age: {age}) to be personalized."
        )
        is_setup_complete = True 

    # 4. RUN LLM INVOCATION
    user_data_status = f"Name: {name}, Age: {age}, Language: {language}"
    full_prompt = PROMPT.format(
        system_instructions=system_goal,
        current_user_data=user_data_status,
        chat_history="\n".join([f"{msg.type.capitalize()}:{msg.content}" for msg in CHAT_HISTORY.messages]),
        user_query=contextual_query, 
    )
    
    # Send to the selected LLM
    try:
        ai_response = llm_to_use.invoke(full_prompt)
    except Exception as e:
        # Catch network/timeout errors from the cloud API
        print(f"FATAL: LLM invocation failed during runtime. Error: {e}")
        # Re-raise the exception so the routes.py handler can catch it and return a 500 JSON error
        raise e 

    # 5. POST-PROCESSING (Extraction & DB Update)
    
    # Note: Use the original user_query for extraction, which is stored in the user_query variable
    
    if name == 'N/A' and language != 'en':
        # Extraction heuristic for Name
        if len(user_query.split()) < 5 and len(user_query) > 1:
             # Basic attempt to capitalize and store the user's response as name
             extracted_name = user_query.strip().title()
             if extracted_name:
                store_db_user_details({'name': extracted_name, 'age': age, 'language': language}, user_id)
    
    elif age == 0 and name != 'N/A':
        match = re.search(r'\b\d{1,2}\b', user_query)
        # Extraction heuristic for Age (look for a number)
        if match:
            extracted_age = int(match.group(0))
            if extracted_age > 5 and extracted_age < 100:
                store_db_user_details({'name': name, 'age': extracted_age, 'language': language}, user_id)
                is_setup_complete = True 

    # 6. Store conversation history
    CHAT_HISTORY.add_user_message(user_query)
    CHAT_HISTORY.add_ai_message(ai_response)

    # CRITICAL FIX: Extract the text content from the LangChain message object
    return ai_response.content.strip(), is_setup_complete
