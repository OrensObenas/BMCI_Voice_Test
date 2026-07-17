# 🎙️ Présentation d'Avancement : Agent Vocal Interactif (LiveKit)

---

## 📌 Diapositive 1 : Page de Garde
### **Simulation d'un Client Bancaire par Agent Vocal Interactif**
*Bilan des Travaux, Expérimentations et Perspectives d'Évolution*

* **Contexte** : Stage de Recherche & Développement - **Atlas Bank**
* **Objectif** : Créer un agent de simulation de négociation commerciale réaliste.
* **Technologie principale** : LiveKit WebRTC, APIs Cloud & Modèles Locaux.

---

## 📌 Diapositive 2 : Le Cas d'Usage de la Simulation
### **Scénario "M. Orens" (Le Client Mécontent)**
* **Le Rôle de l'IA** : Incarner M. Orens, un client pressé et énervé qui exige de retirer immédiatement **100 000 dirhams en espèces** pour finaliser l'achat d'une maison.
* **Le Défi pour le Conseiller (l'apprenant)** : Faire face à la colère, proposer des alternatives (comme le virement rapide) tout en respectant la limite de sécurité réglementaire de **50 000 dirhams par jour**.
* **Contraintes Techniques** :
  * Voix expriment la colère et la frustration.
  * Latence inférieure à 1,5 seconde.
  * Possibilité de couper la parole de l'agent (Full-Duplex / Barge-in).

---

## 📌 Diapositive 3 : Chronologie du Projet (Début ➔ Aujourd'hui)
### **Les Grandes Étapes du Travail Pratique**
1. **Étape 1 : État de l'Art & Benchmarks**
   * Recherche théorique et développement de scripts pour comparer les meilleurs modèles de voix (TTS) et d'écoute (STT) du marché.
2. **Étape 2 : Prototypage Vocal (LiveKit)**
   * Développement de l'architecture d'agent vocal en temps réel via WebRTC.
3. **Étape 3 : Résilience & Optimisation**
   * Résolution des crashs, création du superviseur automatique, nettoyage textuel et gestion fine de la détection de silence (VAD).

---

## 📌 Diapositive 4 : État de l'Art - Sélection des Modèles

### **La confrontation Local (PC) vs. APIs (Cloud)**
* **Le Local** : Testé pour des raisons de gratuité et de confidentialité.
  * *Constat* : Inenvisageable sur la machine de développement (CPU standard portable). L'entraînement de modèles de voix (F5-TTS) est impossible par manque de VRAM, et l'inférence prend plus de 2 minutes pour 3 secondes de voix.
* **Le Cloud (APIs)** : Choisi comme solution pivot pour déporter la puissance de calcul.
  * *Constat* : Temps de réponse ultra-rapides (< 1,5s) et modèles d'intonation de qualité supérieure.

---

## 📌 Diapositive 5 : Résultats des Tests TTS (Synthèse Vocale)

### **Échecs, Réussites et Choix Finaux**
* **Hume AI (Benjamin)** :
  * *Résultat* : **Réussite Qualitative / Échec Technique**. Voix incroyablement naturelle (MOS de 4.03), mais bloquée par des quotas d'essai stricts (erreurs HTTP 429).
* **F5-TTS (Local)** :
  * *Résultat* : **Échec Temps Réel**. Excellente voix, mais génère en 128 secondes pour 3 secondes de voix (RTF de 37.4).
* **ElevenLabs (Adam)** :
  * *Résultat* : **Réussite Modérée**. Permet de générer des rires ou soupirs, mais s'avère coûteux et présente une latence réseau sensible.
* **Mistral Voxtral (Marie angry)** :
  * *Résultat* : **Grande Réussite (Choix Actuel)**. Voix nativement en colère, très stable, temps de réponse court (1.57s) et quotas fiables.

---

## 📌 Diapositive 6 : Résultats des Tests STT (Reconnaissance Vocale)

### **Échecs, Réussites et Choix Finaux**
* **ElevenLabs Scribe v2** :
  * *Résultat* : **Échec Temps Réel**. Excellente précision (3.12% de WER), mais latence de 21 secondes.
* **Whisper Large-Turbo (Local)** :
  * *Résultat* : **Échec CPU**. Plus de 2 minutes de calcul pour transcrire 3 minutes de voix.
* **Cohere Transcribe v2** :
  * *Résultat* : **Grande Réussite (Choix Actuel)**. Transcription très précise (5.82% de WER), robuste aux bruits d'agence, et quasi-instantanée en streaming.

---

## 📌 Diapositive 7 : L'Option LiveKit & Ses Avantages

### **Pourquoi avoir choisi LiveKit pour le temps réel ?**
* **Le Full-Duplex** : L'utilisateur et le robot peuvent se parler en continu sans appuyer sur aucun bouton (comme lors d'un vrai appel téléphonique).
* **Le Barge-in automatique** : Dès que l'utilisateur commence à parler, l'agent interrompt sa phrase à la milliseconde près pour l'écouter.
* **Modularité totale** : Possibilité de changer de modèle (STT, LLM, TTS) en modifiant seulement quelques lignes de code grâce à des plugins standardisés.
* **Hébergement cloud gratuit** : Infrastructure WebRTC gérée sur LiveKit Cloud pour les tests.

---

## 📌 Diapositive 8 : Résultats Obtenus sur LiveKit

### **Les Fonctionnalités Pratiques Implémentées**
* **Le Superviseur de Résilience (`run_agent.py`)** : Détection des déconnexions du playground et redémarrage automatique de l'agent en moins de 2 secondes.
* **Optimisation des Tours de Parole (`min_delay=0.8`)** : Une pause fixe de 0,8s de silence configurée pour s'assurer que l'écoute (STT) reçoive la phrase en entier avant que le LLM ne réponde.
* **Filtre anti-didacalies et anti-épellation** : Nettoyage automatique des crochets émotionnels (`[gasp]`) et conversion des mots en majuscules (`MON` ➔ `mon`) pour éviter que la voix ne les épelle lettre par lettre.

---

## 📌 Diapositive 9 : Limites Rencontrées dans tout le Projet

### **Les Goulots d'Étranglement Techniques**
1. **Contrainte Matérielle Locale** : CPU insuffisant pour faire tourner le STT, le VAD et le TTS en local sans latence critique.
2. **Latence cumulée en cascade** : L'enchaînement `STT (Cohere) ➔ LLM (Mistral) ➔ TTS (Voxtral)` induit un délai de 1 à 1,5s dû aux requêtes réseau successives.
3. **Absence de streaming sur Mistral TTS** : L'agent doit attendre la génération de la phrase complète pour la lire, créant un léger temps mort.
4. **Quotas d'APIs gratuits** : Blocages fréquents (erreurs HTTP 429) sur Hume AI et Gemini API lors des phases de tests rapides.

---

## 📌 Diapositive 10 : Perspectives d'Évolution

### **Pistes pour amener le projet en production**
* **Piste 1 : Passage au Speech-to-Speech (S2S) natif** :
  * Intégrer les APIs *OpenAI Realtime* ou *Gemini Multimodal Live* pour éliminer la cascade (STT/LLM/TTS) et descendre sous les **400ms de latence globale** (conversation instantanée).
* **Piste 2 : Déploiement Local sur Serveur GPU Dédié** :
  * Héberger des modèles open-source (*Whisper-Faster* local et *Llama 3*) sur un serveur cloud GPU pour éliminer les abonnements payants tout en gardant une vitesse maximale.
* **Piste 3 : Passage aux comptes APIs payants** :
  * Lever les limites 429 en acquérant un plan professionnel Hume AI/ElevenLabs.
