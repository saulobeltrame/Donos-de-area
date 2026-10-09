import streamlit as st
from PIL import Image
from src.services.data_loader import carregar_dados, carregar_prefixos
from src.components.sidebar import render_sidebar
from src.components.cards import render_cards
from src.components.charts import render_charts
from src.components.changelog import verificar_novidades
import urllib.parse

@st.cache_resource
def get_icone_quadrado(caminho_imagem="assets/icon.png"):
    img = Image.open(caminho_imagem)
    maior_lado = max(img.size)
    img_quadrada = Image.new("RGBA", (maior_lado, maior_lado), (0, 0, 0, 0))
    posicao = ((maior_lado - img.width) // 2, (maior_lado - img.height) // 2)
    img_quadrada.paste(img, posicao)
    return img_quadrada

@st.cache_data
def get_css(caminho="assets/style.css"):
    with open(caminho, encoding="utf-8") as f:
        return f.read()

EMAIL_DESTINO = "saulo.junior@latam.com"
ASSUNTO_EMAIL = "[MRO - Donos de Área] Reporte de Inconsistência / Bug"
CORPO_EMAIL = (
    "Olá,\n\n"
    "Identifiquei uma inconsistência no Dashboard de Donos de Área:\n"
    "- Aeronave / Linha:\n"
    "- Data do apontamento:\n"
    "- Descrição do problema:\n\n"
    "Atenciosamente,"
)

EMAIL_DESTINO = "saulo.junior@latam.com"
ASSUNTO_EMAIL = "[MRO - Donos de Área] Reporte de Inconsistência / Bug"
CORPO_EMAIL = (
    "Olá,\n\n"
    "Identifiquei uma inconsistência no Dashboard de Donos de Área:\n"
    "- Aeronave / Linha: \n"
    "- Data do apontamento: \n"
    "- Descrição do problema: \n\n"
    "Atenciosamente,"
)

params_gmail = urllib.parse.urlencode({
    "view": "cm",
    "fs": "1",
    "to": EMAIL_DESTINO,
    "su": ASSUNTO_EMAIL,
    "body": CORPO_EMAIL
})
LINK_GMAIL = f"https://mail.google.com/mail/?{params_gmail}"

st.set_page_config(
    page_title="LATAM | Donos de Área", 
    page_icon=get_icone_quadrado("assets/icon.png"), 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": LINK_GMAIL,
        "About": """
            ### ✈️ Projeto Donos de Área: Líderes
            **LATAM MRO • São Carlos**
            
            *Acompanhamento contínuo das inspeções de liderança e conformidade operacional.*
            
            ---
            * **Versão:** `1.0.0 (Enterprise)`
            * **Sincronização:** Automática.
        """
    }
)

st.markdown(f"<style>{get_css()}</style>", unsafe_allow_html=True)

st.logo("assets/icon.png", size="medium")

col_logo, col_titulo = st.columns([1, 8])

with col_logo:
    st.image("assets/icon.png", width=85)

with col_titulo:
    st.markdown("""
        <div class="latam-badge">
            <span class="brand-indigo">LATAM</span>
            <span class="brand-coral">MRO</span>
            <span class="brand-dot">•</span>
            <span class="brand-indigo">SÃO CARLOS</span>
        </div>
        <h1 class="latam-title">Projeto Donos de Área: Líderes</h1>
        <p class="latam-subtitle">Acompanhamento contínuo das inspeções da liderança</p>
    """, unsafe_allow_html=True)

URL_FALLBACK = 'https://docs.google.com/spreadsheets/d/1jmxxEX6nQ-fyT47LfvThGpe9rlL8Apu5_yKskUHJSm8/edit?gid=0#gid=0'
url_planilha = st.secrets.get("URL_PLANILHA_MRO", URL_FALLBACK)

df = carregar_dados(url_planilha)
df_prefixos = carregar_prefixos(url_planilha)

if df.empty:
    st.info("ℹ️ Não há registros disponíveis no momento para exibição dos indicadores. Por favor, tente novamente mais tarde.")
    st.stop()

verificar_novidades()
df_filtrado = render_sidebar(df, df_prefixos)
render_cards(df_filtrado)
render_charts(df_filtrado, df_prefixos)