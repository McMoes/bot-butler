import os
import re

po_file = r'c:\Users\McMoe\Documents\Python\bot_butler\locale\de\LC_MESSAGES\django.po'

with open(po_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the accidentally appended translations at the end
content = re.sub(r'msgid "Your"\nmsgstr "Dein"\n+msgid "Command Center."\nmsgstr "Command Center."\n+msgid "Admin"\nmsgstr "Admin"\n+msgid "Manage global support workflows and infrastructure requests."\nmsgstr "Verwalte globale Support-Workflows und Infrastruktur-Anfragen."\n*', '', content)

# Fix the existing empty translations
content = content.replace('msgid "Your"\nmsgstr ""', 'msgid "Your"\nmsgstr "Dein"')
content = content.replace('msgid "Command Center."\nmsgstr ""', 'msgid "Command Center."\nmsgstr "Command Center."')

content = content.replace('msgid ""\n"Manage your active bots, view invoices, and request custom integrations."\nmsgstr ""', 'msgid ""\n"Manage your active bots, view invoices, and request custom integrations."\nmsgstr "Verwalte deine aktiven Bots, sieh dir Rechnungen an und frage individuelle Integrationen an."')

# Add missing Admin strings properly if they don't exist
if 'msgid "Admin"' not in content:
    content += '\n\nmsgid "Admin"\nmsgstr "Admin"\n\nmsgid "Manage global support workflows and infrastructure requests."\nmsgstr "Verwalte globale Support-Workflows und Infrastruktur-Anfragen."\n'

with open(po_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("django.po fixed successfully.")
