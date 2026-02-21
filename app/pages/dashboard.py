import streamlit as st
import os
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

# Configuração da página
st.set_page_config(
    page_title="Painel de indicadores econômicos",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go
import warnings
import sys
import pytz

try:
    from bcb import sgs
except ImportError:
    # Fallback para versões antigas
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bcb==1.1.0"])
    from bcb import sgs

# Verificar versão do Python
st.sidebar.info(f"Python {sys.version}")

# Suprimir warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def main():

    # Configuração inicial com fuso horário
    def get_brasil_time():
        """Retorna o horário atual de Brasília (America/Sao_Paulo)"""
        try:
            # Método mais robusto com pytz
            brasil_tz = pytz.timezone('America/Sao_Paulo')
            return datetime.now(brasil_tz)
        except:
            # Fallback para UTC-3
            return datetime.now(timezone.utc) - timedelta(hours=3)
    
    start_date = '1994-07-01'
    end_date = (get_brasil_time() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Dicionário de indicadores
    indicadores = {
        'Ibovespa': {'codigo': '^BVSP', 'fonte': 'YF', 'unidade': 'Pontos'},
        'PIB Total': {'codigo': 4380, 'fonte': 'BCB', 'unidade': 'R$ milhões'},
        'Taxa Selic': {'codigo': 4189, 'fonte': 'BCB', 'unidade': '% ao ano'},
        'IPCA Mensal': {'codigo': 433, 'fonte': 'BCB', 'unidade': '%'},
        'Câmbio USD/BRL': {'codigo': 3696, 'fonte': 'BCB', 'unidade': 'R$'},
        'Taxa de Desemprego': {'codigo': 24369, 'fonte': 'BCB', 'unidade': '%'},
    }
    
    # Cache otimizado
    @st.cache_data(ttl=3600, show_spinner="Carregando dados...")
    def fetch_yfinance_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Busca dados do Yahoo Finance com tratamento robusto"""
        try:
            # PARA yfinance 1.1.0 - parâmetros corretos
            data = yf.download(
                tickers=ticker,
                start=start_date,
                end=end_date,
                auto_adjust=True,
                progress=False,
                timeout=30,
                threads=True
                # NÃO USAR: show_errors (não existe na 1.1.0)
            )
            
            if data.empty:
                st.warning(f"⚠️ Nenhum dado encontrado para {ticker}")
                return pd.DataFrame()
            
            # Verifica se temos a coluna Close
            if 'Close' in data.columns:
                df_result = data[['Close']].copy()
                df_result.columns = [ticker]
                return df_result
            elif len(data.columns) > 0:
                # Pega primeira coluna disponível
                df_result = data.iloc[:, [0]].copy()
                df_result.columns = [ticker]
                return df_result
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar {ticker}: {str(e)}")
            return pd.DataFrame()
    
    # Função principal para baixar dados
    @st.cache_data(ttl=1800)
    def baixar_dados(indicador_nome: str) -> pd.DataFrame:
        """Baixa dados do indicador selecionado"""
        indicador_info = indicadores.get(indicador_nome)
        
        if not indicador_info:
            st.error(f"Indicador {indicador_nome} não encontrado")
            return pd.DataFrame()
        
        try:
            if indicador_info['fonte'] == 'YF':
                return fetch_yfinance_data(indicador_info['codigo'], start_date, end_date)
            else:
                # BCB data
                df = sgs.get(
                    {indicador_nome: indicador_info['codigo']},
                    start=start_date,
                    end=end_date
                )
                return df
        except Exception as e:
            st.error(f"Erro ao processar {indicador_nome}: {e}")
            return pd.DataFrame()
    
    # Interface
    st.title("📊 Painel de indicadores econômicos")
    st.caption(f"Última atualização: {get_brasil_time().strftime('%d/%m/%Y %H:%M')} (Horário de Brasília)")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        indicador_selecionado = st.selectbox(
            "**Selecione o indicador:**",
            options=list(indicadores.keys()),
            index=0
        )
        
        st.divider()
        
        # Botão de atualização corrigido
        if st.button("🔄 Atualizar dados", type="secondary", use_container_width=True):
            # Limpa cache específico
            fetch_yfinance_data.clear()
            baixar_dados.clear()
            st.rerun()
        
        st.divider()
        st.markdown("### 📈 Fontes de dados")
        st.info("""
        - **Yahoo Finance:** Índices B3 (Ibovespa)
        - **Banco Central:** Indicadores macroeconômicos
        """)
    
    # Layout principal
    tab1, tab2, tab3 = st.tabs(["📈 Gráfico", "📊 Tabela", "ℹ️ Informações"])
    
    with tab1:
        with st.spinner("Carregando dados..."):
            dados = baixar_dados(indicador_selecionado)
        
        if not dados.empty and len(dados) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                valor_atual = dados.iloc[-1, 0]
                delta = None
                if len(dados) > 1:
                    try:
                        delta = ((dados.iloc[-1, 0] / dados.iloc[-2, 0]) - 1) * 100
                    except:
                        delta = None
                
                st.metric(
                    label="Valor Atual",
                    value=f"{valor_atual:,.2f}",
                    delta=f"{delta:.2f}%" if delta is not None else None,
                    delta_color="normal"
                )
            
            with col2:
                st.metric("Mínimo", f"{dados.min().iloc[0]:,.2f}")
            
            with col3:
                st.metric("Máximo", f"{dados.max().iloc[0]:,.2f}")
            
            with col4:
                st.metric("Média", f"{dados.mean().iloc[0]:,.2f}")
            
            # Gráfico
            fig = go.Figure()
            
            # Escolhe cor baseada no tipo de indicador
            if any(x in indicador_selecionado for x in ['Taxa', 'IPCA', 'Desemprego']):
                cor = '#FF6B6B'
                fill = 'tozeroy'
            else:
                cor = '#1E88E5'
                fill = None
            
            fig.add_trace(go.Scatter(
                x=dados.index,
                y=dados[dados.columns[0]],
                name=indicador_selecionado,
                line=dict(width=2, color=cor),
                fill=fill,
                mode='lines'
            ))
            
            fig.update_layout(
                title=f"{indicador_selecionado} ({dados.index.min().strftime('%d/%m/%Y')} a {dados.index.max().strftime('%d/%m/%Y')})",
                xaxis_title="Data",
                yaxis_title=indicadores[indicador_selecionado]['unidade'],
                height=500,
                hovermode="x unified",
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"⚠️ Não foi possível carregar dados para {indicador_selecionado}")
            st.info("Verifique sua conexão com a internet ou tente outro indicador.")
    
    with tab2:
        if 'dados' in locals() and not dados.empty:
            st.subheader("Dados Tabelados")
            
            # Formatação
            dados_display = dados.copy()
            dados_display.index = dados_display.index.strftime('%d/%m/%Y')
            dados_display.columns = [f"{indicador_selecionado}"]
            
            st.dataframe(
                dados_display.sort_index(ascending=False),
                use_container_width=True,
                height=400
            )
            
            # Download
            csv = dados.to_csv()
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{indicador_selecionado.replace(' ', '_').lower()}.csv",
                mime="text/csv"
            )
    
    with tab3:
        st.subheader(f"Informações sobre {indicador_selecionado}")
        
        descricoes = {
            'Ibovespa': "Principal indicador do desempenho médio das cotações das ações negociadas na B3.",
            'PIB Total': "Produto Interno Bruto - soma de todos os bens e serviços finais produzidos.",
            'Taxa Selic': "Taxa básica de juros da economia brasileira, definida pelo COPOM.",
            'IPCA Mensal': "Índice Nacional de Preços ao Consumidor Amplo - inflação oficial do Brasil.",
            'Câmbio USD/BRL': "Taxa de câmbio dólar americano/real brasileiro.",
            'Taxa de Desemprego': "Porcentagem da população economicamente ativa que está desempregada."
        }
        
        st.info(descricoes.get(indicador_selecionado, "Indicador econômico."))
        
        if not dados.empty:
            st.write(f"**Unidade:** {indicadores[indicador_selecionado]['unidade']}")
            st.write(f"**Fonte:** {indicadores[indicador_selecionado]['fonte']}")
            st.write(f"**Período disponível:** {dados.index.min().strftime('%d/%m/%Y')} a {dados.index.max().strftime('%d/%m/%Y')}")
            st.write(f"**Total de observações:** {len(dados)}")
    
    # Rodapé
    st.divider()
    st.caption("Dashboard desenvolvido com Python • Streamlit • Dados: Yahoo Finance e Banco Central do Brasil")

if __name__ == "__main__":
    main()
