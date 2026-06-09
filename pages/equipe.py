"""
App Equipe — Acesso Equipe
"""
import streamlit as st
import pandas as pd
from datetime import date
from graph_api import (
    ler_cadastro, ler_inventario, ler_compras, ler_depara, ler_historico_precos,
    append_row, calcular_saldo, get_codigos_vinculados, get_codigo_atual, get_preco_atual
)

def calcular_saldo_multi(codigos, tamanho, df_inventario, df_compras):
    """Calcula saldo somando todos os códigos vinculados"""
    total = 0
    for cod in codigos:
        total += calcular_saldo(cod, tamanho, df_inventario, df_compras)
    return total


st.set_page_config(page_title="Equipe Reissa Modas", page_icon="👗", layout="centered")

LOGO_B64 = "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"

st.markdown("""
<style>
    .big-code { font-size: 26px !important; font-weight: bold; color: #1F3864; }
    .big-tam  { font-size: 22px !important; font-weight: bold; }
    .card     { background: #f8f9fa; border-radius: 10px; padding: 16px; margin: 8px 0; border: 1px solid #dee2e6; }
    .preco    { font-size: 22px; font-weight: bold; color: #0F6E56; }
    .aviso    { background: #FFF3CD; border-radius: 8px; padding: 12px; border: 1px solid #BA7517; color: #333; }
    .nome-produto { font-size: 16px; color: #333333; font-weight: normal; }
    div[data-testid="stNumberInput"] input { font-size: 22px !important; font-weight: bold; }
    div[data-testid="stTable"] { font-size: 16px !important; }
    .resultado-consulta { background: #EBF3FB; border-radius: 10px; padding: 16px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

TAMANHOS_REG  = [36, 38, 40, 42, 44, 46]
TAMANHOS_PLUS = [48, 50, 52, 54, 56]
TAMANHOS_OVER = [58, 60, 62]

def tamanhos_por_grupo(grupo):
    if grupo == "REG":   return TAMANHOS_REG
    if grupo == "Plus":  return TAMANHOS_PLUS
    if grupo == "Over":  return TAMANHOS_OVER
    return TAMANHOS_REG

def seguir_depara(codigo, df_depara):
    """Segue a cadeia de de-para até o código mais atual"""
    if df_depara.empty: return str(codigo)
    cod = str(int(float(str(codigo)))) if str(codigo).replace('.','').isdigit() else str(codigo)
    visitados = set()
    while cod not in visitados:
        visitados.add(cod)
        mask = df_depara["Código Antigo"].astype(str).str.strip() == cod
        if mask.any():
            novo = str(df_depara[mask]["Código Atual"].iloc[0])
            novo = str(int(float(novo))) if novo.replace('.','').isdigit() else novo
            if novo == cod: break
            cod = novo
        else:
            break
    return cod

if "tela" not in st.session_state:
    st.session_state.tela = "senha"
if "dados_lev" not in st.session_state:
    st.session_state.dados_lev = {}

# ============================================================
# SENHA
# ============================================================
if st.session_state.tela == "senha":
    st.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{LOGO_B64}" width="180"></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password", placeholder="Digite a senha")
    if st.button("Entrar", use_container_width=True, type="primary"):
        senha_correta = st.secrets.get("SENHA_EQUIPE", "time1010")
        if senha == senha_correta:
            st.session_state.tela = "menu"
            st.rerun()
        else:
            st.error("Senha incorreta!")

# ============================================================
# MENU
# ============================================================
elif st.session_state.tela == "menu":
    st.title("👗 Equipe Reissa Modas")
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
# ESTOQUE TÉRREO — P1
# ============================================================
elif st.session_state.tela == "terreo_p1":
    st.title("📦 Estoque Térreo")
    st.progress(0.33, text="Passo 1 de 3")
    with st.form("form_terreo_p1"):
        data_lev = st.date_input("📅 Data", value=date.today())
        sexo     = st.selectbox("Sexo", ["Feminino", "Masculino"])
        grupo    = st.selectbox("Grupo Tamanho", ["REG", "Plus", "Over"])
        tecido   = st.selectbox("Tecido", ["Jeans", "Sarja"])
        tamanho  = st.selectbox("Tamanho", tamanhos_por_grupo(grupo))
        col1, col2 = st.columns(2)
        with col1: voltar  = st.form_submit_button("← Voltar", use_container_width=True)
        with col2: avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
    if voltar:
        st.session_state.tela = "menu"
        st.rerun()
    if avancar:
        st.session_state.dados_lev = {
            "data": data_lev.strftime("%d/%m/%Y"),
            "sexo": sexo, "grupo": grupo, "tecido": tecido,
            "tamanho": str(tamanho), "tipo": "terreo"
        }
        st.session_state.tela = "terreo_p2"
        st.rerun()

# ============================================================
# ESTOQUE TÉRREO — P2
# ============================================================
elif st.session_state.tela == "terreo_p2":
    d = st.session_state.dados_lev
    st.title("📦 Estoque Térreo")
    st.progress(0.66, text="Passo 2 de 3 — Contar calças")
    st.markdown(f"""<div class="card">
        <b>{d['sexo']} · {d['grupo']} · {d['tecido']} · Tam {d['tamanho']}</b><br>
        Data: {d['data']}
    </div>""", unsafe_allow_html=True)

    df_cad    = ler_cadastro()
    df_depara = ler_depara()
    df_inv    = ler_inventario()
    sexo_cod  = "F" if d["sexo"] == "Feminino" else "M"

    # Filtrar cadastro pelo cluster
    if not df_cad.empty:
        df_cad["Código"] = df_cad["Código"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
        mask = (
            (df_cad["Sexo"].astype(str).str.strip() == sexo_cod) &
            (df_cad["Grupo Tamanho"].astype(str).str.strip() == d["grupo"]) &
            (df_cad["Tecido"].astype(str).str.strip() == d["tecido"])
        )
        codigos_cluster = df_cad[mask]["Código"].unique().tolist()
    else:
        codigos_cluster = []

    # Filtrar apenas códigos com saldo atual > 0 nesse tamanho
    if not df_inv.empty and codigos_cluster:
        df_cad["Código"] = df_cad["Código"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
        df_inv["Código"] = df_inv["Código"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
        df_inv["Tamanho"] = df_inv["Tamanho"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
        df_comp2 = ler_compras()
        if not df_comp2.empty:
            df_comp2["Código"] = df_comp2["Código"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
            df_comp2["Tamanho"] = df_comp2["Tamanho"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
        else:
            df_comp2 = pd.DataFrame()

        codigos_filtrados = []
        for cod in codigos_cluster:
            todos_vinculados = get_codigos_vinculados(cod, df_depara)
            saldo = calcular_saldo_multi(todos_vinculados, d["tamanho"], df_inv, df_comp2)
            if saldo > 0:
                codigos_filtrados.append(cod)
    else:
        codigos_filtrados = codigos_cluster

    if not codigos_filtrados:
        st.warning(f"Nenhum código com inventário registrado para Tam {d['tamanho']} nesse cluster.")
        if st.button("← Voltar"):
            st.session_state.tela = "terreo_p1"
            st.rerun()
    else:
        st.markdown(f"**{len(codigos_filtrados)} código(s) encontrado(s)**")
        quantidades = {}
        with st.form("form_terreo_p2"):
            for cod in codigos_filtrados:
                todos_cods = get_codigos_vinculados(cod, df_depara)
                cods_str = " / ".join([str(c) for c in todos_cods])
                nome_row = df_cad[df_cad["Código"] == cod]
                nome = str(nome_row["Nome (auto)"].iloc[0]) if not nome_row.empty and "Nome (auto)" in nome_row.columns else ""
                
                st.markdown(f'<div class="big-code">Cód: {cods_str}</div>', unsafe_allow_html=True)
                if nome:
                    st.markdown(f'<div class="nome-produto">{nome}</div>', unsafe_allow_html=True)
                qtd = st.number_input(f"Quantidade", min_value=0, value=0, step=1, key=f"qtd_{cod}")
                quantidades[cod] = {"qtd": qtd, "nome": nome, "cods": cods_str}
                st.divider()
            col1, col2 = st.columns(2)
            with col1: voltar  = st.form_submit_button("← Voltar", use_container_width=True)
            with col2: avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
        if voltar:
            st.session_state.tela = "terreo_p1"
            st.rerun()
        if avancar:
            st.session_state.dados_lev["quantidades"] = quantidades
            st.session_state.tela = "terreo_p3"
            st.rerun()

# ============================================================
# ESTOQUE TÉRREO — P3
# ============================================================
elif st.session_state.tela == "terreo_p3":
    d = st.session_state.dados_lev
    st.title("📦 Estoque Térreo")
    st.progress(1.0, text="Passo 3 de 3 — Confirmar")
    st.markdown(f"""<div class="card">
        <b>{d['sexo']} · {d['grupo']} · {d['tecido']} · Tam {d['tamanho']}</b><br>
        Data: {d['data']}
    </div>""", unsafe_allow_html=True)
    total = 0
    for cod, info in d["quantidades"].items():
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
                    linha = [d["data"], "Shyros", int(cod), int(d["tamanho"]), info["qtd"], "Térreo"]
                    append_row("Inventário", linha)
                st.session_state.tela = "ok_terreo"
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ============================================================
# ESTOQUE MEZANINO — P1
# ============================================================
elif st.session_state.tela == "mezanino_p1":
    st.title("🏪 Estoque Mezanino")
    st.progress(0.33, text="Passo 1 de 3")
    with st.form("form_mez_p1"):
        data_lev = st.date_input("📅 Data", value=date.today())
        sexo     = st.selectbox("Sexo", ["Feminino", "Masculino"])
        grupo    = st.selectbox("Grupo Tamanho", ["REG", "Plus", "Over"])
        tecido   = st.selectbox("Tecido", ["Jeans", "Sarja"])
        col1, col2 = st.columns(2)
        with col1: voltar  = st.form_submit_button("← Voltar", use_container_width=True)
        with col2: avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
    if voltar:
        st.session_state.tela = "menu"
        st.rerun()
    if avancar:
        st.session_state.dados_lev = {
            "data": data_lev.strftime("%d/%m/%Y"),
            "sexo": sexo, "grupo": grupo, "tecido": tecido
        }
        st.session_state.tela = "mezanino_p2"
        st.rerun()

# ============================================================
# ESTOQUE MEZANINO — P2
# ============================================================
elif st.session_state.tela == "mezanino_p2":
    d = st.session_state.dados_lev
    st.title("🏪 Estoque Mezanino")
    st.progress(0.66, text="Passo 2 de 3 — Selecionar código")
    df_cad    = ler_cadastro()
    df_depara = ler_depara()
    sexo_cod  = "F" if d["sexo"] == "Feminino" else "M"
    if not df_cad.empty:
        df_cad["Código"] = df_cad["Código"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
        mask = (
            (df_cad["Sexo"].astype(str).str.strip() == sexo_cod) &
            (df_cad["Grupo Tamanho"].astype(str).str.strip() == d["grupo"]) &
            (df_cad["Tecido"].astype(str).str.strip() == d["tecido"])
        )
        codigos_df = df_cad[mask][["Código", "Nome (auto)"]].drop_duplicates()
    else:
        codigos_df = pd.DataFrame()

    if codigos_df.empty:
        st.warning("Nenhum código encontrado.")
        if st.button("← Voltar"):
            st.session_state.tela = "mezanino_p1"
            st.rerun()
    else:
        opcoes = [f"{row['Código']} — {row.get('Nome (auto)', '')}" for _, row in codigos_df.iterrows()]
        with st.form("form_mez_p2"):
            selecionado = st.selectbox("Selecione o código:", opcoes)
            col1, col2 = st.columns(2)
            with col1: voltar  = st.form_submit_button("← Voltar", use_container_width=True)
            with col2: avancar = st.form_submit_button("Próximo →", use_container_width=True, type="primary")
        if voltar:
            st.session_state.tela = "mezanino_p1"
            st.rerun()
        if avancar:
            cod  = selecionado.split(" — ")[0]
            nome = selecionado.split(" — ")[1] if " — " in selecionado else ""
            st.session_state.dados_lev["codigo_sel"] = cod
            st.session_state.dados_lev["nome_sel"]   = nome
            st.session_state.tela = "mezanino_p3"
            st.rerun()

# ============================================================
# ESTOQUE MEZANINO — P3
# ============================================================
elif st.session_state.tela == "mezanino_p3":
    d = st.session_state.dados_lev
    st.title("🏪 Estoque Mezanino")
    st.progress(1.0, text="Passo 3 de 3 — Preencher quantidades")
    st.markdown(f"""<div class="card">
        <b>Cód: {d['codigo_sel']}</b> — <span class="nome-produto">{d['nome_sel']}</span><br>
        {d['sexo']} · {d['grupo']} · {d['tecido']} · {d['data']}
    </div>""", unsafe_allow_html=True)
    tams = tamanhos_por_grupo(d["grupo"])
    with st.form("form_mez_p3"):
        quantidades = {}
        cols = st.columns(3)
        for i, tam in enumerate(tams):
            with cols[i % 3]:
                st.markdown(f'<div class="big-tam">Tam {tam}</div>', unsafe_allow_html=True)
                qtd = st.number_input(f"q{tam}", min_value=0, value=0, step=1,
                                      label_visibility="collapsed", key=f"mez_{tam}")
                quantidades[tam] = qtd
        col1, col2 = st.columns(2)
        with col1: voltar    = st.form_submit_button("← Voltar", use_container_width=True)
        with col2: confirmar = st.form_submit_button("✅ Confirmar", use_container_width=True, type="primary")
    if voltar:
        st.session_state.tela = "mezanino_p2"
        st.rerun()
    if confirmar:
        try:
            for tam, qtd in quantidades.items():
                linha = [d["data"], "Shyros", int(d["codigo_sel"]), int(tam), qtd, "Mezanino"]
                append_row("Inventário", linha)
            st.session_state.tela = "ok_mezanino"
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# ============================================================
# CONSULTA ESTOQUE E PREÇO
# ============================================================
elif st.session_state.tela == "consulta":
    st.title("🔍 Consulta Estoque e Preço")
    if st.button("← Voltar ao menu"):
        st.session_state.tela = "menu"
        st.rerun()
    codigo = st.text_input("Código (novo ou antigo):", placeholder="Ex: 38474")
    if codigo:
        with st.spinner("Consultando..."):
            df_cad    = ler_cadastro()
            df_inv    = ler_inventario()
            df_comp   = ler_compras()
            df_depara = ler_depara()
            df_precos = ler_historico_precos()

            # Normalizar códigos
            for df in [df_cad, df_inv, df_comp, df_depara, df_precos]:
                if not df.empty and "Código" in df.columns:
                    df["Código"] = df["Código"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
            if not df_depara.empty:
                for col in ["Código Atual", "Código Antigo"]:
                    if col in df_depara.columns:
                        df_depara[col] = df_depara[col].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))

            cod_atual = seguir_depara(codigo, df_depara)
            linha_cad = df_cad[df_cad["Código"] == cod_atual]

            if linha_cad.empty:
                st.error(f"Código {codigo} não encontrado!")
            else:
                info  = linha_cad.iloc[0]
                nome  = str(info.get("Nome (auto)", "") or "")
                grupo = str(info.get("Grupo Tamanho", "") or "")
                prod  = str(info.get("Produto", "") or "")

                st.markdown(f"""<div class="resultado-consulta">
                    <div class="big-code">Cód: {cod_atual}</div>
                    <div class="nome-produto">{prod} — {nome}</div>
                </div>""", unsafe_allow_html=True)

                # Preço
                pv, _ = get_preco_atual(cod_atual, grupo, df_precos)
                if pv:
                    st.markdown(f'<div class="preco">💰 Preço: R$ {int(float(str(pv)))}</div>', unsafe_allow_html=True)

                # Saldo por tamanho
                st.divider()
                st.subheader("Estoque por tamanho")
                tams = tamanhos_por_grupo(grupo)

                # Normalizar tamanhos
                if not df_inv.empty and "Tamanho" in df_inv.columns:
                    df_inv["Tamanho"] = df_inv["Tamanho"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))
                if not df_comp.empty and "Tamanho" in df_comp.columns:
                    df_comp["Tamanho"] = df_comp["Tamanho"].apply(lambda x: str(int(float(str(x)))) if str(x).replace('.','').isdigit() else str(x))

                # Todos os códigos vinculados (atual + antigos)
                todos_cods_vinculados = get_codigos_vinculados(cod_atual, df_depara)

                sem_tipo = False
                dados_tabela = []
                for tam in tams:
                    # Buscar inventário de TODOS os códigos vinculados
                    inv_tam = df_inv[
                        (df_inv["Código"].isin(todos_cods_vinculados)) &
                        (df_inv["Tamanho"] == str(tam))
                    ] if not df_inv.empty else pd.DataFrame()

                    tipo_col = inv_tam["Tipo"].astype(str).str.strip() if not inv_tam.empty and "Tipo" in inv_tam.columns else pd.Series([])

                    if not inv_tam.empty and tipo_col.str.len().sum() == 0:
                        # Tipo vazio — calcular total apenas
                        saldo = calcular_saldo(cod_atual, tam, df_inv, df_comp)
                        dados_tabela.append({"Tamanho": tam, "Térreo": "—", "Mezanino": "—", "Total": saldo})
                        sem_tipo = True
                    else:
                        inv_t = inv_tam[tipo_col.str.contains("rreo", na=False)] if not inv_tam.empty else pd.DataFrame()
                        inv_m = inv_tam[tipo_col.str.contains("ezanino", na=False)] if not inv_tam.empty else pd.DataFrame()
                        terreo   = calcular_saldo(cod_atual, tam, inv_t, df_comp) if not inv_t.empty else 0
                        mezanino = calcular_saldo(cod_atual, tam, inv_m, df_comp) if not inv_m.empty else 0
                        dados_tabela.append({"Tamanho": tam, "Térreo": terreo, "Mezanino": mezanino, "Total": terreo + mezanino})

                df_tabela = pd.DataFrame(dados_tabela)
                st.dataframe(df_tabela, use_container_width=True, hide_index=True)

                if sem_tipo:
                    st.markdown('<div class="aviso">⚠️ Sem informação de localização (Térreo/Mezanino) para alguns tamanhos</div>', unsafe_allow_html=True)

                total_geral = sum(r["Total"] for r in dados_tabela if isinstance(r["Total"], int))
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
