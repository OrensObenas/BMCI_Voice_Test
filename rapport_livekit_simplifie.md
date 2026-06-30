# 🎙️ Rapport Simplifié : Mon Travail avec LiveKit

Ce document résume de manière simple et directe le travail réalisé pour concevoir l'agent vocal interactif d'**Atlas Bank**, les avantages de la technologie utilisée, et ses pistes d'amélioration.

---

## 1. Le Travail Réalisé : Création de l'Agent Vocal

Nous avons construit un **agent vocal conversationnel en temps réel** capable de jouer le rôle de **M. Orens**, un client très mécontent venu retirer 100 000 dirhams.

Pour cela, nous avons connecté plusieurs briques d'intelligence artificielle ensemble dans un "pipeline" (flux) géré par **LiveKit** :

1. **L'écoute (STT - Reconnaissance Vocale)** : L'agent écoute votre voix et la transforme en texte grâce à l'API **Cohere**.
2. **La réflexion (LLM - Cerveau)** : L'API **Mistral** reçoit le texte, comprend le contexte bancaire et rédige la réponse de M. Orens en colère.
3. **La parole (TTS - Synthèse Vocale)** : Le texte de la réponse est envoyé à l'API **Mistral Voxtral** pour être lu avec une voix française nativement énervée (la voix Marie).

### 🛠️ Les solutions pratiques développées :
* **Un Superviseur anti-crash (`run_agent.py`)** : Un script qui surveille l'agent et le relance automatiquement en moins de 2 secondes s'il se déconnecte ou s'il y a un bug.
* **Un filtre de texte intelligent** : Pour éviter que la voix ne lise bêtement les indications de jeu d'acteur (ex: *"astérisque soupir astérisque"*), nous avons créé un nettoyeur qui supprime ces tags à l'oral mais les garde affichés par écrit dans le chat.
* **Un réglage de temps de pause (`min_delay=0.8`)** : Nous avons configuré l'agent pour qu'il attende 0,8 seconde après que vous ayez fini de parler. Cela évite que l'IA ne vous coupe la parole ou ne réponde trop vite à une phrase incomplète.

---

## 2. Les Avantages de LiveKit

LiveKit s'est révélé être une technologie excellente pour ce projet. Voici ses points forts :

* **Le Full-Duplex (Échange naturel)** : L'utilisateur et l'IA peuvent parler en même temps. Il n'y a pas besoin d'appuyer sur un bouton pour parler.
* **Le Barge-in (Interruption immédiate)** : Si l'IA est en train de parler et que vous commencez à parler pour la calmer, elle **s'arrête instantanément** pour vous écouter. C'est indispensable pour un jeu de rôle de négociation.
* **L'architecture modulaire** : Il est très facile de remplacer une brique par une autre (par exemple, remplacer la voix Mistral par la voix Hume AI ou ElevenLabs) sans réécrire tout le code, grâce aux plugins officiels.
* **Stabilité audio** : LiveKit gère le streaming audio sous forme de flux WebRTC (technologie utilisée par Discord ou Zoom), ce qui garantit une bonne qualité sonore même avec une connexion moyenne.

---

## 3. Les Limites Actuelles

* **La latence cumulée** : Comme le système fonctionne en cascade (Écoute ➔ Réflexion ➔ Parole), chaque étape ajoute son propre délai réseau. Le temps de réaction total est d'environ **1 à 1,5 seconde**.
* **La dépendance aux APIs Cloud** : Les versions gratuites des APIs (comme Hume AI ou Gemini) bloquent rapidement l'agent si on parle trop vite (erreurs 429 Too Many Requests). 
* **L'absence de streaming audio sur Mistral TTS** : Mistral Voxtral doit générer toute la phrase d'un coup avant de commencer à parler, ce qui crée un léger temps d'attente au début de sa réplique.

---

## 4. Perspectives d'Amélioration

Pour rendre l'agent encore plus humain et instantané, voici les pistes à suivre :

### A. Passer au "Speech-to-Speech" natif (S2S)
* **Comment ça marche** : Utiliser des modèles comme **OpenAI Realtime** ou **Gemini Live**. Au lieu de faire STT ➔ LLM ➔ TTS, on envoie directement le son de votre voix à l'IA, et elle répond directement avec sa voix.
* **Avantage** : La latence descend sous les **400 millisecondes** (presque instantané, comme un humain), et l'IA comprend l'intonation de votre voix (si vous êtes calme, stressé, etc.).

### B. Héberger les modèles en local (Serveur GPU)
* **Comment ça marche** : Installer des modèles gratuits open-source (*Whisper* pour l'écoute, *Llama 3* pour la réflexion) sur un serveur équipé d'une carte graphique dédiée.
* **Avantage** : Plus aucun abonnement payant à régler, aucune limite de requêtes par minute (plus de bugs 429), et une confidentialité totale des données.
