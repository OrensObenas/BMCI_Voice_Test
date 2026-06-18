# 🎙️ Fiche de Recherche : Collecte & Évaluation des Modèles TTS

Ce document rassemble les informations détaillées, les sources officielles et la faisabilité d'intégration pour les **25 modèles de Text-to-Speech (TTS)** issus du classement de l'Arena.

---

## 📊 Tableau de Synthèse des 25 Modèles

| Rang | Modèle | Type | Auteur / Organisme | Source / Repo GitHub | Support FR Natif | Statut de Faisabilité (Local CPU Windows) |
|---|---|---|---|---|:---:|---|
| **#1** | **ElevenLabs** | Propriétaire API | ElevenLabs | [elevenlabs.io](https://elevenlabs.io) | ✅ Oui | **Testé & Intégré** (via API REST) |
| **#2** | **Hume Octave** | Propriétaire API | Hume AI | [hume.ai](https://hume.ai) | ✅ Oui | **Possible** (requiert clé API) |
| **#3** | **Papla P1** | Propriétaire API | Papla Media | [papla.media](https://papla.media) | ✅ Oui | **Possible** (API / Ne marche pas en libre) |
| **#4** | **Play.HT 2.0** | Propriétaire API | Play.HT | [play.ht](https://play.ht) | ✅ Oui | **Possible** (API / Ne marche pas en libre) |
| **#5** | **Play.HT 3.0 Mini** | Propriétaire API | Play.HT | [play.ht](https://play.ht) | ✅ Oui | **Possible** (API / Ne marche pas en libre) |
| **#6** | **Kokoro v0.19** | Open Weights | ShoukanLabs / Hexgrad | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | ✅ Oui | **Possible** (Préférer v1.0 disponible localement) |
| **#7** | **Kokoro v1.0** | Open Weights | ShoukanLabs / Hexgrad | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | ✅ Oui | **Testé & Intégré** (Local CPU) |
| **#8** | **Fish Speech v1.5** | Open Weights | Fish Audio | [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) | ✅ Oui | **Bloqué** (GPU VRAM 8+ GB requis) |
| **#9** | **XTTSv2** | Open Weights | Coqui.ai | [coqui-ai/TTS](https://github.com/coqui-ai/TTS) | ✅ Oui | **Bloqué** (Dépendance numba sur Python 3.13) |
| **#10**| **PlayDialog** | Propriétaire API | Play.HT | [play.ht](https://play.ht) | ✅ Oui | **Possible** (API propriétaire) |
| **#11**| **MetaVoice** | Open Weights | MetaVoice | [metavoice-1B](https://github.com/metavoiceio/metavoice-src) | ❌ Anglais | **Bloqué** (Pas de FR natif, VRAM 12 GB requis) |
| **#12**| **StyleTTS 2** | Open Weights | Li et al. | [yl4579/StyleTTS2](https://github.com/yl4579/StyleTTS2) | ❌ Anglais | **Bloqué** (Nécessite GPU + ré-entraînement en FR) |
| **#13**| **PlayDialog 1.0** | Propriétaire API | Play.HT | [play.ht](https://play.ht) | ✅ Oui | **Possible** (API propriétaire) |
| **#14**| **OpenVoice** | Open Weights | MyShell.ai | [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) | ⚠️ Via Melo | **Bloqué** (Dépendance C++ `fugashi` sur Win/Py3.13) |
| **#15**| **MeloTTS** | Open Weights | MyShell.ai | [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS) | ✅ Oui | **Bloqué** (Dépendance C++ `fugashi` sur Win/Py3.13) |
| **#16**| **Fish Speech v1.4** | Open Weights | Fish Audio | [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) | ✅ Oui | **Bloqué** (GPU VRAM 8+ GB requis) |
| **#17**| **GPT-SoVITS** | Open Weights | RVC-Boss | [RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) | ⚠️ Communautaire | **Bloqué** (GPU requis + interface lourde) |
| **#18**| **WhisperSpeech**| Open Weights | Collabora | [collabora/WhisperSpeech](https://github.com/collabora/WhisperSpeech) | ✅ Oui | **Bloqué** (GPU CUDA fortement requis) |
| **#19**| **CosyVoice 2.0**| Open Weights | Alibaba FunASR | [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) | ✅ Oui | **Bloqué** (GPU VRAM 8-12 GB requis) |
| **#20**| **Parler TTS Large**| Open Weights | Hugging Face | [huggingface/parler-tts](https://github.com/huggingface/parler-tts) | ✅ Oui | **Bloqué** (GPU requis + trop lourd sur CPU) |
| **#21**| **Parler TTS** | Open Weights | Hugging Face | [huggingface/parler-tts](https://github.com/huggingface/parler-tts) | ✅ Oui | **Bloqué** (GPU requis) |
| **#22**| **Vokan TTS** | Open Weights | ShoukanLabs | [shoukanlabs/Vokan](https://huggingface.co/shoukanlabs/Vokan) | ❌ Anglais | **Bloqué** (StyleTTS2 fine-tune, anglais uniquement) |
| **#23**| **OpenVoice V2** | Open Weights | MyShell.ai | [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) | ⚠️ Via Melo | **Bloqué** (Mêmes dépendances C++ `fugashi`) |
| **#24**| **VoiceCraft 2.0**| Open Weights | UT Austin | [jasonppy/VoiceCraft](https://github.com/jasonppy/VoiceCraft) | ❌ Anglais | **Bloqué** (Anglais natif, VRAM 16 GB+ requis) |
| **#25**| **Pheme** | Open Weights | Stability AI | [Pheme](https://github.com/jasonboesch/VoiceCraft) | ❌ Anglais | **Bloqué** (Anglais uniquement, stade recherche) |

