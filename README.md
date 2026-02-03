# Dashboard Econômico Brasil

Dashboard interativo para monitoramento de indicadores econômicos brasileiros.

## 🚀 Deploy no Vercel

### Pré-requisitos
- Conta no [Vercel](https://vercel.com)
- Conta no GitHub/GitLab (opcional)

### Método 1: Deploy via Git
1. Faça fork/clone deste repositório
2. Acesse [vercel.com](https://vercel.com)
3. Clique em "New Project"
4. Importe seu repositório
5. Configure as opções:
   - Framework Preset: Other
   - Build Command: (deixe em branco)
   - Output Directory: (deixe em branco)
   - Install Command: `pip install -r requirements.txt`
6. Clique em "Deploy"

### Método 2: Deploy via CLI
```bash
# Instale a CLI do Vercel
npm i -g vercel

# Faça login
vercel login

# Deploy
vercel