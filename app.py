import streamlit as st

st.set_page_config(
    page_title="Reissa Modas — Estoque Equipe",
    page_icon="👗",
    layout="centered"
)

st.markdown("""
<style>
    .titulo { font-size: 32px; font-weight: bold; color: #1F3864; text-align: center; margin-bottom: 8px; }
    .subtitulo { font-size: 16px; color: #6c757d; text-align: center; margin-bottom: 32px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">👗 Reissa Modas</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Sistema de Gestão de Estoque</div>', unsafe_allow_html=True)
st.divider()

if st.button("Entrar →", use_container_width=True, type="primary"):
    st.switch_page("pages/equipe.py")
