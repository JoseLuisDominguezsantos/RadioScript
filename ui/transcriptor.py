# ─── RadioScript · ui/transcriptor.py ────────────────────────────────────────
import threading
from faster_whisper import WhisperModel
from config import *


class Transcriptor:
    """Maneja la transcripción de audios con Faster-Whisper en hilo separado."""

    def __init__(self):
        self._modelo    = None
        self._ocupado   = False

    @property
    def ocupado(self):
        return self._ocupado

    def _cargar_modelo(self):
        if not self._modelo:
            self._modelo = WhisperModel("small", device="cpu", compute_type="int8")

    def transcribir_pendientes(self, audios: dict,
                                on_inicio,
                                on_progreso,
                                on_terminado):
        """Transcribe solo los audios con estado 'pendiente', uno a la vez.

        Callbacks:
            on_inicio(path)           — cuando empieza un audio
            on_progreso(path, texto)  — cuando termina con éxito
            on_terminado()            — cuando termina toda la cola
        """
        pendientes = [p for p, info in audios.items()
                      if info.get("estado") == "pendiente"]

        if not pendientes:
            on_terminado()
            return

        self._ocupado = True

        def _worker():
            self._cargar_modelo()
            for path in pendientes:
                on_inicio(path)
                try:
                    segments, _ = self._modelo.transcribe(path, language="es")
                    texto = " ".join(s.text.strip() for s in segments).strip()
                    on_progreso(path, texto)
                except Exception as e:
                    on_progreso(path, None, error=str(e))

            self._ocupado = False
            on_terminado()

        threading.Thread(target=_worker, daemon=True).start()