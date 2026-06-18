"""
Classe de base abstraite pour les adaptateurs de modèles STT.

Définit l'interface commune que chaque modèle doit implémenter.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Résultat d'une transcription vocale (STT)."""

    text: str
    latency: float  # secondes — temps total d'exécution de la requête
    error: str | None = None


class STTModel(ABC):
    """Interface abstraite pour un modèle STT.

    Chaque adaptateur de transcription concret doit hériter de cette classe
    et implémenter au minimum ``setup()`` et ``transcribe()``.

    Attributes:
        name: Identifiant court du modèle (ex. ``"mistral"``).
        description: Description lisible du modèle.
        tier: Catégorie de ressource — ``"local"`` ou ``"api"``.
    """

    name: str = "base_stt"
    description: str = "Abstract STT model"
    tier: str = "local"  # 'local', 'api'

    @abstractmethod
    def setup(self) -> None:
        """Initialise le modèle (chargement en mémoire ou setup API).

        Appelé une seule fois avant la première transcription.
        """

    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcrit un fichier audio et retourne le résultat.

        Args:
            audio_path: Chemin du fichier audio à transcrire (.wav ou .mp3).

        Returns:
            TranscriptionResult contenant le texte brut transcrit et la latence.
        """

    def teardown(self) -> None:
        """Libère les ressources du modèle."""
        logger.debug("%s: teardown (no-op)", self.name)

    def is_available(self) -> bool:
        """Vérifie si le modèle est disponible (dépendances, clé API, etc.)."""
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} tier={self.tier!r}>"
