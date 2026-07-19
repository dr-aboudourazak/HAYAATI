import os
import urllib.request

# 📁 1. Création sécurisée du dossier fonts
os.makedirs("fonts", exist_ok=True)

# 🔗 2. Liens officiels absolus vers les fichiers de polices Google Noto
POLICES = {
    "fonts/NotoSansArabic-Regular.ttf": "https://githubusercontent.com",
    "fonts/NotoSansSC-Regular.ttf": "https://githubusercontent.com"
}

print("⏳ Début du téléchargement des polices multilingues (Arabe & Chinois)...")

for chemin_local, url in POLICES.items():
    try:
        print(f"📥 Téléchargement de : {chemin_local} ...")
        # Téléchargement natif avec gestion des redirections réseau
        urllib.request.urlretrieve(url, chemin_local)
        print(f"✅ Réussi : {chemin_local} ({os.path.getsize(chemin_local) / 1024 / 1024:.2f} Mo)")
    except Exception as e:
        print(f"❌ Échec pour {chemin_local}. Erreur : {e}")

print("\n🏁 Processus terminé. Vérifiez votre dossier 'fonts/' dans votre barre latérale VS Code !")
