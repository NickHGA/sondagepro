import json

# Charge la fixture originale
with open('sauvegarde.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filtre pour exclure les entrées contenttypes.contenttype
filtered_data = [entry for entry in data if entry.get('model') != 'contenttypes.contenttype']

# Sauvegarde dans un nouveau fichier
with open('sauvegarde_clean.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=4)

print("Fixture nettoyée enregistrée dans 'sauvegarde_clean.json'")
