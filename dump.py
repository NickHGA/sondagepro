import io
import os
import django
from django.core.management import call_command

# 🔥 Point essentiel : configure Django manuellement
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sondagepro_project.settings")
django.setup()

# 🔄 Export des données avec encodage UTF-8
with io.open("sauvegarde.json", "w", encoding="utf-8") as f:
    call_command("dumpdata", stdout=f, indent=2)
