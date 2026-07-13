# 📋 Rapport Spécifique : Spécifications & Traitements Spéciaux de Fine-Tuning

Ce rapport détaille les spécifications requises (volumes, formats, matériel) pour fine-tuner chaque type de modèle (TTS, STT, LLM) et présente pour chaque modèle étudié dans notre projet les **traitements spéciaux** ou prérequis uniques nécessaires à leur ajustement.

---

## 📊 Tableau Synthétique : Prérequis de Fine-Tuning par Modèle

| Modèle | Type | Volume de données min. | Format requis | Ressource GPU | Traitement Spécial / Prérequis Unique |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **ElevenLabs (PVC)** | TTS | 30 min (idéalement 3h) | Audio brut continu | Cloud (Aucun GPU local) | Abonnement payant (Creator) + Authentification vocale obligatoire (anti-deepfake). |
| **Hume AI** | TTS | Aucun | Texte de description | Cloud (Aucun GPU local) | Pas d'entraînement classique. Ajustement via prompt comportemental ou curseurs API. |
| **F5-TTS** | TTS | 30 min à 2h | WAV Mono 24 kHz + `metadata.csv` | GPU local (min. 16 Go VRAM) | Suppression du bruit (Denoiser) + Convertisseur phonétique (G2P) français obligatoire. |
| **Whisper** | STT | 10h à 50h | WAV/MP3 + Textes horodatés | GPU local (min. 24 Go VRAM) | Tokenizer Whisper requis + Gel de l'encodeur (saving memory) + Normalisation du texte. |
| **Cohere Transcribe** | STT | Aucun | Liste écrite de termes | Cloud (Aucun GPU local) | Pas d'entraînement direct. Utilisation de la fonction "Custom Vocabulary" (Hotwords) par API. |
| **Mistral Small** | LLM | 100 à 200 dialogues | JSONL (Format Chat strict) | Cloud (Aucun GPU local) | Entraînement géré sur la console cloud de Mistral. Format de rôles (system/user/assistant) obligatoire. |
| **Google Gemini** | LLM | 100+ dialogues | JSONL (Format Chat) | Cloud (Aucun GPU local) | Entraînement par adaptateur LoRA hébergé et configuré sur Google AI Studio. |

---

## 1. Modèles de Synthèse Vocale (TTS)

### A. Spécifications Générales
* **Volume de données** : **30 minutes à 2 heures** d'enregistrements audio de haute qualité d'une seule voix pour un entraînement complet (ou 1 à 3 minutes pour du clonage rapide).
* **Format** : Fichiers **WAV Mono**, échantillonnés proprement à **22050 Hz** ou **44100 Hz**.
* **Alignement** : Un fichier de transcription `metadata.csv` (lien direct entre le fichier audio et le texte lu).

### B. Traitements Spéciaux par Modèle Étudié

* **ElevenLabs (Professional Voice Cloning - PVC)** :
  * **Traitement spécial** : Vous n'avez pas besoin de découper les fichiers ou de faire de transcription manuelle ! ElevenLabs traite des fichiers audio bruts en continu dans le cloud.
  * **Prérequis uniques** : 
    * Requiert au moins **30 minutes** d'audio continu (idéalement 3 heures).
    * Nécessite un **abonnement payant** (Creator minimum).
    * Exige une **authentification vocale** : vous devez lire un paragraphe affiché à l'écran pour prouver que vous êtes le propriétaire de la voix (anti-deepfake).
* **Hume AI (Modèle d'intonation)** :
  * **Traitement spécial** : Hume AI ne permet pas de fine-tuner les poids de leur modèle TTS de manière classique.
  * **Prérequis uniques** : Le contrôle de la voix s'effectue via un **Prompt de description comportemental** (ex: *description="An angry client"*). Pour un traitement spécialisé, on ajuste les curseurs de leurs APIs vocales interactives (EVI) plutôt qu'un jeu de données audio.
* **F5-TTS (Local)** :
  * **Traitement spécial** : Très sensible au bruit. Il nécessite de passer tous vos fichiers audio dans un outil de **réduction de bruit (Denoiser)** et de normaliser la fréquence d'échantillonnage à exactement **24 000 Hz** (le format natif de F5-TTS).
  * **Prérequis uniques** : Demande d'extraire les phonèmes du texte français via un convertisseur *Grapheme-to-Phoneme (G2P)* spécifique au français pour éviter les erreurs de prononciation.
* **Mistral Voxtral** :
  * **Traitement spécial** : Aucune option de fine-tuning ou de clonage n'est ouverte au public à ce jour sur Voxtral. Le modèle s'utilise uniquement tel quel (voix par défaut).

---

## 2. Modèles de Reconnaissance Vocale (STT)

### A. Spécifications Générales
* **Volume de données** : **10 à 50 heures** de fichiers audio avec leurs transcriptions précises pour un entraînement complet.
* **Format** : Audio varié (bruit de fond d'agence, voix téléphoniques) pour habituer le modèle aux conditions réelles.

### B. Traitements Spéciaux par Modèle Étudié

* **Whisper (Local - Base, Large-Turbo)** :
  * **Traitement spécial** : Pour fine-tuner Whisper en local, il faut convertir le texte écrit en jetons à l'aide du *Tokenizer* multilingue spécifique de OpenAI Whisper.
  * **Prérequis uniques** :
    * Il faut souvent **geler l'encodeur audio** (Encoder Freezing) pendant l'entraînement pour économiser la mémoire de la carte graphique (VRAM) et éviter de dépasser les 24 Go de la carte.
    * Le texte de transcription doit être normalisé (ex: transformer "cent mille" en "100 000" ou inversement selon la façon dont le modèle doit l'écrire).
* **Cohere Transcribe v2 & ElevenLabs Scribe** :
  * **Traitement spécial** : Ces modèles cloud n'autorisent pas le fine-tuning de leurs poids neuronaux.
  * **Prérequis uniques** : Pour ajouter vos termes personnalisés (ex: "Atlas Bank", jargon bancaire), vous devez utiliser la fonctionnalité de **Vocabulaire Personnalisé (Custom Vocabulary)** en transmettant une liste de termes spécifiques lors de chaque requête de transcription.

---

## 3. Modèles de Langage (LLM)

### A. Spécifications Générales
* **Volume de données** : **500 à 2000 conversations** au format système/utilisateur/assistant.
* **Format** : Fichier **JSON Lines (JSONL)** où chaque ligne contient un échange complet.

### B. Traitements Spéciaux par Modèle Étudié

* **Mistral Small (mistral-small-latest)** :
  * **Traitement spécial** : Le fine-tuning de Mistral se fait sur la console cloud de Mistral AI. Vous ne faites aucun calcul sur votre PC. Vous chargez simplement votre fichier JSONL.
  * **Prérequis uniques** :
    * Mistral exige un format de chat strict (chaque message doit avoir un `role` parmi `system`, `user`, `assistant`, et un `content`).
    * La plateforme demande un minimum de **100 à 200 exemples** de dialogue de qualité pour pouvoir démarrer le processus d'entraînement dans le cloud.
* **Google Gemini (Gemini 2.5 Flash)** :
  * **Traitement spécial** : Le fine-tuning s'effectue via l'interface **Google AI Studio** ou son SDK Python.
  * **Prérequis uniques** : Google permet l'entraînement par adaptateurs (LoRA) directement hébergé dans leur cloud. Il nécessite de structurer le dataset dans leur format de chat spécifique et de définir des paramètres d'hyperparamètres (learning rate, epochs) directement dans la console d'AI Studio.
