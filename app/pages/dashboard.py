import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go
import warnings
from bcb import sgs
import sys

# Verificar versão do Python
st.sidebar.info(f"Python {sys.version}")

# Suprimir warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Configuração da página com recursos mais recentes
st.set_page_config(
    page_title="Dashboard Econômico Brasil",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/seu-usuario/dashboard-economico',
        'Report a bug': "https://github.com/seu-usuario/dashboard-economico/issues",
        'About': "### Dashboard Econômico Brasil\n\nMonitoramento em tempo real de indicadores econômicos."
    }
)

# Configuração inicial com fuso horário
def get_brasil_time():
    """Retorna o horário atual de Brasília"""
    return datetime.now(timezone.utc).astimezone()

start_date = '1994-07-01'
end_date = (get_brasil_time() + timedelta(days=1)).strftime('%Y-%m-%d')

# Dicionário de indicadores atualizado
indicadores = {
    'Ibovespa': {'codigo': '^BVSP', 'fonte': 'YF', 'unidade': 'Pontos'},
    'PIB Total': {'codigo': 4380, 'fonte': 'BCB', 'unidade': 'R$ milhões'},
    'Taxa Selic': {'codigo': 4189, 'fonte': 'BCB', 'unidade': '% ao ano'},
    'IPCA Mensal': {'codigo': 433, 'fonte': 'BCB', 'unidade': '%'},
    'Câmbio USD/BRL': {'codigo': 3696, 'fonte': 'BCB', 'unidade': 'R$'},
    'Taxa de Desemprego': {'codigo': 24369, 'fonte': 'BCB', 'unidade': '%'},
}

