"""
Módulo de conexão com Microsoft Graph API
Acessa o Excel no OneDrive via autenticação com conta pessoal Microsoft
"""
import requests
import msal
import streamlit as st
import pandas as pd
import json
from io import BytesIO

# ============================================================
# CONFIGURAÇÕES
# ============================================================
CLIENT_ID     = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
TENANT_ID     = "consumers"
AUTHORITY     = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES        = ["Files.ReadWrite", "User.Read"]
FILE_NAME     = "Gestao_Estoque_Reissa_Modas.xlsx"

# ============================================================
# AUTENTICAÇÃO
# ============================================================
def get_token():
    """Obtém token de acesso via Device Code Flow"""
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    # Tenta usar token em cache
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]
    
    # Device code flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("Erro ao iniciar autenticação")
    
    st.warning(f"""
    **Autenticação necessária!**
    
    1. Acesse: **{flow['verification_uri']}**
    2. Digite o código: **{flow['user_code']}**
    3. Aguarde a confirmação...
    """)
    
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Erro de autenticação: {result.get('error_description')}")

def get_headers():
    token = get_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# ============================================================
# LOCALIZAR ARQUIVO NO ONEDRIVE
# ============================================================
@st.cache_data(ttl=3600)
def get_file_id():
    """Busca o ID do arquivo Excel no OneDrive"""
    headers = get_headers()
    url = f"https://graph.microsoft.com/v1.0/me/drive/root/search(q='{FILE_NAME}')"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    
    for item in data.get("value", []):
        if item["name"] == FILE_NAME:
            return item["id"]
    
    raise Exception(f"Arquivo '{FILE_NAME}' não encontrado no OneDrive!")

def get_base_url():
    file_id = get_file_id()
    return f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/workbook"

# ============================================================
# LER ABAS
# ============================================================
@st.cache_data(ttl=300)
def ler_aba(nome_aba):
    """Lê uma aba do Excel e retorna como DataFrame"""
    headers = get_headers()
    url = f"{get_base_url()}/worksheets/{nome_aba}/usedRange"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    
    if "values" not in data:
        return pd.DataFrame()
    
    values = data["values"]
    if len(values) < 2:
        return pd.DataFrame()
    
    # Linha 1 = título, Linha 2 = headers (para abas com título)
    # Detectar automaticamente onde estão os headers
    headers_row = 1  # padrão: segunda linha
    df = pd.DataFrame(values[headers_row+1:], columns=values[headers_row])
    df = df.dropna(how='all')
    return df

@st.cache_data(ttl=300)
def ler_cadastro():
    return ler_aba("Cadastro")

@st.cache_data(ttl=300)
def ler_compras():
    return ler_aba("Compras")

@st.cache_data(ttl=300)
def ler_inventario():
    return ler_aba("Inventário")

@st.cache_data(ttl=300)
def ler_depara():
    return ler_aba("De-Para Códigos")

@st.cache_data(ttl=300)
def ler_historico_precos():
    return ler_aba("Histórico Preços")

# ============================================================
# ESCREVER DADOS
# ============================================================
def append_row(nome_aba, valores):
    """Adiciona uma linha no fim de uma aba"""
    headers = get_headers()
    
    # Pegar última linha usada
    url = f"{get_base_url()}/worksheets/{nome_aba}/usedRange"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    
    if "rowCount" not in data:
        next_row = 3
    else:
        next_row = data["rowCount"] + 1
    
    # Escrever nova linha
    n_cols = len(valores)
    col_end = chr(64 + n_cols) if n_cols <= 26 else f"A{chr(64 + n_cols - 26)}"
    range_addr = f"A{next_row}:{col_end}{next_row}"
    
    url_update = f"{get_base_url()}/worksheets/{nome_aba}/range(address='{range_addr}')"
    body = {"values": [valores]}
    resp = requests.patch(url_update, headers=headers, json=body)
    
    if resp.status_code not in [200, 201]:
        raise Exception(f"Erro ao salvar: {resp.text}")
    
    # Limpar cache
    st.cache_data.clear()
    return True

