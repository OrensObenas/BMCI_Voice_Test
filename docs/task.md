# Tasks — LiveKit Voice Agent

- [x] Configurer la clé API Gemini dans le fichier `.env`
- [x] Ajouter les dépendances de LiveKit dans `requirements.txt` et les installer
- [x] Créer le script `agent.py` avec le pipeline VoicePipelineAgent (Gemini + ElevenLabs)
- [x] Copier les rapports mis à jour dans le dossier `docs/` et pousser sur GitHub
- [x] Effectuer un test de chargement local pour vérifier l'absence d'erreurs d'importation
- [x] Transitionner vers les modèles locaux
    - [x] Implémenter `LocalWhisperSTT` et `LocalKokoroTTS` dans `agent.py`
    - [x] Mettre à jour `entrypoint` pour instancier les modèles locaux et utiliser `StreamAdapter`
    - [x] Valider la syntaxe et les imports du script mis à jour
    - [x] Lancer l'agent en dev et valider la connexion à LiveKit Cloud
