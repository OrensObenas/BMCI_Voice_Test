"""
Registre des modèles TTS disponibles pour le benchmark.

Ce module expose :

- ``MODEL_REGISTRY`` : dictionnaire ``{nom: classe}`` de tous les adaptateurs.
- ``get_model(name)`` : instancie et retourne un adaptateur par son nom.

Usage::

    from models import get_model, MODEL_REGISTRY

    # Lister les modèles
    print(list(MODEL_REGISTRY.keys()))

    # Instancier un modèle
    model = get_model("kokoro")
    if model.is_available():
        model.setup()
        result = model.synthesize("Bonjour !", "output.wav")
        model.teardown()
"""

import logging

from models.base import SynthesisResult, TTSModel  # noqa: F401 — réexport public
from models.kokoro_model import KokoroModel
from models.melo_model import MeloModel
from models.xtts_model import XTTSModel
from models.elevenlabs_model import ElevenLabsModel
from models.f5tts_model import F5TTSModel
from models.gtts_model import GTTSModel
from models.edgetts_model import EdgeTTSModel
from models.openai_model import OpenAIModel
from models.hume_model import HumeModel
from models.mistral_model import MistralModel

logger = logging.getLogger(__name__)

# ── Registre des modèles ─────────────────────────────────────────────────────
MODEL_REGISTRY: dict[str, type[TTSModel]] = {
    "kokoro": KokoroModel,
    "melo": MeloModel,
    "xtts": XTTSModel,
    "elevenlabs": ElevenLabsModel,
    "f5tts": F5TTSModel,
    "gtts": GTTSModel,
    "edgetts": EdgeTTSModel,
    "openai": OpenAIModel,
    "hume": HumeModel,
    "mistral": MistralModel,
}


def get_model(name: str) -> TTSModel:
    """Instancie un adaptateur TTS par son nom.

    Args:
        name: Clé du modèle dans ``MODEL_REGISTRY``
              (ex. ``"kokoro"``, ``"melo"``, ``"xtts"``, ``"elevenlabs"``,
              ``"f5tts"``).

    Returns:
        Instance (non initialisée) du modèle demandé.

    Raises:
        KeyError: Si *name* n'existe pas dans le registre.
    """
    name_lower = name.lower().strip()
    if name_lower not in MODEL_REGISTRY:
        available = ", ".join(sorted(MODEL_REGISTRY.keys()))
        raise KeyError(
            f"Modèle inconnu : {name!r}. Modèles disponibles : {available}"
        )

    model_cls = MODEL_REGISTRY[name_lower]
    instance = model_cls()
    logger.debug("Modèle instancié : %r", instance)
    return instance


def list_available_models() -> list[str]:
    """Retourne les noms des modèles dont les dépendances sont installées.

    Returns:
        Liste triée des noms de modèles disponibles.
    """
    available = []
    for name, cls in sorted(MODEL_REGISTRY.items()):
        try:
            instance = cls()
            if instance.is_available():
                available.append(name)
        except Exception:
            logger.debug("Erreur lors du check de %s", name, exc_info=True)
    return available
