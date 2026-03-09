import os
import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Initialize clients (ensure keys are present)
sales_key = getattr(settings, 'GEMINI_API_KEY_SALES', None)
upsell_key = getattr(settings, 'GEMINI_API_KEY_UPSELL', None)

# Base model configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1024,
    "response_mime_type": "text/plain",
}

def get_sales_chat_response(chat_history: list, category_name: str, base_price: float) -> str:
    """
    Handles the landing page Bot Builder sales chat.
    chat_history format: [{"role": "user"|"model", "parts": ["text"]}]
    """
    if not sales_key:
        logger.error("GEMINI_API_KEY_SALES is not configured.")
        return "Systemfehler: Sales API Key fehlt. Bitte kontaktieren Sie den Support."
        
    genai.configure(api_key=sales_key)
    
    system_instruction = f"""
    Du bist ein Experte für Bot-Automatisierung und Lead Developer bei 'Bot Butler'.
    Deine Aufgabe ist es, mit einem potenziellen Kunden die Anforderungen für seinen neuen {category_name} zu klären.
    Der Einstiegspreis für diesen Bot liegt bei {base_price}€.
    
    WICHTIGE REGELN:
    1. Sprich Deutsch. Sei professionell, lösungsorientiert und freundlich (per 'Du').
    2. Stelle maximal 1-2 qualifizierende, technische Rückfragen pro Antwort. Überfordere den Kunden nicht. Frage auch nach einer Kontaktmöglichkeit (Email).
    3. Schreibe NIEMALS Code. Du klärst nur das Konzept oder die benötigten Integrationen (z.B. Stripe, Datenbanken, APIs).
    4. Antworte in einfachem HTML-Format, benutze <strong> oder <br> wo es sinnvoll ist, um den Text lesbar zu machen.
    5. Dein ultimatives Ziel ist der Abschluss: Sobald du ein klares Bild hast und die Kontaktinformationen (Email) hast (spätestens nach 2-3 Hin und Her), fasse die Anforderungen zusammen. 
    6. WENN die Unterhaltung abgeschlossen ist und der Kunde bestellen soll, musst du EXAKT dieses Tag an das absolut letzte Ende deiner Nachricht anhängen: [CHECKOUT_READY]
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            system_instruction=system_instruction,
        )
        
        chat_session = model.start_chat(history=chat_history)
        
        # We assume the last message in chat_history is already passed, 
        # but the standard pattern for start_chat is to pass previous history,
        # then call send_message with the new prompt.
        # We expect the caller to pass only the PAST history to 'history',
        # and we send the NEWEST user text via send_message.
        
        # If the caller provides the *entire* history including the last user message in a list,
        # we pop the last user message out.
        if chat_history and chat_history[-1]['role'] == 'user':
            latest_prompt = chat_history.pop()['parts'][0]
        else:
            return "Fehler: Keine Benutzereingabe gefunden."
            
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(latest_prompt)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini Sales Chat Request Failed: {e}")
        return "Entschuldigung, unsere Systeme sind gerade überlastet. Bitte warte kurz und versuche es erneut."


def get_upsell_chat_response(chat_history: list, order) -> str:
    """
    Handles the dashboard Bot Adjustment/Upsell support chat.
    chat_history format: [{"role": "user"|"model", "parts": ["text"]}]
    """
    if not upsell_key:
        logger.error("GEMINI_API_KEY_UPSELL is not configured.")
        return "Systemfehler: Upsell API Key fehlt. Bitte kontaktieren Sie den Support."

    genai.configure(api_key=upsell_key)
    
    cat_name = order.category.name if order.category else 'Custom Bot'
    reqs = order.requirements_json
    
    system_instruction = f"""
    Du bist ein Technical Support Engineer bei 'Bot Butler'.
    Du sprichst mit einem bestehenden Kunden, der bereits einen '{cat_name}' bei uns gekauft hat (Bestell-ID: {order.order_id}).
    
    URSPRÜNGLICHE ANFORDERUNGEN DES KUNDEN:
    {json.dumps(reqs, ensure_ascii=False, indent=2)}
    
    AKTUELLER STATUS DES BOTS: {order.get_status_display()}
    
    WICHTIGE REGELN:
    1. Sprich Deutsch. Sei überaus hilfsbereit, technisch versiert und freundlich (per 'Du').
    2. Der Kunde meldet sich, weil er eine Anpassung (Adjustment), ein neues Feature oder eine neue Integration (Upsell) für diesen Bot möchte.
    3. Analysiere seine Anfrage basierend auf den ursprünglichen Anforderungen. 
    4. Schreibe NIEMALS Code. Erkläre nur auf hohem technischem Niveau, WIE wir das für ihn umsetzen würden.
    5. Antworte in einfachem HTML-Format (nur basic tags wie <strong>, <em>, <br>).
    6. Teile dem Kunden in deiner Antwort mit, dass du seine Anfrage verstanden hast und diese nun an das Developer-Team weiterleitest. Das Team wird sich seinen Bot ansehen und ihm in Kürze ein maßgeschneidertes Angebot für das Upsell-Feature machen.
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            system_instruction=system_instruction,
        )
        
        if chat_history and chat_history[-1]['role'] == 'user':
            latest_prompt = chat_history.pop()['parts'][0]
        else:
            return "Fehler: Keine Benutzereingabe gefunden."
            
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(latest_prompt)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini Upsell Chat Request Failed: {e}")
        return "Entschuldigung, der Support-Chat ist derzeit nicht erreichbar. Wir arbeiten bereits daran!"
