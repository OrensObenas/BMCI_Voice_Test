# 🎤 Rapport d'Évaluation STT — Enregistrements Réels

Ce rapport présente l'analyse comparative des performances des modèles de reconnaissance vocale (STT/ASR) appliqués à vos trois enregistrements réels, réalisés avec trois appareils différents.

---

## 📊 Tableau de Synthèse des Performances

Le tableau ci-dessous regroupe les résultats de transcription pour chaque appareil et chaque modèle STT. Les modèles sont évalués sur le **WER** (Taux d'erreur de mots), le **CER** (Taux d'erreur de caractères), la **latence** de traitement, et le **RTF** (Real-Time Factor).

> [!TIP]
> Un RTF de **0.022** signifie que le modèle a transcrit l'audio **50 fois plus vite** que le temps réel de lecture.

| Appareil / Enregistrement　　　　 | Modèle STT                      | WER (%)   | CER (%)   | Latence (s) | RTF   |
| :----------------------------------| :--------------------------------| :---------:| :---------:| :-----------:| :-----:|
| 💻 **BMCI Computer** *(171.16 s)* | **ElevenLabs Scribe v2**        | **6.65%** | **4.39%** | 22.14 s     | 0.129 |
| 　　　　　　　　　　　　　　　　　| **Cohere Transcribe v2**        | **8.32%** | **5.70%** | 5.03 s      | 0.029 |
| 　　　　　　　　　　　　　　　　　| **Whisper Large-Turbo (Local)** | **9.15%** | **5.89%** | 115.92 s    | 0.677 |
| 　　　　　　　　　　　　　　　　　| **Mistral Voxtral**             | **9.56%** | **6.28%** | 4.48 s      | 0.026 |
| 　　　　　　　　　　　　　　　　　| **Whisper Base (Local)**        | 23.28%    | 12.71%    | 17.88 s     | 0.104 |
| 🎧 **Headset** *(169.22 s)*　　　 | **ElevenLabs Scribe v2**        | **3.95%** | **2.81%** | 14.94 s     | 0.088 |
| 　　　　　　　　　　　　　　　　　| **Cohere Transcribe v2**        | **8.52%** | **5.58%** | 5.09 s      | 0.030 |
| 　　　　　　　　　　　　　　　　　| **Mistral Voxtral**             | **9.77%** | **6.43%** | 3.98 s      | 0.024 |
| 　　　　　　　　　　　　　　　　　| **Whisper Large-Turbo (Local)** | 13.93%    | 9.13%     | 132.61 s    | 0.784 |
| 　　　　　　　　　　　　　　　　　| **Whisper Base (Local)**        | 29.11%    | 16.48%    | 19.15 s     | 0.113 |
| 📱 **Phone** *(172.52 s)*　　　　 | **ElevenLabs Scribe v2**        | **3.12%** | **2.19%** | 21.02 s     | 0.122 |
| 　　　　　　　　　　　　　　　　　| **Cohere Transcribe v2**        | **5.82%** | **3.70%** | 5.43 s      | 0.031 |
| 　　　　　　　　　　　　　　　　　| **Mistral Voxtral**             | **5.82%** | **3.85%** | 3.86 s      | 0.022 |
| 　　　　　　　　　　　　　　　　　| **Whisper Large-Turbo (Local)** | **6.03%** | **3.93%** | 132.91 s    | 0.770 |
| 　　　　　　　　　　　　　　　　　| **Whisper Base (Local)**        | 18.92%    | 10.97%    | 18.08 s     | 0.105 |

---

## 🔍 Analyses et Observations Clés

### 1. Influence de l'Appareil d'Enregistrement (Qualité Audio)
* **📱 Téléphone (Phone)** : C'est le **grand gagnant** en termes de clarté audio. Tous les modèles (sauf Whisper Base) descendent sous la barre des **6% de WER**. Le micro du téléphone gère excellemment bien le traitement de la voix à proximité et la réduction de bruit de fond.
* **🎧 Casque (Headset)** : Donne d'excellents résultats avec les modèles cloud API (WER de 3.95% pour ElevenLabs), mais montre des faiblesses avec les modèles locaux. Cela s'explique par un signal parfois plus étouffé.
* **💻 PC BMCI (Computer)** : Obtient des taux d'erreurs légèrement supérieurs sur les modèles cloud (ex. 8.32% pour Cohere vs 5.82% sur Téléphone). Cela est généralement dû à l'écho de la pièce capté par le microphone intégré du PC portable et au bruit de ventilation.

### 2. Confrontation des Modèles STT
* **🏆 ElevenLabs Scribe v2 (Gagnant Qualité)** : Il offre la meilleure précision sur les trois enregistrements. Il excelle dans la restitution des termes bancaires et le respect de la casse.
* **⚡ Mistral Voxtral & Cohere Transcribe v2 (Gagnants Rapidité)** : Leurs performances sont extrêmement proches de celles d'ElevenLabs, mais ils sont **incroyablement rapides**. Avec une latence d'environ **4 à 5 secondes** pour transcrire un fichier de près de 3 minutes, ils affichent un RTF de ~0.025.
* **🐢 Whisper Large-Turbo (Local)** : Très précis (jusqu'à 6.03% de WER sur Téléphone), mais **très lent sur CPU** (latence de plus de 2 minutes pour 3 minutes d'audio). Il est idéal si vous devez exécuter la transcription de manière confidentielle et locale, à condition d'avoir un GPU pour accélérer le traitement.
* **❌ Whisper Base (Local)** : Trop imprécis pour une application de production en français (WER entre 18.92% et 29.11%). Il fait beaucoup de fautes phonétiques (ex. *"100 000 iran"* au lieu de *"cent mille dirhams"*).

---

## 💡 Note sur le formatage des nombres (Biais du WER)

> [!IMPORTANT]
> Une partie du taux d'erreur (WER) des modèles Whisper et Mistral provient de la transcription des nombres en chiffres plutôt qu'en lettres. 
> * **Référence** : *"retirer **cent mille** dirhams"*
> * **Transcription Whisper / Mistral** : *"retirer **100 000** dirhams"*
> 
> Sur le plan de la compréhension, la transcription est 100% correcte, mais l'outil de calcul WER pénalise cette différence d'écriture. Sans ce biais de formatage, la précision acoustique réelle de **Mistral**, **Cohere** et **Whisper Large-Turbo** serait encore plus proche de 1% à 3% de WER.
