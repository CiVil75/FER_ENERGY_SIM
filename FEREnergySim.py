# FEREnergySim.py
import streamlit as st
import requests
import matplotlib.pyplot as plt
import folium
import math
import numpy as np
from streamlit_folium import st_folium

# --- CONFIGURAZIONE INTERFACCIA ED ESTETICA ---
st.set_page_config(page_title="RES-Based Home Simulator 8760", layout="wide")

# CSS Avanzato per layout ultra-compatto e stilizzazione reportistica
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    .reportview-container .main .block-container { padding-top: 0.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.8rem !important; font-weight: 700; color: #0F172A; margin-bottom: 0.1rem; letter-spacing: -0.02em; }
    h2 { font-size: 1.25rem !important; font-weight: 600; color: #1E293B; margin-top: 1rem; margin-bottom: 0.5rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.1rem; }
    h3 { font-size: 1.0rem !important; font-weight: 600; color: #334155; margin-bottom: 0.4rem; }
    h4 { font-size: 0.9rem !important; font-weight: 600; color: #475569; margin-top: 0.4rem; }
    .stNumberInput > label, .stSelectbox > label, .stTextInput > label, .stCheckbox > label { font-size: 0.78rem !important; font-weight: 500; color: #475569; }
    .stMetric { background-color: #F8FAFC; padding: 0.4rem 0.6rem; border-radius: 0.375rem; border: 1px solid #E2E8F0; }
    div[data-testid="stExpander"] { border: 1px solid #E2E8F0 !important; box-shadow: none !important; margin-bottom: 0.4rem; }
    
    .custom-note { 
        padding: 0.5rem 0.75rem; border-radius: 0.25rem; font-size: 0.8rem; 
        background-color: #F8FAFC; color: #475569; border-left: 3px solid #3B82F6; margin-bottom: 0.6rem; line-height: 1.3;
    }
    .tech-explanation {
        padding: 0.75rem 1rem; border-radius: 0.375rem; font-size: 0.82rem; 
        background-color: #F1F5F9; color: #334155; border-left: 4px solid #64748B; margin-bottom: 0.8rem; line-height: 1.45;
    }
    .custom-note-result { 
        padding: 0.6rem 0.75rem; border-radius: 0.25rem; font-size: 0.82rem; 
        background-color: #F0FDF4; color: #166534; border-left: 3px solid #22C55E; margin-bottom: 0.8rem;
    }
    div[data-testid="column"] { padding: 0px 1px !important; }
    </style>
""", unsafe_allow_html=True)

# --- DIZIONARIO DI TRADUZIONE BILINGUE E DOCUMENTAZIONE (8760h REVISION) ---
LANG_DICT = {
    "ITA": {
        "title": "🌍 Simulatore Residenziale FER (8760h continuo) - Prof. Ing. C. Villante",
        "subtitle": "Modellazione dinamica oraria su base annua (8760 punti) per micro-reti accoppiate a sistemi BESS e V2H.",
        
        "doc_expander_title": "📖 Spiegazione Architettura del Codice e Flussi Dati a 8760 ore (Technical Documentation)",
        "doc_global_text": """
        ### 🔬 Architettura del Modello e Algoritmo di Simulazione Continua
        Questo simulatore esegue un'analisi energetica dinamica a **risoluzione oraria sequenziale per l'intero anno ($8760 \\text{ ore}$)**. A differenza dei modelli semplificati a giorni medi mensili, questa struttura garantisce la conservazione della memoria storica degli stati di carica degli accumuli, catturando l'effetto di transitori su più giorni consecutivi di scarso soleggiamento o vento forte.

        #### 1. Origine dei Dati e Ingestione (Data Ingestion)
        * **Fotovoltaico (PV):** L'applicazione interroga le API **EU-PVGIS** per ricavare l'irraggiamento mensile tipico, ridistribuendolo poi su base oraria annua (8760 punti) legandolo alla geometria solare del sito (elevazione ed equazione del tempo).
        * **Micro-Eolico (WT) e Temperature Esterne:** Scarica serie climatiche storiche orarie annuali (8760 punti) tramite le API **Open‑Meteo Archive API (ERA5 Reanalysis)**:
        https://archive-api.open-meteo.com

        Variabili utilizzate:
        - `temperature_2m`
        - `windspeed_10m`

        Le serie climatiche vengono utilizzate per:
        - modellazione HVAC dinamica;
        - generazione carichi termici;
        - simulazione microeolico;
        - simulazione continua annuale 8760h.

        I profili vento vengono inoltre riscalati all'altezza mozzo tramite legge logaritmica.
        * **Firma Termica dell'Edificio:** Genera la richiesta oraria di climatizzazione invernale ed estiva per tutte le 8760 ore dell'anno incrociando la temperatura esterna oraria del dataset Open-Meteo con le dispersioni geometriche della classe energetica dell'involucro edilizio.

        #### 2. Logica dei Tre Scenari di Controllo Comparati
        * **Scenario 1 (Monodirezionale Standard):** L'EV assorbe potenza dalla Wallbox a tasso costante esclusivamente nelle ore in cui è fisicamente connesso, ripartendo linearmente il fabbisogno chilometrico giornaliero. Il BESS agisce da tampone locale passivo.
        * **Scenario 2 (Smart Charging):** La ricarica dell'EV viene modulata attimo per attimo inseguendo l'eccedenza di produzione FER generata sul nodo domestico al netto dei carichi di casa. La ricarica da rete interviene como emergenza solo se il SoC dell'auto scende sotto la soglia minima di sicurezza per il viaggio.
        * **Scenario 3 (Bidirectional V2H):** La batteria dell'EV diventa un accumulo mobile cooperante in parallelo al BESS domestico. Nelle ore di connessione domestica, se il veicolo ha carica residua superiore alla soglia di viaggio, inietta potenza nella rete interna della casa per abbattere i picchi termici serali ed elettrici (*Peak Shaving*).
        """,
        
        "guide_metrics_title": "📊 Guida all'Interpretazione dei KPI e Indicatori Finanziari",
        "guide_metrics_text": """
        * **Indice di Autoconsumo (Self-Consumption Rate):** Percentuale dell'energia FER generata (PV + Eolico) consumata all'interno dell'abitazione (direttamente o immagazzinata nei sistemi di accumulo).
        * **Grado di Indipendenza Energetica (Autosufficienza):** Quota dei consumi globali annui dell'edificio (inclusa la mobilità) coperta dalla microgenerazione locale.
        * **Tempo di Ritorno (Payback Period):** Periodo di ammortamento finanziario calcolato sul CAPEX totale di ciascuno scenario (Impianto base + Wallbox specifica) diviso per i risparmi cumulati orariamente sulle bollette elettriche e la valorizzazione delle eccedenze immesse in rete.
        """,
        
        "guide_table_title": "📋 Analisi Critica della Matrice Comparativa delle Strategie",
        "guide_table_text": """
        La tabella riassume i risultati integrati sommandoli sulle **8760 ore della simulazione continua**. 
        Osserva come l'adozione dello **Scenario 3 (V2H)** converta l'auto in un generatore di flussi di cassa, aumentando drasticamente l'autosufficienza e riducendo il prelievo globale dalla rete elettrica nazionale rispetto alla ricarica passiva dello Scenario 1.
        """,
        
        "guide_macro_charts_title": "📉 Guida ai Grafici di Sintesi Mensile (Macro Bilanci)",
        "guide_macro_charts_text": """
        * **Grafico di Generazione Mensile (Sinistra):** Aggrega l'output energetico orario per mostrare il bilancio stagionale.
        * **Grafico di Fabbisogno Mensile (Destra):** Evidenzia l'andamento stagionale dei consumi. I picchi invernali corrispondono al riscaldamento con Pompa di Calore (firma termica legata alle temperature Open-Meteo), mentre quelli estivi riflettono la domanda di condizionamento (AC).
        """,
        
        "guide_hourly_charts_title": "⏱️ Guida all'Analisi dei Giorni Reali Calendatoriali Selezionati",
        "guide_hourly_charts_text": """
        I grafici mostrano la risposta dinamica del sistema su **4 giorni reali specifici del calendario (tutti ricadenti in giorni feriali dal lunedì al venerdì)**, scelti come rappresentativi delle stagioni:
        * **Inverno (15 Gennaio - Lunedì):** Radiazione solare minima, forte carico termico della pompa di calore.
        * **Primavera (15 Aprile - Lunedì):** Ottimo bilancio FER, riscaldamento quasi nullo.
        * **Estate (15 Luglio - Lunedì):** Picco solare a mezzogiorno, carico AC concentrato nelle ore pomeridiane.
        * **Autunno (15 Ottobre - Martedì):** Transizione climatica con intermittenza meteorologica.
        *I grafici di destra mostrano l'evoluzione dei SoC evidenziando la carica/scarica delle diverse strategie della batteria dell'auto.*
        """,
        
        "guide_8760_charts_title": "📈 Guida all'Analisi delle Curve Continue Annuali (8760 ore)",
        "guide_8760_charts_text": """
        Questi grafici visualizzano l'andamento continuo orario **dal punto 1 (1 Gennaio) al punto 8760 (31 Dicembre)**:
        * **Profilo Continuo dei Flussi (Sinistra):** Consente di studiare visivamente la sovrapposizione tra la campana della produzione solare/eolica e la linea dei consumi totali.
        * **Evoluzione Continua del SoC (Destra):** Mostra la ciclicità a lungo termine degli accumuli. Se l'EV è attivo, vengono messi a confronto i diversi profili di carica residua dell'auto per metterne in risalto i benefici gestionali.
        """,
        
        "params_title": "🎛️ Configurazione Parametri Tecnici ed Economici",
        "pv_title": "☀️ Fotovoltaico (Max 20 kWp)",
        "pv_help": "💡 1 kWp occupa ~5-7 m². Inclinazione ottimale in Italia: 30°-35°.",
        "pv_tech_expl": "⚙️ **Modellazione PV:** L'output PVGIS viene riscalato sul rendimento del modulo e distribuito geometricamente sulle 8760 ore dell'anno.",
        "wind_title": "🌬️ Micro-Eolico",
        "wind_help": "💡 Profilo orario a 8760 punti riscalato con la legge logaritmica sull'altezza mozzo.",
        "wind_tech_expl": "⚙️ **Modellazione WT:** Calcola la potenza oraria applicando l'equazione cinetica del vento sul rotore con limite di Betz reale.",
        "batt_title": "🔋 Accumulo Stazionario (BESS)",
        "batt_help": "💡 Il DoD Max preserva la vita dell'accumulo vincolando la carica minima oraria residua.",
        "batt_tech_expl": "⚙️ **Modellazione BESS:** Algoritmo ricorsivo orario ad accumulo di carica con rendimento round-trip applicato a ogni variazione energetica.",
        "load_title": "🏠 Profilo Utenza & Edificio",
        "load_help": "💡 Calcola la firma termica oraria integrando i dati storici ambientali Open-Meteo.",
        "load_tech_expl": "⚙️ **Modellazione Carichi:** Combina un profilo base elettrico stocastico con la domanda termica oraria calcolata sulle 8760 ore in funzione delle temperature esterne reali.",
        "eco_title": "💰 Parametri Economici & Tariffe Grid",
        "eco_help": "💡 Inserisci i costi per valutare il tempo di ammortamento semplice.",
        "eco_tech_expl": "⚙️ **Analisi Finanziaria:** Integra orariamente i risparmi in bolletta causati dall'autoconsumo e i profitti derivanti dall'energia immessa.",
        
        "load_ev_check": "Abilita Veicolo Elettrico (EV)",
        "ev_section_title": "🚗 Profilazione EV & Configurazione Infrastruttura di Ricarica / V2H Configuration",
        "ev_help": "💡 Spunta le ore in cui l'auto è connessa alla Wallbox domestica. Nelle ore non spuntate l'auto si assume in movimento.",
        "ev_tech_expl": "⚙️ **Modellazione EV & V2H:** Quando disconnesso, il veicolo drena energia dalla batteria interna in base ai km giornalieri; quando è connesso partecipa al bilanciamento del nodo energetico domestico.",
        
        "pv_p": "Potenza Impianto (kWp)", "pv_t": "Tilt Angle (°)", "pv_az": "Azimuth Angle (°)", "pv_eff": "Rendimento Modulo (%)",
        "wind_p": "Potenza Nominale (kW)", "wind_h": "Altezza Mozzo (m)",
        "batt_c": "Capacità Nominale (kWh)", "batt_eff": "Efficienza Round-Trip (%)", "batt_dod": "DoD Massimo (%)",
        "load_area": "Superficie Calpestabile (m²)", "load_class": "Classe Energetica", "load_occ": "Numero Occupanti", "load_cop": "COP/EER Medio Pompa Calore",
        "eco_cost": "Costo Energia Prelevata (€/kWh)", "eco_sell": "Tariffa Immissione / RID (€/kWh)", "eco_capex": "CAPEX Impianto Base (PV+Wind) (€)",
        
        "ev_cap": "Capacità Batteria EV (kWh)", "ev_km": "Distanza Giornaliera (km)", "ev_whkm": "Consumo Specifico (Wh/km)",
        "ev_v2hp": "Potenza Wallbox / Inverter V2H (kW)", "ev_v2heff": "Efficienza Convertitore (%)", "ev_soc_init": "SoC Iniziale di Partenza (%)", "ev_soc_min": "SoC Minimo di Sicurezza per Viaggio (%)",
        "ev_capex_s1": "Costo Aggiuntivo Wallbox S1 Standard (€)", "ev_capex_s2": "Costo Aggiuntivo Smart Wallbox S2 (€)", "ev_capex_s3": "Costo Aggiuntivo Stazione Bidirezionale V2H S3 (€)",
        "ev_grid_matrix": "Matrice di Disponibilità Oraria dell'EV alla Rete Domestica (Spuntato = Connesso alla Wallbox)",
        
        "gis_title": "📍 Posizionamento Geografico Impianto", "gis_search": "Cerca Comune o Coordinate", "gis_btn": "🔍 Aggiorna Mappa Sito", "gis_active": "**Sito Attivo:**",
        "run_btn": "⚡ Esegui Simulazione Energetica Dinamica (8760 Punti)",
        "results_title": "📊 Analisi Output e Indicatori di Performance Annuali",
        "results_help": "🔬 Risultati consolidati sull'orizzonte temporale continuo di 8760 ore annuali.",
        "kpi_ac": "Autoconsumo", "kpi_bill_savings": "Risparmio Economico", "kpi_payback": "Tempo di Ritorno",
        "chart_gen_title": "Profili di Generazione Mensile Integrata", "chart_load_title": "Profili di Fabbisogno Mensile Integrato (Riscaldamento vs Condizionamento)",
        "chart_x_month": "Mese", "chart_y_kwh": "Energia [kWh]",
        "season_title": "📈 Dinamica Oraria Dettagliata sui Giorni Tipici Reali Selezionati",
        "season_help": "🔬 Analisi intra-giornaliera su specifiche giornate reali feriali del calendario continuo.",
        "inv": "Inverno (15 Gennaio - Lunedì)", "pri": "Primavera (15 Aprile - Lunedì)", "est": "Estate (15 Luglio - Lunedì)", "aut": "Autunno (15 Ottobre - Martedì)",
        "inv_t": "❄️ Giorno Reale Invernale (15 Gennaio - Lunedì)", "pri_t": "🌱 Giorno Reale Primavera (15 Aprile - Lunedì)", "est_t": "☀️ Giorno Reale Estivo (15 Luglio - Lunedì)", "aut_t": "🍂 Giorno Reale Autunnale (15 Ottobre - Martedì)",
        "chart_hourly_title": "Bilancio di Potenza Orario", "chart_soc_title": "Stato di Carica (SoC)",
        "chart_h_x": "Ora del Giorno [h]", "chart_h_y_flow": "Potenza/Energia Oraria [kWh]", "chart_h_y_soc": "State of Charge [%]",
        "legend_fer": "Generazione FER", "legend_base_heat": "Carico Base + Riscaldamento", "legend_ac": "Carico Condizionamento (AC)", "legend_tot_ev": "Carico Totale + Ricarica EV",
        "legend_soc_h": "SoC Batteria Casa", "legend_grid_on": "Accoppiamento Veicolo Attivo",
        "legend_ac_power": "Potenza Richiesta Climatizzazione",
        "legend_ev_conn": "EV Connesso alla Wallbox",
        "final_chart_title": "📊 Analisi Comparativa delle Strategie di Autoconsumo sull'Anno",
        "final_chart_sub": "Copertura Energetica ed Autoconsumo Mensile Effettivo nelle Strategie Simulation",
        "final_x": "Mese dell'Anno", "final_l1": "Fabbisogno Utenza Lordo", "final_l2": "S1: Monodirezionale Standard", "final_l3": "S2: Smart Charging", "final_l4": "S3: Bidirectional V2H/V2L",
        "months_labels": ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'],
        "hp_share": "Quota Riscaldamento", "ac_share": "Quota Condizionamento (AC)",
        "show_tech_details": "Mostra Dettagli Algoritmo Modulo"
    },
    "ENG": {
        "title": "🌍 RES-Based Home Simulator (8760h continuous) by Prof. Eng. C. Villante",
        "subtitle": "Hourly annual dynamic modeling (8760 points) for micro-grids coupled with BESS and V2H ecosystems.",
        
        "doc_expander_title": "📖 Code Architecture and Data Flows Deep Explanation at 8760 Hours (Technical Documentation)",
        "doc_global_text": """
        ### 🔬 Model Architecture and Continuous Simulation Algorithm
        This simulator executes a dynamic energy analysis with a **sequential hourly resolution for the entire year ($8760 \\text{ hours}$)**. Unlike simplified monthly average day models, this structure preserves the historical memory of storage states of charge, capturing the effect of multi-day transients of low solar radiation or high wind speeds.

        #### 1. Data Ingestion & Sources
        * **Photovoltaic (PV):** Queries **EU-PVGIS** APIs for monthly typical irradiation, then maps it to an annual hourly timeline (8760 points) using local solar geometry formulas (elevation and equation of time).
        * **Micro-Wind (WT):** Downloads a full 8760-hour wind speed profile at 10m from the **Open-Meteo (Reanalysis)** API, extrapolating it to the chosen hub height via logarithmic power law.
        * **Building Thermal Signature:** Computes hourly heating and cooling demands across all 8760 hours of the year by intersecting real historical ambient temperatures with building envelope thermal transmittances.

        #### 2. Logic of the Three Compared Control Strategies
        * **Scenario 1 (Standard Monodirectional):** EV absorbs power linearly exclusively during designated availability matrix hours, splitting the total daily driving demand. The BESS acts as a passive local buffer.
        * **Scenario 2 (Smart Charging):** EV charging is dynamically modulated to track real-time local green generation surplus. Grid charging occurs only as a backup if the EV SoC falls below the safe trip threshold.
        * **Scenario 3 (Bidirectional V2H):** The EV battery behaves as a shared mobile distributed storage cooperating in parallel with the stationary home BESS. When connected, if its SoC exceeds the trip safety margin, it injects power back into the house (*Peak Shaving*).
        """,
        
        "guide_metrics_title": "📊 Interpretation Guide for KPI and Financial Indicators",
        "guide_metrics_text": """
        * **Self-Consumption Rate:** Percentage of total generated green energy consumed locally or stored, instead of being exported.
        * **Grid Independence (Self-Sufficiency Rate):** Faction of overall annual building energy consumption (mobility included) covered by local generation.
        * **Payback Period:** Financial amortization time calculated by dividing total strategy CAPEX by annualized integrated savings and feed-in tariff revenues.
        """,
        
        "guide_table_title": "📋 Critical Review of the Strategy Comparative Matrix",
        "guide_table_text": """
        The table shows the integrated data summed over the **8760 hours of continuous simulation**. 
        Note how **Scenario 3 (V2H)** turns the car into a cash-flow generator, increasing self-sufficiency and reducing grid reliance significantly compared to passive model.
        """,
        
        "guide_macro_charts_title": "📉 Guide to Monthly Summary Charts (Macro Energy Balance)",
        "guide_macro_charts_text": """
        * **Monthly Generation Profiles (Left):** Aggregates hourly energy output to show seasonal matching.
        * **Monthly Demand Profiles (Right):** Visualizes seasonal load variations. Winter peaks track Heat Pump demand, while summer ones represent AC cooling loads.
        """,
        
        "guide_hourly_charts_title": "⏱️ Guide to Intra-Day Analysis on Selected Real Typical Days",
        "guide_hourly_charts_text": """
        These plots focus on dynamic system responses across **4 specific real calendar days (all falling on standard business weekdays from Monday to Friday)**, chosen as seasonal representatives:
        * **Winter (Jan 15th - Monday):** Low solar radiation, massive heat pump thermal load.
        * **Spring (Apr 15th - Monday):** High RES generation, negligible ambient conditioning.
        * **Summer (Jul 15th - Monday):** Peak solar output at noon, high AC loads during afternoon hours.
        * **Autumn (Oct 15th - Tuesday):** Weather transition with highly intermittent wind and solar resource.
        """,
        
        "guide_8760_charts_title": "📈 Guide to Continuous Annual Curve Analysis (8760 Hours)",
        "guide_8760_charts_text": """
        These plots illustrate continuous trends **from hour 1 (January 1st) to hour 8760 (December 31st)**:
        * **Continuous Flows Profile (Left):** Visually displays matching or mismatches between solar/wind bell curves and building aggregated total consumption.
        * **Continuous SoC Evolution (Right):** Tracks battery status over a long horizon. When the EV option is checked, it evaluates the EV charging state across all scenarios to highlight algorithmic variances.
        """,
        
        "params_title": "🎛️ Technical and Economic Parameters Configuration",
        "pv_title": "☀️ Photovoltaic (Max 20 kWp)",
        "pv_help": "💡 1 kWp requires ~5-7 m². Optimal Tilt in Italy: 30°-35°.",
        "pv_tech_expl": "⚙️ **PV Modeling:** The normalized PVGIS output is scaled to module efficiency and mapped on 8760 chronological hours.",
        "wind_title": "🌬️ Micro-Wind",
        "wind_help": "💡 8760 hourly profile extrapolated using logarithmic power law on hub height.",
        "wind_tech_expl": "⚙️ **WT Modeling:** Computes instantaneous power on rotor disk considering real aerodynamic Betz coefficient.",
        "batt_title": "🔋 Stationary Storage (BESS)",
        "batt_help": "💡 Max DoD preserves stationary battery cycle life.",
        "batt_tech_expl": "⚙️ **BESS Modeling:** Continuous chronological charge loop with internal charging efficiency losses applied hourly.",
        "load_title": "🏠 Load Profile & Building",
        "load_help": "💡 Computes building thermal signature crossing insulation traits with Open-Meteo weather data.",
        "load_tech_expl": "⚙️ **Load Modeling:** Merges a basic stochastic appliance baseline with hourly heat pump power requirements calculated over 8760 points.",
        "eco_title": "💰 Economic Parameters & Grid Tariffs",
        "eco_help": "💡 Feed values to evaluate simple payback performance.",
        "eco_tech_expl": "⚙️ **Financial Engine:** Integrates hourly reduced grid bills and energy sold net revenues.",
        
        "load_ev_check": "Enable Electric Vehicle (EV)",
        "ev_section_title": "🚗 EV Profiling & Charging Infrastructure / V2H Configuration",
        "ev_help": "💡 Check hours when the car is plugged into the wallbox. Unchecked hours imply driving.",
        "ev_tech_expl": "⚙️ **Modellazione EV & V2H:** While traveling, the vehicle drains energy based on daily kilometers; while parked, it supports bidirectional home balancing.",
        
        "pv_p": "System Power (kWp)", "pv_t": "Tilt Angle (°)", "pv_az": "Azimuth Angle (°)", "pv_eff": "Module Efficiency (%)",
        "wind_p": "Nominal Power (kW)", "wind_h": "Hub height (m)",
        "batt_c": "Nominal Capacity (kWh)", "batt_eff": "Round-Trip Efficiency (%)", "batt_dod": "Max DoD (%)",
        "load_area": "Floor Area (m²)", "load_class": "Energy Class", "load_occ": "Occupants Number", "load_cop": "Heat Pump Average COP/EER",
        "eco_cost": "Purchased Electricity Cost (€/kWh)", "eco_sell": "Injection Price / RID (€/kWh)", "eco_capex": "Base Installation CAPEX (PV+Wind) (€)",
        
        "ev_cap": "EV Battery Capacity (kWh)", "ev_km": "Daily Distance (km)", "ev_whkm": "Specific Consumption (Wh/km)",
        "ev_v2hp": "Wallbox / V2H Inverter Power (kW)", "ev_v2heff": "Converter Efficiency (%)", "ev_soc_init": "Initial SoC (%)", "ev_soc_min": "Safety Trip Minimum SoC (%)",
        "ev_capex_s1": "S1 Standard Wallbox Extra Cost (€)", "ev_capex_s2": "S2 Smart Wallbox Extra Cost (€)", "ev_capex_s3": "S3 Bidirectional V2H Station Extra Cost (€)",
        "ev_grid_matrix": "EV Hourly Availability Matrix to Home Network (Checked = Connected to Wallbox)",
        
        "gis_title": "📍 GIS Site Localization", "gis_search": "Search Municipality or Coordinates", "gis_btn": "🔍 Update Site Map", "gis_active": "**Active Site:**",
        "run_btn": "⚡ Run Dynamic Energy Simulation (8760 Points)",
        "results_title": "📊 Simulation Output & Performance Indicators",
        "results_help": "🔬 Consolidated performance metrics computed over a continuous annual 8760-hour horizon.",
        "kpi_ac": "Self-Consumption", "kpi_bill_savings": "Economic Savings", "kpi_payback": "Payback Period",
        "chart_gen_title": "Monthly Generation Profiles", "chart_load_title": "Monthly Demand Profiles (Heating vs Cooling)",
        "chart_x_month": "Month", "chart_y_kwh": "Energy [kWh]",
        "season_title": "📈 Detailed Hourly Dynamics on Selected Real Typical Days",
        "season_help": "🔬 Intra-day analysis on specific calendar real business days.",
        "inv": "Winter (Jan 15th - Monday)", "pri": "Spring (Apr 15th - Monday)", "est": "Summer (Jul 15th - Monday)", "aut": "Autumn (Oct 15th - Tuesday)",
        "inv_t": "❄️ Real Winter Day (January 15th - Monday)", "pri_t": "🌱 Real Spring Day (April 15th - Monday)", "est_t": "☀️ Real Summer Day (July 15th - Monday)", "aut_t": "🍂 Real Autumn Day (October 15th - Tuesday)",
        "chart_hourly_title": "Hourly Power Balance", "chart_soc_title": "State of Charge (SoC)",
        "chart_h_x": "Time of Day [h]", "chart_h_y_flow": "Hourly Power/Energy [kWh]", "chart_h_y_soc": "State of Charge [%]",
        "legend_fer": "RES Generation", "legend_base_heat": "Base Load + Heating", "legend_ac": "Cooling Load (AC)", "legend_tot_ev": "Total Load + EV Charge",
        "legend_soc_h": "Home BESS SoC", "legend_grid_on": "Vehicle Connected",
        "legend_ac_power": "Cooling Power Demand",
        "legend_ev_conn": "EV Connected to Wallbox",
        "final_chart_title": "📊 Comparative Analysis of Self-Consumption Strategies over the Year",
        "final_chart_sub": "Energy Coverage and Effective Monthly Self-Consumption across Simulation Scenarios",
        "final_x": "Month of the Year", "final_l1": "Gross Load", "final_l2": "S1: Standard Monodirectional", "final_l3": "S2: Smart Charging", "final_l4": "S3: Bidirectional V2H/V2L",
        "months_labels": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        "hp_share": "Heating Share", "ac_share": "Cooling Share (AC)",
        "show_tech_details": "Show Component Technical Insights"
    }
}

# --- SELEZIONE LINGUA INIZIALE ---
lang = st.radio("🌐 Language / Lingua", ["ITA", "ENG"], horizontal=True)
T = LANG_DICT[lang]

st.title(T["title"])
st.caption(T["subtitle"])

with st.expander(T["doc_expander_title"], expanded=False):
    st.markdown(T["doc_global_text"])

if "lat" not in st.session_state: st.session_state.lat = 42.3498
if "lon" not in st.session_state: st.session_state.lon = 13.3995

# --- PANNELLO DI CONTROLLO PARAMETRI ---
st.markdown(f"## {T['params_title']}")
exp_pv, exp_wind, exp_batt, exp_load, exp_eco = st.columns(5)

with exp_pv.expander(T["pv_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['pv_help']}</div>", unsafe_allow_html=True)
    pv_power = st.number_input(T["pv_p"], min_value=1, max_value=20, value=6, step=1)
    pv_tilt = st.number_input(T["pv_t"], min_value=0, max_value=90, value=35, step=5)
    pv_azimuth = st.number_input(T["pv_az"], min_value=-180, max_value=180, value=0, step=5)
    pv_efficiency = st.number_input(T["pv_eff"], min_value=10, max_value=30, value=20, step=1)

with exp_wind.expander(T["wind_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['wind_help']}</div>", unsafe_allow_html=True)
    wind_power_kw = st.number_input(T["wind_p"], min_value=1, max_value=20, value=3, step=1)
    hub_height = st.number_input(T["wind_h"], min_value=10, max_value=200, value=25, step=5)

with exp_batt.expander(T["batt_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['batt_help']}</div>", unsafe_allow_html=True)
    battery_capacity_kwh = st.number_input(T["batt_c"], min_value=0, max_value=100, value=15, step=1)
    battery_eff = st.number_input(T["batt_eff"], min_value=70, max_value=100, value=92, step=1) / 100.0
    dod_limit = st.number_input(T["batt_dod"], min_value=50, max_value=100, value=80, step=5)
    soc_min = battery_capacity_kwh * (1 - (dod_limit / 100.0))
    soc_max = battery_capacity_kwh

with exp_load.expander(T["load_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['load_help']}</div>", unsafe_allow_html=True)
    house_area = st.number_input(T["load_area"], min_value=40, max_value=300, value=130, step=10)
    building_class = st.selectbox(T["load_class"], ["A4", "A3", "A2", "A1", "B", "C", "D"])
    occupants = st.number_input(T["load_occ"], min_value=1, max_value=8, value=4, step=1)
    heat_pump_cop = st.number_input(T["load_cop"], min_value=2.0, max_value=5.0, value=3.6, step=0.1, format="%.1f")
    has_ev = st.checkbox(T["load_ev_check"], value=True)

with exp_eco.expander(T["eco_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['eco_help']}</div>", unsafe_allow_html=True)
    cost_electricity = st.number_input(T["eco_cost"], min_value=0.01, max_value=2.00, value=0.30, step=0.01, format="%.2f")
    val_injection = st.number_input(T["eco_sell"], min_value=0.00, max_value=2.00, value=0.09, step=0.01, format="%.2f")
    capex_base = st.number_input(T["eco_capex"], min_value=1000, max_value=100000, value=11000, step=500)

# Profilazione EV Matrix
ev_hours_status = [False] * 24
if has_ev:
    st.markdown(f"### {T['ev_section_title']}")
    st.markdown(f"<div class='custom-note'>{T['ev_help']}</div>", unsafe_allow_html=True)
    
    c_p1, c_p2, c_p3, c_p4, c_p5, c_p6, c_p7 = st.columns(7)
    ev_capacity_kwh = c_p1.number_input(T["ev_cap"], min_value=20, max_value=150, value=65, step=5)
    ev_km_day = c_p2.number_input(T["ev_km"], min_value=10, max_value=150, value=50, step=5)
    ev_efficiency_wh_km = c_p3.number_input(T["ev_whkm"], min_value=120, max_value=250, value=165, step=5)
    v2h_power_kw = c_p4.number_input(T["ev_v2hp"], min_value=2.3, max_value=22.0, value=7.4, step=0.1, format="%.1f")
    v2h_eff = c_p5.number_input(T["ev_v2heff"], min_value=70, max_value=100, value=91, step=1) / 100.0
    ev_soc_init_pct = c_p6.number_input(T["ev_soc_init"], min_value=10, max_value=100, value=60, step=5)
    ev_soc_min_pct = c_p7.number_input(T["ev_soc_min"], min_value=10, max_value=50, value=30, step=5)
    
    c_cx1, c_cx2, c_cx3 = st.columns(3)
    capex_ev_s1 = c_cx1.number_input(T["ev_capex_s1"], value=650, step=50)
    capex_ev_s2 = c_cx2.number_input(T["ev_capex_s2"], value=1200, step=100)
    capex_ev_s3 = c_cx3.number_input(T["ev_capex_s3"], value=3400, step=200)
    
    daily_ev_demand_kwh = (ev_km_day * ev_efficiency_wh_km) / 1000.0
    ev_soc_travel_min = ev_capacity_kwh * (ev_soc_min_pct / 100.0)
        
    st.markdown(f"**{T['ev_grid_matrix']}**")
    cols_grid = st.columns(24)
    for h_idx in range(24):
        default_state = (h_idx >= 19 or h_idx < 7)
        ev_hours_status[h_idx] = cols_grid[h_idx].checkbox(f"{h_idx:02d}", value=default_state)
else:
    daily_ev_demand_kwh, ev_capacity_kwh = 0, 0
    capex_ev_s1, capex_ev_s2, capex_ev_s3 = 0, 0, 0

# --- LOCALIZZAZIONE GIS ---
st.markdown(f"### {T['gis_title']}")
col_loc1, col_loc2 = st.columns([1, 3])
with col_loc1:
    location_query = st.text_input(T["gis_search"], value="L'Aquila, Italia")
    if st.button(T["gis_btn"], use_container_width=True):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1"
            data = requests.get(geo_url, headers={"User-Agent": "EnergyGIS/1.0"}).json()
            if data: st.session_state.lat, st.session_state.lon = float(data[0]["lat"]), float(data[0]["lon"])
        except: st.error("Geocoding Error")
    lat, lon = st.session_state.lat, st.session_state.lon
    st.info(f"{T['gis_active']}\nLat: {lat:.4f}°\nLon: {lon:.4f}°")

with col_loc2:
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=6, tiles="CartoDB positron")
    folium.Marker([st.session_state.lat, st.session_state.lon]).add_to(m)
    map_data = st_folium(m, width="100%", height=150)

def setup_plot_style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=9, fontweight='600', color='#0F172A', loc='left', pad=8)
    ax.set_xlabel(xlabel, fontsize=7.5, color='#475569', labelpad=4)
    ax.set_ylabel(ylabel, fontsize=7.5, color='#475569', labelpad=4)
    ax.tick_params(axis='both', which='major', labelsize=7, labelcolor='#475569')
    ax.grid(True, linestyle='--', alpha=0.4, color='#CBD5E1', lw=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# --- ENGINE DI SIMULAZIONE GENERAZIONE E DOMANDA CONTINUA (8760 Ore) ---
def get_8760_profiles():
    pvgis_url = f"https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?lat={lat}&lon={lon}&peakpower={pv_power}&angle={pv_tilt}&aspect={pv_azimuth}&loss=14&outputformat=json"
    sol_m = [0]*12
    try:
        sol_data = requests.get(pvgis_url).json()
        sol_m = [m["E_m"] * (pv_efficiency / 20) for m in sol_data["outputs"]["monthly"]["fixed"]]
    except:
        sol_m = [pv_power * 110] * 12
        
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    pv_8760 = []
    m_idx = 0
    for m_days in days_in_months:
        m_energy = sol_m[m_idx]
        for d in range(m_days):
            for h in range(24):
                factor = max(0, math.sin((h - 6) / 12 * math.pi))
                pv_8760.append((m_energy / m_days) * factor / 6.5)
        m_idx += 1

    open_meteo_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2024-01-01&end_date=2024-12-31&hourly=windspeed_10m,temperature_2m"
    try:
        meteo_res = requests.get(open_meteo_url).json()
        wind_10m = meteo_res["hourly"]["windspeed_10m"]
        temp_2m = meteo_res["hourly"]["temperature_2m"]
    except:
        wind_10m = [4.5 + 2*math.sin(i/100) for i in range(8760)]
        temp_2m = [12 + 10*math.sin(i/500) for i in range(8760)]

    wt_8760 = []
    rotor_area = math.pi * (8 / 2) ** 2
    for v10 in wind_10m:
        vh = v10 * ((hub_height / 10) ** 0.14)
        p_wt = min((0.5 * 1.225 * rotor_area * 0.35 * (vh ** 3)) / 1000, wind_power_kw)
        wt_8760.append(max(0.0, p_wt))

    thermal_coefficients = {"A4": 10, "A3": 18, "A2": 28, "A1": 38, "B": 55, "C": 80, "D": 120}
    coeff = thermal_coefficients[building_class]
    
    base_load_annual = (1100 + occupants * 650) / 8760
    
    load_8760, heating_8760, cooling_8760, base_8760 = [], [], [], []
    
    for idx, t_ext in enumerate(temp_2m):
        h = idx % 24
        base_factor = (0.8 + 0.5 * math.exp(-((h - 20) ** 2) / 12))
        p_base = base_load_annual * base_factor
        
        # Heating demand active below 20°C
        p_heat = (
            max(0, 20 - t_ext)
            * coeff
            * house_area
            / 1000
            / heat_pump_cop
            / 24
        )

        # Cooling demand active above 25°C
        # Includes latent thermal component
        cooling_gain_factor = 0.75
        latent_factor = 1.10

        p_cool = (
            max(0, t_ext - 25)
            * (coeff * cooling_gain_factor)
            * house_area
            / 1000
            / (heat_pump_cop * 0.9)
            * latent_factor
            / 24
        )
        
        base_8760.append(p_base)
        heating_8760.append(p_heat)
        cooling_8760.append(p_cool)
        load_8760.append(p_base + p_heat + p_cool)

    return {
        "pv": pv_8760, "wt": wt_8760, "fer": [pv_8760[i] + wt_8760[i] for i in range(8760)],
        "load": load_8760, "heating": heating_8760, "cooling": cooling_8760, "base": base_8760
    }

# --- AVVIO COMPUTAZIONE GLOBALE ---
if st.button(T["run_btn"], type="primary", use_container_width=True):
    sim = get_8760_profiles()
    
    # 4 Giorni feriali reali di dettaglio impostati sul calendario sequenziale (ore annue)
    hours_indices = {
        T["inv"]: list(range(336, 360)),    # 15 Gennaio (Lunedì)
        T["pri"]: list(range(2520, 2544)),  # 15 Aprile (Lunedì)
        T["est"]: list(range(4680, 4704)),  # 15 Luglio (Lunedì)
        T["aut"]: list(range(6888, 6912))   # 15 Ottobre (Martedì)
    }

    annual_ev_kwh = (daily_ev_demand_kwh * 365) if has_ev else 0.0

    # Vettori per memorizzare l'autoconsumo orario effettivo
    ac_s1_hourly = [0.0] * 8760
    ac_s2_hourly = [0.0] * 8760
    ac_s3_hourly = [0.0] * 8760
    total_load_with_ev_s1 = [0.0] * 8760

    # --- SIMULAZIONE SCENARIO 1: Monodirezionale Standard ---
    soc_h_s1 = soc_min
    ac_s1, grid_s1, sell_s1 = 0, 0, 0
    soc_track_h_s1 = []
    soc_track_ev_s1 = []
    current_ev_soc_s1 = ev_capacity_kwh * (ev_soc_init_pct / 100.0) if has_ev else 0
    
    for i in range(8760):
        h = i % 24
        if has_ev and not ev_hours_status[h] and h == 12: 
            current_ev_soc_s1 = max(ev_capacity_kwh*0.1, current_ev_soc_s1 - daily_ev_demand_kwh)
            
        ev_load = (daily_ev_demand_kwh / ev_hours_status.count(True)) if (has_ev and ev_hours_status[h] and ev_hours_status.count(True) > 0) else 0.0
        tot_load = sim["load"][i] + ev_load
        total_load_with_ev_s1[i] = tot_load
        
        if has_ev and ev_hours_status[h] and ev_load > 0:
            current_ev_soc_s1 = min(ev_capacity_kwh, current_ev_soc_s1 + ev_load * v2h_eff)
            
        prod = sim["fer"][i]
        diretto = min(prod, tot_load)
        local_ac = diretto
        surplus, deficit = prod - diretto, tot_load - diretto
        
        if surplus > 0 and battery_capacity_kwh > 0:
            ch = min(surplus * battery_eff, soc_max - soc_h_s1)
            soc_h_s1 += ch
            surplus -= (ch / battery_eff)
            local_ac += ch
        sell_s1 += surplus
        
        if deficit > 0 and battery_capacity_kwh > 0:
            dh = min(deficit, (soc_h_s1 - soc_min) * battery_eff)
            soc_h_s1 -= (dh / battery_eff)
            local_ac += dh
            deficit -= dh
        grid_s1 += deficit
        
        ac_s1 += local_ac
        ac_s1_hourly[i] = local_ac
        soc_track_h_s1.append(soc_h_s1)
        soc_track_ev_s1.append(current_ev_soc_s1)

    if has_ev:
        # --- SIMULAZIONE SCENARIO 2: Smart Charging ---
        soc_h_s2 = soc_min
        current_ev_soc_s2 = ev_capacity_kwh * (ev_soc_init_pct / 100.0)
        ac_s2, grid_s2, sell_s2 = 0, 0, 0
        soc_track_h_s2 = []
        soc_track_ev_s2 = []
        
        for i in range(8760):
            h = i % 24
            if not ev_hours_status[h] and h == 12: 
                current_ev_soc_s2 = max(ev_capacity_kwh*0.1, current_ev_soc_s2 - daily_ev_demand_kwh)
                
            prod, house_load = sim["fer"][i], sim["load"][i]
            diretto = min(prod, house_load)
            local_ac = diretto
            surplus = prod - diretto
            
            if surplus > 0:
                if battery_capacity_kwh > 0 and soc_h_s2 < soc_max:
                    ch = min(surplus * battery_eff, soc_max - soc_h_s2)
                    soc_h_s2 += ch
                    surplus -= (ch / battery_eff)
                    local_ac += ch
                if ev_hours_status[h] and surplus > 0 and current_ev_soc_s2 < ev_capacity_kwh:
                    ch_ev = min(min(v2h_power_kw, surplus) * v2h_eff, ev_capacity_kwh - current_ev_soc_s2)
                    current_ev_soc_s2 += ch_ev
                    surplus -= (ch_ev / v2h_eff)
                    local_ac += ch_ev
                sell_s2 += surplus
                deficit = 0
            else:
                deficit = house_load - prod
                if battery_capacity_kwh > 0 and soc_h_s2 > soc_min:
                    dh = min(deficit, (soc_h_s2 - soc_min) * battery_eff)
                    soc_h_s2 -= (dh / battery_eff)
                    local_ac += dh
                    deficit -= dh
                if ev_hours_status[h] and current_ev_soc_s2 < ev_soc_travel_min:
                    f_ch = min(v2h_power_kw, (ev_soc_travel_min - current_ev_soc_s2) / v2h_eff)
                    current_ev_soc_s2 += f_ch * v2h_eff
                    deficit += f_ch
                grid_s2 += deficit
                
            ac_s2 += local_ac
            ac_s2_hourly[i] = local_ac
            soc_track_h_s2.append(soc_h_s2)
            soc_track_ev_s2.append(current_ev_soc_s2)

        # --- SIMULAZIONE SCENARIO 3: Bidirezionale V2H ---
        soc_h_s3 = soc_min
        current_ev_soc_s3 = ev_capacity_kwh * (ev_soc_init_pct / 100.0)
        ac_s3, grid_s3, sell_s3 = 0, 0, 0
        soc_track_h_s3 = []
        soc_track_ev_s3 = []
        
        for i in range(8760):
            h = i % 24
            if not ev_hours_status[h] and h == 12: 
                current_ev_soc_s3 = max(ev_capacity_kwh*0.1, current_ev_soc_s3 - daily_ev_demand_kwh)
                
            prod, house_load = sim["fer"][i], sim["load"][i]
            diretto = min(prod, house_load)
            local_ac = diretto
            surplus, deficit = prod - diretto, house_load - diretto
            
            if surplus > 0:
                if ev_hours_status[h] and current_ev_soc_s3 < ev_capacity_kwh:
                    ch_ev = min(min(v2h_power_kw, surplus) * v2h_eff, ev_capacity_kwh - current_ev_soc_s3)
                    current_ev_soc_s3 += ch_ev
                    surplus -= (ch_ev / v2h_eff)
                    local_ac += ch_ev
                if battery_capacity_kwh > 0 and soc_h_s3 < soc_max:
                    ch = min(surplus * battery_eff, soc_max - soc_h_s3)
                    soc_h_s3 += ch
                    surplus -= (ch / battery_eff)
                    local_ac += ch
                sell_s3 += surplus
            elif deficit > 0:
                if ev_hours_status[h] and current_ev_soc_s3 > ev_soc_travel_min:
                    dh_v2h = min(min(v2h_power_kw, deficit), (current_ev_soc_s3 - ev_soc_travel_min) * v2h_eff)
                    current_ev_soc_s3 -= (dh_v2h / v2h_eff)
                    deficit -= dh_v2h
                    local_ac += dh_v2h
                if deficit > 0 and battery_capacity_kwh > 0 and soc_h_s3 > soc_min:
                    dh = min(deficit, (soc_h_s3 - soc_min) * battery_eff)
                    soc_h_s3 -= (dh / battery_eff)
                    local_ac += dh
                    deficit -= dh
                grid_s3 += deficit
                
            ac_s3 += local_ac
            ac_s3_hourly[i] = local_ac
            soc_track_h_s3.append(soc_h_s3)
            soc_track_ev_s3.append(current_ev_soc_s3)

    # Aggregazione mensile esatta
    monthly_load_agg = [0]*12
    monthly_load_with_ev_s1_agg = [0]*12
    monthly_ac_s1_agg, monthly_ac_s2_agg, monthly_ac_s3_agg = [0]*12, [0]*12, [0]*12
    monthly_sol_agg, monthly_wind_agg = [0]*12, [0]*12
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    c_idx = 0
    for m in range(12):
        h_count = days_in_months[m] * 24
        monthly_load_agg[m] = sum(sim["load"][c_idx : c_idx + h_count])
        monthly_load_with_ev_s1_agg[m] = sum(total_load_with_ev_s1[c_idx : c_idx + h_count])
        monthly_sol_agg[m] = sum(sim["pv"][c_idx : c_idx + h_count])
        monthly_wind_agg[m] = sum(sim["wt"][c_idx : c_idx + h_count])
        
        monthly_ac_s1_agg[m] = sum(ac_s1_hourly[c_idx : c_idx + h_count])
        if has_ev:
            monthly_ac_s2_agg[m] = sum(ac_s2_hourly[c_idx : c_idx + h_count])
            monthly_ac_s3_agg[m] = sum(ac_s3_hourly[c_idx : c_idx + h_count])
        c_idx += h_count

    # Finanza 8760h coerente
    savings_s1 = (ac_s1 * cost_electricity) + (sell_s1 * val_injection)
    capex_s1_tot = capex_base + capex_ev_s1
    payback_s1 = capex_s1_tot / savings_s1 if savings_s1 > 0 else 99
    
    if has_ev:
        savings_s2 = (ac_s2 * cost_electricity) + (sell_s2 * val_injection)
        savings_s3 = (ac_s3 * cost_electricity) + (sell_s3 * val_injection)
        capex_s2_tot = capex_base + capex_ev_s2
        capex_s3_tot = capex_base + capex_ev_s3
        payback_s2 = capex_s2_tot / savings_s2 if savings_s2 > 0 else 99
        payback_s3 = capex_s3_tot / savings_s3 if savings_s3 > 0 else 99
    
    total_demand_annual = sum(sim["load"]) + annual_ev_kwh
    total_generation_annual = sum(sim["fer"])

    # --- RENDERIZZAZIONE INTERFACCIA RISULTATI ---
    st.markdown(f"## {T['results_title']}")
    st.markdown(f"<div class='custom-note-result'>{T['results_help']}</div>", unsafe_allow_html=True)
    
    with st.expander(T["guide_metrics_title"], expanded=False):
        st.markdown(T["guide_metrics_text"])
        
    sc_rate_s1 = (ac_s1 / total_generation_annual) * 100 if total_generation_annual > 0 else 0
    ss_rate_s1 = (ac_s1 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    
    if has_ev:
        sc_rate_s2 = (ac_s2 / total_generation_annual) * 100 if total_generation_annual > 0 else 0
        ss_rate_s2 = (ac_s2 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
        sc_rate_s3 = (ac_s3 / total_generation_annual) * 100 if total_generation_annual > 0 else 0
        ss_rate_s3 = (ac_s3 / total_demand_annual) * 100 if total_demand_annual > 0 else 0

        tab1, tab2, tab3 = st.tabs(["🛑 Scenario 1: Monodirezionale Standard", "☀️ Scenario 2: Smart Charging", "🔄 Scenario 3: Bidirectional V2H"])
    else:
        tab1, = st.tabs(["🏠 Configurazione Impianto Base (Senza EV)"])

    with tab1:
        st.markdown(f"### 📊 Bilancio Energetico - {'Configurazione Passiva' if has_ev else 'Impianto Base'}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["kpi_ac"], f"{ac_s1:.0f} kWh"); c2.metric("Indice Autoconsumo", f"{sc_rate_s1:.1f} %"); c3.metric("Autosufficienza", f"{ss_rate_s1:.1f} %"); c4.metric("Prelievo da Rete", f"{grid_s1:.0f} kWh")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric(T["kpi_bill_savings"], f"{savings_s1:.2f} €/anno"); ec2.metric(T["kpi_payback"], f"{payback_s1:.1f} Anni"); ec3.metric("CO₂ Evitata", f"{ac_s1*0.41:.1f} kg/anno")
    
    if has_ev:
        with tab2:
            st.markdown("### 📊 Bilancio Energetico - Smart Charging")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(T["kpi_ac"], f"{ac_s2:.0f} kWh"); c2.metric("Indice Autoconsumo", f"{sc_rate_s2:.1f} %"); c3.metric("Autosufficienza", f"{ss_rate_s2:.1f} %"); c4.metric("Prelievo da Rete", f"{grid_s2:.0f} kWh")
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric(T["kpi_bill_savings"], f"{savings_s2:.2f} €/anno"); ec2.metric(T["kpi_payback"], f"{payback_s2:.1f} Anni"); ec3.metric("CO₂ Evitata", f"{ac_s2*0.41:.1f} kg/anno")
        with tab3:
            st.markdown("### 📊 Bilancio Energetico - Ecosistema V2H")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(T["kpi_ac"], f"{ac_s3:.0f} kWh"); c2.metric("Indice Autoconsumo", f"{sc_rate_s3:.1f} %"); c3.metric("Autosufficienza", f"{ss_rate_s3:.1f} %"); c4.metric("Prelievo da Rete", f"{grid_s3:.0f} kWh")
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric(T["kpi_bill_savings"], f"{savings_s3:.2f} €/anno"); ec2.metric(T["kpi_payback"], f"{payback_s3:.1f} Anni"); ec3.metric("CO₂ Evitata", f"{ac_s3*0.41:.1f} kg/anno")

    # Matrice comparativa globale
    st.markdown("### 📈 Matrice Comparativa Tecno-Economica Globale (8760h)")
    with st.expander(T["guide_table_title"], expanded=False):
        st.markdown(T["guide_table_text"])
        
    if has_ev:
        summary_data = {
            "Parametro Energetico / Finanziario": [
                "Fabbisogno Annuo Lordo Utente (kWh)", "Volume di Autoconsumo Locale Reale (kWh)", "Energia Eccedentaria Immessa in Rete (kWh)",
                "Energia Totale Prelevata dalla Rete (kWh)", "Grado di Autoconsumo (Self-Consumption Rate)", "Grado di Indipendenza Energetica (Autosufficienza)",
                "Investimento Iniziale Stimato (CAPEX Hardware)", "Flusso Economico Positivo Annuale (€/anno)", "Tempo di Ritorno dell'Investimento (PBP)"
            ],
            "1. Monodirezionale Standard": [f"{total_demand_annual:.0f}", f"{ac_s1:.0f}", f"{sell_s1:.0f}", f"{grid_s1:.0f}", f"{sc_rate_s1:.1f}%", f"{ss_rate_s1:.1f}%", f"{capex_s1_tot:.0f} €", f"{savings_s1:.2f} €", f"{payback_s1:.1f} anni"],
            "2. Smart Charging": [f"{total_demand_annual:.0f}", f"{ac_s2:.0f}", f"{sell_s2:.0f}", f"{grid_s2:.0f}", f"{sc_rate_s2:.1f}%", f"{ss_rate_s2:.1f}%", f"{capex_s2_tot:.0f} €", f"{savings_s2:.2f} €", f"{payback_s2:.1f} anni"],
            "3. Bidirezionale V2H/V2L": [f"{total_demand_annual:.0f}", f"{ac_s3:.0f}", f"{sell_s3:.0f}", f"{grid_s3:.0f}", f"{sc_rate_s3:.1f}%", f"{ss_rate_s3:.1f}%", f"{capex_s3_tot:.0f} €", f"{savings_s3:.2f} €", f"{payback_s3:.1f} anni"]
        }
    else:
        summary_data = {
            "Parametro Energetico / Finanziario": [
                "Fabbisogno Edificio Annuo Lordo (kWh)", "Volume di Autoconsumo Locale Reale (kWh)", "Energia Eccedentaria Immessa in Rete (kWh)",
                "Energia Totale Prelevata dalla Rete (kWh)", "Grado di Autoconsumo (Self-Consumption Rate)", "Grado di Indipendenza Energetica (Autosufficienza)",
                "Investimento Iniziale Stimato (CAPEX Impianto)", "Flusso Economico Positivo Annuale (€/anno)", "Tempo di Ritorno dell'Investimento (PBP)"
            ],
            "Impianto Standalone": [f"{total_demand_annual:.0f}", f"{ac_s1:.0f}", f"{sell_s1:.0f}", f"{grid_s1:.0f}", f"{sc_rate_s1:.1f}%", f"{ss_rate_s1:.1f}%", f"{capex_s1_tot:.0f} €", f"{savings_s1:.2f} €", f"{payback_s1:.1f} anni"]
        }
    st.table(summary_data)

    # Macro Bilanci
    st.markdown("### 📊 Macro Bilanci Energetici su Base Mensile")
    with st.expander(T["guide_macro_charts_title"], expanded=False):
        st.markdown(T["guide_macro_charts_text"])
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_mac_gen, ax_mac_gen = plt.subplots(figsize=(6, 2.2), dpi=200)
        ax_mac_gen.plot(range(1, 13), monthly_sol_agg, label="Fotovoltaico", color="#D97706", lw=1.2)
        ax_mac_gen.bar(range(1, 13), monthly_wind_agg, label="Eolico", color="#2563EB", alpha=0.15, width=0.35)
        setup_plot_style(ax_mac_gen, T["chart_gen_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax_mac_gen.legend(fontsize=6.5, frameon=False)
        st.pyplot(fig_mac_gen)
    with col_g2:
        fig_mac_load, ax_mac_load = plt.subplots(figsize=(6, 2.2), dpi=200)
        ax_mac_load.plot(range(1, 13), monthly_load_with_ev_s1_agg, color="#DC2626", lw=1.6)
        setup_plot_style(ax_mac_load, T["chart_load_title"], T["chart_x_month"], T["chart_y_kwh"])
        st.pyplot(fig_mac_load)

    # --- SEZIONE GIORNI TIPICI REALI CALENDATORIALI ---
    st.markdown("---")
    st.subheader(T["season_title"])
    with st.expander(T["guide_hourly_charts_title"], expanded=False):
        st.markdown(T["guide_hourly_charts_text"])

    for season_name, idx_list in hours_indices.items():
        st.markdown(f"#### {season_name}")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            fig_f1, ax_f1 = plt.subplots(figsize=(6, 2.3), dpi=200)

            # RES generation
            ax_f1.plot(
                range(24),
                [sim["fer"][idx] for idx in idx_list],
                label=T["legend_fer"],
                color="#059669",
                lw=1.4
            )

            # Base load + heating
            ax_f1.plot(
                range(24),
                [sim["base"][idx] + sim["heating"][idx] for idx in idx_list],
                label=T["legend_base_heat"],
                color="#475569",
                lw=1.2
            )

            # Cooling demand profile
            cooling_profile = [sim["cooling"][idx] for idx in idx_list]

            ax_f1.fill_between(
                range(24),
                [0 for _ in range(24)],
                cooling_profile,
                label=T["legend_ac"],
                color="#38BDF8",
                alpha=0.35
            )

            ax_f1.plot(
                range(24),
                cooling_profile,
                label=T["legend_ac_power"],
                color="#0284C7",
                lw=1.3,
                linestyle="--"
            )

            setup_plot_style(ax_f1, f"{T['chart_hourly_title']}", T["chart_h_x"], "Potenza [kW]")
            ax_f1.legend(fontsize=6.5, frameon=False, loc="upper left")
            st.pyplot(fig_f1)
            
        with col_chart2:
            fig_f2, ax_f2 = plt.subplots(figsize=(6, 2.3), dpi=200)

            # EV connection overlay
            if has_ev:
                ev_connection_profile = [
                    100 if ev_hours_status[h] else 0
                    for h in range(24)
                ]

                ax_f2.fill_between(
                    range(24),
                    0,
                    ev_connection_profile,
                    color="#A855F7",
                    alpha=0.08,
                    label=T["legend_ev_conn"]
                )
            target_soc_h = soc_track_h_s3 if has_ev else soc_track_h_s1
            h_soc_pct = [(target_soc_h[idx] / battery_capacity_kwh * 100) if battery_capacity_kwh > 0 else 0 for idx in idx_list]
            
            ax_f2.plot(range(24), h_soc_pct, label=T["legend_soc_h"], color='#D97706', lw=1.3, marker='s', markersize=2)
            if has_ev:
                ev_soc_s1_pct = [(soc_track_ev_s1[idx] / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for idx in idx_list]
                ev_soc_s2_pct = [(soc_track_ev_s2[idx] / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for idx in idx_list]
                ev_soc_s3_pct = [(soc_track_ev_s3[idx] / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for idx in idx_list]
                
                ax_f2.plot(range(24), ev_soc_s1_pct, label="SoC EV (S1 Standard)", color='#EF4444', lw=1.3, marker='o', markersize=2, alpha=0.8)
                ax_f2.plot(range(24), ev_soc_s2_pct, label="SoC EV (S2 Smart)", color='#3B82F6', lw=1.3, marker='^', markersize=2, alpha=0.8)
                ax_f2.plot(range(24), ev_soc_s3_pct, label="SoC EV (S3 V2H)", color='#10B981', lw=1.3, marker='v', markersize=2, alpha=0.9)
            setup_plot_style(ax_f2, f"{T['chart_soc_title']}", T["chart_h_x"], "State of Charge [%]")
            ax_f2.set_ylim(-5, 105)
            ax_f2.legend(fontsize=6.5, frameon=False, loc="lower left")
            st.pyplot(fig_f2)

    # --- SEZIONE: GRAFICI ANNUALI CONTINUI A 8760 ORE ---
    st.markdown("---")
    st.subheader("📈 Analisi delle Curve Continue Annuali (Profilo Completo 8760 Ore)")
    with st.expander(T["guide_8760_charts_title"], expanded=False):
        st.markdown(T["guide_8760_charts_text"])
        
    col_ann1, col_ann2 = st.columns(2)
    with col_ann1:
        fig_ann_flows, ax_ann_flows = plt.subplots(figsize=(7, 2.5), dpi=200)

        ax_ann_flows.plot(
            range(8760),
            sim["fer"],
            label="Generazione FER Totale",
            color="#10B981",
            alpha=0.6,
            lw=0.4
        )

        ax_ann_flows.plot(
            range(8760),
            total_load_with_ev_s1,
            label="Carico Totale Utente",
            color="#EF4444",
            alpha=0.45,
            lw=0.45
        )

        ax_ann_flows.plot(
            range(8760),
            sim["cooling"],
            label=T["legend_ac_power"],
            color="#0EA5E9",
            alpha=0.9,
            lw=0.6
        )
        setup_plot_style(ax_ann_flows, "Andamento Continuo Potenze (8760 h)", "Ore dell'Anno [1-8760]", "Potenza [kW]")
        ax_ann_flows.legend(fontsize=6.5, frameon=False, loc="upper right")
        st.pyplot(fig_ann_flows)
        
    with col_ann2:
        fig_ann_soc, ax_ann_soc = plt.subplots(figsize=(7, 2.5), dpi=200)
        ref_soc_track_h = soc_track_h_s3 if has_ev else soc_track_h_s1
        h_soc_annual_pct = [(v / battery_capacity_kwh * 100) if battery_capacity_kwh > 0 else 0 for v in ref_soc_track_h]
        ax_ann_soc.plot(range(8760), h_soc_annual_pct, label="SoC BESS Casa", color="#D97706", lw=0.5)
        
        if has_ev:

            annual_ev_connection = [
                100 if ev_hours_status[i % 24] else 0
                for i in range(8760)
            ]

            ax_ann_soc.fill_between(
                range(8760),
                0,
                annual_ev_connection,
                color="#A855F7",
                alpha=0.04,
                label=T["legend_ev_conn"]
            )

            ev_soc_s1_pct = [(v / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for v in soc_track_ev_s1]
            ev_soc_s2_pct = [(v / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for v in soc_track_ev_s2]
            ev_soc_s3_pct = [(v / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for v in soc_track_ev_s3]
            
            ax_ann_soc.plot(range(8760), ev_soc_s1_pct, label="SoC EV (S1 Standard)", color="#EF4444", lw=0.4, alpha=0.6)
            ax_ann_soc.plot(range(8760), ev_soc_s2_pct, label="SoC EV (S2 Smart)", color="#3B82F6", lw=0.4, alpha=0.6)
            ax_ann_soc.plot(range(8760), ev_soc_s3_pct, label="SoC EV (S3 V2H)", color="#10B981", lw=0.4, alpha=0.7)
            
        setup_plot_style(ax_ann_soc, "Evoluzione dello Stato di Carica (8760 h)", "Ore dell'Anno [1-8760]", "Stato di Carica [%]")
        ax_ann_soc.set_ylim(-5, 105)
        ax_ann_soc.legend(fontsize=6.5, frameon=False, loc="lower left")
        st.pyplot(fig_ann_soc)

    # Sintesi Annuale Istogramma Comparativo
    st.markdown("---")
    st.subheader(T["final_chart_title"])
    fig12, ax12 = plt.subplots(figsize=(12, 2.4), dpi=200)
    x_idx = range(1, 13)
    ax12.bar([x - 0.22 for x in x_idx], monthly_load_with_ev_s1_agg, width=0.18, label=T["final_l1"], color='#94A3B8', alpha=0.25)
    ax12.bar([x - 0.07 for x in x_idx], monthly_ac_s1_agg, width=0.15, label=T["final_l2"] if has_ev else "Autoconsumo", color='#EF4444', alpha=0.7)
    
    if has_ev:
        ax12.bar([x + 0.07 for x in x_idx], monthly_ac_s2_agg, width=0.15, label=T["final_l3"], color='#3B82F6', alpha=0.8)
        ax12.bar([x + 0.22 for x in x_idx], monthly_ac_s3_agg, width=0.15, label=T["final_l4"], color='#10B981', alpha=0.9)
        
    setup_plot_style(ax12, T["final_chart_sub"], T["final_x"], T["chart_y_kwh"])
    ax12.set_xticks(x_idx)
    ax12.set_xticklabels(T["months_labels"])
    ax12.legend(fontsize=7, frameon=False, loc="upper right")
    st.pyplot(fig12)

# --- FOOTER ---
st.markdown("---")
st.caption("RES-EV Microgrid Core Platform | 8760-Hour Chronological Solver | Engine: PVGIS API & Open-Meteo Weather Dataset")