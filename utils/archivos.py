# ─── RadioScript · utils/archivos.py ─────────────────────────────────────────
import os
from config import FORMATOS_VALIDOS


def validar_audio(path: str) -> tuple[bool, str]:
    """Valida si un archivo es un audio aceptado.
    Retorna (es_valido, motivo_si_falla)."""
    ext = os.path.splitext(path)[1].lower()
    if not os.path.isfile(path):
        return False, "no_existe"
    if ext not in FORMATOS_VALIDOS:
        return False, "formato_invalido"
    return True, ""


def formato_tamaño(bytes: int) -> str:
    """Convierte bytes a formato legible."""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 ** 2:
        return f"{bytes / 1024:.1f} KB"
    else:
        return f"{bytes / 1024 ** 2:.1f} MB"


def procesar_paths(paths: list[str], audios_actuales: dict) -> dict:
    """Procesa una lista de paths y retorna estadísticas.
    Retorna dict con: nuevos, duplicados, invalidos, paths_nuevos."""
    resultado = {"nuevos": 0, "duplicados": 0, "invalidos": 0, "paths_nuevos": []}

    for path in paths:
        path = path.strip().strip("{}")

        valido, motivo = validar_audio(path)
        if not valido:
            resultado["invalidos"] += 1
            continue

        if path in audios_actuales:
            resultado["duplicados"] += 1
            continue

        resultado["paths_nuevos"].append(path)
        resultado["nuevos"] += 1

    return resultado