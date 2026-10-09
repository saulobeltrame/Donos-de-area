import pandas as pd
import unicodedata

def formatar_tempo(segundos, padrao="-"):
    try:
        if pd.isna(segundos):
            return padrao
        val = float(segundos)
        if val <= 0:
            return padrao
        horas = int(val // 3600)
        minutos = int((val % 3600) // 60)
        segs = int(val % 60)
        if horas > 0:
            return f"{horas}h {minutos:02d}m {segs:02d}s"
        return f"{minutos}m {segs:02d}s"
    except Exception:
        return padrao

def formatar_tempo_scalar(segundos):
    try:
        val = float(segundos)
        if val <= 0 or pd.isna(val):
            return "-"
        horas = int(val // 3600)
        minutos = int((val % 3600) // 60)
        segs = int(val % 60)
        if horas > 0:
            return f"{horas}h {minutos:02d}m {segs:02d}s"
        return f"{minutos}m {segs:02d}s"
    except Exception:
        return "-"

def normalizar_str(texto):
    return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8').lower()