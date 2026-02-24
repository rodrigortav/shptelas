import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçador Shopee", page_icon="🟠", layout="centered")

# --- 2. CARREGAR TABELA (USANDO A TABELA SHOPEE) ---
@st.cache_data
def carregar_tabela():
    try:
        # Carrega a tabela (ajuste o nome do arquivo se necessário)
        df = pd.read_excel("tabela_shopee.xlsx", index_col=0)
        df.index = df.index.astype(float)
        df.columns = df.columns.astype(float)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar tabela 'tabela_shopee.xlsx': {e}")
        return pd.DataFrame()

df_precos = carregar_tabela()

# --- 3. FUNÇÕES ---
def saudacao():
    hora = datetime.now().hour
    if 5 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def extrair_medidas_avancado(texto):
    texto = texto.lower()
    texto = re.sub(r'\s+e\s+', '|', texto)
    texto = texto.replace('\n', '|').replace(',', '|')
    
    blocos = texto.split('|')
    itens_encontrados = []
    
    padrao_medida = r'(\d+[.,]?\d*)\s*[xX*]\s*(\d+[.,]?\d*)'
    
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco: continue
        
        match_medida = re.search(padrao_medida, bloco)
        
        if match_medida:
            l_raw, a_raw = match_medida.groups()
            texto_sem_medida = bloco.replace(match_medida.group(0), '')
            match_qtd = re.search(r'\b(\d+)\b', texto_sem_medida)
            
            qtd = 1
            if match_qtd:
                qtd = int(match_qtd.group(1))
            
            l = float(l_raw.replace(',', '.'))
            a = float(a_raw.replace(',', '.'))
            if l > 4: l /= 100
            if a > 4: a /= 100
            
            itens_encontrados.append((qtd, l, a))
            
    return itens_encontrados

def buscar_preco(largura, altura):
    medidas = sorted([largura, altura])
    menor, maior = medidas[0], medidas[1]
    
    if menor > 1.50 or maior > 3.00: return None
    
    try:
        cols_validas = df_precos.columns[df_precos.columns >= menor - 0.001]
        if cols_validas.empty: return None
        col = cols_validas.min()

        lins_validas = df_precos.index[df_precos.index >= maior - 0.001]
        if lins_validas.empty: return None
        lin = lins_validas.min()
        
        return df_precos.loc[lin, col]
    except:
        return None

# --- 4. INTERFACE ---
st.title("🟠 Orçador Shopee")
st.caption("Cole a mensagem do cliente (ex: 'Preciso de 2 telas 60x120')")

pergunta = st.text_area("Mensagem do Cliente:", height=100, label_visibility="collapsed")

if st.button("Gerar Resposta 🚀", type="primary", use_container_width=True):
    if not pergunta:
        st.warning("Cole uma pergunta primeiro!")
    else:
        itens = extrair_medidas_avancado(pergunta)
        
        if not itens:
            st.error("Não entendi as medidas. Tente usar o formato LxH (ex: 60x120).")
        else:
            linhas_orcamento = []
            total_geral = 0
            
            for i, (qtd, l, a) in enumerate(itens):
                preco_unitario = buscar_preco(l, a)
                l_cm, a_cm = int(l*100), int(a*100)
                
                if preco_unitario:
                    preco_total_item = preco_unitario * qtd
                    total_geral += preco_total_item
                    
                    # Removido o "Tela {num}" conforme solicitado
                    if qtd > 1:
                        linhas_orcamento.append(f"• {qtd} x Tela ({l_cm}cm x {a_cm}cm): R$ {preco_total_item:.2f} (R$ {preco_unitario:.2f} cada)")
                    else:
                        linhas_orcamento.append(f"• Tela ({l_cm}cm x {a_cm}cm): R$ {preco_unitario:.2f}")
                else:
                    linhas_orcamento.append(f"• {qtd} x Tela ({l_cm}x{a_cm}): ⚠️ Medida excede o padrão (Máx 1.50x3.00)")

            texto_atencao = """ATENÇÃO:
Nossas telas são produzidas com medidas exatas, então verifique se com a medida que me informou você já considerou a bordinha da janela para fazer a instalação onde o velcro é fixado, caso a medida que me informou seja apenas do vão acrescente 3cm na largura total e 3cm na altura total e me informe novamente. Obrigada"""

            texto_final = (
                f"{saudacao()}, tudo bem?\n\n"
                f"O custo para a produção fica no total de: R$ {total_geral:.2f}\n"
                f"{chr(10).join(linhas_orcamento)}\n\n"
                f"Caso tenha interesse, me informe seu NOME e SOBRENOME que crio a variação no anúncio de personalizadas.\n"
                f"{texto_atencao}"
            )
            
            # Formata para padrão brasileiro (troca ponto por vírgula no visual)
            texto_final_display = texto_final.replace('.', ',')
            
            st.success(f"Orçamento Gerado! Total: R$ {total_geral:.2f}")
            st.markdown("**Copie a resposta abaixo:**")
            st.code(texto_final_display, language=None)
