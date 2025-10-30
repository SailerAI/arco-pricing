import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configurações da Página ---
st.set_page_config(
    page_title="Simulador de Custos de Prospecção", page_icon="💡", layout="wide"
)

# --- Configuração de Edição de Tabelas de Preços ---
# Altere para False para desabilitar a edição das tabelas de preços
ENABLE_PRICE_EDITING = True

# --- Funções de Cálculo ---


def calculate_tiered_cost(quantity, tiers_df):
    """
    Calcula o custo total com base em uma tabela de preços escalonada (por faixas).
    A tabela deve ter as colunas 'Mínimo', 'Máximo', 'Valor'.
    """
    if quantity == 0:
        return 0

    # Garante que os tipos de dados estão corretos
    tiers_df["Mínimo"] = tiers_df["Mínimo"].astype(float)
    tiers_df["Máximo"] = tiers_df["Máximo"].astype(float)
    tiers_df["Valor"] = tiers_df["Valor"].astype(float)

    tiers_df = tiers_df.sort_values(by="Mínimo").reset_index(drop=True)

    total_cost = 0

    for _, row in tiers_df.iterrows():
        min_val, max_val, price = row["Mínimo"], row["Máximo"], row["Valor"]

        if quantity > min_val:
            # Calcula a quantidade dentro desta faixa
            items_in_tier = min(quantity, max_val) - min_val
            cost_in_tier = items_in_tier * price
            total_cost += cost_in_tier

    return total_cost


def run_simulation(total_leads, rates, pricing_tables, minimum_billing=0.0):
    """
    Executa uma simulação completa para um dado cenário.
    """
    # 1. Calcular a quantidade de eventos em cada etapa do funil
    num_replies = total_leads * rates["response"]
    num_no_replies = total_leads - num_replies
    num_qualified = num_replies * rates["qualification"]
    num_booked = num_qualified * rates["booking"]

    # 2. Calcular o custo de cada componente
    # Custo base: leads que não responderam
    cost_no_reply = num_no_replies * pricing_tables["no_reply"].iloc[0]["Valor"]

    # Custo dos leads que responderam (substitui o custo de R$0,20)
    cost_replies = calculate_tiered_cost(num_replies, pricing_tables["leads"])

    # Custos adicionais para eventos de sucesso
    cost_qualified = calculate_tiered_cost(num_qualified, pricing_tables["qualified"])
    cost_booked = calculate_tiered_cost(num_booked, pricing_tables["booked"])

    # 3. Calcular o custo total e métricas
    calculated_cost = cost_no_reply + cost_replies + cost_qualified + cost_booked

    # Aplicar consumo mínimo
    total_cost = max(calculated_cost, minimum_billing)

    cpl = total_cost / total_leads if total_leads > 0 else 0
    cpa = total_cost / num_booked if num_booked > 0 else 0

    return {
        "total_leads": total_leads,
        "num_no_replies": num_no_replies,
        "num_replies": num_replies,
        "num_qualified": num_qualified,
        "num_booked": num_booked,
        "cost_no_reply": cost_no_reply,
        "cost_replies": cost_replies,
        "cost_qualified": cost_qualified,
        "cost_booked": cost_booked,
        "calculated_cost": calculated_cost,
        "total_cost": total_cost,
        "cpl": cpl,
        "cpa": cpa,
    }


# --- Paleta de Cores ---
BRAND_COLOR = "#39B5FF"  # Cor principal da marca
LIGHT_BLUE_1 = "#A8DAFF"  # Azul claro 1
LIGHT_BLUE_2 = "#70C7FF"  # Azul claro 2
LIGHT_BLUE_3 = "#D4EDFF"  # Azul muito claro
GRAY_1 = "#9E9E9E"  # Cinza médio
GRAY_2 = "#BDBDBD"  # Cinza claro
GRAY_3 = "#E0E0E0"  # Cinza muito claro
GRAY_4 = "#424242"  # Cinza escuro

# --- Interface do Usuário (UI) ---

