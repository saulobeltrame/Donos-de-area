import pandas as pd

def obter_ids_finalizados(df):
    if 'STATUS FORM' not in df.columns or 'ID' not in df.columns:
        return set(df['ID'].dropna().unique()) if 'ID' in df.columns else set()
        
    status_upper = df['STATUS FORM'].astype(str).str.strip().str.upper()
    ids_incompletos = set(df.loc[
        status_upper.isin(['NÃO FINALIZADO', 'NAO FINALIZADO', 'EM ANDAMENTO']), 'ID'
    ].dropna().unique())
    ids_finalizados = set(df.loc[
        status_upper == 'FINALIZADO', 'ID'
    ].dropna().unique())
    
    return ids_finalizados - ids_incompletos