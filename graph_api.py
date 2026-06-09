import requests
import streamlit as st
import pandas as pd

CLIENT_ID     = st.secrets["CLIENT_ID"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
FILE_NAME     = "Gestao_Estoque_Reissa_Modas.xlsx"

def get_token():
    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    data = {
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "refresh_token": REFRESH_TOKEN,
        "scope":         "Files.ReadWrite User.Read offline_access"
    }
    resp = requests.post(url, data=data)
    result = resp.json()
    if "access_token" not in result:
        raise Exception(f"Erro de autenticação: {result.get('error_description', result)}")
    return result["access_token"]

def get_headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}

@st.cache_data(ttl=3600)
def get_file_id():
    headers = get_headers()
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/Aplicativo Reissa Modas/{FILE_NAME}:"
    resp = requests.get(url, headers=headers).json()
    if "id" not in resp:
        raise Exception(f"Arquivo não encontrado: {resp}")
    return resp["id"]


# Abas com headers na linha 3 (título + aviso + header)
ABAS_LINHA3 = ["Histórico Preços"]

@st.cache_data(ttl=300)
def ler_aba(nome_aba):
    headers = get_headers()
    url = f"{get_base_url()}/worksheets/{nome_aba}/usedRange"
    data = requests.get(url, headers=headers).json()
    if "values" not in data or len(data["values"]) < 2:
        return pd.DataFrame()
    values = data["values"]
    if nome_aba in ABAS_LINHA3:
        # Header na linha 3 (índice 2), dados a partir da linha 4 (índice 3)
        df = pd.DataFrame(values[3:], columns=values[2])
    else:
        # Header na linha 2 (índice 1), dados a partir da linha 3 (índice 2)
        df = pd.DataFrame(values[2:], columns=values[1])
    return df.dropna(how='all')

@st.cache_data(ttl=300)
def ler_cadastro():         return ler_aba("Cadastro")

@st.cache_data(ttl=300)
def ler_compras():          return ler_aba("Compras")

@st.cache_data(ttl=300)
def ler_inventario():       return ler_aba("Inventário")

@st.cache_data(ttl=300)
def ler_depara():           return ler_aba("De-Para Códigos")

@st.cache_data(ttl=300)
def ler_historico_precos(): return ler_aba("Histórico Preços")

def append_row(nome_aba, valores):
    headers = get_headers()
    url = f"{get_base_url()}/worksheets/{nome_aba}/usedRange"
    data = requests.get(url, headers=headers).json()
    next_row = data.get("rowCount", 2) + 1
    n = len(valores)
    col_end = chr(64 + n) if n <= 26 else f"A{chr(64 + n - 26)}"
    url2 = f"{get_base_url()}/worksheets/{nome_aba}/range(address='A{next_row}:{col_end}{next_row}')"
    resp = requests.patch(url2, headers=headers, json={"values": [valores]})
    if resp.status_code not in [200, 201]:
        raise Exception(f"Erro ao salvar: {resp.text}")
    st.cache_data.clear()

def get_codigo_atual(codigo, df_depara):
    if df_depara.empty: return str(codigo)
    cod = str(codigo)
    visitados = set()
    while cod not in visitados:
        visitados.add(cod)
        mask = df_depara["Código Antigo"].astype(str) == cod
        if mask.any():
            cod = str(df_depara[mask]["Código Atual"].iloc[0])
        else:
            break
    return cod

def get_codigos_vinculados(codigo_atual, df_depara):
    if df_depara.empty: return [str(codigo_atual)]
    codigos = [str(codigo_atual)]
    mask = df_depara["Código Atual"].astype(str) == str(codigo_atual)
    antigos = df_depara[mask]["Código Antigo"].astype(str).tolist()
    return list(set(codigos + antigos))

def calcular_saldo(codigo, tamanho, df_inventario, df_compras):
    cod, tam = str(codigo), str(tamanho)
    inv = df_inventario[
        (df_inventario["Código"].astype(str) == cod) &
        (df_inventario["Tamanho"].astype(str) == tam)
    ]
    if inv.empty:
        comp = df_compras[
            (df_compras["Código"].astype(str) == cod) &
            (df_compras["Tamanho"].astype(str) == tam) &
            (df_compras["Tipo"].astype(str) == "Compra")
        ]
        return int(comp["Quantidade"].sum()) if not comp.empty else 0
    try:
        inv = inv.copy()
        inv["Data_dt"] = pd.to_datetime(inv["Data"], dayfirst=True, errors='coerce')
        ultimo = inv.sort_values("Data_dt").iloc[-1]
        ultima_data = ultimo["Data_dt"]
        qtd_inv = int(float(str(ultimo["Quantidade"] or 0)))
    except:
        return 0
    comp = df_compras[
        (df_compras["Código"].astype(str) == cod) &
        (df_compras["Tamanho"].astype(str) == tam)
    ].copy()
    qtd_comp = 0
    if not comp.empty:
        try:
            comp["Data_dt"] = pd.to_datetime(comp["Data"], dayfirst=True, errors='coerce')
            entradas = comp[(comp["Data_dt"] > ultima_data) & (comp["Tipo"].astype(str) == "Compra")]
            saidas   = comp[(comp["Data_dt"] > ultima_data) & (comp["Tipo"].astype(str) == "Devolução")]
            qtd_comp = int(entradas["Quantidade"].sum()) - int(saidas["Quantidade"].sum())
        except:
            pass
    return qtd_inv + qtd_comp

def get_preco_atual(codigo, grupo_tamanho, df_precos):
    if df_precos.empty: return None, None
    mask = df_precos["Código"].astype(str) == str(codigo)
    if "Grupo Tamanho" in df_precos.columns:
        mask = mask & (df_precos["Grupo Tamanho"].astype(str) == str(grupo_tamanho))
    filtrado = df_precos[mask]
    if filtrado.empty: return None, None
    try:
        filtrado = filtrado.copy()
        filtrado["Data_dt"] = pd.to_datetime(filtrado["Data"], dayfirst=True, errors='coerce')
        ultimo = filtrado.sort_values("Data_dt").iloc[-1]
        return ultimo.get("Preço Venda"), ultimo.get("Preço Compra")
    except:
        return None, None