st.title("Simulador de Custos de Prospecção")
st.markdown(
    "Use esta ferramenta para simular custos mensais com base no volume de leads e taxas de conversão, de acordo com a estrutura de preços escalonada."
)

# --- Barra Lateral de Configurações ---
st.sidebar.image("LOGO-COR.png", width=200)
st.sidebar.header("⚙️ Configure a Simulação")

st.sidebar.info(
    "**📊 Dados do POC:**\n\n"
    "• 716 disparos\n"
    "• 425 respostas (59,4%)\n"
    "• 96 qualificados (22,6%)\n"
    "• 32 agendamentos (33,3%)"
)

st.sidebar.subheader("🎯 Cenário de Simulação")

target_total_leads = st.sidebar.slider(
    "Quantidade de Leads a serem processados",
    min_value=0,
    max_value=3500,
    value=2500,
    step=100,
)

# Colunas para organizar as taxas de conversão
col1, col2 = st.sidebar.columns(2)
target_response_rate = (
    col1.slider(
        "Taxa de Resposta (%)",
        min_value=0.0,
        max_value=100.0,
        value=15.0,
        step=0.5,
        format="%.1f%%",
        help="POC alcançou 59,4%",
    )
    / 100.0
)

target_qualification_rate = (
    col2.slider(
        "Taxa de Qualificação (% de Respostas)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=0.5,
        format="%.1f%%",
        help="POC alcançou 22,6%",
    )
    / 100.0
)

target_booking_rate = (
    st.sidebar.slider(
        "Taxa de Agendamento (% de Qualificados)",
        min_value=0.0,
        max_value=100.0,
        value=33.0,
        step=0.5,
        format="%.1f%%",
        help="POC alcançou 33,3%",
    )
    / 100.0
)

# Consumo mínimo mensal
st.sidebar.subheader("💳 Cobrança Mínima")
minimum_billing = st.sidebar.number_input(
    "Consumo Mínimo Mensal (R$)",
    min_value=0.0,
    max_value=50000.0,
    value=0.0,
    step=100.0,
    help="Se o custo total for menor que este valor, você pagará o mínimo configurado",
)

# --- Tabelas de Preços Configuráveis ---
st.sidebar.subheader("💰 Tabelas de Preços")

with st.sidebar.expander("Tabela de Custo por Envio (Sem Resposta)"):
    df_no_reply = pd.DataFrame([{"Valor": 0.20}])
    # Este não precisa ser editado, mas mantemos a estrutura
    st.dataframe(df_no_reply, hide_index=True)


with st.sidebar.expander("Tabela de Custo por Lead (com Resposta)"):
    df_leads = pd.DataFrame(
        [
            {"Mínimo": 0, "Máximo": 500, "Valor": 5.00},
            {"Mínimo": 500, "Máximo": 1500, "Valor": 3.80},
            {"Mínimo": 1500, "Máximo": 2000, "Valor": 3.00},
            {"Mínimo": 2000, "Máximo": 3000, "Valor": 2.40},
            {
                "Mínimo": 3000,
                "Máximo": 99999,
                "Valor": 2.00,
            },  # Máximo alto para pegar todos os excedentes
        ]
    )
    if ENABLE_PRICE_EDITING:
        edited_df_leads = st.data_editor(df_leads, key="leads_editor", num_rows="dynamic")
    else:
        st.dataframe(df_leads, hide_index=True)
        edited_df_leads = df_leads

with st.sidebar.expander("Tabela de Custo por Lead Qualificado"):
    df_qualified = pd.DataFrame(
        [
            {"Mínimo": 0, "Máximo": 50, "Valor": 20.00},
            {"Mínimo": 50, "Máximo": 100, "Valor": 15.00},
            {"Mínimo": 100, "Máximo": 150, "Valor": 10.00},
            {"Mínimo": 150, "Máximo": 99999, "Valor": 5.00},
        ]
    )
    if ENABLE_PRICE_EDITING:
        edited_df_qualified = st.data_editor(
            df_qualified, key="qualified_editor", num_rows="dynamic"
        )
    else:
        st.dataframe(df_qualified, hide_index=True)
        edited_df_qualified = df_qualified

