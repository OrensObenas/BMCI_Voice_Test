import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# S'assurer que GOOGLE_API_KEY et GEMINI_API_KEY sont synchronisés pour le SDK Google
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from livekit.agents import JobContext, WorkerOptions, cli, llm, inference
from livekit.agents.voice_agent import VoicePipelineAgent
from livekit.plugins import google, elevenlabs

logger = logging.getLogger("bank-agent")

# Prompt de personnalité pour le client mécontent (M. Orens)
SYSTEM_INSTRUCTIONS = """
Tu es M. Orens, un client de la banque Atlas Bank. Tu es extrêmement irrité, frustré et pressé. 
Tu viens de te déplacer en agence pour retirer 100 000 dirhams en liquide, mais la conseillère t'annonce que la limite de retrait sans préavis est de 50 000 dirhams par jour.

Consignes de rôle pour la simulation :
- Tu es fâché. Tu refuses d'abord les excuses de la conseillère et tu trouves ridicule de ne pas pouvoir disposer de ton propre argent librement.
- Tu es insistant et exigeant, tu hausses légèrement le ton si on ne te propose pas de solution rapide.
- Tu n'expliques pourquoi tu as besoin de cette somme (acheter une maison, le vendeur attend l'argent aujourd'hui sinon il vend à quelqu'un d'autre) QUE si la conseillère te le demande poliment ou s'intéresse sincèrement à ton problème.
- Tu es méfiant face aux solutions alternatives (comme le virement). Tu ne te laisses convaincre par un virement que si la conseillère t'assure patiemment qu'il arrivera aujourd'hui avant midi sans risque.
- Réponds avec des phrases courtes, directes et naturelles (langage parlé de tous les jours). Ne fais pas de longues phrases littéraires ou de listes à puces. Sois réactif et coupé dans ton élan si l'agent t'interrompt.
"""

async def entrypoint(ctx: JobContext):
    logger.info("Connexion au salon LiveKit...")
    await ctx.connect()
    logger.info(f"Connecté avec succès au salon : {ctx.room.name}")

    # Initialisation du module VAD (Voice Activity Detection)
    logger.info("Chargement du modèle VAD...")
    vad_plugin = inference.VAD.load()

    # Configuration du STT (Speech-to-Text) ElevenLabs Scribe v2
    logger.info("Configuration du STT ElevenLabs...")
    stt_plugin = elevenlabs.STT(language="fr")

    # Configuration du LLM Google Gemini
    logger.info("Configuration du LLM Google Gemini...")
    llm_plugin = google.LLM(model="gemini-1.5-flash")

    # Configuration du TTS (Text-to-Speech) ElevenLabs avec la voix Adam (gronchonne)
    logger.info("Configuration du TTS ElevenLabs (voix Adam)...")
    tts_plugin = elevenlabs.TTS(
        voice_id="pNInz6obpgDQGcFmaJgB", # ID de la voix masculine 'Adam'
        model_id="eleven_multilingual_v2"
    )

    # Définition du contexte initial du chat avec le prompt de personnalité
    chat_context = llm.ChatContext().append(
        role="system",
        text=SYSTEM_INSTRUCTIONS
    )

    # Création de l'agent vocal interactif
    logger.info("Initialisation de l'agent vocal (VoicePipelineAgent)...")
    agent = VoicePipelineAgent(
        vad=vad_plugin,
        stt=stt_plugin,
        llm=llm_plugin,
        tts=tts_plugin,
        chat_ctx=chat_context,
        will_first_say="Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant.",
    )

    # Démarrage de l'agent dans le salon LiveKit
    logger.info("Démarrage de l'agent conversationnel...")
    agent.start(ctx.room)
    logger.info("Agent actif et en attente d'interaction vocale.")

if __name__ == "__main__":
    # Lancement du worker LiveKit CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
