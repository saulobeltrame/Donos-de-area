import streamlit as st
import pandas as pd

def render_sidebar(df, df_prefixos=None):
    st.sidebar.header("Filtros")

    datas_validas = df['DATA_OBJ'].dropna() if 'DATA_OBJ' in df.columns else pd.Series()
    
    if datas_validas.empty:
        st.sidebar.warning("Nenhum dado temporal disponível para filtragem.")
        return df.copy()

    data_min = datas_validas.min()
    data_max = datas_validas.max()

    intervalo_datas = st.sidebar.date_input(
        "Selecione o Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
        format="DD/MM/YYYY"
    )

    if isinstance(intervalo_datas, (tuple, list)):
        if len(intervalo_datas) == 2:
            data_inicio, data_fim = intervalo_datas
        elif len(intervalo_datas) == 1:
            data_inicio = data_fim = intervalo_datas[0]
        else:
            data_inicio, data_fim = data_min, data_max
    else:
        data_inicio = data_fim = intervalo_datas or data_min

    mask_periodo = (df['DATA_OBJ'] >= data_inicio) & (df['DATA_OBJ'] <= data_fim)
    df_periodo = df[mask_periodo].copy()

    filtros_chaves = {
        'f_linha': 'LINHA',
        'f_turno': 'TURNO',
        'f_aero': 'ACFT-LINHA',
        'f_aval': 'NOME LÍDER'
    }

    for chave in filtros_chaves:
        if chave not in st.session_state:
            st.session_state[chave] = []

    def get_opcoes_dinamicas(coluna_alvo):
        mask = pd.Series(True, index=df_periodo.index)
        for chave, col in filtros_chaves.items():
            if col != coluna_alvo and st.session_state.get(chave):
                mask &= df_periodo[col].isin(st.session_state[chave])
        return sorted(df_periodo.loc[mask, coluna_alvo].dropna().unique().tolist())

    opcoes_linha = get_opcoes_dinamicas('LINHA')
    st.session_state['f_linha'] = [x for x in st.session_state['f_linha'] if x in opcoes_linha]

    opcoes_turno = get_opcoes_dinamicas('TURNO')
    st.session_state['f_turno'] = [x for x in st.session_state['f_turno'] if x in opcoes_turno]

    if df_prefixos is not None and not df_prefixos.empty and 'Prefixos' in df_prefixos.columns:
        prefixos_base = df_prefixos['Prefixos'].dropna().unique().tolist()
        if st.session_state.get('f_linha'):
            linhas_sel = st.session_state['f_linha']
            opcoes_aero = sorted([
                p for p in prefixos_base
                if ':' in p and p.split(':')[1].strip() in linhas_sel
            ])
        else:
            opcoes_aero = sorted(prefixos_base)
    else:
        opcoes_aero = get_opcoes_dinamicas('ACFT-LINHA')

    st.session_state['f_aero'] = [x for x in st.session_state['f_aero'] if x in opcoes_aero]

    opcoes_aval = get_opcoes_dinamicas('NOME LÍDER')
    st.session_state['f_aval'] = [x for x in st.session_state['f_aval'] if x in opcoes_aval]

    linha_selecionada = st.sidebar.multiselect("Selecione a Linha", opcoes_linha, key='f_linha')
    turno_selecionado = st.sidebar.multiselect("Selecione o Turno", opcoes_turno, key='f_turno')
    aeronave_selecionada = st.sidebar.multiselect("Selecione a Aeronave", opcoes_aero, key='f_aero')
    avaliador_selecionado = st.sidebar.multiselect("Selecione o Avaliador", opcoes_aval, key='f_aval')

    mask_final = pd.Series(True, index=df_periodo.index)
    if linha_selecionada:
        mask_final &= df_periodo['LINHA'].isin(linha_selecionada)
    if turno_selecionado:
        mask_final &= df_periodo['TURNO'].isin(turno_selecionado)
    if aeronave_selecionada:
        mask_final &= df_periodo['ACFT-LINHA'].isin(aeronave_selecionada)
    if avaliador_selecionado:
        mask_final &= df_periodo['NOME LÍDER'].isin(avaliador_selecionado)

    return df_periodo[mask_final].copy()