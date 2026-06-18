# BMCI Voice Test — French TTS & STT Benchmark

Ce dépôt contient le pipeline d'évaluation comparative de modèles de synthèse vocale (TTS) et de reconnaissance vocale (STT/ASR) en français.

## 🚀 Fonctionnalités Clés

1. **Génération de Discussions Continues** :
   * Synthèse de dialogues complets de 21 répliques en alternant dynamiquement les rôles de l'**Agent** (voix féminine, polie) et du **Client** (voix masculine, irritée/grincheuse).
   * Insertion de silences naturels de 0.8 seconde entre les répliques.
   * Modèles supportés : `kokoro`, `melo`, `edgetts`, `gtts`, `hume`, `elevenlabs`, `mistral`, `f5tts`, `openai`.

2. **Clonage de Voix (Voice Cloning)** :
   * Clonage vocal local *zero-shot* avec **F5-TTS** à partir d'un échantillon audio personnalisé (ex. `my_voice.ogg`).

3. **Évaluation STT/ASR (Transcription)** :
   * Mesure de la qualité des transcriptions (taux d'erreur de mots - WER, taux d'erreur de caractères - CER).
   * Mesure de la latence de génération et du RTF (Real-Time Factor).

## 🛠️ Installation & Démarrage

1. Installer les dépendances :
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configurer vos clés API dans un fichier `.env` à la racine :
   ```env
   ELEVENLABS_API_KEY=votre_cle
   HUME_API_KEY=votre_cle
   OPENAI_API_KEY=votre_cle
   MISTRAL_API_KEY=votre_cle
   COHERE_API_KEY=votre_cle
   ```

3. Générer la discussion complète pour un ou plusieurs modèles :
   ```powershell
   # Exemple pour F5-TTS et ElevenLabs
   python generate_discussion.py --models f5tts elevenlabs
   ```

4. Lancer le benchmark STT/ASR sur les audios générés :
   ```powershell
   python run_stt_benchmark.py
   ```
