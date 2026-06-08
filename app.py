"""
App principal — escolha entre Acesso Equipe e Acesso Gestão
"""
import streamlit as st

st.set_page_config(
    page_title="Reissa Modas — Gestão de Estoque",
    page_icon="👗",
    layout="centered"
)

st.markdown("""
<style>
    .titulo { font-size: 32px; font-weight: bold; color: #1F3864; text-align: center; 
              margin-bottom: 8px; }
    .subtitulo { font-size: 16px; color: #6c757d; text-align: center; margin-bottom: 32px; }
    .btn-grande { font-size: 20px !important; height: 80px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">👗 Reissa Modas</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Sistema de Gestão de Estoque</div>', unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👥 Equipe")
    st.caption("Levantamento de estoque e consultas")
    if st.button("Acessar →", key="btn_equipe", use_container_width=True, type="primary"):
        st.switch_page("pages/equipe.py")

with col2:
    st.markdown("### 📊 Gestão")
    st.caption("Resumo, compras, preços e visões")
    if st.button("Acessar →", key="btn_gestao", use_container_width=True):
        st.switch_page("pages/gestao.py")
