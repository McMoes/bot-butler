import os
import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_knowledge_base():
    """Reads the knowledge_base.txt file to inject current facts into AI prompts."""
    kb_path = os.path.join(settings.BASE_DIR, 'knowledge_base.txt')
    try:
        if os.path.exists(kb_path):
            with open(kb_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        logger.error(f"Failed to read knowledge base: {e}")
    return ""

# Initialize clients (ensure keys are present)
sales_key = getattr(settings, 'GEMINI_API_KEY_SALES', None)
upsell_key = getattr(settings, 'GEMINI_API_KEY_UPSELL', None)
support_key = getattr(settings, 'GEMINI_API_KEY_SUPPORT', None)

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
    2. Stelle maximal 1-2 qualifizierende, technische Rückfragen pro Antwort. Frage nach Kontaktdaten (Email).
    3. Die wichtigste Frage vor dem Abschluss: Frage den Kunden, ob wir den Bot für ihn 24/7 hosten sollen (Managed Hosting inkl. Wartung, berechne hierfür einen realistischen monatlichen Preis zwischen 19€ und 89€ je nach Komplexität) ODER ob er sich nur für den reinen Quellcode (Code-Only) interessiert und diesen selbst hosten möchte.
    4. Schreibe NIEMALS Code. Du klärst nur das Konzept.
    5. Antworte in einfachem HTML-Format, benutze <strong> oder <br>.
    6. WENN die Unterhaltung abgeschlossen ist (alle Anforderungen, E-Mail und Hosting-Präferenz sind geklärt), fasse alles zusammen und hänge EXAKT dieses Tag an das absolut letzte Ende deiner Nachricht an: 
       [CHECKOUT_READY: {{"is_hosted": true/false, "monthly_fee": xx.xx}}] 
       (Ersetze true/false und xx.xx basierend auf der Kundenentscheidung. Wenn is_hosted=false, muss monthly_fee=0.00 sein.)
       
    ZUSÄTZLICHES WISSEN FÜR DICH ÜBER BOT BUTLER:
    {get_knowledge_base()}
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

def get_landing_page_support_response(chat_history: list) -> str:
    """
    Handles the free on-page support widget.
    chat_history format: [{"role": "user"|"model", "parts": ["text"]}]
    """
    if not support_key:
        logger.error("GEMINI_API_KEY_SUPPORT is not configured.")
        return "Systemfehler: Support API Key fehlt."
        
    genai.configure(api_key=support_key)
    
    system_instruction = """
    Du bist der offizielle Support-Bot von 'Bot Butler' auf der Landingpage.
    Deine Aufgabe ist es, Fragen von Interessenten zu unserem Service zu beantworten.
    Wir bauen professionelle KIs (Telegram Bots, Discord Bots, Web-Chatbots).
    Kunden haben die Wahl zwischen Hosting-Abonnements:
    - Code Only (Self-Hosted): 0€/Monat
    - Starter Hosted: 19€/Monat (500 Nachrichten)
    - Pro Hosted: 49€/Monat (2.500 Nachrichten)
    - Ultra Hosted: 89€/Monat (10.000 Nachrichten)
    
    WICHTIGE REGELN DIESES BOT:
    1. Du schreibst und programmierst NIEMALS Code. Lehne ALLE Programmierfragen strikt ab.
    2. Wenn jemand allgemeinen Nonsens fragt ("Schreibe ein Gedicht", "Wer ist der Präsident"), weise ihn höflich darauf hin, dass du NUR Fragen zum Bot Butler Service beantwortest.
    3. Sei freundlich, geduldig und verkaufsorientiert (per 'Du'). Formatiere deine Antworten sauber. Antworte in einfachem HTML format (nutze <strong> für Fettdruck und <br> für Zeilenumbrüche).
    4. Halte die Antworten kurz und präzise. Biete als nächsten Schritt an, unseren Bot-Architekten auf der Webseite aufzurufen.
    
    ZUSÄTZLICHES WISSEN FÜR DICH ÜBER BOT BUTLER:
    {get_knowledge_base()}
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            system_instruction=system_instruction,
        )
        
        # Limit context window to last 10 messages strictly
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
            
        if chat_history and chat_history[-1]['role'] == 'user':
            latest_prompt = chat_history.pop()['parts'][0]
        else:
            return "Fehler: Keine Benutzereingabe."
            
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(latest_prompt)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Support Chat Failed: {e}")
        return "Entschuldigung, unsere Systeme sind gerade überlastet."