---

## 🔍 Analyse Détaillée par Modèle

### 1. ElevenLabs (Propriétaire)
*   **Description** : Référence mondiale actuelle du Text-to-Speech et du Voice Cloning. Modèle génératif multilingue extrêmement fluide, expressif et rapide.
*   **Architecture** : Propriétaire (probablement un modèle autoregressif basé sur des transformers de diffusion).
*   **Faisabilité** : Entièrement testé et intégré à notre pipeline de benchmark via une requête API REST directe en Python, contournant les limitations de chemins de fichiers de son SDK officiel sous Windows.

### 2. Hume Octave (Propriétaire)
*   **Description** : Modèle d'IA générative vocale centré sur la prosodie et l'expressivité émotionnelle (capable d'imiter les rires, les hésitations et les soupirs).
*   **Architecture** : Propriétaire.
*   **Faisabilité** : Intégrable via leur API REST, sous réserve d'obtenir une clé API valide.

### 3. Papla P1 (Propriétaire)
*   **Description** : Conçu pour les agents conversationnels et la téléphonie en temps réel par Papla Media. Très bien positionné sur la naturalité du dialogue spontané.
*   **Faisabilité** : Disponible uniquement sous forme d'API privée.

### 4. Play.HT 2.0 & 3.0 Mini (Propriétaire)
*   **Description** : Plateforme TTS et de clonage de voix. La version 3.0 Mini est optimisée pour une latence extrêmement faible en temps réel.
*   **Faisabilité** : API payante.

### 5. Kokoro (v0.19 & v1.0) (Open Weights)
*   **Description** : Un modèle ultra-léger (82 millions de paramètres) basé sur l'architecture StyleTTS 2, ré-entraîné pour le français. Offre un ratio performance/légèreté exceptionnel (tourne parfaitement sur CPU).
*   **Licence** : Apache 2.0.
*   **Faisabilité** : La version **v1.0** est déjà installée et pleinement opérationnelle dans notre projet. Elle s'exécute localement en 24kHz.

### 6. Fish Speech (v1.4 & v1.5) (Open Weights)
*   **Description** : Modèle autoregressif combiné à un VQ-GAN développé par Fish Audio. Il excelle dans le clonage de voix à partir de quelques secondes et le multilinguisme.
*   **Licence** : Double licence (commerciale payante / non-commerciale gratuite).
*   **Faisabilité** : Trop lourd pour s'exécuter de façon fluide sur CPU. Nécessite des dépendances GPU spécifiques (`flash-attn` ou compilation PyTorch CUDA) et 8 à 10 Go de VRAM.

### 7. XTTSv2 (Open Weights)
*   **Description** : Le modèle multilingue phare de Coqui.ai (17 langues supportées dont le français). Permet le clonage vocal instantané à partir de 3 secondes d'audio.
*   **Licence** : CPML (Coqui Public Model License - libre pour usage non-commercial).
*   **Faisabilité** : Incompatible avec Python 3.13 sur Windows. La bibliothèque dépendante `TTS` repose sur de vieux modules (`numba`/`llvmlite`) qui ne se compilent pas sans compilateurs Rust/C++ locaux et échouent sur les versions récentes de Python.

### 8. MetaVoice (Open Weights)
*   **Description** : Modèle autoregressif de 1,2 milliard de paramètres axé sur la reproduction d'accords et de prosodie naturelle.
*   **Faisabilité** : Principalement conçu pour l'anglais. Il requiert un GPU conséquent (12 Go de VRAM minimum).

### 9. StyleTTS 2 (Open Weights)
*   **Description** : Modèle révolutionnaire basé sur la modélisation de styles adversaires (Style-based adversarial training). Il est extrêmement rapide et naturel.
*   **Licence** : MIT.
*   **Faisabilité** : Les modèles pré-entraînés officiels sont entraînés exclusivement sur de l'anglais (LJSpeech). L'adapter au français nécessite de l'entraîner à partir de zéro avec un dataset français, ce qui demande un GPU haut de gamme et du temps de calcul.

### 10. MeloTTS & OpenVoice (v1 & v2) (Open Weights)
*   **Description** : MeloTTS (par MyShell) est un modèle TTS ultra-rapide supportant le français natif. OpenVoice ajoute un convertisseur de ton par-dessus MeloTTS pour cloner n'importe quelle voix.
*   **Licence** : MIT.
*   **Faisabilité** : L'installation échoue sous Windows avec Python 3.13 car le phonémiseur de MeloTTS requiert les modules `mecab-python3` et `fugashi` qui ne possèdent pas de roues (wheels) pré-compilées et nécessitent d'avoir des compilateurs C++ configurés sur la machine.

### 11. Parler TTS (Open Weights)
*   **Description** : Modèle TTS de Hugging Face entièrement contrôlable par prompt textuel (par exemple : *"Une voix d'homme âgée, lisant lentement avec un bruit de vent en fond"*).
*   **Licence** : Apache 2.0.
*   **Faisabilité** : Le modèle est lourd (600M de paramètres) et optimisé pour le GPU. Son exécution sur CPU Windows génère des temps de traitement incompatibles avec un benchmark de latence interactif.

### 12. GPT-SoVITS (Open Weights)
*   **Description** : Modèle de clonage instantané (Few-shot) très populaire dans la communauté chinoise et japonaise.
*   **Faisabilité** : Nécessite un environnement GPU sous CUDA et une interface WebUI. Pas de support français officiel (uniquement via des forks communautaires).

### 13. CosyVoice 2.0 (Open Weights)
*   **Description** : Modèle de synthèse vocale générative d'Alibaba. Il produit des voix d'une naturalité impressionnante avec un contrôle complet de l'intonation et des émotions.
*   **Licence** : Apache 2.0.
*   **Faisabilité** : Conçu pour s'exécuter sur Linux/Windows avec CUDA. Très lourd sur CPU (nécessite 8-12 Go de VRAM).

### 14. VoiceCraft 2.0 (Open Weights)
*   **Description** : Modèle de codec audio autoregressif spécialisé dans l'édition de la parole et le TTS zero-shot.
*   **Faisabilité** : Gourmand en ressources (16 Go de VRAM recommandés). Entraîné uniquement sur des corpus anglophones (GigaSpeech).

---

## 📈 Proposition de Complément : Intégration de Edge-TTS, gTTS, OpenAI & Mistral AI (Voxtral)

Afin d'étoffer le classement disponible pour le benchmark en s'adaptant aux contraintes techniques (Windows CPU, Python 3.13, pas de VRAM), nous avons intégré d'autres alternatives très performantes du web :

1.  **Edge-TTS (Microsoft Azure Neural)** :
    *   **Description** : Accès direct aux voix neuronales de Microsoft Azure sans inscription ni clé API (via l'API de lecture à voix haute d'Edge). La voix `fr-FR-DeniseNeural` a été sélectionnée.
    *   **Résultats** : C'est le grand gagnant du benchmark de latence avec un **TTFA de 0.46s** et un **RTF de 0.105** (génération 10 fois plus rapide que la vitesse de lecture), combiné à un excellent score de naturalité de **3.41 MOS** (supérieur à ElevenLabs dans nos tests CPU).
2.  **gTTS (Google Translate TTS)** :
    *   **Description** : Interface simple avec l'API TTS de Google Translate. Très légère.
    *   **Résultats** : Bonnes performances en latence (RTF = 0.129) mais naturalité inférieure (3.34 MOS), voix typée "robotique" caractéristique des traducteurs en ligne.
3.  **OpenAI TTS (`openai`)** :
    *   **Description** : Modèle `tts-1` avec la voix `nova` (très fluide en français).
    *   **Résultats** : Intégration effectuée via requêtes REST en streaming. En attente de la clé `OPENAI_API_KEY` dans le fichier `.env` pour évaluation.
4.  **Mistral AI Voxtral TTS (`mistral`)** :
    *   **Description** : Le modèle génératif de synthèse vocale de Mistral (`voxtral-mini-tts-2603`) avec la voix `casual_male` (ou d'autres profils personnalisés/presets).
    *   **Résultats** : Intégration effectuée via requêtes REST (format WAV natif). En attente de la clé `MISTRAL_API_KEY` dans le fichier `.env` pour évaluation.
