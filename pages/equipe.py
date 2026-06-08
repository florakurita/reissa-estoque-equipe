"""
App Equipe — Acesso Equipe
Levantamento de estoque (Térreo e Mezanino) + Consulta estoque e preço
"""
import streamlit as st
import pandas as pd
from datetime import date
from graph_api import (
    ler_cadastro, ler_inventario, ler_compras, ler_depara, ler_historico_precos,
    append_row, calcular_saldo, get_codigos_vinculados, get_codigo_atual, get_preco_atual
)

st.set_page_config(page_title="Acesso Equipe", page_icon="👕", layout="centered")

# CSS — fontes grandes para os pais
st.markdown("""
<style>
    .big-code { font-size: 28px !important; font-weight: bold; color: #1F3864; }
    .big-tam  { font-size: 22px !important; font-weight: bold; }
    .card     { background: #f8f9fa; border-radius: 10px; padding: 16px; margin: 8px 0; border: 1px solid #dee2e6; }
    .preco    { font-size: 22px; font-weight: bold; color: #0F6E56; }
    .aviso    { background: #FFF3CD; border-radius: 8px; padding: 12px; border: 1px solid #BA7517; }
    div[data-testid="stNumberInput"] input { font-size: 22px !important; font-weight: bold; }
    .stSelectbox select { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO
# ============================================================
if "tela" not in st.session_state:
    st.session_state.tela = "senha"
if "dados_lev" not in st.session_state:
    st.session_state.dados_lev = {}

TAMANHOS_REG  = [36, 38, 40, 42, 44, 46]
TAMANHOS_PLUS = [48, 50, 52, 54, 56]
TAMANHOS_OVER = [58, 60, 62]
TAMANHOS_BERM = ["P", "M", "G", "GG", "EXG"]

def tamanhos_por_grupo(grupo):
    if grupo == "REG":   return TAMANHOS_REG
    if grupo == "Plus":  return TAMANHOS_PLUS
    if grupo == "Over":  return TAMANHOS_OVER
    return TAMANHOS_REG

# ============================================================
# TELA: SENHA
# ============================================================
if st.session_state.tela == "senha":
    st.title("👕 Acesso Equipe")
    st.subheader("Gestão de Estoque — Reissa Modas")
    st.divider()
    
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True, type="primary"):
        senha_correta = st.secrets.get("SENHA_EQUIPE", "equipe123")
        if senha == senha_correta:
            st.session_state.tela = "menu"
            st.rerun()
        else:
            st.error("Senha incorreta!")

# ============================================================
# TELA: MENU
# ============================================================
elif st.session_state.tela == "menu":
    st.title("👕 Acesso Equipe")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Estoque\nTérreo", use_container_width=True, type="primary"):
            st.session_state.tela = "terreo_p1"
            st.session_state.dados_lev = {}
            st.rerun()
        if st.button("🔍 Consulta\nEstoque e Preço", use_container_width=True):
            st.session_state.tela = "consulta"
            st.rerun()
    with col2:
        if st.button("🏪 Estoque\nMezanino", use_container_width=True, type="primary"):
            st.session_state.tela = "mezanino_p1"
            st.session_state.dados_lev = {}
            st.rerun()

# ============================================================
# TELA: ESTOQUE TÉRREO — PASSO 1 (Requisitos)
# ============================================================
elif st.session_state.tela == "terreo_p1":
    st.title("📦 Estoque Térreo")
    st.progress(0.33, text="Passo 1 de 3 — Identificar prateleira")
    st.divider()
    
    with st.form("form_terreo_p1"):
        data_lev = st.date_input("📅 Data do levantamento", value=date.today())
        sexo      = st.selectbox("Sexo", ["Feminino", "Masculino"])
        grupo     = st.selectbox("Grupo Tamanho", ["REG", "Plus", "Over"])
        tecido    = st.selectbox("Tecido", ["Jeans", "Sarja"])
        tamanho   = st.selectbox("Tamanho", tamanhos_por_grupo(grupo))
        
        col1, col2 = st.columns(2)
        with col1:
            voltar = st.form_submit_button("← Voltar", use_container_width=True)
        with col2:
            avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
    
    if voltar:
        st.session_state.tela = "menu"
        st.rerun()
    
    if avancar:
        # Verificar duplicidade
        df_inv = ler_inventario()
        hoje = str(data_lev.strftime("%d/%m/%Y"))
        
        if not df_inv.empty and "Data" in df_inv.columns:
            mask = (
                (df_inv["Data"].astype(str) == hoje) &
                (df_inv["Tamanho"].astype(str) == str(tamanho))
            )
            if "Sexo" in df_inv.columns:
                mask = mask & (df_inv.get("Sexo", "").astype(str) == sexo[:1])
            if mask.any():
                st.markdown('<div class="aviso">⚠️ Este grupo já foi levantado hoje! Tem certeza que deseja continuar?</div>', 
                           unsafe_allow_html=True)
        
        st.session_state.dados_lev = {
            "data": hoje, "sexo": sexo, "grupo": grupo,
            "tecido": tecido, "tamanho": str(tamanho), "tipo": "terreo"
        }
        st.session_state.tela = "terreo_p2"
        st.rerun()

# ============================================================
# TELA: ESTOQUE TÉRREO — PASSO 2 (Preencher quantidades)
# ============================================================
elif st.session_state.tela == "terreo_p2":
    d = st.session_state.dados_lev
    st.title("📦 Estoque Térreo")
    st.progress(0.66, text="Passo 2 de 3 — Contar calças")
    
    st.markdown(f"""
    <div class="card">
        <b>Levantando:</b> {d['sexo']} · {d['grupo']} · {d['tecido']} · Tamanho {d['tamanho']}<br>
        <b>Data:</b> {d['data']}
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar códigos do cluster + códigos vinculados
    df_cad   = ler_cadastro()
    df_depara = ler_depara()
    
    sexo_cod = "F" if d["sexo"] == "Feminino" else "M"
    
    if not df_cad.empty:
        mask = (
            (df_cad["Sexo"].astype(str) == sexo_cod) &
            (df_cad["Grupo Tamanho"].astype(str) == d["grupo"]) &
            (df_cad["Tecido"].astype(str) == d["tecido"])
        )
        codigos_df = df_cad[mask][["Código", "Nome (auto)", "Produto"]].drop_duplicates()
    else:
        codigos_df = pd.DataFrame()
    
    if codigos_df.empty:
        st.warning("Nenhum código encontrado para esse cluster.")
        if st.button("← Voltar"):
            st.session_state.tela = "terreo_p1"
            st.rerun()
    else:
        st.markdown(f"**{len(codigos_df)} código(s) encontrado(s)** — preencha a quantidade de cada um:")
        
        quantidades = {}
        with st.form("form_terreo_p2"):
            for _, row in codigos_df.iterrows():
                cod_atual = get_codigo_atual(row["Código"], df_depara)
                todos_cods = get_codigos_vinculados(cod_atual, df_depara)
                
                # Mostrar código atual + antigos
                cods_str = " / ".join([str(c) for c in todos_cods])
                nome = str(row.get("Nome (auto)", "") or "")
                
                st.markdown(f'<div class="big-code">Cód: {cods_str}</div>', unsafe_allow_html=True)
                if nome:
                    st.caption(nome)
                
                qtd = st.number_input(
                    f"Quantidade — cód {cod_atual}",
                    min_value=0, value=0, step=1,
                    key=f"qtd_{cod_atual}",
                    label_visibility="collapsed"
                )
                quantidades[cod_atual] = {"qtd": qtd, "nome": nome, "cods": cods_str}
                st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                voltar = st.form_submit_button("← Voltar", use_container_width=True)
            with col2:
                avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
        
        if voltar:
            st.session_state.tela = "terreo_p1"
            st.rerun()
        
        if avancar:
            st.session_state.dados_lev["quantidades"] = quantidades
            st.session_state.tela = "terreo_p3"
            st.rerun()

# ============================================================
# TELA: ESTOQUE TÉRREO — PASSO 3 (Confirmar)
# ============================================================
elif st.session_state.tela == "terreo_p3":
    d = st.session_state.dados_lev
    st.title("📦 Estoque Térreo")
    st.progress(1.0, text="Passo 3 de 3 — Confirmar")
    
    st.markdown(f"""
    <div class="card">
        <b>Levantando:</b> {d['sexo']} · {d['grupo']} · {d['tecido']} · Tamanho {d['tamanho']}<br>
        <b>Data:</b> {d['data']}
    </div>
    """, unsafe_allow_html=True)
    
    total = 0
    for cod, info in d["quantidades"].items():
        if info["qtd"] > 0:
            st.markdown(f"**Cód {info['cods']}** — {info['qtd']} un")
            total += info["qtd"]
    
    st.markdown(f"**Total: {total} unidades**")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Corrigir", use_container_width=True):
            st.session_state.tela = "terreo_p2"
            st.rerun()
    with col2:
        if st.button("✅ Confirmar", use_container_width=True, type="primary"):
            try:
                for cod, info in d["quantidades"].items():
                    linha = [
                        d["data"], "Shyros", cod, d["tamanho"],
                        info["qtd"], "Térreo"
                    ]
                    append_row("Inventário", linha)
                
                st.session_state.tela = "ok_terreo"
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ============================================================
# TELA: ESTOQUE MEZANINO — PASSO 1 (Requisitos)
# ============================================================
elif st.session_state.tela == "mezanino_p1":
    st.title("🏪 Estoque Mezanino")
    st.progress(0.33, text="Passo 1 de 3 — Identificar cluster")
    st.divider()
    
    with st.form("form_mez_p1"):
        data_lev = st.date_input("📅 Data do levantamento", value=date.today())
        sexo     = st.selectbox("Sexo", ["Feminino", "Masculino"])
        grupo    = st.selectbox("Grupo Tamanho", ["REG", "Plus", "Over"])
        tecido   = st.selectbox("Tecido", ["Jeans", "Sarja"])
        
        col1, col2 = st.columns(2)
        with col1:
            voltar = st.form_submit_button("← Voltar", use_container_width=True)
        with col2:
            avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
    
    if voltar:
        st.session_state.tela = "menu"
        st.rerun()
    
    if avancar:
        st.session_state.dados_lev = {
            "data": data_lev.strftime("%d/%m/%Y"),
            "sexo": sexo, "grupo": grupo, "tecido": tecido, "tipo": "mezanino"
        }
        st.session_state.tela = "mezanino_p2"
        st.rerun()

# ============================================================
# TELA: ESTOQUE MEZANINO — PASSO 2 (Selecionar código)
# ============================================================
elif st.session_state.tela == "mezanino_p2":
    d = st.session_state.dados_lev
    st.title("🏪 Estoque Mezanino")
    st.progress(0.66, text="Passo 2 de 3 — Selecionar código")
    
    st.markdown(f"""
    <div class="card">
        <b>Cluster:</b> {d['sexo']} · {d['grupo']} · {d['tecido']}<br>
        <b>Data:</b> {d['data']}
    </div>
    """, unsafe_allow_html=True)
    
    df_cad    = ler_cadastro()
    df_depara = ler_depara()
    
    sexo_cod = "F" if d["sexo"] == "Feminino" else "M"
    
    if not df_cad.empty:
        mask = (
            (df_cad["Sexo"].astype(str) == sexo_cod) &
            (df_cad["Grupo Tamanho"].astype(str) == d["grupo"]) &
            (df_cad["Tecido"].astype(str) == d["tecido"])
        )
        codigos_df = df_cad[mask][["Código", "Nome (auto)"]].drop_duplicates()
    else:
        codigos_df = pd.DataFrame()
    
    if codigos_df.empty:
        st.warning("Nenhum código encontrado para esse cluster.")
        if st.button("← Voltar"):
            st.session_state.tela = "mezanino_p1"
            st.rerun()
    else:
        # Só código atual no mezanino
        opcoes = [f"{row['Código']} — {row.get('Nome (auto)','')}" 
                  for _, row in codigos_df.iterrows()]
        
        with st.form("form_mez_p2"):
            selecionado = st.selectbox("Selecione o código da calça:", opcoes)
            
            col1, col2 = st.columns(2)
            with col1:
                voltar = st.form_submit_button("← Voltar", use_container_width=True)
            with col2:
                avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
        
        if voltar:
            st.session_state.tela = "mezanino_p1"
            st.rerun()
        
        if avancar:
            cod = selecionado.split(" — ")[0]
            nome = selecionado.split(" — ")[1] if " — " in selecionado else ""
            st.session_state.dados_lev["codigo_sel"] = cod
            st.session_state.dados_lev["nome_sel"] = nome
            st.session_state.tela = "mezanino_p3"
            st.rerun()

# ============================================================
# TELA: ESTOQUE MEZANINO — PASSO 3 (Preencher tamanhos)
# ============================================================
elif st.session_state.tela == "mezanino_p3":
    d = st.session_state.dados_lev
    st.title("🏪 Estoque Mezanino")
    st.progress(1.0, text="Passo 3 de 3 — Preencher quantidades")
    
    st.markdown(f"""
    <div class="card">
        <b>Calça:</b> {d['codigo_sel']} — {d['nome_sel']}<br>
        <b>Cluster:</b> {d['sexo']} · {d['grupo']} · {d['tecido']}<br>
        <b>Data:</b> {d['data']}
    </div>
    """, unsafe_allow_html=True)
    
    tams = tamanhos_por_grupo(d["grupo"])
    
    with st.form("form_mez_p3"):
        quantidades = {}
        cols = st.columns(3)
        for i, tam in enumerate(tams):
            with cols[i % 3]:
                st.markdown(f'<div class="big-tam">Tam {tam}</div>', unsafe_allow_html=True)
                qtd = st.number_input(f"qtd_{tam}", min_value=0, value=0, step=1,
                                      label_visibility="collapsed", key=f"mez_{tam}")
                quantidades[tam] = qtd
        
        col1, col2 = st.columns(2)
        with col1:
            voltar = st.form_submit_button("← Voltar", use_container_width=True)
        with col2:
            confirmar = st.form_submit_button("✅ Confirmar", use_container_width=True, type="primary")
    
    if voltar:
        st.session_state.tela = "mezanino_p2"
        st.rerun()
    
    if confirmar:
        try:
            for tam, qtd in quantidades.items():
                if qtd >= 0:
                    linha = [d["data"], "Shyros", d["codigo_sel"], str(tam), qtd, "Mezanino"]
                    append_row("Inventário", linha)
            st.session_state.tela = "ok_mezanino"
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# ============================================================
# TELA: CONSULTA ESTOQUE E PREÇO
# ============================================================
elif st.session_state.tela == "consulta":
    st.title("🔍 Consulta Estoque e Preço")
    st.divider()
    
    if st.button("← Voltar ao menu"):
        st.session_state.tela = "menu"
        st.rerun()
    
    codigo = st.text_input("Digite o código (novo ou antigo):", placeholder="Ex: 38474")
    
    if codigo:
        df_cad    = ler_cadastro()
        df_inv    = ler_inventario()
        df_comp   = ler_compras()
        df_depara = ler_depara()
        df_precos = ler_historico_precos()
        
        # Resolver código atual
        cod_atual = get_codigo_atual(codigo, df_depara)
        
        # Buscar no cadastro
        linha_cad = df_cad[df_cad["Código"].astype(str) == cod_atual]
        
        if linha_cad.empty:
            st.error(f"Código {codigo} não encontrado!")
        else:
            info = linha_cad.iloc[0]
            nome = str(info.get("Nome (auto)", "") or "")
            grupo = str(info.get("Grupo Tamanho", "") or "")
            
            st.markdown(f"""
            <div class="card">
                <div class="big-code">Cód: {cod_atual}</div>
                <div>{nome}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Preço
            preco_venda, preco_compra = get_preco_atual(cod_atual, grupo, df_precos)
            if preco_venda:
                st.markdown(f'<div class="preco">💰 Preço: R$ {int(preco_venda)}</div>', 
                           unsafe_allow_html=True)
            
            # Saldo por tamanho
            st.divider()
            st.subheader("Estoque por tamanho")
            
            tams = tamanhos_por_grupo(grupo)
            
            col_headers = st.columns(4)
            col_headers[0].markdown("**Tamanho**")
            col_headers[1].markdown("**Térreo**")
            col_headers[2].markdown("**Mezanino**")
            col_headers[3].markdown("**Total**")
            
            total_geral = 0
            for tam in tams:
                # Filtrar por local
                inv_tam = df_inv[
                    (df_inv["Código"].astype(str) == cod_atual) &
                    (df_inv["Tamanho"].astype(str) == str(tam))
                ]
                
                terreo = 0
                mezanino = 0
                
                if not inv_tam.empty:
                    if "Tipo" in inv_tam.columns:
                        inv_t = inv_tam[inv_tam["Tipo"].astype(str).str.contains("rreo", na=False)]
                        inv_m = inv_tam[inv_tam["Tipo"].astype(str).str.contains("ezanino", na=False)]
                        
                        if not inv_t.empty:
                            terreo = calcular_saldo(cod_atual, tam, inv_t, df_comp)
                        if not inv_m.empty:
                            mezanino = calcular_saldo(cod_atual, tam, inv_m, df_comp)
                    else:
                        saldo = calcular_saldo(cod_atual, tam, inv_tam, df_comp)
                        terreo = saldo
                
                total = terreo + mezanino
                total_geral += total
                
                cols = st.columns(4)
                cols[0].markdown(f'<div class="big-tam">{tam}</div>', unsafe_allow_html=True)
                cols[1].write(terreo)
                cols[2].write(mezanino)
                cols[3].write(f"**{total}**")
            
            st.divider()
            st.markdown(f"**Total geral: {total_geral} unidades**")

# ============================================================
# TELAS DE SUCESSO
# ============================================================
elif st.session_state.tela == "ok_terreo":
    st.title("✅ Levantamento registrado!")
    st.success("Estoque Térreo salvo com sucesso!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Novo levantamento", use_container_width=True):
            st.session_state.tela = "terreo_p1"
            st.session_state.dados_lev = {}
            st.rerun()
    with col2:
        if st.button("Menu principal", use_container_width=True, type="primary"):
            st.session_state.tela = "menu"
            st.rerun()

elif st.session_state.tela == "ok_mezanino":
    st.title("✅ Levantamento registrado!")
    st.success("Estoque Mezanino salvo com sucesso!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Novo levantamento", use_container_width=True):
            st.session_state.tela = "mezanino_p1"
            st.session_state.dados_lev = {}
            st.rerun()
    with col2:
        if st.button("Menu principal", use_container_width=True, type="primary"):
            st.session_state.tela = "menu"
            st.rerun()
