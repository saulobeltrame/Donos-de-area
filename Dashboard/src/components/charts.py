import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.services.business_rules import obter_ids_finalizados
from src.utils.formatters import formatar_tempo
from src.components.tables import exibir_tabela_drilldown

@st.fragment
def fragment_cobertura(df_filtrado, df_prefixos):
    st.markdown("<div id='cobertura'></div><br>", unsafe_allow_html=True)
    st.subheader("Cobertura de Inspeções: Realizado vs Meta")
    st.caption("Meta: Ter no mínimo 1 inspeção para cada aeronave na linha, em cada turno.")

    if df_prefixos is not None and not df_prefixos.empty and 'Prefixos' in df_prefixos.columns:
        if 'LINHA_META' not in df_prefixos.columns:
            df_prefixos['LINHA_META'] = df_prefixos['Prefixos'].astype(str).apply(
                lambda x: str(x).split(':')[1].strip().capitalize() if ':' in str(x) else None
            )
        df_meta = df_prefixos['LINHA_META'].value_counts().reset_index()
        df_meta.columns = ['LINHA', 'Meta']
    else:
        df_meta = pd.DataFrame(columns=['LINHA', 'Meta'])

    ids_validos = obter_ids_finalizados(df_filtrado)
    df_finalizadas = df_filtrado[df_filtrado['ID'].isin(ids_validos)].copy()

    df_finalizadas['PREFIXO_CURTO'] = df_finalizadas['ACFT-LINHA'].apply(
        lambda x: str(x).split(':')[0].strip() if ':' in str(x) else str(x)
    )

    df_realizado = df_finalizadas.groupby(['LINHA', 'TURNO']).agg(
        Realizado=('PREFIXO_CURTO', 'nunique'),
        Lista_Aeronaves=('PREFIXO_CURTO', lambda x: ', '.join(sorted(x.unique())))
    ).reset_index()

    df_grafico = pd.merge(df_realizado, df_meta, on='LINHA', how='left').fillna(0)

    fig = go.Figure()
    cores_turnos = {'1º Turno': '#8B93BC', '2º Turno': '#46508A', '3º Turno': '#10004F'}

    for turno in sorted(df_grafico['TURNO'].unique()):
        df_t = df_grafico[df_grafico['TURNO'] == turno]
        fig.add_trace(go.Bar(
            name=turno,
            x=df_t['LINHA'],
            y=df_t['Realizado'],
            text=df_t['Realizado'],
            textposition='auto',
            customdata=df_t['Lista_Aeronaves'],
            marker_color=cores_turnos.get(turno, '#3B82F6'),
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Turno: %{data.name}<br>Inspecionadas (%{y}):<br><span style='color:#00D2D3'>%{customdata}</span><extra></extra>"
        ))

    df_linha_meta = df_grafico[['LINHA', 'Meta']].drop_duplicates()
    fig.add_trace(go.Scatter(
        name='Meta (Aeronaves Totais)',
        x=df_linha_meta['LINHA'],
        y=df_linha_meta['Meta'],
        mode='markers',
        marker=dict(symbol='line-ew', size=50, color='#E8114B', line=dict(color='#E8114B', width=4)),
        hovertemplate="<b>%{x}</b><br>Meta: %{y}<extra></extra>"
    ))

    fig.update_layout(
        font=dict(family="Montserrat, sans-serif"),
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        margin=dict(l=10, r=20, t=50, b=45),
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.18)', title='Qtd de Aeronaves')
    )
    
    eventos = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_cobertura")

    if eventos and len(eventos.selection.get("points", [])) > 0:
        ponto_clicado = eventos.selection["points"][0]
        indice_trace = ponto_clicado["curve_number"]
        lista_turnos = sorted(df_grafico['TURNO'].unique())
        
        if indice_trace < len(lista_turnos):
            linha_clicada = ponto_clicado["x"]
            turno_clicado = lista_turnos[indice_trace]
            
            st.markdown(f"<br><h4 style='color: #6366F1;'>Inspeções detalhadas: {linha_clicada} | {turno_clicado}</h4>", unsafe_allow_html=True)
            
            df_tabela = df_finalizadas[
                (df_finalizadas['LINHA'] == linha_clicada) & 
                (df_finalizadas['TURNO'] == turno_clicado)
            ].copy()
            
            if 'ID' in df_tabela.columns and 'DATA' in df_tabela.columns:
                df_tabela = df_tabela.sort_values(by=['ID', 'DATA'], ascending=[True, True])
            
            exibir_tabela_drilldown(df_tabela)

