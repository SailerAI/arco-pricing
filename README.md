# Simulador de Custos de Prospecção 💡

Uma aplicação web interativa desenvolvida com Streamlit para simular custos de prospecção baseados em volumes de leads e taxas de conversão, utilizando uma estrutura de preços escalonada (tiered pricing).

## 📋 Descrição

O Simulador de Custos de Prospecção permite que você:

- Configure diferentes volumes de leads e taxas de conversão
- Visualize custos em cada etapa do funil de vendas (disparos, respostas, qualificações, agendamentos)
- Analise sensibilidade através de gráficos interativos
- Explore diferentes cenários com tabelas de preços configuráveis
- Configure cobrança mínima mensal

## 🚀 Instalação

### Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passos

1. Clone o repositório ou navegue até o diretório do projeto:

```bash
cd arco-pricing
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## 🎯 Como Usar

1. Inicie a aplicação Streamlit:

```bash
streamlit run arco_prices.py
```

2. A aplicação será aberta automaticamente no seu navegador, geralmente em `http://localhost:8501`

3. Use a barra lateral para:
   - Configurar a quantidade de leads a serem processados
   - Ajustar as taxas de conversão (resposta, qualificação, agendamento)
   - Definir o consumo mínimo mensal
   - Editar as tabelas de preços (se habilitado)

4. Visualize os resultados na área principal:
   - Métricas do funil de conversão
   - Composição detalhada dos custos
   - Gráficos de sensibilidade
   - Matriz de sensibilidade (heatmaps)

## ⚙️ Configurações

### Habilitar/Desabilitar Edição de Tabelas de Preços

Por padrão, as tabelas de preços podem ser editadas diretamente na interface. Para desabilitar a edição (modo somente leitura), edite o arquivo `arco_prices.py` e altere a variável:

```python
ENABLE_PRICE_EDITING = False  # Mude para False para desabilitar
```

- `True`: Permite editar as tabelas de preços na interface (padrão)
- `False`: Tabelas de preços ficam somente leitura

### Tabelas de Preços

O simulador utiliza quatro tabelas de preços:

1. **Custo por Envio (Sem Resposta)**: Custo fixo por lead que não respondeu
2. **Custo por Lead (com Resposta)**: Preço escalonado baseado no volume de respostas
3. **Custo por Lead Qualificado**: Preço escalonado baseado no volume de leads qualificados
4. **Custo por Reunião Agendada**: Preço escalonado baseado no volume de reuniões agendadas

Cada tabela (exceto a primeira) utiliza uma estrutura de preços por faixas (tiered pricing), onde o preço varia conforme o volume.

## 📊 Funcionalidades

### Simulação Principal

- Cálculo automático do funil de conversão
- Métricas principais: Respostas, Qualificados, Agendamentos, Custo Total
- Detalhamento da composição de custos
- Suporte para cobrança mínima mensal

### Análise de Sensibilidade

O simulador oferece três tipos de análises gráficas:

1. **Sensibilidade por Taxa de Resposta**: Visualiza o impacto de diferentes taxas de resposta nos custos
2. **Sensibilidade por Taxa de Qualificação**: Analisa o impacto da taxa de qualificação
3. **Sensibilidade por Taxa de Agendamento**: Explora diferentes taxas de agendamento

### Matriz de Sensibilidade

Heatmaps interativos que mostram:
- Custo Total por combinação de taxas
- Custo por Reunião (CPA) por combinação de taxas
- Quantidade de Reuniões Agendadas por combinação de taxas

## 📁 Estrutura do Projeto

```
arco-pricing/
├── arco_prices.py          # Aplicação principal Streamlit
├── requirements.txt        # Dependências do projeto
└── README.md              # Este arquivo
```

## 📦 Dependências

- `streamlit`: Framework web para criar a interface
- `pandas`: Manipulação e análise de dados
- `plotly`: Gráficos interativos
- `numpy`: Operações numéricas (usado indiretamente por pandas e plotly)
- `matplotlib`: Visualizações adicionais (opcional)

## 🔧 Desenvolvimento

### Estrutura do Código

- **Configurações**: Configuração da página e variáveis de controle
- **Funções de Cálculo**: Lógica de cálculo de custos e simulação
- **Interface do Usuário**: Componentes Streamlit (sidebar, métricas, gráficos)
- **Visualizações**: Gráficos Plotly para análise de dados

### Personalização

Para personalizar o simulador:

1. **Cores da marca**: Ajuste as variáveis `BRAND_COLOR`, `LIGHT_BLUE_*`, `GRAY_*` no início do arquivo
2. **Valores padrão**: Modifique os valores default nos widgets da sidebar
3. **Tabelas de preços padrão**: Edite os DataFrames iniciais nas expanders

## 📝 Notas

- Os cálculos utilizam preços escalonados (tiered pricing), onde diferentes volumes pagam preços diferentes
- O consumo mínimo mensal é aplicado apenas se o custo calculado for menor que o valor mínimo
- As referências ao POC no simulador são baseadas em dados reais de teste (716 disparos, 59,4% resposta, 22,6% qualificação, 33,3% agendamento)

## 🤝 Contribuindo

Para contribuir com melhorias:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -am 'Adiciona NovaFeature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.

## 👤 Autor

Desenvolvido para análise de custos de prospecção.

---

**Versão**: 1.0.0  
**Última atualização**: 2024

