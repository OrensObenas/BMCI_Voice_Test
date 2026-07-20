# 📱 Architecture Technique : Pipeline Vocal 100% On-Device (Mobile Offline)

Pour déployer l'intégralité de la simulation vocale (STT ➔ SLM ➔ TTS) directement sur un appareil mobile (iOS/Android) sans dépendre d'un serveur ou d'une connexion internet, le pipeline doit être repensé avec des moteurs d'exécution embarqués ultra-optimisés.

---

## 🏗️ Schéma global de l'architecture On-Device

```
[Microphone] 
     │  (PCM Audio Stream)
     ▼
┌────────────────────────────────────────────────────────┐
│ 🎙️ STT Local : Whisper.cpp (Whisper Tiny Quantized)     │
└────────────────────────────────────────────────────────┘
     │  (Texte transcrit)
     ▼
┌────────────────────────────────────────────────────────┐
│ 🧠 SLM Local : Qwen 2.5 0.5B (via MLC LLM / GPU Mobile)│
└────────────────────────────────────────────────────────┘
     │  (Streaming de jetons textuels)
     ▼
┌────────────────────────────────────────────────────────┐
│ 🔊 TTS Local : Kokoro ONNX (via ONNX Runtime Mobile)    │
└────────────────────────────────────────────────────────┘
     │  (WAV Audio Stream)
     ▼
[Haut-Parleur Mobile]
```

---

## 🛠️ Les Briques Techniques Recommandées

### 1. Le Cerveau (SLM) : Qwen 2.5 0.5B / 1.5B via MLC LLM
Pour exécuter un LLM localement sur un processeur mobile sans vider la batterie ou saturer la RAM :
* **Framework : MLC LLM (Machine Learning Compilation)**
  * *Pourquoi* : Il compile les modèles LLM spécifiquement pour les puces mobiles. Il exploite **Metal** sur iOS (processeurs Apple Silicon) et **Vulkan / OpenCL** sur Android pour utiliser le processeur graphique (GPU) ou le NPU de l'appareil.
  * *Performance* : Permet d'atteindre plus de **30 à 45 tokens par seconde** sur un smartphone récent avec un modèle Qwen 2.5 de 0.5B ou 1.5B.
* **Quantification** : Le modèle doit être converti au format `q4f16` (quantification 4 bits, poids en demi-précision float16) pour occuper moins de **400 Mo de RAM** (pour le 0.5B).
* **SDK mobiles** : MLC LLM fournit des bibliothèques prêtes pour **Swift (iOS)**, **Kotlin (Android)** et **Flutter / React Native**.

---

### 2. L'Écoute (STT) : Whisper.cpp (Tiny ou Base)
Pour traduire la voix en texte en local avec une latence quasi-nulle :
* **Framework : Whisper.cpp** (portage C/C++ ultra-optimisé du modèle Whisper d'OpenAI).
  * *Pourquoi* : Il est conçu pour tourner sur CPU mobile en utilisant les instructions vectorielles Neon (ARM).
  * *Modèle* : Utilisez le modèle **`Whisper Tiny (quantifié en q4_0)`** ou **`Whisper Base`**. Le fichier pèse moins de 80 Mo et s'exécute en temps réel (Real-Time Factor < 0.5 sur un téléphone standard).
* **Alternative : Sherpa-onnx**
  * Basé sur ONNX Runtime, il supporte les modèles de type *Zipformer* et *Whisper* avec une excellente gestion de la mémoire sous Android/iOS.

---

### 3. La Voix (TTS) : Kokoro ONNX (82M)
Pour synthétiser la voix émotionnelle de M. Orens en local :
* **Framework : ONNX Runtime Mobile (Java/Kotlin pour Android, Objective-C/Swift pour iOS)**
* **Moteur TTS : Kokoro TTS (82 millions de paramètres)**
  * *Pourquoi* : Kokoro est le meilleur compromis actuel entre qualité naturelle de la voix (MOS élevé) et légèreté (modèle d'environ 330 Mo, compressible en version quantifiée à 100 Mo).
  * *Phonétisation* : Il nécessite d'embarquer la bibliothèque `espeak-ng` compilée pour mobile avec ses fichiers de données phonétiques pour convertir le texte français en phonemes avant de l'envoyer au fichier ONNX.
  * *Intégration* : Il existe des wrappers open-source comme `flutter_kokoro_tts` ou des templates Expo/React-Native (`expo-kokoro-onnx`) qui simplifient son intégration.

---

## 📱 Avantages du Passage au 100% Mobile

1. **Latence Imbattable** : Plus de cascades de requêtes HTTPS vers le cloud. La latence totale (STT + SLM + TTS) peut descendre **sous les 300ms** sur un iPhone ou un Samsung récent, offrant une réactivité humaine.
2. **Confidentialité Totale** : Aucune donnée audio ou textuelle ne quitte le téléphone.
3. **Fonctionnement Offline** : Idéal pour des simulations de formation sur tablette ou mobile en déplacement sans connexion réseau stable.
4. **Zéro coût d'infrastructure** : Pas de serveurs GPU haut de gamme à louer mensuellement. Le calcul est déporté sur le processeur du client.

---

## 📈 Par quoi commencer pour tester ?

Si vous souhaitez valider cette approche mobile, voici la feuille de route conseillée :

1. **Tester le SLM sur mobile** :
   * Installez l'application de démonstration **MLC Chat** (disponible gratuitement sur l'App Store iOS et le Play Store Android).
   * Chargez le modèle Qwen 2.5 1.5B ou 3B depuis les dépôts publics pour tester la vitesse de génération locale sur vos smartphones de test.
2. **Tester le TTS localement** :
   * Utilisez un wrapper comme `flutter_kokoro_tts` pour créer une mini-application de démonstration capable de faire parler le téléphone offline avec le modèle Kokoro-ONNX.
3. **Fusionner le pipeline** :
   * Une fois les deux briques testées individuellement, assemblez-les dans un projet mobile (Flutter de préférence pour la portabilité) en y ajoutant le package d'enregistrement audio natif.
