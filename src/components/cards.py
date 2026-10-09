import streamlit as st
import pandas as pd
from src.services.business_rules import obter_ids_finalizados
from src.utils.formatters import formatar_tempo_scalar

def render_cards(df_filtrado):
    ids_validos = obter_ids_finalizados(df_filtrado)
    df_cards = df_filtrado[df_filtrado['ID'].isin(ids_validos)].copy() if ids_validos else pd.DataFrame()
    total_inspecoes = len(ids_validos)
    
    status = df_cards['STATUS'] if not df_cards.empty else pd.Series(dtype='object')
    nao_conformes = (status == 'Não Conforme').sum()
    conformes = (status == 'Conforme').sum()    
    base_avaliada = conformes + nao_conformes
    taxa_conformidade = (conformes / base_avaliada * 100) if base_avaliada > 0 else 0.0

    segundos = 0.0
    if not df_cards.empty and 'ID' in df_cards.columns:
        col_tempo = next(
            (c for c in ['TIME_SEGUNDOS', 'TIME TOTAL FORMATADO', 'TIME TOTAL', 'TIME TOTAL FORM'] if c in df_cards.columns), 
            None
        )
        if col_tempo:
            def extrair_seg(v):
                if pd.isna(v):
                    return 0
                t = str(v).strip()
                if not t or t in ['-', '0', '00:00:00']:
                    return 0
                if ':' in t:
                    partes = t.split(':')
                    try:
                        if len(partes) == 3:
                            return int(float(partes[0]) * 3600 + float(partes[1]) * 60 + float(partes[2]))
                        elif len(partes) == 2:
                            return int(float(partes[0]) * 60 + float(partes[1]))
                    except Exception:
                        return 0
                try:
                    num = float(t)
                    return int(round(num * 86400)) if 0 < num < 1 else int(num)
                except ValueError:
                    return 0

            df_tempo = df_cards.assign(_segundos=df_cards[col_tempo].apply(extrair_seg))
            tempo_por_id = df_tempo.groupby('ID')['_segundos'].max()
            tempo_valido = tempo_por_id[tempo_por_id > 0]
            segundos = tempo_valido.mean() if not tempo_valido.empty else 0.0

    tempo_formatado = formatar_tempo_scalar(segundos)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total de Inspeções", f"{total_inspecoes:,}".replace(",", "."), help="Soma de todos os formulários concluídos no período selecionado.")
    with c2:
        st.metric("Não Conformes", f"{nao_conformes:,}".replace(",", "."), help="Quantidade absoluta de desvios encontrados pelas lideranças.")
    with c3:
        st.metric("Taxa de Conformidade", f"{taxa_conformidade:.1f}%", help="Porcentagem de itens avaliados como 'Conforme' em relação ao total de avaliações (Conformes + Não Conformes).")
    with c4:
        st.metric("Tempo Médio", tempo_formatado, help="Tempo médio que a liderança tem levado para preencher a inspeção no aplicativo (Apenas Completas).")

    st.markdown('<hr style="margin-top: 15px; margin-bottom: 20px; border-color: rgba(128, 128, 128, 0.2);">', unsafe_allow_html=True)