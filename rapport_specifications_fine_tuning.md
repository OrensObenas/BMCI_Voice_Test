# 📋 Rapport Technique : Spécifications de Fine-Tuning & Analyse des Modèles Étudiés

Ce rapport a pour but de guider les équipes techniques d'**Atlas Bank** sur les prérequis nécessaires pour le fine-tuning (ajustement) des modèles de voix, de transcription et de langage, ainsi que de récapituler les caractéristiques des modèles étudiés lors de notre benchmark.

---

## I. Spécifications pour le Fine-Tuning par Type de Modèle

### 1. Synthèse Vocale (TTS - Text-to-Speech)
Le fine-tuning en synthèse vocale sert à cloner une voix spécifique pour lui faire lire n'importe quel texte avec les émotions voulues (colère, calme).

* **Volume de données requis** :
  * **Clonage basique (Few-Shot)** : **1 à 3 minutes** d'audio de haute qualité suffisent.
  * **Fine-Tuning professionnel (Modèle dédié)** : **30 minutes à 2 heures** d'audio de haute qualité.
* **Format des données** :
  * Fichiers audio au format **WAV**, échantillonnés à **22050 Hz** ou **44100 Hz**, en **Mono** (1 seul canal).
  * Audio nettoyé (pas de bruit de fond, pas de musique, pas d'échos).
  * Découpage en courts extraits (de 2 à 10 secondes par fichier).
  * Un fichier texte de métadonnées (généralement `metadata.csv`) associant le nom de chaque fichier audio à sa transcription écrite exacte (ex: `audio_01.wav|Bonjour, je voudrais faire un retrait.`).
* **Matériel de calcul (GPU)** :
  * Inenvisageable sur CPU. Requiert un GPU Nvidia avec au moins **16 Go à 24 Go de VRAM** (ex : Nvidia RTX 3090, RTX 4090, ou GPU cloud A10G/A100).
* **Temps d'entraînement** :
  * Environ **2 à 6 heures** sur un GPU professionnel.

---

### 2. Reconnaissance Vocale (STT - Speech-to-Text)
Le fine-tuning en reconnaissance vocale sert à apprendre au modèle à mieux transcrire des accents spécifiques, des termes techniques bancaires ou des noms propres propres à Atlas Bank.

* **Volume de données requis** :
  * **Ajustement léger (Vocabulaire)** : Aucun entraînement (on utilise la technique de "prompting" ou "hotwords" en passant une liste de mots-clés par API).
  * **Fine-Tuning profond (Whisper)** : **10 à 50 heures** d'enregistrements audio variés.
* **Format des données** :
  * Fichiers audio (WAV or MP3) de conversations réelles enregistrées dans des conditions d'utilisation réelles (bruit d'agence, appels téléphoniques).
  * Fichiers de transcription au format texte avec horodatage (couplage précis de l'audio et du texte).
* **Matériel de calcul (GPU)** :
  * Requiert une puissance importante : GPU avec au moins **24 Go de VRAM** (RTX 4090 ou A100).
* **Temps d'entraînement** :
  * De **12 heures à 3 jours** selon le volume du dataset.

---

### 3. Modèle de Langage (LLM)
Le fine-tuning du LLM sert à lui enseigner le scénario de négociation bancaire exact, la politique interne d'Atlas Bank, et le comportement psychologique de M. Orens.

* **Volume de données requis** :
  * **Fine-tuning par LoRA (méthode légère recommandée)** : **500 à 2 000 exemples** de dialogue.
* **Format des données** :
  * Fichier structuré en **JSON Lines (JSONL)** au format Chat (Système, Utilisateur, Assistant).
  * Exemple de structure de données :
    ```json
    {"messages": [{"role": "system", "content": "Tu es M. Orens..."}, {"role": "user", "content": "Bonjour, comment puis-je vous aider ?"}, {"role": "assistant", "content": "Je veux retirer 100 000 dirhams tout de suite !"}]}
    ```
* **Matériel de calcul (GPU)** :
  * Un GPU grand public comme la **RTX 3090 / 4090 (24 Go de VRAM)** est largement suffisant grâce aux techniques d'optimisation (QLoRA).
* **Temps d'entraînement** :
  * **1 à 3 heures** pour un modèle de 7 ou 8 milliards de paramètres (type Llama 3 ou Mistral 7B).

---

## II. Analyse Comparative des Modèles Étudiés (Benchmarks)

Voici la fiche technique des modèles que nous avons testés et comparés durant le projet.

### 🎙️ 1. Modèles de Synthèse Vocale (TTS)

#### A. Les Modèles Cloud (API)
* **Hume AI (Voix : Benjamin)** :
  * *Caractéristiques* : Modèle empathique générant des émotions naturelles basées sur une description textuelle.
  * *MOS (Qualité)* : **4.03 / 5** (Le plus naturel).
  * *Latence* : 1.97 s.
  * *Forces* : Qualité vocale impressionnante, gestion fine du ton de la voix.
  * *Faiblesses* : Latence élevée et quotas gratuits très stricts (erreur 429 fréquente).
* **Mistral Voxtral (Voix : Marie angry)** :
  * *Caractéristiques* : Modèle de synthèse de Mistral AI.
  * *MOS (Qualité)* : **3.78 / 5**.
  * *Latence* : **1.57 s** (Rapide).
  * *Forces* : Voix en colère native extrêmement convaincante, très grande stabilité des quotas de l'API.
  * *Faiblesses* : Ne supporte pas le streaming de tokens (l'agent doit attendre la fin de la phrase avant de parler).
* **ElevenLabs (Voix : Adam / Eleven v3)** :
  * *Caractéristiques* : Leader du clonage de voix.
  * *MOS (Qualité)* : **3.45 / 5**.
  * *Latence* : 1.96 s.
  * *Forces* : Capable de générer des rires, soupirs et chuchotements à partir de tags textuels `[sighs]`.
  * *Faiblesses* : Assez lent pour le temps réel et coûteux en production.
* **Google TTS & Edge-TTS** :
  * *MOS (Qualité)* : ~3.55 / 5.
  * *Latence* : **0.46 s à 0.70 s** (Ultra-rapides).
  * *Forces* : Extrêmement rapides et très économiques.
  * *Faiblesses* : Voix trop neutres, lisses et robotiques, inadaptées pour simuler la colère.

#### B. Les Modèles Locaux
* **F5-TTS** :
  * *Caractéristiques* : Modèle open-source de clonage de voix non-autorégulatif.
  * *MOS (Qualité)* : **3.79 / 5** (Excellent naturel).
  * *Latence* : **127.91 s** (Sur CPU).
  * *Forces* : Clone une voix avec seulement 3 secondes de référence. Gratuit et open-source.
  * *Faiblesses* : **Inutilisable** en direct sans un GPU puissant dédié.
* **MeloTTS & Kokoro v0.19** :
  * *MOS (Qualité)* : 3.17 à 3.56 / 5.
  * *Latence* : 3.03 s à 7.98 s.
  * *Forces* : Légers et faciles à déployer.
  * *Faiblesses* : Manque d'expressivité et voix françaises moyennes.

---

### 🎤 2. Modèles de Reconnaissance Vocale (STT)

* **Cohere Transcribe v2** :
  * *WER (Taux d'erreur)* : **5.82%** (Très précis).
  * *Latence* : **5.43 s** (Pour l'analyse de gros fichiers) / Temps réel instantané.
  * *Forces* : Gère extrêmement bien le bruit de fond et les accents. Très rapide en streaming.
  * *Faiblesses* : Nécessite une connexion Internet stable.
* **ElevenLabs Scribe v2** :
  * *WER (Taux d'erreur)* : **3.12%** (La meilleure précision).
  * *Latence* : **21.02 s** (Trop lent pour le direct).
  * *Forces* : Qualité de transcription quasi-parfaite sur les termes financiers.
  * *Faiblesses* : Latence inutilisable pour un agent de discussion en direct.
* **Whisper Large-Turbo (Local)** :
  * *WER (Taux d'erreur)* : **6.03%**.
  * *Latence* : **132.91 s** (Sur CPU).
  * *Forces* : Open-source, gratuit, fonctionne hors-ligne.
  * *Faiblesses* : Trop lourd en calcul sur un ordinateur portable d'internat.

---

### 🧠 3. Modèles de Langage (LLM - Le Cerveau)

* **Google Gemini 2.5 Flash** :
  * *Type* : Modèle cloud multimodal.
  * *Forces* : Extrêmement rapide pour générer les premiers jetons (TTFT très bas), gratuit.
  * *Faiblesses* : Limites de requêtes gratuites trop basses pour des tests en continu (erreur 429 fréquente).
* **Mistral Small (mistral-small-latest)** :
  * *Type* : Modèle cloud via API OpenAI.
  * *Forces* : Excellente maîtrise du français et du contexte de négociation. Pas de blocage de quota.
  * *Faiblesses* : Légèrement plus lent que Gemini au démarrage de la réponse.
