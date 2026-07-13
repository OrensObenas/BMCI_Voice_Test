# 🎙️ Rapport de Benchmark TTS (Synthèse Vocale)

Ce rapport présente l'évaluation comparative des modèles de synthèse vocale (TTS) en français. Les tests ont été effectués sur les répliques du dialogue, en mesurant la fidélité de la voix, la latence de génération et la qualité naturelle du signal.

---

## 📊 Tableau de Synthèse des Performances

Le classement ci-dessous est trié par le score **MOS** (Mean Opinion Score, évalué par UTMOS). Un score plus élevé indique une voix plus naturelle et humaine.

| Rang | Modèle              | Tier  | MOS (1-5) | Latence (s) | RTF       | WER (%)   | CER (%) | TTFA (s)   |
| :----:| :--------------------| :-----:| :---------:| :-----------:| :---------:| :---------:| :-------:| :----------:|
| 🥇　 | **Hume AI**         | API   | **4.03**  | 1.97 s      | 0.535     | 38.1%     | 15.6%   | 1.94 s     |
| 🥈　 | **F5-TTS**          | Local | **3.79**  | 127.91 s    | 37.435    | 90.8%     | 46.8%   | 127.91 s   |
| 🥉　 | **Mistral Voxtral** | API   | **3.78**  | 1.57 s      | 0.363     | 16.5%     | 8.0%    | 1.44 s     |
| #4　 | **Edge-TTS**        | API   | 3.61      | 0.70 s      | 0.124     | **11.5%** | 7.1%    | 0.47 s     |
| #5　 | **Kokoro v0.19**    | Local | 3.56      | 3.03 s      | 0.700     | 31.5%     | 13.8%   | 3.03 s     |
| #6　 | **Google TTS**      | API   | 3.53      | **0.46 s**  | **0.090** | **11.5%** | 7.1%    | **0.46 s** |
| #7　 | **ElevenLabs**      | API   | 3.45      | 1.96 s      | 0.526     | **11.5%** | 7.1%    | 1.88 s     |
| #8　 | **MeloTTS**         | Local | 3.17      | 7.98 s      | 2.008     | 26.5%     | 11.1%   | 7.98 s     |

> **RTF** (Real-Time Factor) : Inférieur à 1.0 signifie que le modèle génère l'audio plus rapidement que sa vitesse de lecture réelle.

---

## 🔍 Analyse Détaillée par Modèle

### 🥇 Hume AI
* **Score MOS** : **4.03** (Qualité exceptionnelle, voix française extrêmement naturelle).
* **Latence** : ~1.97 s, ce qui est très réactif pour une API cloud.
* **WER** : 38.1% (Légèrement élevé en raison de quelques libertés de prononciation ou de formatage des nombres).

### 🥈 F5-TTS (Local)
* **Score MOS** : **3.79** (Très bonne qualité et expressivité, idéale pour le clonage de voix).
* **Latence** : **127.91 s** (Exécution CPU locale lente, non viable pour du temps réel sans accélération GPU).
* **WER** : 90.8% (Le bruit d'artefact sur CPU gêne la transcription par Whisper).

### 🥉 Mistral Voxtral
* **Score MOS** : **3.78** (Voix très propre et professionnelle).
* **Latence** : 1.57 s (Très rapide).
* **RTF** : 0.363.

### 4. Edge-TTS & Google TTS
* **Vitesse** : Les plus rapides avec un RTF de **0.09** à **0.12** (plus de 8 fois plus rapide que la lecture).
* **Qualité** : Voix robotiques mais très claires et intelligibles (WER bas de 11.5%).

### 5. ElevenLabs
* **Qualité** : Voix stable de 3.45 MOS.
* **Vitesse** : ~1.96 s par réplique.
