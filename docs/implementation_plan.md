# Plan d'implémentation : Génération d'Audios de Discussion Complets avec Alternance de Voix

Ce plan décrit les modifications à apporter aux adaptateurs de modèles et le nouveau script à créer pour générer l'intégralité du dialogue bancaire (21 répliques) sous forme d'un seul fichier audio par modèle, avec des voix distinctes pour l'**Agent** (conseillère bancaire, voix généralement féminine/professionnelle) et le **Client** (client mécontent, voix généralement masculine/insistante).

---

## 1. Modifications Proposées sur les Adaptateurs de Modèles

Afin de permettre au script de discussion de modifier dynamiquement la voix ou le style (vitesse, accent) de chaque modèle entre chaque réplique sans recréer l'instance, nous allons effectuer de légers ajustements non-intrusifs :

### A. Kokoro v1.0
* **Fichier** : [kokoro_model.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/models/kokoro_model.py)
* **Changements** :
  * Déclarer `self.voice = "ff_siwis"` et `self.speed = 1.0` dans le constructeur `__init__`.
  * Utiliser ces attributs d'instance dynamiques dans l'appel du pipeline.
  * *Stratégie d'alternance* : N'ayant qu'une seule voix française (`ff_siwis`), nous différencierons l'Agent et le Client par la vitesse (`speed=1.05` pour l'Agent, `speed=0.9` pour le Client).

### B. MeloTTS
* **Fichier** : [melo_model.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/models/melo_model.py)
* **Changements** :
  * Déclarer `self.speed = 1.0` dans le constructeur `__init__`.
  * Passer l'argument `speed` à `self._tts.tts_to_file`.
  * *Stratégie d'alternance* : Vitesse normale (`speed=1.0`) pour l'Agent et vitesse ralentie/insistante (`speed=0.9`) pour le Client.

### C. Google Translate TTS (gTTS)
* **Fichier** : [gtts_model.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/models/gtts_model.py)
* **Changements** :
  * Ajouter `self.tld = "fr"` dans le constructeur.
  * Passer `tld` à l'instanciation de `gTTS(text, lang=self.lang, tld=self.tld)`.
  * *Stratégie d'alternance* : Accent de France (`tld="fr"`) pour l'Agent, et accent Canadien-Français (`tld="ca"`) pour le Client.

### D. ElevenLabs REST
* **Fichier** : [elevenlabs_model.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/models/elevenlabs_model.py)
* **Changements** :
  * Stocker la liste de toutes les voix retournées par l'API dans `self.available_voices = []` lors de l'appel à `setup()`.
  * Cela permettra au script de discussion de sélectionner deux voix différentes configurées sur votre compte.

---

## 2. Nouveau Script de Génération de Discussion

Nous allons créer un nouveau script principal :
* **Fichier** : `generate_discussion.py`
* **Fonctionnalités** :
  1. Charger les 21 répliques de [dialogue.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/dialogue.py).
  2. Charger et initialiser chaque modèle configuré.
  3. Maper les rôles aux voix selon les règles suivantes :

| Modèle TTS | Voix / Style Agent | Voix / Style Client |
| :--- | :--- | :--- |
| **kokoro** | `ff_siwis` (vitesse 1.05) | `ff_siwis` (vitesse 0.90) |
| **melo** | `FR` (vitesse 1.0) | `FR` (vitesse 0.90) |
| **edgetts** | `fr-FR-DeniseNeural` (féminin) | `fr-FR-HenriNeural` (masculin) |
| **gtts** | `lang="fr"`, `tld="fr"` (France) | `lang="fr"`, `tld="ca"` (Canada) |
| **f5tts** | Clonage voix féminine (référence Kokoro) | Clonage voix masculine (générée par Edge-TTS) |
| **openai** | `nova` (féminin) | `onyx` (masculin) |
| **mistral** | `fr_marie_neutral` (neutre) | `fr_marie_angry` (fâchée) |
| **elevenlabs** | Première voix française trouvée | Deuxième voix française trouvée |

  4. Pour chaque ligne de dialogue, appliquer la voix associée au rôle de la ligne et synthétiser l'audio individuel temporaire.
  5. Charger tous les audios générés d'une discussion et les concaténer avec un **silence de pause de 0,8 seconde** entre chaque réplique.
  6. Sauvegarder l'audio final fusionné dans le dossier `outputs/discussions/discussion_<model>.wav`.
  7. Nettoyer les fichiers temporaires de répliques individuelles.

---

## 3. Plan de Vérification

### Validation Locale
* Lancer la génération de la discussion complète pour les modèles CPU légers (`kokoro`, `gtts`, `edgetts`) :
  ```powershell
  .venv\Scripts\python generate_discussion.py --models kokoro gtts edgetts
  ```
* Vérifier la création des fichiers audio fusionnés dans `outputs/discussions/` et valider à l'écoute l'alternance de voix / styles entre l'Agent et le Client.