def update_cell(nome_aba, row, col, valor):
    """Atualiza uma célula específica"""
    headers = get_headers()
    col_letter = chr(64 + col)
    range_addr = f"{col_letter}{row}"
    url = f"{get_base_url()}/worksheets/{nome_aba}/range(address='{range_addr}')"
    body = {"values": [[valor]]}
    resp = requests.patch(url, headers=headers, json=body)
    st.cache_data.clear()
    return resp.status_code == 200

# ============================================================
# LÓGICA DE NEGÓCIO
# ============================================================
def get_codigo_atual(codigo, df_depara):
    """Segue a cadeia de de-para até o código mais atual"""
    if df_depara.empty:
        return str(codigo)
    
    cod = str(codigo)
    visitados = set()
    
    while cod not in visitados:
        visitados.add(cod)
        # Verificar se esse código é um "antigo" na tabela de-para
        mask = df_depara["Código Antigo"].astype(str) == cod
        if mask.any():
            cod = str(df_depara[mask]["Código Atual"].iloc[0])
        else:
            break
    
    return cod

def calcular_saldo(codigo, tamanho, df_inventario, df_compras):
    """
    Saldo atual = último inventário + compras após essa data
    """
    cod = str(codigo)
    tam = str(tamanho)
    
    # Filtrar inventário
    inv = df_inventario[
        (df_inventario["Código"].astype(str) == cod) &
        (df_inventario["Tamanho"].astype(str) == tam)
    ]
    
    if inv.empty:
        # Sem inventário — soma todas as compras
        comp = df_compras[
            (df_compras["Código"].astype(str) == cod) &
            (df_compras["Tamanho"].astype(str) == tam)
        ]
        return int(comp["Quantidade"].sum()) if not comp.empty else 0
    
    # Último inventário
    try:
        inv["Data_dt"] = pd.to_datetime(inv["Data"], dayfirst=True, errors='coerce')
        ultimo_inv = inv.sort_values("Data_dt").iloc[-1]
        ultima_data = ultimo_inv["Data_dt"]
        qtd_inv = int(float(str(ultimo_inv["Quantidade"] or 0)))
    except:
        return 0
    
    # Compras após última data do inventário
    comp = df_compras[
        (df_compras["Código"].astype(str) == cod) &
        (df_compras["Tamanho"].astype(str) == tam)
    ].copy()
    
    if not comp.empty:
        try:
            comp["Data_dt"] = pd.to_datetime(comp["Data"], dayfirst=True, errors='coerce')
            comp_depois = comp[comp["Data_dt"] > ultima_data]
            qtd_comp = int(comp_depois["Quantidade"].sum())
        except:
            qtd_comp = 0
    else:
        qtd_comp = 0
    
    return qtd_inv + qtd_comp

def get_preco_atual(codigo, grupo_tamanho, df_precos):
    """Retorna preço de venda e compra mais recente por código + grupo tamanho"""
    if df_precos.empty:
        return None, None
    
    mask = (df_precos["Código"].astype(str) == str(codigo))
    if "Grupo Tamanho" in df_precos.columns:
        mask = mask & (df_precos["Grupo Tamanho"].astype(str) == str(grupo_tamanho))
    
    filtrado = df_precos[mask]
    if filtrado.empty:
        return None, None
    
    try:
        filtrado = filtrado.copy()
        filtrado["Data_dt"] = pd.to_datetime(filtrado["Data"], dayfirst=True, errors='coerce')
        ultimo = filtrado.sort_values("Data_dt").iloc[-1]
        return ultimo.get("Preço Venda"), ultimo.get("Preço Compra")
    except:
        return None, None

def get_codigos_vinculados(codigo_atual, df_depara):
    """Retorna todos os códigos antigos vinculados a um código atual"""
    if df_depara.empty:
        return [str(codigo_atual)]
    
    codigos = [str(codigo_atual)]
    mask = df_depara["Código Atual"].astype(str) == str(codigo_atual)
    antigos = df_depara[mask]["Código Antigo"].astype(str).tolist()
    codigos.extend(antigos)
    return list(set(codigos))
