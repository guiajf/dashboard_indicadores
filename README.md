# Painel de indicadores econômicos

Dashboard interativo para monitoramento de indicadores econômicos brasileiros.

## 🚀 Deploy no Streamlit Cloud

### Pré-requisitos
- Conta no [Streamlit](https://streamlit.io/)
- Conta no GitHub/GitLab (opcional)

### Método 1: Deploy via Git
1. Acesse [Streamlit](share.streamlit.io)
2. Faça login com sua conta do GitHub
3. Clique: "Create app"
4. Clique: "Create a public app from GitHub"
5. Selecione:
   - Repo: seu-repositorio-github
   - Branch: main
   - Main file path: caminho-do-arquivo-no-repositório
6. Clique em "Deploy"


### ATENÇÃO

Verifique se o arquivo *requirements.txt* está na raiz do repositório.

### Método 2: Deploy via CLI
```bash
# Instale a CLI do Streamlit
pip install streamlit
streamlit config show  # Verifica configurações

# Tenta deploy direto
streamlit run arquivo.py --server.port=8501
```

### Formas de Compartilhar:

1. **Link direto**: https://seu-app.streamlit.app
2. **QR Code**: Gerar para acesso mobile
3. **Embed**: Em blogs/sites (se necessário)

   
### Monitoramento:
**No Streamlit Cloud Dashboard:**
* **Metrics**: Visualizações, tempo de sessão
* **Errors**: Logs de erros em tempo real
* **Settings**: Recursos, variáveis de ambiente

### Para Acessar Logs:
1. No **Streamlit Cloud**: Seu app → ⋯ (menu) → View app logs
2. Ou via **URL**: https://seu-app.streamlit.app/_logs
   
### Atualizações Futuras:
Quando fizer mudanças no GitHub:

1. Commit e push para o branch main
2. **Streamlit Cloud** detecta automaticamente
3. Faz *redeploy* instatâneo
