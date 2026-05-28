# --- STAMPA RISULTATI SULL'INTERFACCIA DETTAGLIATA ---
    st.markdown(f"## {T['results_title']}")
    st.markdown(f"<div class='custom-note-result'>{T['results_help']}</div>", unsafe_allow_html=True)
    
    # Calcolo metriche di performance avanzate per i tre scenari
    # Totale energia generata nell'anno (stima cumulativa)
    total_generation = sum(solar_monthly) + sum(wind_monthly)
    
    # Fabbisogno elettrico totale annuo comprensivo di EV per scenario
    demand_ann_house = sum(sum(hourly_house_load[m]) * days_in_months[m-1] for m in range(1, 12))
    demand_ann_ev = daily_ev_demand_kwh * 365 if has_ev else 0
    total_demand_annual = demand_ann_house + demand_ann_ev

    # Scenario 1 KPI
    sc_rate_s1 = (autoconsumo_s1 / total_generation) * 100 if total_generation > 0 else 0
    ss_rate_s1 = (autoconsumo_s1 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    co2_saved_s1 = autoconsumo_s1 * 0.415  # 0.415 kg CO2/kWh (Fattore medio mix elettrico)

    # Scenario 2 KPI
    sc_rate_s2 = (autoconsumo_s2 / total_generation) * 100 if total_generation > 0 else 0
    ss_rate_s2 = (autoconsumo_s2 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    co2_saved_s2 = autoconsumo_s2 * 0.415

    # Scenario 3 KPI
    sc_rate_s3 = (autoconsumo_s3 / total_generation) * 100 if total_generation > 0 else 0
    ss_rate_s3 = (autoconsumo_s3 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    co2_saved_s3 = autoconsumo_s3 * 0.415

    # Creazione dei Tab per un'analisi granulare e scansionabile
    tab1, tab2, tab3 = st.tabs([
        "🛑 Scenario 1: Monodirezionale Standard", 
        "☀️ Scenario 2: Smart Charging", 
        "🔄 Scenario 3: Bidirezionale V2H/V2L"
    ])
    
    with tab1:
        st.markdown("### 📊 Bilancio Energetico & Performance - Standard")
        st.write("In questa configurazione l'auto si comporta come un elettrodomestico passivo ad alta potenza. La ricarica parte alla massima potenza disponibile non appena il veicolo viene connesso, indipendentemente dalla produzione locale.")
        
        c1_1, c1_2, c1_3, c1_4 = st.columns(4)
        c1_1.metric(T["kpi_ac"], f"{autoconsumo_s1:.0f} kWh", help="Energia prodotta localmente e consumata direttamente in casa o nell'EV.")
        c1_2.metric("Indice Autoconsumo (🔋/⚡)", f"{sc_rate_s1:.1f} %", help="Percentuale di energia FER prodotta che è stata consumata all'interno del sito.")
        c1_3.metric("Autosufficienza (Grid Independence)", f"{ss_rate_s1:.1f} %", help="Percentuale del fabbisogno totale coperta dall'impianto locale.")
        c1_4.metric("Prelievo da Rete Esterna", f"{prelievo_grid_s1:.0f} kWh")
        
        st.markdown("#### 💰 Impatto Economico e Sostenibilità")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric(T["kpi_bill_savings"], f"{savings_s1:.2f} €/anno")
        ec2.metric(T["kpi_payback"], f"{payback_s1:.1f} Anni")
        ec3.metric("Emissioni $CO_2$ Evitate", f"{co2_saved_s1:.1f} kg")

    with tab2:
        st.markdown("### 📊 Bilancio Energetico & Performance - Smart Charging")
        st.write("La colonnina modula la potenza di ricarica inseguendo il surplus di produzione FER non assorbito dalle utenze domestiche e dalla batteria di casa. Riduce drasticamente i prelievi di picco.")
        
        c2_1, c2_2, c2_3, c2_4 = st.columns(4)
        c2_1.metric(T["kpi_ac"], f"{autoconsumo_s2:.0f} kWh", f"+{autoconsumo_s2 - autoconsumo_s1:.0f} kWh")
        c2_2.metric("Indice Autoconsumo (🔋/⚡)", f"{sc_rate_s2:.1f} %", f"+{sc_rate_s2 - sc_rate_s1:.1f} %")
        c2_3.metric("Autosufficienza (Grid Independence)", f"{ss_rate_s2:.1f} %", f"+{ss_rate_s2 - ss_rate_s1:.1f} %")
        c2_4.metric("Prelievo da Rete Esterna", f"{prelievo_grid_s2:.0f} kWh", f"-{prelievo_grid_s1 - prelievo_grid_s2:.0f} kWh", delta_color="inverse")
        
        st.markdown("#### 💰 Impatto Economico e Sostenibilità")
        ec2_1, ec2_2, ec2_3 = st.columns(3)
        ec2_1.metric(T["kpi_bill_savings"], f"{savings_s2:.2f} €/anno", f"+{savings_s2 - savings_s1:.2f} €")
        ec2_2.metric(T["kpi_payback"], f"{payback_s2:.1f} Anni", f"{payback_s2 - payback_s1:.1f} Anni", delta_color="inverse")
        ec3_2.metric("Emissioni $CO_2$ Evitate", f"{co2_saved_s2:.1f} kg", f"+{co2_saved_s2 - co2_saved_s1:.1f} kg")

    with tab3:
        st.markdown("### 📊 Bilancio Energetico & Performance - V2H/V2L Bidirezionale")
        st.write("L'auto elettrica è integrata dinamicamente come un vettore di storage bidirezionale flessibile. Non solo assorbe l'energia in eccesso, ma nei momenti di picco o assenza di sole/vento reimmette energia (V2L/V2H) per alimentare i carichi domestici.")
        
        c3_1, c3_2, c3_3, c3_4 = st.columns(4)
        c3_1.metric(T["kpi_ac"], f"{autoconsumo_s3:.0f} kWh", f"+{autoconsumo_s3 - autoconsumo_s2:.0f} kWh")
        c3_2.metric("Indice Autoconsumo (🔋/⚡)", f"{sc_rate_s3:.1f} %", f"+{sc_rate_s3 - sc_rate_s2:.1f} %")
        c3_3.metric("Autosufficienza (Grid Independence)", f"{ss_rate_s3:.1f} %", f"+{ss_rate_s3 - ss_rate_s2:.1f} %")
        c3_4.metric("Prelievo da Rete Esterna", f"{prelievo_grid_s3:.0f} kWh", f"-{prelievo_grid_s2 - prelievo_grid_s3:.0f} kWh", delta_color="inverse")
        
        st.markdown("#### 💰 Impatto Economico e Sostenibilità")
        ec3_1, ec3_2, ec3_3 = st.columns(3)
        ec3_1.metric(T["kpi_bill_savings"], f"{savings_s3:.2f} €/anno", f"+{savings_s3 - savings_s2:.2f} €")
        ec3_2.metric(T["kpi_payback"], f"{payback_s3:.1f} Anni", help="Include il costo addizionale dell'hardware di ricarica bidirezionale.")
        ec3_3.metric("Emissioni $CO_2$ Evitate", f"{co2_saved_s3:.1f} kg", f"+{co2_saved_s3 - co2_saved_s2:.1f} kg")

    # --- TABELLA DI RIEPILOGO COMPARATIVA COMPLETA ---
    st.markdown("### 📈 Matrice Comparativa Tecno-Economica")
    st.write("La tabella seguente sintetizza le metriche prestazionali ed economiche simulate su base oraria per l'intero anno solare:")
    
    summary_data = {
        "Metrica di Confronto": [
            "Fabbisogno Energetico Totale Lordo (kWh)",
            "Volume Autoconsumato in Loco (kWh)",
            "Energia Immessa/Venduta alla Rete (kWh)",
            "Energia Prelevata dalla Rete (kWh)",
            "Indice di Autoconsumo Effettivo (%)",
            "Grado di Indipendenza Energetica (%)",
            "Costo dell'Infrastruttura (CAPEX Totale)",
            "Risparmio Economico Annuale Corrente (€/anno)",
            "Ritorno dell'Investimento (Payback Period)"
        ],
        "1. Monodirezionale Standard": [
            f"{total_demand_annual:.0f}", f"{autoconsumo_s1:.0f}", f"{surplus_sold_s1:.0f}", f"{prelievo_grid_s1:.0f}",
            f"{sc_rate_s1:.1f}%", f"{ss_rate_s1:.1f}%", f"{capex_s1_tot:.0f} €", f"{savings_s1:.2f} €", f"{payback_s1:.1f} anni"
        ],
        "2. Monodirezionale Smart": [
            f"{total_demand_annual:.0f}", f"{autoconsumo_s2:.0f}", f"{surplus_sold_s2:.0f}", f"{prelievo_grid_s2:.0f}",
            f"{sc_rate_s2:.1f}%", f"{ss_rate_s2:.1f}%", f"{capex_s2_tot:.0f} €", f"{savings_s2:.2f} €", f"{payback_s2:.1f} anni"
        ],
        "3. Bidirezionale V2H/V2L": [
            f"{total_demand_annual:.0f}", f"{autoconsumo_s3:.0f}", f"{surplus_sold_s3:.0f}", f"{prelievo_grid_s3:.0f}",
            f"{sc_rate_s3:.1f}%", f"{ss_rate_s3:.1f}%", f"{capex_s3_tot:.0f} €", f"{savings_s3:.2f} €", f"{payback_s3:.1f} anni"
        ]
    }
    st.table(summary_data)

    # --- GRAFICI DI CONFRONTO FINANZIARIO ED ENERGETICO ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_gen, ax_gen = plt.subplots(figsize=(6, 2.3), dpi=200)
        ax_gen.plot(range(1, 13), solar_monthly, label="PV", color="#D97706", lw=1.2)
        ax_gen.bar(range(1, 13), wind_monthly, label="Wind", color="#2563EB", alpha=0.15, width=0.4)
        setup_plot_style(ax_gen, T["chart_gen_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax_gen.legend(fontsize=6, frameon=False)
        st.pyplot(fig_gen)
    with col_g2:
        fig_eco, ax_eco = plt.subplots(figsize=(6, 2.3), dpi=200)
        scenariolabels = ['Standard', 'Smart', 'V2H/V2L']
        capex_all = [capex_s1_tot, capex_s2_tot, capex_s3_tot]
        savings_10y = [savings_s1*10, savings_s2*10, savings_s3*10]
        ax_eco.bar(scenariolabels, capex_all, width=0.3, label="CAPEX", color="#64748B", align='center')
        ax_eco.bar(scenariolabels, savings_10y, width=0.3, label="Savings 10Y", color="#10B981", alpha=0.6, align='edge')
        setup_plot_style(ax_eco, T["chart_eco_title"], "", "€")
        ax_eco.legend(fontsize=6, frameon=False)
        st.pyplot(fig_eco)

    # --- SEZIONE SOC STAGIONALI IN DETTAGLIO ---
    st.markdown("---")
    st.subheader(T["season_title"])
    st.markdown(f"<div class='custom-note'>{T['season_help']}</div>", unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns(2)
    seasons_list = [T["inv"], T["est"]]
    titles_list = [T["inv_t"], T["est_t"]]
    
    for idx, (s_name, s_title) in enumerate(zip(seasons_list, titles_list)):
        target_col = col_s1 if idx == 0 else col_s2
        with target_col:
            fig_soc, ax_soc = plt.subplots(figsize=(6, 2.4), dpi=200)
            ax_soc.plot(range(24), soc_tracking_ev[s_name]["s1"], label=T["legend_soc_s1"], color="#EF4444", lw=1.2, linestyle=":")
            ax_soc.plot(range(24), soc_tracking_ev[s_name]["s2"], label=T["legend_soc_s2"], color="#3B82F6", lw=1.2, linestyle="-.")
            ax_soc.plot(range(24), soc_tracking_ev[s_name]["s3"], label=T["legend_soc_s3"], color="#10B981", lw=1.5, linestyle="-")
            
            # Evidenzia ore di connessione wallbox a casa
            ax_soc.fill_between(range(24), 0, 100, where=ev_hours_status, color='#475569', alpha=0.04, label=T["legend_grid_on"])
            setup_plot_style(ax_soc, f"{s_title}", T["chart_h_x"], T["chart_h_y_soc"])
            ax_soc.set_ylim(-5, 105)
            ax_soc.set_xlim(0, 23)
            ax_soc.legend(fontsize=5.5, frameon=False, loc="lower left")
            st.pyplot(fig_soc)

    # --- SINTESI MENSILE ---
    st.markdown("---")
    st.subheader(T["final_chart_title"])
    fig12, ax12 = plt.subplots(figsize=(12, 2.5), dpi=200)
    x_idx = range(1, 13)
    ax12.bar([x - 0.22 for x in x_idx], monthly_gross_load_all, width=0.2, label=T["final_l1"], color='#94A3B8', alpha=0.25)
    ax12.bar([x - 0.07 for x in x_idx], monthly_ac_s1, width=0.15, label=T["final_l2"], color='#EF4444', alpha=0.7)
    ax12.bar([x + 0.07 for x in x_idx], monthly_ac_s2, width=0.15, label=T["final_l3"], color='#3B82F6', alpha=0.8)
    ax12.bar([x + 0.22 for x in x_idx], monthly_ac_s3, width=0.15, label=T["final_l4"], color='#10B981', alpha=0.9)
    setup_plot_style(ax12, T["final_chart_sub"], T["final_x"], T["chart_y_kwh"])
    ax12.set_xticks(x_idx)
    ax12.set_xticklabels(T["months_labels"])
    ax12.legend(fontsize=6.5, frameon=False, loc="upper right")
    st.pyplot(fig12)

st.markdown("---")
st.caption("RES-EV Microgrid Core Platform | Dual-Language Optimization Framework (ITA/ENG)")