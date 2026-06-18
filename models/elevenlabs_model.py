"""
Adaptateur TTS pour l'API ElevenLabs (via REST / requests).

N'utilise PAS le SDK ``elevenlabs`` (problème de chemins longs sur Windows).
Appelle directement l'API REST avec ``requests`` + ``httpx`` pour le streaming.

Variable d'environnement requise : ``ELEVENLABS_API_KEY``
"""

import io
import logging
import time
from pathlib import Path

import requests
import soundfile as sf

from models.base import SynthesisResult, TTSModel

logger = logging.getLogger(__name__)

# ── Constantes ElevenLabs ────────────────────────────────────────────────────
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_SAMPLE_RATE = 44100
RATE_LIMIT_SLEEP = 1.0


class ElevenLabsModel(TTSModel):
    """Adaptateur pour l'API ElevenLabs (cloud, REST direct).

    Utilise l'API REST directement au lieu du SDK Python pour éviter
    les problèmes de chemins longs sur Windows.
    """

    name = "elevenlabs"
    description = "ElevenLabs API — eleven_multilingual_v2 (cloud REST)"
    tier = "api"

    def __init__(self) -> None:
        self._api_key: str = ""
        self._voice_id: str = ""
        self._voice_name: str = ""
        self._headers: dict = {}
        self.available_voices: list[dict] = []
        self.voice_id: str = ""

    # ── Lifecycle ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Vérifie que la clé API est configurée."""
        try:
            from config import ELEVENLABS_API_KEY
            if not ELEVENLABS_API_KEY:
                logger.warning("ELEVENLABS_API_KEY est vide — modèle indisponible")
                return False
            return True
        except ImportError:
            logger.warning("Impossible d'importer config — modèle indisponible")
            return False

    def setup(self) -> None:
        """Initialise les headers et résout le voice_id."""
        from config import ELEVENLABS_API_KEY

        self._api_key = ELEVENLABS_API_KEY
        self._headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        # Récupérer la liste des voix et trouver une voix française
        try:
            resp = requests.get(
                f"{ELEVENLABS_API_BASE}/voices",
                headers={"xi-api-key": self._api_key},
                timeout=15,
            )
            resp.raise_for_status()
            voices = resp.json().get("voices", [])

            # Chercher une voix française ou prendre "Charlotte" / la première
            french_voice = None
            charlotte_voice = None
            for v in voices:
                labels = v.get("labels", {})
                name = v.get("name", "")
                if name == "Charlotte":
                    charlotte_voice = v
                # Chercher des labels indiquant le français
                accent = labels.get("accent", "").lower()
                lang = labels.get("language", "").lower()
                if "french" in accent or "french" in lang or "français" in lang:
                    french_voice = v
                    break

            self.available_voices = voices
            chosen = french_voice or charlotte_voice or (voices[0] if voices else None)
            if chosen:
                self._voice_id = chosen["voice_id"]
                self._voice_name = chosen.get("name", "unknown")
                logger.info(
                    "ElevenLabs: voix sélectionnée '%s' (id=%s)",
                    self._voice_name, self._voice_id,
                )
            else:
                raise RuntimeError("Aucune voix disponible sur le compte ElevenLabs")

        except requests.RequestException as e:
            logger.error("Impossible de récupérer les voix ElevenLabs : %s", e)
            raise

        logger.info(
            "Client ElevenLabs REST initialisé (model=%s, voice=%s)",
            ELEVENLABS_MODEL, self._voice_name,
        )

    def teardown(self) -> None:
        """Pas de ressources à libérer."""
        logger.debug("ElevenLabs REST: teardown (no-op)")

    # ── Synthèse ─────────────────────────────────────────────────────────

    def synthesize(self, text: str, output_path: str) -> SynthesisResult:
        """Synthétise *text* via l'API REST ElevenLabs.

        Utilise le streaming pour mesurer le TTFA réel.

        Args:
            text: Texte français à synthétiser.
            output_path: Chemin du fichier audio de sortie.

        Returns:
            SynthesisResult avec métriques de performance.
        """
        voice_id = getattr(self, "voice_id", None) or self._voice_id
        if not voice_id:
            raise RuntimeError("Appeler setup() avant synthesize()")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        logger.debug("ElevenLabs: synthèse de %d caractères", len(text))

        url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}/stream"
        payload = {
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        ttfa: float | None = None
        audio_chunks: list[bytes] = []
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                t_start = time.perf_counter()

                resp = requests.post(
                    url,
                    json=payload,
                    headers=self._headers,
                    stream=True,
                    timeout=30,
                )

                if resp.status_code == 429:
                    if attempt < max_retries:
                        sleep_time = RATE_LIMIT_SLEEP * attempt
                        logger.warning(
                            "ElevenLabs: rate-limit (429), pause %.1f s (tentative %d/%d)",
                            sleep_time, attempt, max_retries,
                        )
                        time.sleep(sleep_time)
                        continue
                    resp.raise_for_status()

                resp.raise_for_status()

                for chunk in resp.iter_content(chunk_size=4096):
                    if chunk and len(chunk) > 0:
                        if ttfa is None:
                            ttfa = time.perf_counter() - t_start
                            logger.debug("ElevenLabs: TTFA = %.4f s", ttfa)
                        audio_chunks.append(chunk)

                break  # Succès

            except requests.RequestException as exc:
                if attempt < max_retries and "429" in str(exc):
                    sleep_time = RATE_LIMIT_SLEEP * attempt
                    logger.warning(
                        "ElevenLabs: erreur réseau, retry %d/%d après %.1f s",
                        attempt, max_retries, sleep_time,
                    )
                    time.sleep(sleep_time)
                    ttfa = None
                    audio_chunks.clear()
                    continue
                logger.exception("ElevenLabs: erreur pendant la synthèse")
                raise

        t_end = time.perf_counter()
        generation_time = t_end - t_start

        if not audio_chunks:
            raise RuntimeError("L'API ElevenLabs n'a retourné aucun audio")

        # L'API retourne du MP3 par défaut — sauvegarder puis lire les métadonnées
        raw_audio = b"".join(audio_chunks)

        # Écrire le MP3 brut d'abord
        mp3_path = output_path.replace(".wav", ".mp3") if output_path.endswith(".wav") else output_path + ".mp3"
        with open(mp3_path, "wb") as f:
            f.write(raw_audio)

        # Convertir MP3 → WAV via soundfile (qui utilise libsndfile)
        try:
            data, sample_rate = sf.read(io.BytesIO(raw_audio))
            sf.write(output_path, data, sample_rate)
            audio_duration = len(data) / sample_rate
        except Exception:
            # Si soundfile ne peut pas lire le MP3, essayer via le fichier
            try:
                import librosa
                data, sample_rate = librosa.load(mp3_path, sr=None, mono=False)
                sf.write(output_path, data.T if data.ndim > 1 else data, sample_rate)
                audio_duration = len(data.T if data.ndim > 1 else data) / sample_rate
            except Exception:
                logger.warning("Impossible de convertir MP3→WAV, conservation du MP3")
                output_path = mp3_path
                try:
                    info = sf.info(mp3_path)
                    audio_duration = info.duration
                    sample_rate = info.samplerate
                except Exception:
                    audio_duration = 0.0
                    sample_rate = ELEVENLABS_SAMPLE_RATE

        # Nettoyer le MP3 temporaire si la conversion WAV a réussi
        mp3_file = Path(mp3_path)
        if mp3_file.exists() and output_path != mp3_path:
            try:
                mp3_file.unlink()
            except OSError:
                pass

        rtf = generation_time / audio_duration if audio_duration > 0 else float("inf")

        result = SynthesisResult(
            audio_path=output_path,
            generation_time=generation_time,
            ttfa=ttfa if ttfa is not None else generation_time,
            sample_rate=sample_rate,
            audio_duration=audio_duration,
            rtf=rtf,
        )
        logger.info(
            "ElevenLabs: %.2f s audio en %.3f s (RTF=%.3f, TTFA=%.3f s)",
            result.audio_duration, result.generation_time, result.rtf, result.ttfa,
        )
        return result
