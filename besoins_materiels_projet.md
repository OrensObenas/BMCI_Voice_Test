# 📋 Liste des Ressources et Matériels Requis - Projet Simulation Vocale BMCI

Cette liste synthétique regroupe les demandes concrètes pour le déploiement et l'industrialisation du projet (exécutions locales, APIs et hébergement Moshi).

---

## 💻 1. Ressources Matérielles (Hardware)

* **Pour le développement local et le Fine-Tuning de petits modèles (SLM)** :
  * 1 Station de travail équipée d'une carte graphique **NVIDIA RTX 4080 ou 4090 (minimum 16 à 24 Go de VRAM dédiée)**. *Indispensable pour faire tourner CUDA, PyTorch et entraîner les modèles locaux.*
* **Pour l'hébergement du modèle Speech-to-Speech (Moshi)** :
  * 1 Instance de serveur Cloud Linux (Ubuntu) dotée d'une carte **NVIDIA L4, A10G, ou A100 (minimum 16 à 24 Go de VRAM)**. *Moshi ne peut pas fonctionner en temps réel sans un GPU professionnel.*

---

## 🔑 2. Comptes & Clés d'APIs (Accès Cloud)

* **Cerveau (LLM)** :
  * Accès à une **API payante** (au choix : *Mistral API, OpenAI API, Gemini API*) avec quotas de production, **OU** accès aux serveurs d'inférence LLM internes existants de la BMCI.
* **Écoute (STT)** :
  * Clé d'API payante pour la transcription en temps réel (*Cohere Transcribe v2* ou *Whisper API*).
* **Voix (TTS)** :
  * Clé d'API payante pour la synthèse vocale émotionnelle (*Mistral Voxtral* pour la voix en colère de Marie, ou *Hume AI* / *ElevenLabs*).

---

## 🌐 3. Infrastructure & Téléphonie

* **Hébergement WebRTC** :
  * Un abonnement **LiveKit Cloud** de production **OU** l'allocation d'une Machine Virtuelle (VM Linux) dédiée à la BMCI pour y déployer un serveur LiveKit open-source auto-hébergé.
* **Interfaçage Téléphonique (SIP / VoIP)** :
  * Un abonnement à un **Trunk SIP** (ex: Twilio, Telnyx) pour relier les appels téléphoniques des stagiaires à l'agent vocal.

---

## 🧠 5. Spécificités d'Intégration pour MOSHI (Kyutai)

Si le modèle Speech-to-Speech natif **Moshi** est retenu :
1. **GPU Serveur obligatoire** (aucune inférence CPU temps réel possible).
2. **Environnement Linux (Ubuntu)** obligatoire en production.
3. **Temps de développement requis** pour :
   * L'intégration du codec audio Mimi côté client.
   * Le codage d'un système de détection d'activité vocale (VAD) pour gérer l'interruption de l'IA (Barge-in).
   * L'analyse du monologue textuel de Moshi en arrière-plan pour déclencher les appels d'API bancaires (Function Calling).
