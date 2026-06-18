"""
Registre des modèles STT disponibles pour le benchmark.
"""

import logging

from stt_models.base import TranscriptionResult, STTModel  # noqa: F401
from stt_models.elevenlabs_stt import ElevenLabsSTT
from stt_models.mistral_stt import MistralSTT
from stt_models.cohere_stt import CohereSTT
from stt_models.openai_stt import OpenAISTT
from stt_models.whisper_local_stt import WhisperLocalSTT

logger = logging.getLogger(__name__)

# ── Registre des classes de modèles STT ───────────────────────────────────────
# Les clés simples mappent directement vers les classes (pour les APIs par exemple)
STT_CLASSES = {
    "elevenlabs": ElevenLabsSTT,
    "mistral": MistralSTT,
    "cohere": CohereSTT,
    "openai": OpenAISTT,
}


def get_stt_model(name: str) -> STTModel:
    """Instancie un adaptateur STT par son nom.

    Prend en charge les modèles d'APIs ainsi que les modèles locaux
    définis dynamiquement (ex. 'whisper-local-base', 'whisper-local-large-turbo').

    Args:
        name: Clé du modèle (ex. ``"mistral"``, ``"whisper-local-base"``).

    Returns:
        Instance (non initialisée) du modèle demandé.

    Raises:
        KeyError: Si le nom de modèle est inconnu.
    """
    name_lower = name.lower().strip()

    # Gérer le cas des modèles Whisper locaux
    if name_lower.startswith("whisper-local-"):
        model_size = name_lower.replace("whisper-local-", "")
        instance = WhisperLocalSTT(model_size=model_size)
        logger.debug("Modèle STT local instancié : %s", instance)
        return instance

    # Gérer les autres modèles (APIs)
    if name_lower in STT_CLASSES:
        model_cls = STT_CLASSES[name_lower]
        instance = model_cls()
        logger.debug("Modèle STT API instancié : %s", instance)
        return instance

    available = ", ".join(sorted(list(STT_CLASSES.keys()) + ["whisper-local-<taille>"]))
    raise KeyError(
        f"Modèle STT inconnu : {name!r}. Modèles disponibles : {available}"
    )


def list_available_stt_models() -> list[str]:
    """Retourne la liste des clés de modèles STT dont les clés API sont configurées ou locaux."""
    from config import AVAILABLE_STT_MODELS
    available = []
    for name in AVAILABLE_STT_MODELS:
        try:
            model = get_stt_model(name)
            if model.is_available():
                available.append(name)
        except Exception:
            pass
    return available