with st.sidebar.expander("Tabela de Custo por Reunião Agendada"):
    df_booked = pd.DataFrame(
        [
            {"Mínimo": 0, "Máximo": 20, "Valor": 100.00},
            {"Mínimo": 20, "Máximo": 50, "Valor": 80.00},
            {"Mínimo": 50, "Máximo": 100, "Valor": 60.00},
            {"Mínimo": 100, "Máximo": 99999, "Valor": 50.00},
        ]
    )
    if ENABLE_PRICE_EDITING:
        edited_df_booked = st.data_editor(
            df_booked, key="booked_editor", num_rows="dynamic"
        )
    else:
        st.dataframe(df_booked, hide_index=True)
        edited_df_booked = df_booked


# --- Coleta dos dados para a simulação ---
rates = {
    "response": target_response_rate,
    "qualification": target_qualification_rate,
    "booking": target_booking_rate,
}
pricing_tables = {
    "no_reply": df_no_reply,
    "leads": edited_df_leads,
    "qualified": edited_df_qualified,
    "booked": edited_df_booked,
}

# --- Execução e Exibição dos Resultados ---
if target_total_leads > 0:
    # Simulação para o cenário target
    target_results = run_simulation(
        target_total_leads, rates, pricing_tables, minimum_billing
    )

    st.header("📊 Resultados da Simulação")
    st.markdown(
        f"Análise para **{target_total_leads:,} disparos** processados com as taxas de conversão configuradas."
    )

    # Verificar se o consumo mínimo foi aplicado
    calculated_cost = target_results["calculated_cost"]
    final_cost = target_results["total_cost"]
    has_minimum_charge = final_cost > calculated_cost

    # Funil de conversão - Métricas principais
    funnel_col1, funnel_col2, funnel_col3, funnel_col4 = st.columns(4)

    with funnel_col1:
        st.metric(
            label="📨 Respostas",
            value=f"{int(target_results['num_replies']):,}",
            delta=f"{target_response_rate * 100:.1f}% dos disparos",
        )

    with funnel_col2:
        st.metric(
            label="✅ Leads Qualificados",
            value=f"{int(target_results['num_qualified']):,}",
            delta=f"{target_qualification_rate * 100:.1f}% das respostas",
        )

    with funnel_col3:
        st.metric(
            label="🤝 Reuniões Agendadas",
            value=f"{int(target_results['num_booked']):,}",
            delta=f"{target_booking_rate * 100:.1f}% dos qualificados",
        )

    with funnel_col4:
        if has_minimum_charge:
            st.metric(
                label="💵 Custo a Pagar",
                value=f"R$ {final_cost:,.2f}",
                delta="Consumo mínimo aplicado",
                delta_color="off",
            )
            st.caption(f"💡 Custo calculado: R$ {calculated_cost:,.2f}")
        else:
            st.metric(
                label="💵 Custo Total",
                value=f"R$ {final_cost:,.2f}",
                delta=None,
            )

    # Separador visual
    st.divider()

    # Detalhamento dos custos
    st.subheader("💰 Composição do Custo")
    cost_data = {
        "Componente": [
            "Sem Resposta",
            "Leads (com Resposta)",
            "Leads Qualificados",
            "Reuniões Agendadas",
        ],
        "Quantidade": [
            int(target_results["num_no_replies"]),
            int(target_results["num_replies"]),
            int(target_results["num_qualified"]),
            int(target_results["num_booked"]),
        ],
        "Custo (R$)": [
            target_results["cost_no_reply"],
            target_results["cost_replies"],
            target_results["cost_qualified"],
            target_results["cost_booked"],
        ],
    }

    # Adicionar linha de consumo mínimo se aplicável
    if has_minimum_charge:
        cost_data["Componente"].append("Ajuste Consumo Mínimo")
        cost_data["Quantidade"].append("-")
        cost_data["Custo (R$)"].append(final_cost - calculated_cost)

    cost_df = pd.DataFrame(cost_data)
    cost_df["% do Total"] = (cost_df["Custo (R$)"] / final_cost * 100).fillna(0)

    # Formatação para exibição
    formatted_cost_df = cost_df.style.format(
        {"Custo (R$)": "R$ {:,.2f}", "% do Total": "{:.1f}%"}
    )

    col_detail, col_pie = st.columns([0.6, 0.4])
    with col_detail:
        st.dataframe(formatted_cost_df, use_container_width=True)

    with col_pie:
        # Cores do gráfico de pizza (incluindo cor para consumo mínimo se aplicável)
        pie_colors = [GRAY_3, LIGHT_BLUE_3, LIGHT_BLUE_2, BRAND_COLOR]
        if has_minimum_charge:
            pie_colors.append(GRAY_1)  # Cor para ajuste de consumo mínimo

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=cost_df["Componente"],
                    values=cost_df["Custo (R$)"],
                    hole=0.3,
                    textinfo="label+percent",
                    marker_colors=pie_colors,
                )
            ]
        )
        fig_pie.update_layout(
            title_text="Distribuição do Custo Total",
            margin=dict(t=40, b=10, l=10, r=10),
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Separador visual
    st.divider()

    # --- Gráficos de Simulação e Variação ---
    st.header("📈 Análise de Sensibilidade por Volume")
    st.markdown(
        "Explore como diferentes taxas de conversão impactam os custos em diversos volumes de leads (0 a 3.500)."
    )

    # Criar abas para os três gráficos de volume
    tab_resp, tab_qual, tab_book = st.tabs(
        ["Taxa de Resposta", "Taxa de Qualificação", "Taxa de Agendamento"]
    )

    # Gráfico 1: Custo Total vs. Quantidade de Leads (Variando Taxa de Resposta)
    with tab_resp:
        lead_volumes = list(range(0, 3501, 100))

        # Variações de taxa de resposta baseadas no target
        response_step = 0.10  # 10 pontos percentuais
        response_rate_variations = {}

        # Duas abaixo do target
        if target_response_rate - 2 * response_step >= 0:
            response_rate_variations[
                f"-20pp ({(target_response_rate - 2 * response_step) * 100:.1f}%)"
            ] = target_response_rate - 2 * response_step
        if target_response_rate - response_step >= 0:
            response_rate_variations[
                f"-10pp ({(target_response_rate - response_step) * 100:.1f}%)"
            ] = target_response_rate - response_step

        # Target
        response_rate_variations[f"Target ({target_response_rate * 100:.1f}%)"] = (
            target_response_rate
        )

        # Duas acima do target
        if target_response_rate + response_step <= 1.0:
            response_rate_variations[
                f"+10pp ({(target_response_rate + response_step) * 100:.1f}%)"
            ] = target_response_rate + response_step
        if target_response_rate + 2 * response_step <= 1.0:
            response_rate_variations[
                f"+20pp ({(target_response_rate + 2 * response_step) * 100:.1f}%)"
            ] = target_response_rate + 2 * response_step

        fig_volume_response = go.Figure()

        # Define colors for each scenario
        scenario_colors = {
            0: GRAY_2,  # -10pp
            1: GRAY_1,  # -5pp
            2: BRAND_COLOR,  # Target
            3: LIGHT_BLUE_2,  # +5pp
            4: LIGHT_BLUE_1,  # +10pp
        }

        for idx, (scenario_name, response_rate) in enumerate(
            response_rate_variations.items()
        ):
            costs = []
            scenario_rates = rates.copy()
            scenario_rates["response"] = response_rate
            for volume in lead_volumes:
                sim_result = run_simulation(
                    volume, scenario_rates, pricing_tables, minimum_billing
                )
                costs.append(sim_result["total_cost"])

            is_target = "Target" in scenario_name
            fig_volume_response.add_trace(
                go.Scatter(
                    x=lead_volumes,
                    y=costs,
                    mode="lines",
                    name=scenario_name,
                    line=dict(
                        width=4 if is_target else 2.5,
                        dash="solid" if is_target else "dot",
                        color=scenario_colors.get(idx, BRAND_COLOR),
                    ),
                )
            )

        # Adicionar ponto do cenário target
        fig_volume_response.add_trace(
            go.Scatter(
                x=[target_total_leads],
                y=[target_results["total_cost"]],
                mode="markers",
                marker=dict(size=12, color="red", symbol="star"),
                name="Seu Cenário Atual",
            )
        )

        fig_volume_response.update_layout(
            xaxis_title="Quantidade de Leads Processados",
            yaxis_title="Custo Total (R$)",
            legend_title="Taxa de Resposta",
            hovermode="x unified",
        )
        st.plotly_chart(fig_volume_response, use_container_width=True)

    # Gráfico 2: Custo Total vs. Quantidade de Leads (Variando Taxa de Qualificação)
    with tab_qual:
        # Variações de taxa de qualificação baseadas no target
        qualification_step = 0.10  # 10 pontos percentuais
        qualification_rate_variations = {}

        # Duas abaixo do target
        if target_qualification_rate - 2 * qualification_step >= 0:
            qualification_rate_variations[
                f"-20pp ({(target_qualification_rate - 2 * qualification_step) * 100:.1f}%)"
            ] = target_qualification_rate - 2 * qualification_step
        if target_qualification_rate - qualification_step >= 0:
            qualification_rate_variations[
                f"-10pp ({(target_qualification_rate - qualification_step) * 100:.1f}%)"
            ] = target_qualification_rate - qualification_step

        # Target
        qualification_rate_variations[
            f"Target ({target_qualification_rate * 100:.1f}%)"
        ] = target_qualification_rate

        # Duas acima do target
        if target_qualification_rate + qualification_step <= 1.0:
            qualification_rate_variations[
                f"+10pp ({(target_qualification_rate + qualification_step) * 100:.1f}%)"
            ] = target_qualification_rate + qualification_step
        if target_qualification_rate + 2 * qualification_step <= 1.0:
            qualification_rate_variations[
                f"+20pp ({(target_qualification_rate + 2 * qualification_step) * 100:.1f}%)"
            ] = target_qualification_rate + 2 * qualification_step

        fig_volume_qualification = go.Figure()

        # Define colors for each scenario
        scenario_colors_qual = {
            0: GRAY_2,  # -20pp
            1: GRAY_1,  # -10pp
            2: BRAND_COLOR,  # Target
            3: LIGHT_BLUE_2,  # +10pp
            4: LIGHT_BLUE_1,  # +20pp
        }

        for idx, (scenario_name, qual_rate) in enumerate(
            qualification_rate_variations.items()
        ):
            costs = []
            scenario_rates = rates.copy()
            scenario_rates["qualification"] = qual_rate
            for volume in lead_volumes:
                sim_result = run_simulation(
                    volume, scenario_rates, pricing_tables, minimum_billing
                )
                costs.append(sim_result["total_cost"])

            is_target = "Target" in scenario_name
            fig_volume_qualification.add_trace(
                go.Scatter(
                    x=lead_volumes,
                    y=costs,
                    mode="lines",
                    name=scenario_name,
                    line=dict(
                        width=4 if is_target else 2.5,
                        dash="solid" if is_target else "dot",
                        color=scenario_colors_qual.get(idx, BRAND_COLOR),
                    ),
                )
            )

        # Adicionar ponto do cenário target
        fig_volume_qualification.add_trace(
            go.Scatter(
                x=[target_total_leads],
                y=[target_results["total_cost"]],
                mode="markers",
                marker=dict(size=12, color="red", symbol="star"),
                name="Seu Cenário Atual",
            )
        )

        fig_volume_qualification.update_layout(
            xaxis_title="Quantidade de Leads Processados",
            yaxis_title="Custo Total (R$)",
            legend_title="Taxa de Qualificação",
            hovermode="x unified",
        )
        st.plotly_chart(fig_volume_qualification, use_container_width=True)

    # Gráfico 3: Custo Total vs. Quantidade de Leads (Variando Taxa de Agendamento)
    with tab_book:
        # Variações de taxa de agendamento baseadas no target
        booking_step = 0.15  # 15 pontos percentuais
        booking_rate_variations = {}

        # Duas abaixo do target
        if target_booking_rate - 2 * booking_step >= 0:
            booking_rate_variations[
                f"-30pp ({(target_booking_rate - 2 * booking_step) * 100:.1f}%)"
            ] = target_booking_rate - 2 * booking_step
        if target_booking_rate - booking_step >= 0:
            booking_rate_variations[
                f"-15pp ({(target_booking_rate - booking_step) * 100:.1f}%)"
            ] = target_booking_rate - booking_step

        # Target
        booking_rate_variations[f"Target ({target_booking_rate * 100:.1f}%)"] = (
            target_booking_rate
        )

        # Duas acima do target
        if target_booking_rate + booking_step <= 1.0:
            booking_rate_variations[
                f"+15pp ({(target_booking_rate + booking_step) * 100:.1f}%)"
            ] = target_booking_rate + booking_step
        if target_booking_rate + 2 * booking_step <= 1.0:
            booking_rate_variations[
                f"+30pp ({(target_booking_rate + 2 * booking_step) * 100:.1f}%)"
            ] = target_booking_rate + 2 * booking_step

        fig_volume_booking = go.Figure()

        # Define colors for each scenario
        scenario_colors_booking = {
            0: GRAY_2,  # -30pp
            1: GRAY_1,  # -15pp
            2: BRAND_COLOR,  # Target
            3: LIGHT_BLUE_2,  # +15pp
            4: LIGHT_BLUE_1,  # +30pp
        }

        for idx, (scenario_name, book_rate) in enumerate(
            booking_rate_variations.items()
        ):
            costs = []
            scenario_rates = rates.copy()
            scenario_rates["booking"] = book_rate
            for volume in lead_volumes:
                sim_result = run_simulation(
                    volume, scenario_rates, pricing_tables, minimum_billing
                )
                costs.append(sim_result["total_cost"])

            is_target = "Target" in scenario_name
            fig_volume_booking.add_trace(
                go.Scatter(
                    x=lead_volumes,
                    y=costs,
                    mode="lines",
                    name=scenario_name,
                    line=dict(
                        width=4 if is_target else 2.5,
                        dash="solid" if is_target else "dot",
                        color=scenario_colors_booking.get(idx, BRAND_COLOR),
                    ),
                )
            )

        # Adicionar ponto do cenário target
        fig_volume_booking.add_trace(
            go.Scatter(
                x=[target_total_leads],
                y=[target_results["total_cost"]],
                mode="markers",
                marker=dict(size=12, color="red", symbol="star"),
                name="Seu Cenário Atual",
            )
        )

        fig_volume_booking.update_layout(
            xaxis_title="Quantidade de Leads Processados",
            yaxis_title="Custo Total (R$)",
            legend_title="Taxa de Agendamento",
            hovermode="x unified",
        )
        st.plotly_chart(fig_volume_booking, use_container_width=True)

    # Separador visual
    st.divider()

    # Heatmap de Taxa de Qualificação vs Taxa de Agendamento
    st.header("🔥 Matriz de Sensibilidade: Qualificação vs Agendamento")
    st.markdown(
        """
        Visualize como diferentes combinações de taxas de qualificação e agendamento impactam o custo total.
        
        **📊 Referência POC:** Em um teste real, foram alcançados: **22,6% de qualificação** e **33,3% de agendamento**.  
        Os limites abaixo refletem cenários realistas baseados nesta performance.
        """
    )

    # Criar ranges para o heatmap (baseado em dados reais de POC)
    # POC: Qualificação 22.6%, Agendamento 33.3%
    qual_rates_heatmap = [i / 100.0 for i in range(0, 36, 5)]  # De 0% a 35%, passo 5%
    booking_rates_heatmap = [
        i / 100.0 for i in range(0, 51, 5)
    ]  # De 0% a 50%, passo 5%

    # Matriz para armazenar os custos
    cost_matrix = []
    cpa_matrix = []
    meetings_matrix = []

    for qual_rate in qual_rates_heatmap:
        cost_row = []
        cpa_row = []
        meetings_row = []
        for book_rate in booking_rates_heatmap:
            temp_rates = rates.copy()
            temp_rates["qualification"] = qual_rate
            temp_rates["booking"] = book_rate
            sim_result = run_simulation(
                target_total_leads, temp_rates, pricing_tables, minimum_billing
            )
            cost_row.append(sim_result["total_cost"])
            cpa_row.append(sim_result["cpa"] if sim_result["cpa"] > 0 else 0)
            meetings_row.append(sim_result["num_booked"])
        cost_matrix.append(cost_row)
        cpa_matrix.append(cpa_row)
        meetings_matrix.append(meetings_row)

    # Criar abas para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(
        ["Custo Total", "Custo por Reunião (CPA)", "Reuniões Agendadas"]
    )

    # Custom colorscale para os heatmaps
    custom_colorscale = [
        [0.0, BRAND_COLOR],  # Menor custo = azul da marca
        [0.5, LIGHT_BLUE_3],  # Médio = azul claro
        [1.0, GRAY_2],  # Maior custo = cinza
    ]

    with tab1:
        fig_heatmap_cost = go.Figure(
            data=go.Heatmap(
                z=cost_matrix,
                x=[f"{r * 100:.0f}%" for r in booking_rates_heatmap],
                y=[f"{q * 100:.0f}%" for q in qual_rates_heatmap],
                colorscale=custom_colorscale,
                text=[[f"R$ {val:,.0f}" for val in row] for row in cost_matrix],
                texttemplate="%{text}",
                textfont={"size": 9},
                colorbar=dict(title="Custo Total (R$)"),
                hovertemplate="Qualificação: %{y}<br>Agendamento: %{x}<br>Custo: R$ %{z:,.2f}<extra></extra>",
            )
        )

        # Adicionar marcador para o cenário target
        target_qual_idx = min(
            range(len(qual_rates_heatmap)),
            key=lambda i: abs(qual_rates_heatmap[i] - target_qualification_rate),
        )
        target_book_idx = min(
            range(len(booking_rates_heatmap)),
            key=lambda i: abs(booking_rates_heatmap[i] - target_booking_rate),
        )

        fig_heatmap_cost.add_trace(
            go.Scatter(
                x=[f"{booking_rates_heatmap[target_book_idx] * 100:.0f}%"],
                y=[f"{qual_rates_heatmap[target_qual_idx] * 100:.0f}%"],
                mode="markers",
                marker=dict(
                    size=20,
                    color=GRAY_4,
                    symbol="star",
                    line=dict(color="white", width=2),
                ),
                name="Seu Target",
                showlegend=True,
            )
        )

        fig_heatmap_cost.update_layout(
            title="Custo Total por Combinação de Taxas",
            xaxis_title="Taxa de Agendamento (% de Qualificados)",
            yaxis_title="Taxa de Qualificação (% de Respostas)",
            height=600,
        )
        st.plotly_chart(fig_heatmap_cost, use_container_width=True)

    with tab2:
        fig_heatmap_cpa = go.Figure(
            data=go.Heatmap(
                z=cpa_matrix,
                x=[f"{r * 100:.0f}%" for r in booking_rates_heatmap],
                y=[f"{q * 100:.0f}%" for q in qual_rates_heatmap],
                colorscale=custom_colorscale,
                text=[[f"R$ {val:,.0f}" for val in row] for row in cpa_matrix],
                texttemplate="%{text}",
                textfont={"size": 9},
                colorbar=dict(title="CPA (R$)"),
                hovertemplate="Qualificação: %{y}<br>Agendamento: %{x}<br>CPA: R$ %{z:,.2f}<extra></extra>",
            )
        )

        fig_heatmap_cpa.add_trace(
            go.Scatter(
                x=[f"{booking_rates_heatmap[target_book_idx] * 100:.0f}%"],
                y=[f"{qual_rates_heatmap[target_qual_idx] * 100:.0f}%"],
                mode="markers",
                marker=dict(
                    size=20,
                    color=GRAY_4,
                    symbol="star",
                    line=dict(color="white", width=2),
                ),
                name="Seu Target",
                showlegend=True,
            )
        )

        fig_heatmap_cpa.update_layout(
            title="Custo por Reunião (CPA) por Combinação de Taxas",
            xaxis_title="Taxa de Agendamento (% de Qualificados)",
            yaxis_title="Taxa de Qualificação (% de Respostas)",
            height=600,
        )
        st.plotly_chart(fig_heatmap_cpa, use_container_width=True)

    # Colorscale invertido para reuniões (mais = melhor)
    meetings_colorscale = [
        [0.0, GRAY_3],  # Menos reuniões = cinza claro
        [0.5, LIGHT_BLUE_2],  # Médio = azul claro
        [1.0, BRAND_COLOR],  # Mais reuniões = azul da marca
    ]

    with tab3:
        fig_heatmap_meetings = go.Figure(
            data=go.Heatmap(
                z=meetings_matrix,
                x=[f"{r * 100:.0f}%" for r in booking_rates_heatmap],
                y=[f"{q * 100:.0f}%" for q in qual_rates_heatmap],
                colorscale=meetings_colorscale,
                text=[[f"{int(val)}" for val in row] for row in meetings_matrix],
                texttemplate="%{text}",
                textfont={"size": 9},
                colorbar=dict(title="Reuniões"),
                hovertemplate="Qualificação: %{y}<br>Agendamento: %{x}<br>Reuniões: %{z:.0f}<extra></extra>",
            )
        )

        fig_heatmap_meetings.add_trace(
            go.Scatter(
                x=[f"{booking_rates_heatmap[target_book_idx] * 100:.0f}%"],
                y=[f"{qual_rates_heatmap[target_qual_idx] * 100:.0f}%"],
                mode="markers",
                marker=dict(
                    size=20,
                    color=GRAY_4,
                    symbol="star",
                    line=dict(color="white", width=2),
                ),
                name="Seu Target",
                showlegend=True,
            )
        )

        fig_heatmap_meetings.update_layout(
            title="Reuniões Agendadas por Combinação de Taxas",
            xaxis_title="Taxa de Agendamento (% de Qualificados)",
            yaxis_title="Taxa de Qualificação (% de Respostas)",
            height=600,
        )
        st.plotly_chart(fig_heatmap_meetings, use_container_width=True)

    # Insights adicionais
    st.subheader("💡 Insights da Matriz de Sensibilidade")
    col_ins1, col_ins2, col_ins3 = st.columns(3)

    # Encontrar o melhor e pior cenário
    flat_costs = [cost for row in cost_matrix for cost in row]
    flat_cpas = [cpa for row in cpa_matrix for cpa in row if cpa > 0]
    flat_meetings = [meeting for row in meetings_matrix for meeting in row]

    col_ins1.metric(
        "Custo Mínimo Possível",
        f"R$ {min(flat_costs):,.2f}",
        delta=f"{((min(flat_costs) - target_results['total_cost']) / target_results['total_cost'] * 100):.1f}% vs Target",
        delta_color="inverse",
    )

    col_ins2.metric(
        "Custo Máximo Possível",
        f"R$ {max(flat_costs):,.2f}",
        delta=f"{((max(flat_costs) - target_results['total_cost']) / target_results['total_cost'] * 100):.1f}% vs Target",
        delta_color="inverse",
    )

    col_ins3.metric(
        "Máximo de Reuniões Possível",
        f"{int(max(flat_meetings))}",
        delta=f"{int(max(flat_meetings) - target_results['num_booked'])} vs Target",
    )

else:
    st.info("Ajuste a quantidade de leads na barra lateral para iniciar a simulação.")
