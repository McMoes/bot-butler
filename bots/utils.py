import requests
import os
from twilio.rest import Client
from django.conf import settings

def send_telegram_message(message_text):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    if not bot_token or not chat_id:
        print("Telegram credentials missing. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def trigger_twilio_call():
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_number = settings.TWILIO_NUMBER
    zielnummer = settings.ZIELNUMMER

    if not all([account_sid, auth_token, twilio_number, zielnummer]):
        print("Twilio credentials missing. Skipping phone call.")
        return

    try:
        client = Client(account_sid, auth_token)
        call = client.calls.create(
            to=zielnummer,
            from_=twilio_number,
            url='http://demo.twilio.com/docs/voice.xml'
        )
        print(f"Twilio Call initiated. SID: {call.sid}")
    except Exception as e:
        print(f"Error initiating Twilio call: {e}")

def generate_draft_file(order):
    """
    Generates the .txt file on the server with the prompt for Antigravity IDE.
    """
    draft_dir = settings.BOT_DRAFTS_DIR
    cat_name = order.category.name if order.category else "Custom"
    filename = f"{order.order_id}.txt"
    filepath = os.path.join(draft_dir, filename)

    consulting_text = "YES" if order.consulting_requested else "NO"
    
    content = f"--- BOT BUTLER REQUIREMENTS ---\n"
    content += f"Order ID: {order.order_id}\n"
    content += f"Category: {cat_name}\n"
    content += f"Consulting Requested: {consulting_text}\n"
    content += f"Total Price: {order.total_price} EUR\n"
    content += f"Contact: {order.contact_info}\n\n"
    
    content += f"--- AI GENERATED JSON SPECIFICATION ---\n"
    import json
    content += json.dumps(order.requirements_json, indent=4)
    content += f"\n\n--- INSTRUCTIONS FOR ANTIGRAVITY IDE ---\n"
    content += f"Please create a fully functioning {cat_name} based on the specification above. "
    content += f"Ensure it connects properly and is ready for production deployment."

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        order.draft_file_path = filepath
        order.save()
        return filepath
    except Exception as e:
        print(f"Failed to generate draft file: {e}")
        return None

def send_order_confirmation_email(order):
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    
    try:
        site_url = 'https://bot-butler.com'
        cat_name = order.category.name if order.category else "Custom Bot"
        
        context = {
            'order': order,
            'category_name': cat_name,
            'username': order.user.username if order.user else None,
            'site_url': site_url
        }
        
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        recipient_email = order.user.email if order.user and order.user.email else None
        
        if recipient_email:
            send_mail(
                f'Order Confirmation: {cat_name}',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                html_message=html_message,
                fail_silently=True,
            )
            print(f"Order confirmation email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send order confirmation email: {e}")

def process_order_notifications(order):
    filepath = generate_draft_file(order)
    
    cat_name = order.category.name if order.category else "Custom"
    t_message = (
        f"🚨 *Es wurde ein neuer Bot beauftragt !!!* 🚨\n\n"
        f"Kategorie: {cat_name}\n"
        f"Preis: {order.total_price} €\n"
        f"Datei mit Ablaufplan: {os.path.basename(filepath) if filepath else 'FEHLER: Dateierstellung fehlgeschlagen'}\n\n"
        f"Consulting gebucht: {'Ja' if order.consulting_requested else 'Nein'}\n"
        f"Kontakt: {order.contact_info}"
    )

    send_telegram_message(t_message)
    trigger_twilio_call()
    send_order_confirmation_email(order)
