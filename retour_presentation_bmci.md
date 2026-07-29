# 📝 Rapport d'Évolution : Retours BMCI & Plan d'Amélioration

Ce document résume les points clés issus de la présentation du projet devant les équipes de la BMCI. Il détaille les améliorations immédiates implémentées dans la pipeline de simulation vocale et trace les perspectives futures pour l'industrialisation.

---

## ⚡ 1. Améliorations Immédiates Implémentées (R&D)

Pour aligner la simulation sur les cas réels de formation de la BMCI, les modifications suivantes ont été déployées dans les profils de scénarios (`scenario_orens.txt`, `scenario_kabbaj.txt`, `scenario_tazi.txt`) et dans le moteur de l'agent :

### 📞 A. Transition vers le format "Appel Téléphonique"
* **Avant** : L'IA agissait comme si elle était physiquement devant le guichet en agence bancaire.
* **Maintenant** : La simulation commence par une phrase de téléphone typique : *"Allô bonjour, je vous appelle parce que..."*. L'échange est formalisé comme une relation de centre d'appels ou de ligne directe client.

### 🆔 B. Processus d'Identification & Formule d'Accueil
* **Avant** : Le client donnait toutes ses informations d'emblée.
* **Maintenant** : Le client (IA) garde le mystère au départ. Il ne dévoile ses informations personnelles de compte (**Nom**, **CIN**, ou **dernières transactions**) **que si le conseiller (l'apprenant) les lui demande explicitement et poliment**.

### 🇲🇦 C. Intégration de Nuances de Darija Marocain
Pour donner une couleur locale authentique à l'agent vocal sans pour autant perdre la compréhension de la langue de base (français) :
* L'IA a pour consigne d'intégrer de manière naturelle et fluide des expressions courantes en darija :
  * **Wakha** (d'accord)
  * **Safi** (c'est bon / d'accord)
  * **Chokran a sidi / a lalla** (merci monsieur / madame)
  * **Blati** (attendez)
  * **Bzaf** (beaucoup)

### 🎭 D. Humeur Adaptative & Variation du Ton
* **Humeur dynamique** : Le LLM adapte en temps réel son comportement selon la posture de l'apprenant :
  * **Posture chaleureuse, polie et orientée solution** : Le client baisse le ton, se détend, coopère et remercie l'agent.
  * **Posture froide, administrative ou rigide** : Le client s'énerve davantage, refuse les explications et exige une remontée immédiate.
* **Résolution/Rappel** : Si l'apprenant propose de remonter le ticket et de rappeler, le client accepte à la seule condition d'obtenir un engagement sur une **heure précise de rappel** (ex: *"D'accord, mais vous me rappelez avant midi, safi ?"*).

---

## 🔮 2. Perspectives à Moyen Terme (Industrialisation & RAG)

Pour aller plus loin dans la personnalisation marocaine et la robustesse de l'agent, deux axes stratégiques ont été identifiés :

### 📚 A. Intégration d'un RAG (Retrieval-Augmented Generation) Contextuel Marocain
* **Objectif** : Permettre à l'IA de faire référence à des réalités locales de la BMCI (noms de produits spécifiques, adresses des agences réelles de Casablanca/Rabat, procédures de réclamation marocaines, tarification locale).
* **Technique** : Brancher une base de connaissances vectorielle contenant les documentations internes de la BMCI. L'agent interrogera cette base à chaque tour pour extraire les termes ou adresses réelles et les inclure dans son dialogue.

### 🎙️ B. Analyse Acoustique du Ton du Conseiller (Classification Audio)
* **Objectif** : Actuellement, le ton de l'agent change en fonction des *mots* retranscrits par le STT. Pour une immersion totale, l'IA doit réagir directement à l'intonation physique de la voix (énervement, hésitation, chaleur).
* **Technique** : Intégrer un classifieur de voix en temps réel (ex: un modèle Wav2Vec2 entraîné sur de la détection d'émotion vocale) connecté sur le flux audio LiveKit, qui injecte un score émotionnel (ex: `politesse=90%` ou `irritation=40%`) directement dans le contexte du LLM à chaque phrase.
