import streamlit as st

VERSAO_ATUAL = "1.1.0"


@st.dialog("✈️ Novidades do Dashboard Donos de Área")
def modal_novidades():
    st.markdown("""
    Confira as melhorias implementadas na versão **v1.1.0**:
    
    * **Visualizador de Evidências Integrado:** Agora você inspeciona fotos em abas deslizantes direto no card, sem precisar abrir abas externas no Google Drive.
    * **Adição do Light Mode:** Agora clicando nos 3 pontinhos no canto superior direito você consegue escolher o tema do app.
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Entendido / Acessar Dashboard", type="primary", use_container_width=True):
        st.session_state["versao_novidades_vista"] = VERSAO_ATUAL
        st.rerun()


def verificar_novidades():
    if st.session_state.get("versao_novidades_vista") != VERSAO_ATUAL:
        modal_novidades()