@st.fragment
def fragment_zonas(df_filtrado):
    st.markdown("<hr><div id='zonas'></div>", unsafe_allow_html=True)
    col_tit_zona, col_btn_zona = st.columns([3, 1])
    with col_btn_zona:
        modo_zona = st.radio("Exibir:", ["Geral", "Por Slot"], horizontal=True, key="radio_zona")
    with col_tit_zona:
        st.subheader("Desvios por Área de Inspeção (% do Total)")
        st.caption("Distribuição percentual de falhas apontadas para identificar as áreas mais críticas.")

    ids_validos = obter_ids_finalizados(df_filtrado)
    df_nc = df_filtrado[
        df_filtrado['ID'].isin(ids_validos) & 
        (df_filtrado['STATUS'] == 'Não Conforme')
    ].copy()

    if df_nc.empty:
        st.markdown("""
            <div style='background-color: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); border-left: 4px solid #10B981; padding: 16px 20px; border-radius: 8px; margin-top: 10px;'>
                <h4 style='color: #10B981; margin:0; font-weight: 700; letter-spacing: -0.5px;'>✅ Operação Padrão: Zero Desvios!</h4>
                <p style='color: #10004F; margin:5px 0 0 0; font-size: 0.9rem; font-weight: 500; opacity: 0.8;'>Nenhuma não conformidade foi identificada para os filtros e o período selecionados.</p>
            </div>
        """, unsafe_allow_html=True)
        return

    nomes_curtos = {
        'Asa Direita + Fuselagem Direita + Motor': 'Asa Dir. + Fus. + Motor',
        'Asa Esquerda + Fuselagem Esquerda + Motor': 'Asa Esq. + Fus. + Motor',
        'Área de Saída de Materiais (Demarcação Vermelho)': 'Saída Materiais (Vermelho)',
        'Área de Recebimento (Demarcação Verde)': 'Recebimento (Verde)',
        'Equipamento de Alertas/Atividades de Risco': 'Alertas / Ativ. Risco',
        'Trolley Avião Não É Bancada': 'Trolley Não É Bancada',
        'Trolleys Microplanning': 'Trolleys Microplan.',
        'Bancada de Parafusos': 'Bancada Parafusos',
        'Porão dianteiro': 'Porão Dianteiro',
    }

    total_desvios = len(df_nc)

    if modo_zona == "Geral":
        df_zonas = df_nc['ZONA DE INSP.'].value_counts().reset_index()
        df_zonas.columns = ['ZONA DE INSP.', 'Qtd']
        df_zonas['Porcentagem'] = (df_zonas['Qtd'] / total_desvios) * 100
        df_zonas['Texto_Barra'] = df_zonas.apply(lambda r: f" {int(r['Qtd'])} ({r['Porcentagem']:.1f}%)", axis=1)

        zonas_vals = df_zonas['ZONA DE INSP.'].tolist()
        zonas_text = [nomes_curtos.get(z, z) for z in zonas_vals]
        max_pct = df_zonas['Porcentagem'].max() if not df_zonas.empty else 10
        altura_zona = max(480, len(df_zonas) * 28)

        fig_zona = px.bar(
            df_zonas,
            x='Porcentagem',
            y='ZONA DE INSP.',
            orientation='h',
            text='Texto_Barra',
            color_discrete_sequence=['#E8114B']
        )

        fig_zona.update_layout(
            font=dict(family="Montserrat, sans-serif"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=altura_zona,
            yaxis=dict(
                categoryorder='total ascending',
                title='',
                tickmode='array',
                tickvals=zonas_vals,
                ticktext=zonas_text
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.18)',
                title='% sobre os desvios totais',
                ticksuffix="%",
                range=[0, max_pct * 1.25]
            ),
            margin=dict(l=0, r=55, t=10, b=45)
        )

        fig_zona.update_traces(
            textposition='outside',
            marker_line_width=0,
            cliponaxis=False,
            customdata=df_zonas['Qtd'],
            hovertemplate="<b>%{y}</b><br>Desvios: %{customdata}<br>Participação: %{x:.1f}%<extra></extra>"
        )
    else:
        df_nc_zona = df_nc.copy()
        if 'SLOT' in df_nc_zona.columns:
            df_nc_zona['SLOT_FMT'] = df_nc_zona['SLOT'].fillna('Sem Slot').astype(str).str.strip()
            df_nc_zona['SLOT_FMT'] = df_nc_zona['SLOT_FMT'].replace({'': 'Sem Slot', 'nan': 'Sem Slot', 'None': 'Sem Slot'})
        else:
            df_nc_zona['SLOT_FMT'] = 'Geral'

        df_zonas_slot = df_nc_zona.groupby(['ZONA DE INSP.', 'SLOT_FMT']).size().reset_index(name='Qtd')
        df_zonas_slot['Porcentagem'] = (df_zonas_slot['Qtd'] / total_desvios) * 100

        total_por_zona = df_zonas_slot.groupby('ZONA DE INSP.')['Qtd'].transform('sum')
        df_zonas_slot['Pct_Zona'] = (df_zonas_slot['Qtd'] / total_por_zona) * 100

        df_totais = df_zonas_slot.groupby('ZONA DE INSP.').agg(
            Qtd_Total=('Qtd', 'sum'),
            Pct_Total=('Porcentagem', 'sum')
        ).reset_index()
        df_totais['Texto_Total'] = df_totais.apply(lambda r: f" {int(r['Qtd_Total'])} ({r['Pct_Total']:.1f}%)", axis=1)

        slots_ordenados = sorted(df_zonas_slot['SLOT_FMT'].unique().tolist())
        cores_palette = px.colors.qualitative.Dark24
        mapa_cores = {s: cores_palette[i % len(cores_palette)] for i, s in enumerate(slots_ordenados)}

        zonas_vals = df_totais['ZONA DE INSP.'].tolist()
        zonas_text = [nomes_curtos.get(z, z) for z in zonas_vals]
        max_pct = df_totais['Pct_Total'].max() if not df_totais.empty else 10
        altura_zona = max(500, len(df_totais) * 30)

        fig_zona = px.bar(
            df_zonas_slot,
            x='Porcentagem',
            y='ZONA DE INSP.',
            color='SLOT_FMT',
            orientation='h',
            barmode='stack',
            category_orders={'SLOT_FMT': slots_ordenados},
            color_discrete_map=mapa_cores,
            custom_data=['Qtd', 'Pct_Zona']
        )

        fig_zona.add_trace(go.Scatter(
            x=df_totais['Pct_Total'],
            y=df_totais['ZONA DE INSP.'],
            text=df_totais['Texto_Total'],
            mode='text',
            textposition='middle right',
            showlegend=False,
            hoverinfo='skip',
            cliponaxis=False
        ))

        fig_zona.update_layout(
            font=dict(family="Montserrat, sans-serif"),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=altura_zona,
            yaxis=dict(
                categoryorder='total ascending',
                title='',
                tickmode='array',
                tickvals=zonas_vals,
                ticktext=zonas_text
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.18)',
                title='% sobre os desvios totais',
                ticksuffix="%",
                range=[0, max_pct * 1.25]
            ),
            margin=dict(l=0, r=55, t=10, b=45)
        )

        fig_zona.update_traces(
            marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>Slot: %{fullData.name}<br>Desvios no Slot: %{customdata[0]}<br>Participação na Área: %{customdata[1]:.1f}%<br>Impacto Geral: %{x:.1f}%<extra></extra>",
            selector=dict(type='bar')
        )

        legenda_html = "".join([
            f'<span class="slot-badge-item">'
            f'<span class="slot-badge-dot" style="background-color:{cor};"></span>{slot}'
            f'</span>'
            for slot, cor in mapa_cores.items()
        ])
        st.markdown(f'<div class="slot-legend-box">{legenda_html}</div>', unsafe_allow_html=True)

    with st.container(key="zonas_container"):
        eventos_zona = st.plotly_chart(fig_zona, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_zonas")

    if eventos_zona and len(eventos_zona.selection.get("points", [])) > 0:
        zona_clicada = eventos_zona.selection["points"][0]["y"]

        st.markdown(f"<br><h4 style='color: #E8114B;'>Desvios apontados na Área: {zona_clicada}</h4>", unsafe_allow_html=True)

        df_tabela_zona = df_nc[df_nc['ZONA DE INSP.'] == zona_clicada].copy()

        if 'ID' in df_tabela_zona.columns and 'DATA' in df_tabela_zona.columns:
            df_tabela_zona = df_tabela_zona.sort_values(by=['ID', 'DATA'], ascending=[True, True])

        exibir_tabela_drilldown(df_tabela_zona, incluir_slot=True)

@st.fragment
def fragment_slots(df_filtrado):
    if 'SLOT' not in df_filtrado.columns or 'STATUS FORM' not in df_filtrado.columns:
        return

    st.markdown("<br><hr><div id='slots'></div>", unsafe_allow_html=True)
    col_tit_slot, col_btn_slot = st.columns([3, 1])
    with col_btn_slot:
        modo_slot = st.radio("Exibir:", ["Conclusão (%)", "Desvios"], horizontal=True, key="radio_slot")
    with col_tit_slot:
        if modo_slot == "Conclusão (%)":
            st.subheader("Status de Conclusão por Slot (%)")
            st.caption("Distribuição percentual de formulários concluídos, em andamento e não finalizados em cada Slot.")
        else:
            st.subheader("Desvios Apontados por Slot")
            st.caption("Volume e percentual de não conformidades identificadas em cada Slot.")

    if modo_slot == "Conclusão (%)":
        df_slot_base = df_filtrado.drop_duplicates(subset=['ID']).copy()
        df_slot_base = df_slot_base[
            df_slot_base['SLOT'].notna() & 
            (df_slot_base['SLOT'].astype(str).str.strip() != '')
        ]

        if not df_slot_base.empty:
            df_slot_base['STATUS_PADRAO'] = df_slot_base['STATUS FORM'].astype(str).str.strip().str.upper()

            df_resumo_slot = df_slot_base.groupby(['SLOT', 'STATUS_PADRAO'])['ID'].count().reset_index()
            df_resumo_slot.columns = ['SLOT', 'Status', 'Qtd']

            total_slot = df_resumo_slot.groupby('SLOT')['Qtd'].transform('sum')
            df_resumo_slot['Porcentagem'] = (df_resumo_slot['Qtd'] / total_slot) * 100
            df_resumo_slot['Texto'] = df_resumo_slot.apply(lambda r: f"{int(r['Qtd'])} ({r['Porcentagem']:.0f}%)", axis=1)

            cores_status_form = {
                'FINALIZADO': '#10B981',
                'EM ANDAMENTO': '#F59E0B',
                'NÃO FINALIZADO': '#E8114B'
            }

            fig_slot = px.bar(
                df_resumo_slot,
                x='SLOT',
                y='Porcentagem',
                color='Status',
                color_discrete_map=cores_status_form,
                text='Texto',
                barmode='stack'
            )

            fig_slot.update_layout(
                font=dict(family="Montserrat, sans-serif"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(ticksuffix="%", range=[0, 100], showgrid=True, gridcolor='rgba(128,128,128,0.18)', title='% de Inspeções'),
                xaxis=dict(showgrid=False, title='Slot', categoryorder='category ascending'),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, title=""),
                margin=dict(l=10, r=30, t=45, b=50)
            )

            fig_slot.update_traces(
                textposition='inside',
                insidetextanchor='middle',
                marker_line_width=0,
                hovertemplate="<b>Slot: %{x}</b><br>Status: %{data.name}<br>Total: %{text}<extra></extra>"
            )

            eventos_slot = st.plotly_chart(fig_slot, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_slot")

            if eventos_slot and len(eventos_slot.selection.get("points", [])) > 0:
                ponto_clicado = eventos_slot.selection["points"][0]
                indice_trace = ponto_clicado["curve_number"]
                slot_clicado = ponto_clicado["x"]
                status_clicado = fig_slot.data[indice_trace].name

                st.markdown(f"<br><h4 style='color: #6366F1;'>Inspeções no Slot: {slot_clicado} ({status_clicado})</h4>", unsafe_allow_html=True)

                df_tabela_slot = df_filtrado[
                    (df_filtrado['SLOT'] == slot_clicado) & 
                    (df_filtrado['STATUS FORM'].astype(str).str.strip().str.upper() == status_clicado)
                ].copy()

                if 'ID' in df_tabela_slot.columns and 'DATA' in df_tabela_slot.columns:
                    df_tabela_slot = df_tabela_slot.sort_values(by=['ID', 'DATA'], ascending=[True, True])

                exibir_tabela_drilldown(df_tabela_slot)
    else:
        ids_validos = obter_ids_finalizados(df_filtrado)
        df_nc_slot = df_filtrado[
            df_filtrado['ID'].isin(ids_validos) &
            (df_filtrado['STATUS'] == 'Não Conforme') & 
            df_filtrado['SLOT'].notna() & 
            (df_filtrado['SLOT'].astype(str).str.strip() != '')
        ].copy()

        if df_nc_slot.empty:
            st.success("Nenhuma Não Conformidade registrada por Slot no período!")
        else:
            df_desvios_slot = df_nc_slot['SLOT'].value_counts().reset_index()
            df_desvios_slot.columns = ['SLOT', 'Qtd']
            total_desvios_slot = df_desvios_slot['Qtd'].sum()
            df_desvios_slot['Porcentagem'] = (df_desvios_slot['Qtd'] / total_desvios_slot) * 100
            df_desvios_slot['Texto'] = df_desvios_slot.apply(lambda r: f"{int(r['Qtd'])} ({r['Porcentagem']:.1f}%)", axis=1)

            fig_slot_desvios = px.bar(
                df_desvios_slot,
                x='SLOT',
                y='Qtd',
                text='Texto',
                color_discrete_sequence=['#E8114B']
            )

            fig_slot_desvios.update_layout(
                font=dict(family="Montserrat, sans-serif"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.18)', title='Qtd de Desvios'),
                xaxis=dict(showgrid=False, title='Slot', categoryorder='category ascending'),
                margin=dict(l=10, r=30, t=30, b=50)
            )

            fig_slot_desvios.update_traces(
                textposition='outside',
                marker_line_width=0,
                customdata=df_desvios_slot['Porcentagem'],
                hovertemplate="<b>Slot: %{x}</b><br>Desvios: %{y}<br>Participação: %{customdata:.1f}%<extra></extra>"
            )

            eventos_slot_desvios = st.plotly_chart(fig_slot_desvios, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_slot_desvios")

            if eventos_slot_desvios and len(eventos_slot_desvios.selection.get("points", [])) > 0:
                ponto_clicado = eventos_slot_desvios.selection["points"][0]
                slot_clicado = ponto_clicado["x"]

                st.markdown(f"<br><h4 style='color: #E8114B;'>Desvios apontados no Slot: {slot_clicado}</h4>", unsafe_allow_html=True)
                df_tabela_slot = df_nc_slot[df_nc_slot['SLOT'] == slot_clicado].copy()

                if 'ID' in df_tabela_slot.columns and 'DATA' in df_tabela_slot.columns:
                    df_tabela_slot = df_tabela_slot.sort_values(by=['ID', 'DATA'], ascending=[True, True])

                exibir_tabela_drilldown(df_tabela_slot)

@st.fragment
def fragment_aeronaves(df_filtrado):
    st.markdown("<br><hr><div id='aeronaves'></div>", unsafe_allow_html=True)
    st.subheader("Ranking de Desvios por Aeronave")
    st.caption("Aeronaves com maior concentração de não conformidades (Coral indica maior criticidade).")

    ids_validos = obter_ids_finalizados(df_filtrado)
    df_nc_acft = df_filtrado[
        df_filtrado['ID'].isin(ids_validos) & 
        (df_filtrado['STATUS'] == 'Não Conforme')
    ].copy()

    if df_nc_acft.empty:
        st.success("Nenhuma Não Conformidade registrada no período!")
        return

    df_acft = df_nc_acft['ACFT-LINHA'].value_counts().reset_index()
    df_acft.columns = ['ACFT-LINHA', 'Qtd']
    total_desvios_acft = df_acft['Qtd'].sum()

    df_acft['Porcentagem'] = (df_acft['Qtd'] / total_desvios_acft) * 100
    df_acft['Texto'] = df_acft.apply(lambda r: f"{int(r['Qtd'])} ({r['Porcentagem']:.1f}%)", axis=1)

    altura_acft = max(450, len(df_acft) * 28)
    max_acft = df_acft['Qtd'].max() if not df_acft.empty else 10

    fig_acft = px.bar(
        df_acft,
        x='Qtd',
        y='ACFT-LINHA',
        orientation='h',
        text='Texto',
        color='Qtd',
        color_continuous_scale=['#10004F', '#7D0842', '#E8114B']
    )

    fig_acft.update_layout(
        font=dict(family="Montserrat, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=altura_acft,
        coloraxis_showscale=False,
        yaxis={'categoryorder': 'total ascending', 'title': ''},
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(128,128,128,0.18)', 
            title='Qtd de Desvios',
            range=[0, max_acft * 1.16]
        ),
        margin=dict(l=0, r=40, t=20, b=50)
    )

    fig_acft.update_traces(
        textposition='outside',
        marker_line_width=0,
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Total de falhas: %{x}<br>Clique para abrir o detalhamento<extra></extra>"
    )

    eventos_acft = st.plotly_chart(fig_acft, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_acft")

    if eventos_acft and len(eventos_acft.selection.get("points", [])) > 0:
        acft_clicada = eventos_acft.selection["points"][0]["y"]

        st.markdown(f"<br><h4 style='color: #E8114B;'>Desvios apontados na Aeronave: {acft_clicada}</h4>", unsafe_allow_html=True)
        df_tabela_acft = df_nc_acft[df_nc_acft['ACFT-LINHA'] == acft_clicada].copy()

        if 'ID' in df_tabela_acft.columns and 'DATA' in df_tabela_acft.columns:
            df_tabela_acft = df_tabela_acft.sort_values(by=['ID', 'DATA'], ascending=[True, True])

        exibir_tabela_drilldown(df_tabela_acft)

@st.fragment
def fragment_lideres(df_filtrado):
    if 'NOME LÍDER' not in df_filtrado.columns:
        return

    st.markdown("<br><hr><div id='lideres'></div>", unsafe_allow_html=True)
    
    col_tit, col_btn1, col_btn2 = st.columns([2.2, 1.3, 1.5])
    with col_btn1:
        modo_visao = st.radio("Exibir:", ["Top 10", "Todos"], horizontal=True, key="radio_lideres_qtd")
    with col_btn2:
        foco_metrica = st.radio("Analisar:", ["Desvios (Risco)", "Uso de N/A"], horizontal=True, key="radio_lideres_metrica")

    with col_tit:
        if "Desvios" in foco_metrica:
            st.subheader("Desempenho por Líder: Falhas Apontadas")
            st.caption("Volume de não conformidades detectadas.")
        else:
            st.subheader("Desempenho por Líder: Uso do 'Não se Aplica'")
            st.caption("Ranking de líderes que mais utilizam a opção N/A.")

    ids_finalizados = obter_ids_finalizados(df_filtrado)

    df_fin = df_filtrado[
        df_filtrado['ID'].isin(ids_finalizados) & 
        df_filtrado['NOME LÍDER'].notna() & 
        (df_filtrado['NOME LÍDER'].astype(str).str.strip() != '')
    ].copy()

    if df_fin.empty:
        st.info("Nenhuma inspeção finalizada no período selecionado.")
        return

    df_lider_insp = df_fin.groupby('NOME LÍDER')['ID'].nunique().reset_index(name='Qtd_Inspecoes')

    if "Desvios" in foco_metrica:
        df_alvo = df_fin[df_fin['STATUS'] == 'Não Conforme']
        cor_grafico = '#E8114B'  
        nome_metrica = "Desvios"
    else:
        status_na = ['Não se Aplica', 'N/A', 'Não Se Aplica', 'Nao se Aplica']
        df_alvo = df_fin[df_fin['STATUS'].isin(status_na)]
        cor_grafico = '#64748B' 
        nome_metrica = "Itens N/A"

    df_lider_metrica = df_alvo.groupby('NOME LÍDER').size().reset_index(name='Valor_Metrica')

    df_lider = pd.merge(df_lider_insp, df_lider_metrica, on='NOME LÍDER', how='left').fillna(0)
    df_lider['Valor_Metrica'] = df_lider['Valor_Metrica'].astype(int)

    df_lider = df_lider[df_lider['Valor_Metrica'] > 0]

    if df_lider.empty:
        st.success(f"Nenhum registro de **{nome_metrica}** encontrado para os filtros atuais!")
        return

    df_lider = df_lider.sort_values(by=['Valor_Metrica', 'Qtd_Inspecoes'], ascending=[False, False])

    if modo_visao == "Top 10":
        df_lider = df_lider.head(10).copy()
        altura_grafico = 420
    else:
        altura_grafico = max(450, len(df_lider) * 28)

    df_lider = df_lider.sort_values(by=['Valor_Metrica', 'Qtd_Inspecoes'], ascending=[True, True])

    if 'TIME_SEGUNDOS' in df_fin.columns and 'ID' in df_fin.columns:
        tempo_por_id = df_fin.groupby(['NOME LÍDER', 'ID'])['TIME_SEGUNDOS'].max().reset_index()
        
        tempo_valido = tempo_por_id[tempo_por_id['TIME_SEGUNDOS'] > 0]

        medias = tempo_valido.groupby('NOME LÍDER')['TIME_SEGUNDOS'].mean().reset_index()
        
        medias['Tempo_Fmt'] = medias['TIME_SEGUNDOS'].apply(formatar_tempo)
        df_lider = pd.merge(df_lider, medias[['NOME LÍDER', 'Tempo_Fmt']], on='NOME LÍDER', how='left')
        df_lider['Tempo_Fmt'] = df_lider['Tempo_Fmt'].fillna("-")
    else:
        df_lider['Tempo_Fmt'] = "-"

    df_lider['Texto_Barra'] = df_lider.apply(
        lambda r: f"Insp: {r['Qtd_Inspecoes']}  |  {nome_metrica}: {r['Valor_Metrica']}  |  {r['Tempo_Fmt']}", axis=1
    )

    fig_lider = px.bar(
        df_lider,
        x='Valor_Metrica',
        y='NOME LÍDER',
        orientation='h',
        text='Texto_Barra',
        color_discrete_sequence=[cor_grafico]
    )

    max_lider = df_lider['Valor_Metrica'].max() if not df_lider.empty else 10

    fig_lider.update_layout(
        font=dict(family="Montserrat, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=altura_grafico,
        yaxis={'title': ''},
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(128,128,128,0.18)', 
            title=f'Quantidade de {nome_metrica}',
            range=[0, max_lider * 1.45] 
        ),
        margin=dict(l=0, r=40, t=20, b=50)
    )

    fig_lider.update_traces(
        textposition='outside',
        marker_line_width=0,
        cliponaxis=False,
        customdata=df_lider[['Tempo_Fmt', 'Qtd_Inspecoes']],
        hovertemplate="<b>%{y}</b><br>Inspeções Finalizadas: %{customdata[1]}<br>" + nome_metrica + ": %{x}<br>Tempo médio: %{customdata[0]}<extra></extra>"
    )

    eventos_lider = st.plotly_chart(fig_lider, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_lider_dinamico")

    if eventos_lider and len(eventos_lider.selection.get("points", [])) > 0:
        lider_clicado = eventos_lider.selection["points"][0]["y"]

        st.markdown(f"<br><h4 style='color: {cor_grafico};'>Detalhamento do Líder: {lider_clicado} ({nome_metrica})</h4>", unsafe_allow_html=True)
        
        df_tabela_lider = df_alvo[df_alvo['NOME LÍDER'] == lider_clicado].copy()

        if 'ID' in df_tabela_lider.columns and 'DATA' in df_tabela_lider.columns:
            df_tabela_lider = df_tabela_lider.sort_values(by=['ID', 'DATA'], ascending=[True, True])

        exibir_tabela_drilldown(df_tabela_lider)


def render_charts(df_filtrado, df_prefixos):
    if df_filtrado.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("Nenhuma inspeção registrada para os filtros selecionados no período.")
        return

    abas = st.tabs([
        "🎯 Realizado vs Meta", 
        "⚠️ Desvios por Área", 
        "📊 Panorama por Slot", 
        "✈️ Desvios Aeronave", 
        "👤 Desempenho Líder"
    ])

    with abas[0]:
        fragment_cobertura(df_filtrado, df_prefixos)
    with abas[1]:
        fragment_zonas(df_filtrado)
    with abas[2]:
        fragment_slots(df_filtrado)
    with abas[3]:
        fragment_aeronaves(df_filtrado)
    with abas[4]:
        fragment_lideres(df_filtrado)