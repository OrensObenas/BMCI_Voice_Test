"""
Classe de base abstraite pour les adaptateurs de modèles TTS.

Définit l'interface commune que chaque modèle doit implémenter :
- setup() : initialisation du modèle
- synthesize() : synthèse vocale d'un texte
- teardown() : libération des ressources
- is_available() : vérification de la disponibilité du modèle
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SynthesisResult:
    """Résultat d'une synthèse vocale."""

    audio_path: str
    generation_time: float  # seconds — total wall-clock time for synthesis
    ttfa: float  # time to first audio chunk (seconds)
    sample_rate: int
    audio_duration: float  # seconds — duration of the generated audio
    rtf: float  # real-time factor = generation_time / audio_duration


class TTSModel(ABC):
    """Interface abstraite pour un modèle TTS.

    Chaque adaptateur concret doit hériter de cette classe et implémenter
    au minimum ``setup()`` et ``synthesize()``.

    Attributes:
        name: Identifiant court du modèle (ex. ``"kokoro"``).
        description: Description lisible du modèle.
        tier: Catégorie de ressource requise — ``"cpu"``, ``"gpu"`` ou ``"api"``.
    """

    name: str = "base"
    description: str = "Abstract TTS model"
    tier: str = "cpu"  # 'cpu', 'gpu', 'api'

    @abstractmethod
    def setup(self) -> None:
        """Initialise le modèle (chargement des poids, pipeline, etc.).

        Appelé une seule fois avant la première synthèse.
        """

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise un texte et sauvegarde l'audio en WAV.

        Args:
            text: Texte à synthétiser (en français).
            output_path: Chemin du fichier WAV de sortie.

        Returns:
            SynthesisResult avec toutes les métriques de performance.
        """

    def teardown(self) -> None:
        """Libère les ressources du modèle.

        Implémentation par défaut : ne fait rien.
        """
        logger.debug("%s: teardown (no-op)", self.name)

    def is_available(self) -> bool:
        """Vérifie si le modèle est disponible (dépendances installées, clé API, etc.).

        Implémentation par défaut : retourne True.

        Returns:
            True si le modèle peut être utilisé, False sinon.
        """
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} tier={self.tier!r}>"
