from backend.models import get_db_user_details

def run_chain(system_goal, user_query):
    """Runs the LLM chain (placeholder for AI logic)."""
    try:
        user_details = get_db_user_details()
        if not isinstance(user_details, dict):
            user_details = {"name": "N/A", "age": 0, "language": "en"}

        name = user_details.get("name", "User")
        language = user_details.get("language", "en")

        prompt = f"{system_goal}\nUser ({language}): {user_query}"
        ai_response_text = f"({language.upper()}) Hello {name}, you said: {user_query}"
        return ai_response_text, True

    except Exception as e:
        print(f"[run_chain ERROR]: {e}")
        return "An error occurred while generating a response.", True