# Cache otimizado para Python 3.12
@st.cache_data(ttl=1800, show_spinner="Carregando dados...")  # 30 minutos
def fetch_yfinance_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Busca dados do Yahoo Finance com tratamento robusto"""
    try:
        data = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
            timeout=15,
            threads=True,
            show_errors=False
        )
        
        if data.empty:
            return pd.DataFrame()
        
        # Python 3.12+: match case para tratamento de colunas
        match ticker:
            case '^BVSP':
                if 'Close' in data.columns:
                    return data[['Close']].rename(columns={'Close': ticker})
            case _:
                if len(data.columns) > 0:
                    return data.iloc[:, :1]  # Pega primeira coluna
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar {ticker}: {str(e)[:100]}...")
        return pd.DataFrame()

# Função principal para baixar dados
@st.cache_data(ttl=1800)
def baixar_dados(indicador_nome: str) -> pd.DataFrame:
    """Baixa dados do indicador selecionado"""
    indicador_info = indicadores.get(indicador_nome)
    
    if not indicador_info:
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

# Interface modernizada
st.title("📊 Painel Econômico")
st.caption(f"Última atualização: {get_brasil_time().strftime('%d/%m/%Y %H:%M')}")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    indicador_selecionado = st.selectbox(
        "**Selecione o indicador:**",
        options=list(indicadores.keys()),
        index=0,
        help="Escolha o indicador econômico para visualização"
    )
    
    # Filtro de período (opcional)
    periodo = st.selectbox(
        "**Período:**",
        options=["Todo o histórico", "Últimos 5 anos", "Último ano", "Últimos 6 meses"],
        index=0
    )
    
    st.divider()
    st.markdown("### 📈 Fontes de Dados")
    st.info("""
    **Yahoo Finance:**
    - Índices B3 (Ibovespa)
   
    
    **Banco Central:**
    - Indicadores macroeconômicos
    - Séries históricas
    """)
    
    st.divider()
    if st.button("🔄 Atualizar dados", type="secondary"):
        st.cache_data.clear()
        st.rerun()

# Layout principal
tab1, tab2, tab3 = st.tabs(["📈 Gráfico", "📊 Tabela", "ℹ️ Informações"])

with tab1:
    dados = baixar_dados(indicador_selecionado)
    
    if not dados.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            valor_atual = dados.iloc[-1, 0]
            st.metric(
                label="Valor Atual",
                value=f"{valor_atual:,.2f}",
                delta=f"{((dados.iloc[-1, 0] / dados.iloc[-2, 0]) - 1) * 100:.2f}%" 
                if len(dados) > 1 else None,
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
        
        # Configurações baseadas no tipo de indicador
        if any(x in indicador_selecionado for x in ['Taxa', 'IPCA', 'Desemprego']):
            fig.add_trace(go.Scatter(
                x=dados.index,
                y=dados[dados.columns[0]],
                name=indicador_selecionado,
                line=dict(width=3, color='#FF6B6B'),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 107, 0.2)',
                mode='lines+markers'
            ))
        else:
            fig.add_trace(go.Scatter(
                x=dados.index,
                y=dados[dados.columns[0]],
                name=indicador_selecionado,
                line=dict(width=2, color='#1E88E5'),
                mode='lines'
            ))
        
        fig.update_layout(
            title={
                'text': f"<b>{indicador_selecionado}</b><br>"
                       f"<span style='font-size:0.8em;color:gray'>"
                       f"{dados.index.min().strftime('%d/%m/%Y')} a {dados.index.max().strftime('%d/%m/%Y')}"
                       f"</span>",
                'x': 0.05,
                'xanchor': 'left'
            },
            xaxis_title="Data",
            yaxis_title=indicadores[indicador_selecionado]['unidade'],
            height=600,
            hovermode="x unified",
            template="plotly_white",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, theme=None)
    else:
        st.warning(f"⚠️ Não foi possível carregar dados para {indicador_selecionado}")
        st.info("Tente selecionar outro indicador ou atualizar a página.")

with tab2:
    if 'dados' in locals() and not dados.empty:
        st.subheader("Dados Tabelados")
        
        # Formatação dos dados
        dados_formatados = dados.copy()
        dados_formatados.index = dados_formatados.index.strftime('%d/%m/%Y')
        dados_formatados.columns = [f"{indicador_selecionado} ({indicadores[indicador_selecionado]['unidade']})"]
        
        st.dataframe(
            dados_formatados.sort_index(ascending=False),
            use_container_width=True,
            height=400
        )
        
        # Estatísticas
        st.subheader("Estatísticas descritivas")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(dados.describe())
        
        with col2:
            st.metric("Observações", len(dados))
            st.metric("Período (dias)", (dados.index.max() - dados.index.min()).days)
        
        # Download
        csv = dados.to_csv()
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{indicador_selecionado.replace(' ', '_').lower()}.csv",
            mime="text/csv",
            type="primary"
        )

with tab3:
    st.subheader(f"Sobre {indicador_selecionado}")
    
    info_text = {
        'Ibovespa': "Principal indicador do desempenho médio das cotações das ações negociadas na B3.",
        'PIB Total': "Produto Interno Bruto - soma de todos os bens e serviços finais produzidos.",
        'Taxa Selic': "Taxa básica de juros da economia brasileira, definida pelo COPOM.",
        'IPCA Mensal': "Índice Nacional de Preços ao Consumidor Amplo - inflação oficial do Brasil.",
        'Câmbio USD/BRL': "Taxa de câmbio dólar americano/real brasileiro.",
        'Taxa de Desemprego': "Porcentagem da população economicamente ativa que está desempregada."
       
    }
    
    st.info(info_text.get(indicador_selecionado, "Informações detalhadas sobre este indicador."))
    
    if not dados.empty:
        st.write(f"**Unidade:** {indicadores[indicador_selecionado]['unidade']}")
        st.write(f"**Fonte:** {indicadores[indicador_selecionado]['fonte']}")
        st.write(f"**Primeira data disponível:** {dados.index.min().strftime('%d/%m/%Y')}")
        st.write(f"**Última atualização:** {dados.index.max().strftime('%d/%m/%Y')}")

# Rodapé
st.divider()
st.caption("""
<div style='text-align: center; color: #666;'>
    <p>Dashboard desenvolvido com Python 3.12 • Streamlit • Yahoo Finance API • BCB API</p>
    <p>Dados atualizados automaticamente • Fonte: Yahoo Finance e Banco Central do Brasil</p>
</div>
""", unsafe_allow_html=True)
