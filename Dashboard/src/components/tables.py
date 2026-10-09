import streamlit as st
import pandas as pd
import time
import re
from streamlit.components.v1 import html as st_html
from src.utils.formatters import normalizar_str

CONFIG_TABELA_DRILLDOWN = {
    "ID": st.column_config.TextColumn("ID da Inspeção", width="medium"),
    "DATA": st.column_config.DatetimeColumn("Data/Hora", format="DD/MM/YYYY - HH:mm"),
    "FOTOS_INFO": st.column_config.TextColumn(
        "Evidências", 
        help="Quantidade de fotos anexadas. Selecione a linha para abrir o painel de fotos.",
        width="small"
    ),
    "TIME_FORMATADO": st.column_config.TextColumn("Tempo Gasto", width="small"),
    "STATUS": st.column_config.TextColumn(
        "Status", 
        help="Conforme ou Não Conforme",
        width="small"
    )
}

def exibir_tabela_drilldown(df_tabela, incluir_slot=False, chave_prefixo="drill"):
    if df_tabela.empty:
        return

    df_drill = df_tabela.copy()
    if 'FOTOS_LISTA' in df_drill.columns:
        def badge_fotos(val):
            if isinstance(val, list) and len(val) > 0:
                return f"📸 {len(val)} foto" if len(val) == 1 else f"📸 {len(val)} fotos"
            return "—"
        df_drill['FOTOS_INFO'] = df_drill['FOTOS_LISTA'].apply(badge_fotos)
    elif 'REGISTRO FOTOS' in df_drill.columns:
        df_drill['FOTOS_INFO'] = df_drill['REGISTRO FOTOS'].apply(
            lambda x: "📸 1 foto" if pd.notna(x) and str(x).strip() not in ['', 'nan', 'None'] else "—"
        )
    else:
        df_drill['FOTOS_INFO'] = "—"

    cols = ['DATA', 'NOME LÍDER', 'ACFT-LINHA']
    if incluir_slot and 'SLOT' in df_drill.columns:
        cols.append('SLOT')
    cols += ['ZONA DE INSP.', 'QUESTÕES', 'STATUS', 'JUSTIFICATIVA', 'TIME_FORMATADO', 'FOTOS_INFO']
    colunas_disp = [c for c in cols if c in df_drill.columns]

    chave_ver = f"ver_tabela_{chave_prefixo}"
    if chave_ver not in st.session_state:
        st.session_state[chave_ver] = 0
    versao_atual = st.session_state[chave_ver]
    chave_df_dinamica = f"df_drill_{chave_prefixo}_{versao_atual}"

    def resetar_filtros_drill():
        st.session_state[f"busca_drill_{chave_prefixo}"] = ""
        st.session_state[f"status_drill_{chave_prefixo}"] = "Todos os Status"
        st.session_state[f"fotos_drill_{chave_prefixo}"] = False
        st.session_state[chave_ver] = st.session_state.get(chave_ver, 0) + 1

    def fechar_painel_detalhes():
        st.session_state[chave_ver] = st.session_state.get(chave_ver, 0) + 1

    tem_busca = bool(st.session_state.get(f"busca_drill_{chave_prefixo}", "").strip())
    tem_status = st.session_state.get(f"status_drill_{chave_prefixo}", "Todos os Status") != "Todos os Status"
    tem_fotos = bool(st.session_state.get(f"fotos_drill_{chave_prefixo}", False))

    estado_tabela = st.session_state.get(chave_df_dinamica)
    tem_selecao = False
    if estado_tabela and isinstance(estado_tabela, dict) and "selection" in estado_tabela:
        sel_info = estado_tabela["selection"]
        tem_selecao = bool(sel_info.get("cells") or sel_info.get("rows"))

    filtros_ativos = tem_busca or tem_status or tem_fotos or tem_selecao

    col_busca, col_status, col_toggle, col_limpar, col_exp = st.columns([3.8, 2.4, 1.6, 1.1, 1.1])
    with col_busca:
        termo_busca = st.text_input(
            "Buscar na tabela",
            placeholder="🔍 Buscar dado (líder, avião, status, data, questão...)",
            help="Pesquise por qualquer palavra-chave visível na tabela.",
            label_visibility="collapsed",
            key=f"busca_drill_{chave_prefixo}"
        )
    with col_status:
        opcoes_status = ["Todos os Status"]
        if 'STATUS' in df_drill.columns:
            opcoes_status += sorted(df_drill['STATUS'].dropna().unique().tolist())
        filtro_status = st.selectbox(
            "Filtrar Status",
            opcoes_status,
            label_visibility="collapsed",
            key=f"status_drill_{chave_prefixo}"
        )
    with col_toggle:
        apenas_fotos = st.checkbox(
            "Apenas fotos",
            value=False,
            key=f"fotos_drill_{chave_prefixo}"
        )
    with col_limpar:
        st.button(
            "↺ Limpar",
            key=f"btn_reset_{chave_prefixo}",
            on_click=resetar_filtros_drill,
            disabled=not filtros_ativos,
            help="Redefinir filtros e fechar o painel de evidências",
            use_container_width=True
        )
    with col_exp:
        csv_data = df_drill[colunas_disp].to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            "📥 CSV",
            data=csv_data,
            file_name=f"inspecoes_latam_mro_{chave_prefixo}.csv",
            mime="text/csv",
            help="Importar registros filtrados em CSV compatível com Excel",
            use_container_width=True
        )

    df_filtrado_tabela = df_drill.copy()

    if termo_busca:
        termo_limpo = termo_busca.replace(' / ', '/').replace(' - ', '-').strip()
        palavras_chave = [normalizar_str(p) for p in termo_limpo.split() if p.strip()]

        if palavras_chave:
            linhas_texto_raw = df_filtrado_tabela[colunas_disp].astype(str).agg(' '.join, axis=1)

            col_data_ref = 'DATA_ORDEM' if 'DATA_ORDEM' in df_filtrado_tabela.columns else ('DATA' if 'DATA' in df_filtrado_tabela.columns else None)
            if col_data_ref:
                s_dt = pd.to_datetime(df_filtrado_tabela[col_data_ref], errors='coerce')
                if not s_dt.isna().all():
                    s_dia = s_dt.dt.day.fillna(0).astype(int).astype(str)
                    s_mes = s_dt.dt.month.fillna(0).astype(int).astype(str)
                    fmt_sem_zero = (s_dia + '/' + s_mes).replace({'0/0': ''})

                    tokens_data = (
                        s_dt.dt.strftime('%d/%m/%Y').fillna('') + ' ' +
                        s_dt.dt.strftime('%d/%m').fillna('') + ' ' +
                        s_dt.dt.strftime('%d-%m-%Y').fillna('') + ' ' +
                        s_dt.dt.strftime('%d-%m').fillna('') + ' ' +
                        fmt_sem_zero + ' ' +
                        s_dt.dt.strftime('%H:%M').fillna('')
                    )
                    linhas_texto_raw = linhas_texto_raw + ' ' + tokens_data

            linhas_normalizadas = (
                linhas_texto_raw.str.normalize('NFKD')
                .str.encode('ascii', errors='ignore')
                .str.decode('utf-8')
                .str.lower()
            )

            mask_global = pd.Series(True, index=df_filtrado_tabela.index)
            for palavra in palavras_chave:
                mask_global &= linhas_normalizadas.str.contains(palavra, na=False, regex=False)

            df_filtrado_tabela = df_filtrado_tabela[mask_global]

    if filtro_status != "Todos os Status" and 'STATUS' in df_filtrado_tabela.columns:
        df_filtrado_tabela = df_filtrado_tabela[df_filtrado_tabela['STATUS'] == filtro_status]

    if apenas_fotos and 'FOTOS_INFO' in df_filtrado_tabela.columns:
        df_filtrado_tabela = df_filtrado_tabela[df_filtrado_tabela['FOTOS_INFO'].str.startswith('📸', na=False)]

    total_orig = len(df_drill)
    total_visivel = len(df_filtrado_tabela)

    st.markdown(
        f"<div style='font-size: 0.80rem; opacity: 0.75; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;'>"
        f"<span>💡 Clique no texto (ex: <b>'8 fotos'</b>) para abrir o painel de evidências.</span>"
        f"<span>Mostrando <b>{total_visivel}</b> de <b>{total_orig}</b> apontamentos</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    if df_filtrado_tabela.empty:
        st.info("Nenhum apontamento encontrado com os critérios de filtro selecionados.")
        return

    evento_tabela = st.dataframe(
        df_filtrado_tabela[colunas_disp],
        use_container_width=True,
        hide_index=True,
        height=320,
        column_config=CONFIG_TABELA_DRILLDOWN,
        on_select="rerun",
        selection_mode="single-cell",
        key=chave_df_dinamica
    )

    idx_linha = None
    if evento_tabela and getattr(evento_tabela, "selection", None):
        sel = evento_tabela.selection
        celulas = sel.get("cells", []) if isinstance(sel, dict) else getattr(sel, "cells", [])
        if celulas:
            primeira_celula = celulas[0]
            idx_linha = primeira_celula[0] if isinstance(primeira_celula, (tuple, list)) else primeira_celula.get("row")
        else:
            linhas = sel.get("rows", []) if isinstance(sel, dict) else getattr(sel, "rows", [])
            if linhas:
                idx_linha = linhas[0]

    if idx_linha is not None and 0 <= idx_linha < len(df_filtrado_tabela):
        row_sel = df_filtrado_tabela.iloc[idx_linha]

        col_espaco, col_fechar = st.columns([8.2, 1.8])
        with col_fechar:
            st.button(
                "✖ Fechar Detalhes",
                key=f"btn_close_panel_{chave_prefixo}_{versao_atual}",
                on_click=fechar_painel_detalhes,
                help="Fechar este painel e desmarcar a linha da tabela",
                use_container_width=True
            )
        
        links_fotos = []
        if 'FOTOS_LISTA' in row_sel and isinstance(row_sel['FOTOS_LISTA'], list):
            links_fotos = row_sel['FOTOS_LISTA']
        elif 'REGISTRO FOTOS' in row_sel and pd.notna(row_sel['REGISTRO FOTOS']):
            val = str(row_sel['REGISTRO FOTOS']).strip()
            if val and val.lower() not in ['nan', 'none', '']:
                links_fotos = [val]

        is_nc = str(row_sel.get('STATUS', '')).strip() == 'Não Conforme'
        cor_destaque = "#ED1651" if is_nc else "#2A0088"
        bg_destaque = "rgba(237, 22, 81, 0.05)" if is_nc else "rgba(42, 0, 136, 0.04)"
        status_tag = "⚠️ NÃO CONFORME" if is_nc else "✅ CONFORME"

        questao = str(row_sel.get('QUESTÕES', 'Item não especificado')).strip()
        zona = str(row_sel.get('ZONA DE INSP.', 'Geral')).strip()
        justificativa = str(row_sel.get('JUSTIFICATIVA', '-')).strip()
        lider = str(row_sel.get('NOME LÍDER', '-')).strip()
        acft = str(row_sel.get('ACFT-LINHA', '-')).strip()

        st.markdown(f"""
            <div id="painel-evidencias-latam" style="background: {bg_destaque}; border-left: 5px solid {cor_destaque}; 
                        border-radius: 8px; padding: 16px 20px; margin-top: 14px; margin-bottom: 12px;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.25);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                    <span style="font-size: 0.82rem; font-weight: 700; color: {cor_destaque}; letter-spacing: 0.5px;">
                        {status_tag} • {zona.upper()}
                    </span>
                    <span style="font-size: 0.8rem; color: inherit; opacity: 0.75;">
                        Aeronave: <b>{acft}</b> | Líder: <b>{lider}</b>
                    </span>
                </div>
                <div style="font-size: 0.96rem; font-weight: 600; color: inherit; opacity: 0.95; margin-bottom: 8px; line-height: 1.4;">
                    {questao}
                </div>
                <div style="font-size: 0.86rem; color: inherit; opacity: 0.82; background: rgba(128,128,128,0.08); padding: 8px 12px; border-radius: 6px;">
                    <b>Justificativa registrada:</b> {justificativa}
                </div>
            </div>
        """, unsafe_allow_html=True)

        if links_fotos:
            total_fotos = len(links_fotos)
            st.markdown(f"**📸 Evidências Fotográficas ({total_fotos} disponíveis):**")

            def resolver_preview_drive(url_original):
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', str(url_original))
                if match:
                    fid = match.group(1)
                    return f"https://drive.google.com/file/d/{fid}/preview"
                match_id = re.search(r'id=([a-zA-Z0-9_-]+)', str(url_original))
                if match_id:
                    fid = match_id.group(1)
                    return f"https://drive.google.com/file/d/{fid}/preview"
                return url_original

            if total_fotos == 1:
                url_unica = links_fotos[0]
                preview_url = resolver_preview_drive(url_unica)
                col_img, col_btn = st.columns([7, 3])
                with col_img:
                    st.markdown(
                        f"""<div style="background: rgba(0,0,0,0.1); border: 1px solid rgba(128,128,128,0.2); 
                                        border-radius: 8px; padding: 4px;">
                                <iframe src="{preview_url}" width="100%" height="420" style="border: none; border-radius: 6px;"></iframe>
                            </div>""",
                        unsafe_allow_html=True
                    )
                with col_btn:
                    st.caption("Evidência anexada ao apontamento.")
                    st.link_button("🔗 Abrir no Drive", url_unica, width="stretch", help="Abrir em nova aba")
            else:
                abas_fotos = st.tabs([f"Foto {i + 1}" for i in range(total_fotos)])
                for i, url_foto in enumerate(links_fotos):
                    with abas_fotos[i]:
                        preview_url = resolver_preview_drive(url_foto)
                        col_img, col_btn = st.columns([7.5, 2.5])
                        with col_img:
                            st.markdown(
                                f"""<div style="background: rgba(0,0,0,0.1); border: 1px solid rgba(128,128,128,0.2); 
                                                border-radius: 8px; padding: 4px; margin-top: 6px;">
                                        <iframe src="{preview_url}" width="100%" height="420" style="border: none; border-radius: 6px;"></iframe>
                                    </div>""",
                                unsafe_allow_html=True
                            )
                        with col_btn:
                            st.markdown(f"**Evidência {i + 1} de {total_fotos}**")
                            st.link_button(f"🔗 Abrir Foto {i + 1} no Drive", url_foto, width="stretch", help="Abrir em tamanho original")
        else:
            st.caption("ℹ️ Nenhuma evidência fotográfica foi anexada a este apontamento.")

        ts_render = time.time()
        st_html(f"""
            <script>
                // Rerun token: {ts_render}
                setTimeout(function() {{
                    try {{
                        var elemento = window.parent.document.getElementById('painel-evidencias-latam');
                        if (elemento) {{
                            elemento.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    }} catch (err) {{
                        console.warn('Auto-scroll LATAM:', err);
                    }}
                }}, 100);
            </script>
        """, height=0)
    else:
        qtd_com_fotos = (df_drill['FOTOS_INFO'].str.startswith('📸')).sum()
        if qtd_com_fotos > 0:
            st.caption(f"Há **{qtd_com_fotos} item(ns)** com fotos anexadas nesta inspeção. Clique na linha correspondente na tabela para inspecionar.")