import os

po_file = r'c:\Users\McMoe\Documents\Python\bot_butler\locale\de\LC_MESSAGES\django.po'

content = """

msgid "Your"
msgstr "Dein"

msgid "Command Center."
msgstr "Command Center."

msgid "Admin"
msgstr "Admin"

msgid "Manage global support workflows and infrastructure requests."
msgstr "Verwalte globale Support-Workflows und Infrastruktur-Anfragen."
"""

with open(po_file, 'a', encoding='utf-8') as f:
    f.write(content)

print("Translations appended.")
