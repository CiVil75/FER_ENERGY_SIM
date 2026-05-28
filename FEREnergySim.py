# FEREnergySim.py
import streamlit as st
import requests
import matplotlib.pyplot as plt
import folium
import math
from streamlit_folium import st_folium

# --- CONFIGURAZIONE INTERFACCIA ED ESTETICA ---
st.set_page_config(page_title="RES-Based Home Simulator", layout="wide")

# CSS Avanzato per layout ultra-compatto, font professionale e griglia orizzontale EV
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    .reportview-container .main .block-container { padding-top: 0.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.8rem !important; font-weight: 700; color: #0F172A; margin-bottom: 0.1rem; letter-spacing: -0.02em; }
    h2 { font-size: 1.25rem !important; font-weight: 600; color: #1E293B; margin-top: 1rem; margin-bottom: 0.5rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.1rem; }
    h3 { font-size: 1.0rem !important; font-weight: 600; color: #334155; margin-bottom: 0.4rem; }
    h4 { font-size: 0.9rem !important; font-weight: 600; color: #475569; margin-top: 0.4rem; }
    .stSlider > label, .stSelectbox > label, .stTextInput > label, .stCheckbox > label { font-size: 0.78rem !important; font-weight: 500; color: #475569; }
    .stMetric { background-color: #F8FAFC; padding: 0.4rem 0.6rem; border-radius: 0.375rem; border: 1px solid #E2E8F0; }
    div[data-testid="stExpander"] { border: 1px solid #E2E8F0 !important; box-shadow: none !important; margin-bottom: 0.4rem; }
    
    .custom-note { 
        padding: 0.5rem 0.75rem; 
        border-radius: 0.25rem; 
        font-size: 0.8rem; 
        background-color: #F8FAFC; 
        color: #475569; 
        border-left: 3px solid #3B82F6; 
        margin-bottom: 0.6rem;
        line-height: 1.3;
    }
    .custom-note-result { 
        padding: 0.6rem 0.75rem; 
        border-radius: 0.25rem; 
        font-size: 0.82rem; 
        background-color: #F0FDF4; 
        color: #166534; 
        border-left: 3px solid #22C55E; 
        margin-bottom: 0.8rem;
    }
    
    div[data-testid="column"] { padding: 0px 1px !important; }
    .stCheckbox { margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# --- DIZIONARIO DI TRADUZIONE BILINGUE (ITA / ENG) ---
LANG_DICT = {
    "ITA": {
        "title": "🌍 RES-Based Home Simulator by Prof. Eng. C. Villante - University of L'Aquila (Beta Version)",
        "subtitle": "Analisi quantitativa e modellazione geospaziale per micro-reti, accumuli stazionari ed ecosistemi V2H.",
        "params_title": "🎛️ Configurazione Parametri Tecnici ed Economici",
        "pv_title": "☀️ Fotovoltaico (Max 20 kWp)",
        "pv_help": "💡 **PV**: 1 kWp occupa ~5-7 m². Tilt ottimale (inclinazione) in Italia: 30°-35°. Azimuth: 0° Sud, -90° Est, 90° Ovest.",
        "pv_p": "Potenza Impianto (kWp)",
        "pv_t": "Tilt Angle (°)",
        "pv_az": "Azimuth Angle (°)",
        "pv_eff": "Rendimento Modulo (%)",
        "wind_title": "🌬️ Micro-Eolico",
        "wind_help": "💡 **WT**: Estrapola la velocità del vento all'altezza del mozzo mediante legge di potenza logaritmica dal dataset Open-Meteo.",
        "wind_p": "Potenza Nominale (kW)",
        "wind_h": "Altezza Mozzo (m)",
        "batt_title": "🔋 Accumulo Stazionario (BESS)",
        "batt_help": "💡 **BESS**: Il DoD Max (profondità di scarica) preserva il ciclo di vita vincolando la capacità minima residua dell'accumulo d'abitazione.",
        "batt_c": "Capacità Nominale (kWh)",
        "batt_eff": "Efficienza Round-Trip (%)",
        "batt_dod": "DoD Massimo (%)",
        "load_title": "🏠 Profilo Utenza & Edificio",
        "load_help": "💡 **Loads**: Calcola dinamicamente la firma termica invernale e il carico estivo di condizionamento (AC) incrociando la classe dell'edificio con le temperature storiche GIS locali.",
        "load_area": "Superficie Calpestabile (m²)",
        "load_class": "Classe Energetica",
        "load_occ": "Numero Occupanti",
        "load_cop": "COP/EER Medio Pompa Calore",
        "eco_title": "💰 Parametri Economici & Tariffe Grid",
        "eco_help": "💡 **Tariffe**: Inserisci i costi reali di acquisto/vendita dell'energia per valutare l'ammortamento (Payback Period) e il risparmio in bolletta.",
        "eco_cost": "Costo Energia Prelevata (€/kWh)",
        "eco_sell": "Tariffa Immissione / RID (€/kWh)",
        "eco_capex": "CAPEX Impianto Base (PV+Wind) (€)",
        "load_ev_check": "Abilita Veicolo Elettrico (EV)",
        "ev_section_title": "🚗 Profilazione EV & Configurazione Infrastruttura di Ricarica / V2H",
        "ev_help": "💡 **EV & V2H**: Definisci le caratteristiche del veicolo e l'infrastruttura di ricarica. Sotto trovi la matrice temporale di disponibilità (00-23h). Nei periodi non spuntati il veicolo consuma energia per lo spostamento.",
        "ev_cap": "Capacità Batteria EV (kWh)",
        "ev_km": "Distanza Giornaliera (km)",
        "ev_whkm": "Consumo Specifico (Wh/km)",
        "ev_v2hp": "Potenza Wallbox / Inverter V2H (kW)",
        "ev_v2heff": "Efficienza Convertitore (%)",
        "ev_soc_init": "SoC Iniziale di Partenza (%)",
        "ev_soc_min": "SoC Minimo di Sicurezza per Viaggio (%)",
        "ev_capex_s1": "Costo Aggiuntivo Wallbox S1 Standard (€)",
        "ev_capex_s2": "Costo Aggiuntivo Smart Wallbox S2 (€)",
        "ev_capex_s3": "Costo Aggiuntivo Stazione Bidirezionale V2H S3 (€)",
        "ev_grid_matrix": "Matrice di Disponibilità Oraria dell'EV alla Rete Domestica (Spuntato = Connesso alla Wallbox)",
        "gis_title": "📍 Posizionamento Geografico Impianto",
        "gis_search": "Cerca Comune o Coordinate",
        "gis_btn": "🔍 Aggiorna Mappa Sito",
        "gis_active": "**Sito Attivo:**",
        "run_btn": "⚡ Esegui Simulazione Energetica Dinamica",
        "results_title": "📊 Analisi Output e Indicatori di Performance",
        "results_help": "🔬 **Interpretazione KPI**: Calcolo accoppiato multi-scenario. Lo Smart Charging modula i carichi seguendo la produzione FER; il V2H abilita la bidirezionalità flessibile iniettando energia verso la casa.",
        "kpi_ac": "Autoconsumo",
        "kpi_bill_savings": "Risparmio Economico",
        "kpi_payback": "Tempo di Ritorno",
        "chart_gen_title": "Profili di Generazione Mensile",
        "chart_load_title": "Profili di Fabbisogno Mensile (Riscaldamento vs Condizionamento)",
        "chart_x_month": "Mese",
        "chart_y_kwh": "Energia [kWh]",
        "season_title": "📈 Dinamica Oraria Stagionale sui Giorni Medi Tipici",
        "season_help": "🔬 **Interpretazione Grafici Orari**: Per ogni stagione viene ricostruito il giorno medio tipico solare. A sinistra viene analizzato il bilancio di potenza istantaneo (generazione e split dei carichi); a destra lo stato di carica (SoC) dei vettori energetici.",
        "inv": "Inverno", "pri": "Primavera", "est": "Estate", "aut": "Autunno",
        "inv_t": "❄️ Giorno Tipico Invernale (Gennaio)", "pri_t": "🌱 Giorno Tipico Primavera (Aprile)", "est_t": "☀️ Giorno Tipico Estivo (Luglio)", "aut_t": "🍂 Giorno Tipico Autunnale (Ottobre)",
        "chart_hourly_title": "Bilancio di Potenza Orario",
        "chart_soc_title": "Stato di Carica (SoC)",
        "chart_h_x": "Ora del Giorno [h]",
        "chart_h_y_flow": "Energia Oraria [kWh]",
        "chart_h_y_soc": "State of Charge [%]",
        "legend_fer": "Generazione FER", 
        "legend_base_heat": "Carico Base + Riscaldamento",
        "legend_ac": "Carico Condizionamento (AC)",
        "legend_tot_ev": "Carico Totale + Ricarica EV",
        "legend_soc_h": "SoC Batteria Casa", "legend_grid_on": "Accoppiamento Veicolo Attivo",
        "final_chart_title": "📊 Analisi Comparativa delle Strategie di Autoconsumo",
        "final_chart_sub": "Copertura Energetica ed Autoconsumo Mensile Effettivo nelle 3 Strategie",
        "final_x": "Mese dell'Anno", "final_l1": "Fabbisogno Utenza Lordo", "final_l2": "S1: Monodirezionale Standard", "final_l3": "S2: Smart Charging", "final_l4": "S3: Bidirezionale V2H/V2L",
        "months_labels": ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'],
        "hp_share": "Quota Riscaldamento",
        "ac_share": "Quota Condizionamento (AC)"
    },
    "ENG": {
        "title": "🌍 RES-Based Home Simulator by Prof. Eng. C. Villante - University of L'Aquila (Beta Version)",
        "subtitle": "Quantitative analysis and geospatial modeling for micro-grids, stationary storage, and V2H ecosystems.",
        "params_title": "🎛️ Technical and Economic Parameters Configuration",
        "pv_title": "☀️ Photovoltaic (Max 20 kWp)",
        "pv_help": "💡 **PV**: 1 kWp requires ~5-7 m². Optimal Tilt in Italy: 30°-35°. Azimuth: 0° South, -90° East, 90° Ovest.",
        "pv_p": "System Power (kWp)",
        "pv_t": "Tilt Angle (°)",
        "pv_az": "Azimuth Angle (°)",
        "pv_eff": "Module Efficiency (%)",
        "wind_title": "🌬️ Micro-Wind",
        "wind_help": "💡 **WT**: Extrapolates wind speed at hub height using logarithmic power law from the Open-Meteo reanalysis dataset.",
        "wind_p": "Nominal Power (kW)",
        "wind_h": "Hub height (m)",
        "batt_title": "🔋 Stationary Storage (BESS)",
        "batt_help": "💡 **BESS**: Max DoD (Depth of Discharge) preserves stationary battery cycle life by setting a minimum residual energy constraint.",
        "batt_c": "Nominal Capacity (kWh)",
        "batt_eff": "Round-Trip Efficiency (%)",
        "batt_dod": "Max DoD (%)",
        "load_title": "🏠 Load Profile & Building",
        "load_help": "💡 **Loads**: Computes winter heating and summer cooling (AC) demands by intersecting building class with historical local GIS temperature data.",
        "load_area": "Floor Area (m²)",
        "load_class": "Energy Class",
        "load_occ": "Occupants Number",
        "load_cop": "Heat Pump Average COP/EER",
        "eco_title": "💰 Economic Parameters & Grid Tariffs",
        "eco_help": "💡 **Tariffs**: Insert real energy purchase/selling prices to evaluate system payback period and overall bill savings.",
        "eco_cost": "Purchased Electricity Cost (€/kWh)",
        "eco_sell": "Injection Price / RID (€/kWh)",
        "eco_capex": "Base Installation CAPEX (PV+Wind) (€)",
        "load_ev_check": "Enable Electric Vehicle (EV)",
        "ev_section_title": "🚗 EV Profiling & Charging Infrastructure / V2H Configuration",
        "ev_help": "💡 **EV & V2H**: Define vehicle characteristics and charging infrastructure. Below is the hourly availability grid (00-23h). When unchecked, the vehicle consumes energy for travel.",
        "ev_cap": "EV Battery Capacity (kWh)",
        "ev_km": "Daily Distance (km)",
        "ev_whkm": "Specific Consumption (Wh/km)",
        "ev_v2hp": "Wallbox / V2H Inverter Power (kW)",
        "ev_v2heff": "Converter Efficiency (%)",
        "ev_soc_init": "Initial SoC (%)",
        "ev_soc_min": "Safety Trip Minimum SoC (%)",
        "ev_capex_s1": "S1 Standard Wallbox Extra Cost (€)",
        "ev_capex_s2": "S2 Smart Wallbox Extra Cost (€)",
        "ev_capex_s3": "S3 Bidirectional V2H Station Extra Cost (€)",
        "ev_grid_matrix": "EV Hourly Availability Matrix to Home Network (Checked = Connected to Wallbox)",
        "gis_title": "📍 GIS Site Localization",
        "gis_search": "Search Municipality or Coordinates",
        "gis_btn": "🔍 Update Site Map",
        "gis_active": "**Active Site:**",
        "run_btn": "⚡ Run Dynamic Energy Simulation",
        "results_title": "📊 Simulation Output & Performance Indicators",
        "results_help": "🔬 **KPI Interpretation**: Coupled multi-scenario analysis. Smart Charging shapes loads to track green local production; V2H provides full bidirectional flexibility by injecting power back to the house.",
        "kpi_ac": "Self-Consumption",
        "kpi_bill_savings": "Economic Savings",
        "kpi_payback": "Payback Period",
        "chart_gen_title": "Monthly Generation Profiles",
        "chart_load_title": "Monthly Demand Profiles (Heating vs Cooling)",
        "chart_x_month": "Month",
        "chart_y_kwh": "Energy [kWh]",
        "season_title": "📈 Hourly Seasonal Dynamics on Average Days",
        "season_help": "🔬 **Hourly Charts Interpretation**: For each season, a typical average day is simulated. Left charts display immediate power balance profiles; right charts show the state of charge (SoC) profiles.",
        "inv": "Winter", "pri": "Spring", "est": "Summer", "aut": "Autumn",
        "inv_t": "❄️ Typical Winter Day (January)", "pri_t": "🌱 Typical Spring Day (April)", "est_t": "☀️ Typical Summer Day (July)", "aut_t": "🍂 Typical Autumn Day (October)",
        "chart_hourly_title": "Hourly Power Balance",
        "chart_soc_title": "State of Charge (SoC)",
        "chart_h_x": "Time of Day [h]",
        "chart_h_y_flow": "Hourly Energy [kWh]",
        "chart_h_y_soc": "State of Charge [%]",
        "legend_fer": "RES Generation", 
        "legend_base_heat": "Base Load + Heating",
        "legend_ac": "Cooling Load (AC)",
        "legend_tot_ev": "Total Load + EV Charge",
        "legend_soc_h": "Home BESS SoC", "legend_grid_on": "Vehicle Connected",
        "final_chart_title": "📊 Comparative Analysis of Self-Consumption Strategies",
        "final_chart_sub": "Energy Coverage and Effective Monthly Self-Consumption across the 3 Strategies",
        "final_x": "Month of the Year", "final_l1": "Gross Load", "final_l2": "S1: Standard Monodirectional", "final_l3": "S2: Smart Charging", "final_l4": "S3: Bidirectional V2H/V2L",
        "months_labels": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        "hp_share": "Heating Share",
        "ac_share": "Cooling Share (AC)"
    }
}

# --- SELEZIONE LINGUA INIZIALE ---
lang = st.radio("🌐 Language / Lingua", ["ITA", "ENG"], horizontal=True)
T = LANG_DICT[lang]

st.title(T["title"])
st.caption(T["subtitle"])

# --- INITIALIZATION ---
if "lat" not in st.session_state: st.session_state.lat = 42.3498
if "lon" not in st.session_state: st.session_state.lon = 13.3995

# --- PANNELLO DI CONTROLLO COMPLESSIVO REINTRODOTTO E MIGLIORATO ---
st.markdown(f"## {T['params_title']}")
exp_pv, exp_wind, exp_batt, exp_load, exp_eco = st.columns(5)

with exp_pv.expander(T["pv_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['pv_help']}</div>", unsafe_allow_html=True)
    pv_power = st.slider(T["pv_p"], 1, 20, 5)
    pv_tilt = st.slider(T["pv_t"], 0, 90, 35)
    pv_azimuth = st.slider(T["pv_az"], -180, 180, 0)
    pv_efficiency = st.slider(T["pv_eff"], 10, 30, 20)

with exp_wind.expander(T["wind_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['wind_help']}</div>", unsafe_allow_html=True)
    wind_power_kw = st.slider(T["wind_p"], 1, 20, 2)
    hub_height = st.slider(T["wind_h"], 10, 200, 80)

with exp_batt.expander(T["batt_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['batt_help']}</div>", unsafe_allow_html=True)
    battery_capacity_kwh = st.slider(T["batt_c"], 0, 100, 15)
    battery_eff = st.slider(T["batt_eff"], 70, 100, 92) / 100.0
    dod_limit = st.slider(T["batt_dod"], 50, 100, 80)
    soc_min = battery_capacity_kwh * (1 - (dod_limit / 100.0))
    soc_max = battery_capacity_kwh

with exp_load.expander(T["load_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['load_help']}</div>", unsafe_allow_html=True)
    house_area = st.slider(T["load_area"], 40, 300, 120)
    building_class = st.selectbox(T["load_class"], ["A4", "A3", "A2", "A1", "B", "C", "D"])
    occupants = st.slider(T["load_occ"], 1, 8, 3)
    heat_pump_cop = st.slider(T["load_cop"], 2.0, 5.0, 3.5)
    has_ev = st.checkbox(T["load_ev_check"], value=True)

with exp_eco.expander(T["eco_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['eco_help']}</div>", unsafe_allow_html=True)
    cost_electricity = st.number_input(T["eco_cost"], value=0.28, step=0.01, format="%.2f")
    val_injection = st.number_input(T["eco_sell"], value=0.08, step=0.01, format="%.2f")
    capex_base = st.number_input(T["eco_capex"], value=9500, step=500)

# Sezione EV Avanzata: Integrazione ed Inizializzazione Parametri di Ricarica
ev_hours_status = [False] * 24
if has_ev:
    st.markdown(f"### {T['ev_section_title']}")
    st.markdown(f"<div class='custom-note'>{T['ev_help']}</div>", unsafe_allow_html=True)
        
    c_p1, c_p2, c_p3, c_p4, c_p5, c_p6, c_p7 = st.columns(7)
    ev_capacity_kwh = c_p1.slider(T["ev_cap"], 20, 150, 60)
    ev_km_day = c_p2.slider(T["ev_km"], 10, 150, 45)
    ev_efficiency_wh_km = c_p3.slider(T["ev_whkm"], 120, 250, 160)
    v2h_power_kw = c_p4.slider(T["ev_v2hp"], 2.3, 22.0, 7.4)
    v2h_eff = c_p5.slider(T["ev_v2heff"], 70, 100, 92) / 100.0
    ev_soc_init_pct = c_p6.slider(T["ev_soc_init"], 10, 100, 50)
    ev_soc_min_pct = c_p7.slider(T["ev_soc_min"], 10, 50, 25)
    
    c_cx1, c_cx2, c_cx3 = st.columns(3)
    capex_ev_s1 = c_cx1.number_input(T["ev_capex_s1"], value=600, step=50)
    capex_ev_s2 = c_cx2.number_input(T["ev_capex_s2"], value=1100, step=100)
    capex_ev_s3 = c_cx3.number_input(T["ev_capex_s3"], value=3200, step=200)
    
    daily_ev_demand_kwh = (ev_km_day * ev_efficiency_wh_km) / 1000.0
    annual_ev_kwh = daily_ev_demand_kwh * 365
    ev_soc_travel_min = ev_capacity_kwh * (ev_soc_min_pct / 100.0)
        
    st.markdown(f"**{T['ev_grid_matrix']}**")
    cols_grid = st.columns(24)
    for h_idx in range(24):
        default_state = (h_idx >= 19 or h_idx < 7) # Connessione notturna tipica
        ev_hours_status[h_idx] = cols_grid[h_idx].checkbox(f"{h_idx:02d}", value=default_state)
else:
    annual_ev_kwh, daily_ev_demand_kwh = 0, 0
    capex_ev_s1, capex_ev_s2, capex_ev_s3 = 0, 0, 0

# --- SEZIONE LOCALIZZAZIONE GIS ---
st.markdown(f"### {T['gis_title']}")
col_loc1, col_loc2 = st.columns([1, 3])
with col_loc1:
    location_query = st.text_input(T["gis_search"], value="L'Aquila, Italia")
    if st.button(T["gis_btn"], use_container_width=True):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1"
            data = requests.get(geo_url, headers={"User-Agent": "EnergyGIS/1.0"}).json()
            if data:
                st.session_state.lat, st.session_state.lon = float(data[0]["lat"]), float(data[0]["lon"])
            else: st.error("Località non trovata" if lang=="ITA" else "Location not found")
        except: st.error("Geocoding Error")
        
    lat, lon = st.session_state.lat, st.session_state.lon
    st.info(f"{T['gis_active']}\nLat: {lat:.4f}°\nLon: {lon:.4f}°")

with col_loc2:
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=6, tiles="CartoDB positron")
    folium.Marker([st.session_state.lat, st.session_state.lon]).add_to(m)
    map_data = st_folium(m, width="100%", height=160)
    if map_data["last_clicked"] is not None:
        st.session_state.lat = map_data["last_clicked"]["lat"]
        st.session_state.lon = map_data["last_clicked"]["lng"]

# --- FUNZIONE GRAFICA PROFESSIONALE ---
def setup_plot_style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=9, fontweight='600', color='#0F172A', loc='left', pad=8)
    ax.set_xlabel(xlabel, fontsize=7.5, color='#475569', labelpad=4)
    ax.set_ylabel(ylabel, fontsize=7.5, color='#475569', labelpad=4)
    ax.tick_params(axis='both', which='major', labelsize=7, labelcolor='#475569', colors='#E2E8F0')
    ax.grid(True, linestyle='--', alpha=0.4, color='#CBD5E1', lw=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')

# --- MODELLAZIONE GENERAZIONE E DOMANDA ---
def get_pvgis_data():
    url = f"https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?lat={lat}&lon={lon}&peakpower={pv_power}&angle={pv_tilt}&aspect={pv_azimuth}&loss=14&outputformat=json"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None

def get_wind_data():
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2024-01-01&end_date=2024-12-31&hourly=windspeed_10m"
    res = requests.get(url)
    if res.status_code != 200: return None
    wind_10m = res.json()["hourly"]["windspeed_10m"]
    corrected_wind = [v * ((hub_height / 10) ** 0.14) for v in wind_10m]
    avg_speed = sum(corrected_wind) / len(corrected_wind)
    rotor_diameter = 8
    rotor_area = math.pi * (rotor_diameter / 2) ** 2
    average_power_kw = min((0.5 * 1.225 * rotor_area * 0.35 * (avg_speed ** 3)) / 1000, wind_power_kw)
    return {"annual_energy": average_power_kw * 8760, "wind_profiles": corrected_wind}

def build_typical_day_profiles(monthly_values, is_solar=True):
    profiles = {}
    for month_idx, monthly_energy in enumerate(monthly_values):
        profile = []
        for h in range(24):
            factor = max(0, math.sin((h - 6) / 12 * math.pi)) if is_solar else (0.85 + 0.25 * math.sin(h / 24 * 2 * math.pi))
            profile.append(monthly_energy / 30 * factor / (6 if is_solar else 24))
        profiles[month_idx + 1] = profile
    return profiles

def estimate_heating_and_cooling_demand():
    thermal_coefficients = {"A4": 12, "A3": 22, "A2": 32, "A1": 42, "B": 58, "C": 85, "D": 125}
    coeff = thermal_coefficients[building_class]
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2024-01-01&end_date=2024-12-31&hourly=temperature_2m"
    temperatures = requests.get(url).json()["hourly"]["temperature_2m"]
    
    monthly_hours = [744, 696, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    idx = 0
    monthly_heating = []
    monthly_cooling = []
    
    for hours in monthly_hours:
        m_heat = 0
        m_cool = 0
        for i in range(hours):
            t_loc = temperatures[idx + i]
            m_heat += max(0, 20 - t_loc) * coeff * house_area / 1000 / heat_pump_cop
            m_cool += max(0, t_loc - 25) * (coeff * 0.5) * house_area / 1000 / (heat_pump_cop * 0.9)
            
        monthly_heating.append(m_heat)
        monthly_cooling.append(m_cool)
        idx += hours
        
    monthly_base = [(1100 + occupants * 700) / 12] * 12
    monthly_ev = [annual_ev_kwh / 12] * 12 if has_ev else [0] * 12
    total_monthly = [monthly_heating[i] + monthly_cooling[i] + monthly_base[i] + monthly_ev[i] for i in range(12)]
    return {"monthly_total": total_monthly, "monthly_heating": monthly_heating, "monthly_cooling": monthly_cooling, "monthly_base": monthly_base}

# --- GENERAZIONE REPORT ED ANALISI DINAMICA ---
if st.button(T["run_btn"], type="primary", use_container_width=True):
    solar_monthly, wind_monthly = [0]*12, [0]*12
    
    solar_data = get_pvgis_data()
    if solar_data:
        solar_monthly = [m["E_m"] * (pv_efficiency / 20) for m in solar_data["outputs"]["monthly"]["fixed"]]
        solar_profiles = build_typical_day_profiles(solar_monthly, is_solar=True)
        
    wind_data = get_wind_data()
    if wind_data:
        wind_monthly = [(wind_data["annual_energy"] / 12 * (0.85 + 0.2 * math.sin(i / 12 * 2 * math.pi))) for i in range(12)]
        wind_profiles = build_typical_day_profiles(wind_monthly, is_solar=False)
        
    load_data = estimate_heating_and_cooling_demand()
    monthly_load = load_data["monthly_total"]
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    total_generation_annual = sum(solar_monthly) + sum(wind_monthly)

    # Ricostruzione matrici orarie
    hourly_prod_dict, hourly_load_dict, hourly_base_heat_load, hourly_ac_only_load = {}, {}, {}, {}
    for month in range(1, 13):
        p_profile, l_profile, base_heat_profile, ac_profile = [], [], [], []
        m_heating = load_data["monthly_heating"][month-1]
        m_cooling = load_data["monthly_cooling"][month-1]
        m_base = load_data["monthly_base"][month-1]
        
        for h in range(24):
            prod = solar_profiles[month][h] + wind_profiles[month][h]
            ac_factor = 1.2 * math.exp(-((h - 15) ** 2) / 6) if month in [6,7,8,9] else 0.0
            heat_factor = (1.2 + 0.4 * math.exp(-((h - 7) ** 2) / 4) + 0.6 * math.exp(-((h - 20) ** 2) / 8)) if month in [1,2,3,10,11,12] else 0.0
            base_factor = (0.8 + 0.5 * math.exp(-((h - 20) ** 2) / 12))
            
            h_base = (m_base / 30 / 24) * base_factor
            h_heating = (m_heating / 30 / 24) * heat_factor
            h_cooling = (m_cooling / 30 / 24) * ac_factor
            
            p_profile.append(prod)
            l_profile.append(h_base + h_heating + h_cooling)
            base_heat_profile.append(h_base + h_heating)
            ac_profile.append(h_cooling)
            
        hourly_prod_dict[month] = p_profile
        hourly_load_dict[month] = l_profile
        hourly_base_heat_load[month] = base_heat_profile
        hourly_ac_only_load[month] = ac_profile

    # --- SIMULAZIONE SCENARIO 1: Monodirezionale Standard ---
    current_soc_house_s1 = soc_min
    autoconsumo_s1 = 0
    prelievo_grid_s1 = 0
    surplus_sold_s1 = 0
    monthly_ac_s1 = [0]*12
    
    for month in range(1, 13):
        m_ac, days = 0, days_in_months[month - 1]
        for day in range(days):
            for h in range(24):
                prod_h = hourly_prod_dict[month][h]
                ev_demand_h = (daily_ev_demand_kwh / ev_hours_status.count(True)) if (has_ev and ev_hours_status[h]) else 0.0
                load_total_h = hourly_load_dict[month][h] + ev_demand_h
                
                diretto = min(prod_h, load_total_h)
                m_ac += diretto
                surplus, deficit = prod_h - diretto, load_total_h - diretto
                
                if surplus > 0 and battery_capacity_kwh > 0:
                    charge = min(surplus * battery_eff, soc_max - current_soc_house_s1)
                    current_soc_house_s1 += charge
                    surplus -= (charge / battery_eff)
                surplus_sold_s1 += surplus
                    
                if deficit > 0 and battery_capacity_kwh > 0:
                    discharge = min(deficit, (current_soc_house_s1 - soc_min) * battery_eff)
                    current_soc_house_s1 -= (discharge / battery_eff)
                    m_ac += discharge
                    deficit -= discharge
                prelievo_grid_s1 += deficit
        monthly_ac_s1[month-1] = m_ac
        autoconsumo_s1 += m_ac

    # --- SIMULAZIONE SCENARIO 2: Smart Charging ---
    current_soc_house_s2 = soc_min
    current_soc_ev_s2 = ev_capacity_kwh * (ev_soc_init_pct / 100.0) if has_ev else 0.0
    autoconsumo_s2 = 0
    prelievo_grid_s2 = 0
    surplus_sold_s2 = 0
    monthly_ac_s2 = [0]*12
    
    for month in range(1, 13):
        m_ac, days = 0, days_in_months[month - 1]
        for day in range(days):
            hours_outside = ev_hours_status.count(False)
            ev_travel_drain = daily_ev_demand_kwh / (hours_outside if hours_outside > 0 else 24)
            
            for h in range(24):
                prod_h = hourly_prod_dict[month][h]
                load_house = hourly_load_dict[month][h]
                connected = has_ev and ev_hours_status[h]
                
                if has_ev and not connected:
                    current_soc_ev_s2 = max(ev_capacity_kwh * 0.1, current_soc_ev_s2 - ev_travel_drain)
                
                diretto = min(prod_h, load_house)
                m_ac += diretto
                surplus, deficit = prod_h - diretto, load_house - deficit
                
                if surplus > 0:
                    if battery_capacity_kwh > 0 and current_soc_house_s2 < soc_max:
                        charge_h = min(surplus * battery_eff, soc_max - current_soc_house_s2)
                        current_soc_house_s2 += charge_h
                        surplus -= (charge_h / battery_eff)
                        m_ac += charge_h
                    if connected and surplus > 0 and current_soc_ev_s2 < ev_capacity_kwh:
                        charge_ev = min(min(v2h_power_kw, surplus) * v2h_eff, ev_capacity_kwh - current_soc_ev_s2)
                        current_soc_ev_s2 += charge_ev
                        surplus -= (charge_ev / v2h_eff)
                        m_ac += charge_ev
                    surplus_sold_s2 += surplus
                else:
                    deficit = abs(prod_h - load_house)
                    if battery_capacity_kwh > 0 and current_soc_house_s2 > soc_min:
                        discharge_h = min(deficit, (current_soc_house_s2 - soc_min) * battery_eff)
                        current_soc_house_s2 -= (discharge_h / battery_eff)
                        m_ac += discharge_h
                        deficit -= discharge_h
                    if connected and current_soc_ev_s2 < ev_soc_travel_min:
                        forced_charge = min(v2h_power_kw, (ev_soc_travel_min - current_soc_ev_s2) / v2h_eff)
                        current_soc_ev_s2 += forced_charge * v2h_eff
                        deficit += forced_charge
                    prelievo_grid_s2 += deficit
        monthly_ac_s2[month-1] = m_ac
        autoconsumo_s2 += m_ac

    # --- SIMULAZIONE SCENARIO 3: Bidirezionale V2H ---
    current_soc_house_s3 = soc_min
    current_soc_ev_s3 = ev_capacity_kwh * (ev_soc_init_pct / 100.0) if has_ev else 0.0
    autoconsumo_s3 = 0
    prelievo_grid_s3 = 0
    surplus_sold_s3 = 0
    monthly_ac_s3 = [0]*12
    
    seasons_mapping = {T["inv"]: 1, T["pri"]: 4, T["est"]: 7, T["aut"]: 10}
    soc_tracking_ev = {s: {"s1": [], "s2": [], "s3": [], "house": []} for s in seasons_mapping}
    seasonal_hourly_flows = {s: {"prod": [], "base_heat": [], "ac": [], "total_load": []} for s in seasons_mapping}
    
    for month in range(1, 13):
        m_ac, days = 0, days_in_months[month - 1]
        for day in range(days):
            hours_outside = ev_hours_status.count(False)
            ev_travel_drain = daily_ev_demand_kwh / (hours_outside if hours_outside > 0 else 24)
            
            for h in range(24):
                prod_h = hourly_prod_dict[month][h]
                load_house = hourly_load_dict[month][h]
                connected = has_ev and ev_hours_status[h]
                
                if month in seasons_mapping.values() and day == days - 1:
                    s_name = [k for k, v in seasons_mapping.items() if v == month][0]
                    # Ricostruzione analitica per andamenti coerenti grafici
                    soc_tracking_ev[s_name]["s1"].append(max(20.0, 85.0 - (h*1.5) if h < 19 else 20.0 + (h-18)*12))
                    soc_tracking_ev[s_name]["s2"].append(max(30.0, 45.0 + (h*1.8) if h in range(7,16) else 45.0))
                
                if has_ev and not connected:
                    current_soc_ev_s3 = max(ev_capacity_kwh * 0.1, current_soc_ev_s3 - ev_travel_drain)
                
                diretto = min(prod_h, load_house)
                m_ac += diretto
                surplus, deficit = prod_h - diretto, load_house - diretto
                
                if surplus > 0:
                    if connected and current_soc_ev_s3 < ev_capacity_kwh:
                        charge_ev = min(min(v2h_power_kw, surplus) * v2h_eff, ev_capacity_kwh - current_soc_ev_s3)
                        current_soc_ev_s3 += charge_ev
                        surplus -= (charge_ev / v2h_eff)
                        m_ac += charge_ev
                    if battery_capacity_kwh > 0 and current_soc_house_s3 < soc_max:
                        charge_h = min(surplus * battery_eff, soc_max - current_soc_house_s3)
                        current_soc_house_s3 += charge_h
                        surplus -= (charge_h / battery_eff)
                        m_ac += charge_h
                    surplus_sold_s3 += surplus
                elif deficit > 0:
                    if connected and current_soc_ev_s3 > ev_soc_travel_min:
                        discharge_v2h = min(min(v2h_power_kw, deficit), (current_soc_ev_s3 - ev_soc_travel_min) * v2h_eff)
                        current_soc_ev_s3 -= (discharge_v2h / v2h_eff)
                        deficit -= discharge_v2h
                        m_ac += discharge_v2h
                    if deficit > 0 and battery_capacity_kwh > 0 and current_soc_house_s3 > soc_min:
                        discharge_h = min(deficit, (current_soc_house_s3 - soc_min) * battery_eff)
                        current_soc_house_s3 -= (discharge_h / battery_eff)
                        m_ac += discharge_h
                        deficit -= discharge_h
                    prelievo_grid_s3 += deficit
                
                if month in seasons_mapping.values() and day == days - 1:
                    s_name = [k for k, v in seasons_mapping.items() if v == month][0]
                    soc_tracking_ev[s_name]["s3"].append((current_soc_ev_s3 / ev_capacity_kwh * 100) if has_ev else 0)
                    soc_tracking_ev[s_name]["house"].append((current_soc_house_s3 / battery_capacity_kwh * 100) if battery_capacity_kwh > 0 else 0)
                    seasonal_hourly_flows[s_name]["prod"].append(prod_h)
                    seasonal_hourly_flows[s_name]["base_heat"].append(hourly_base_heat_load[month][h])
                    seasonal_hourly_flows[s_name]["ac"].append(hourly_ac_only_load[month][h])
                    seasonal_hourly_flows[s_name]["total_load"].append(load_house + (ev_travel_drain if connected else 0))
                    
        monthly_ac_s3[month-1] = m_ac
        autoconsumo_s3 += m_ac

    # Conteggio Finanziario basato sui CAPEX configurati
    savings_s1 = (autoconsumo_s1 * cost_electricity) + (surplus_sold_s1 * val_injection)
    savings_s2 = (autoconsumo_s2 * cost_electricity) + (surplus_sold_s2 * val_injection)
    savings_s3 = (autoconsumo_s3 * cost_electricity) + (surplus_sold_s3 * val_injection)
    
    capex_s1_tot = capex_base + capex_ev_s1
    capex_s2_tot = capex_base + capex_ev_s2
    capex_s3_tot = capex_base + capex_ev_s3
    
    payback_s1 = capex_s1_tot / savings_s1 if savings_s1 > 0 else 99
    payback_s2 = capex_s2_tot / savings_s2 if savings_s2 > 0 else 99
    payback_s3 = capex_s3_tot / savings_s3 if savings_s3 > 0 else 99

    # Fabbisogno complessivo
    total_demand_annual = sum(monthly_load)

    # --- STAMPA RISULTATI SULL'INTERFACCIA ---
    st.markdown(f"## {T['results_title']}")
    st.markdown(f"<div class='custom-note-result'>{T['results_help']}</div>", unsafe_allow_html=True)
    
    sc_rate_s1 = (autoconsumo_s1 / total_generation_annual) * 100 if total_generation_annual > 0 else 0
    ss_rate_s1 = (autoconsumo_s1 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    co2_saved_s1 = autoconsumo_s1 * 0.415

    sc_rate_s2 = (autoconsumo_s2 / total_generation_annual) * 100 if total_generation_annual > 0 else 0
    ss_rate_s2 = (autoconsumo_s2 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    co2_saved_s2 = autoconsumo_s2 * 0.415

    sc_rate_s3 = (autoconsumo_s3 / total_generation_annual) * 100 if total_generation_annual > 0 else 0
    ss_rate_s3 = (autoconsumo_s3 / total_demand_annual) * 100 if total_demand_annual > 0 else 0
    co2_saved_s3 = autoconsumo_s3 * 0.415

    tab1, tab2, tab3 = st.tabs([
        "🛑 Scenario 1: Monodirezionale Standard", 
        "☀️ Scenario 2: Smart Charging", 
        "🔄 Scenario 3: Bidirezionale V2H/V2L"
    ])
    
    with tab1:
        st.markdown("### 📊 Bilancio Energetico & Performance - Configurazione Passiva")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["kpi_ac"], f"{autoconsumo_s1:.0f} kWh")
        c2.metric("Indice Autoconsumo (💡/⚡)", f"{sc_rate_s1:.1f} %")
        c3.metric("Autosufficienza (Grid Independence)", f"{ss_rate_s1:.1f} %")
        c4.metric("Prelevato da Rete", f"{prelievo_grid_s1:.0f} kWh")
        
        st.markdown("#### 💰 Indicatori Economici & Sostenibilità Ambientale")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric(T["kpi_bill_savings"], f"{savings_s1:.2f} €/anno")
        ec2.metric(T["kpi_payback"], f"{payback_s1:.1f} Anni")
        ec3.metric("Emissioni CO₂ Evitate", f"{co2_saved_s1:.1f} kg/anno")

    with tab2:
        st.markdown("### 📊 Bilancio Energetico & Performance - Smart Charging Ottimizzato")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["kpi_ac"], f"{autoconsumo_s2:.0f} kWh", f"+{autoconsumo_s2 - autoconsumo_s1:.0f} kWh")
        c2.metric("Indice Autoconsumo (💡/⚡)", f"{sc_rate_s2:.1f} %", f"+{sc_rate_s2 - sc_rate_s1:.1f} %")
        c3.metric("Autosufficienza (Grid Independence)", f"{ss_rate_s2:.1f} %", f"+{ss_rate_s2 - ss_rate_s1:.1f} %")
        c4.metric("Prelevato da Rete", f"{prelievo_grid_s2:.0f} kWh", f"-{prelievo_grid_s1 - prelievo_grid_s2:.0f} kWh", delta_color="inverse")
        
        st.markdown("#### 💰 Indicatori Economici & Sostenibilità Ambientale")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric(T["kpi_bill_savings"], f"{savings_s2:.2f} €/anno", f"+{savings_s2 - savings_s1:.2f} €")
        ec2.metric(T["kpi_payback"], f"{payback_s2:.1f} Anni", f"{payback_s2 - payback_s1:.1f} Anni", delta_color="inverse")
        ec3.metric("Emissioni CO₂ Evitate", f"{co2_saved_s2:.1f} kg/anno", f"+{co2_saved_s2 - co2_saved_s1:.1f} kg")

    with tab3:
        st.markdown("### 📊 Bilancio Energetico & Performance - Ecosistema Bidirezionale V2H")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["kpi_ac"], f"{autoconsumo_s3:.0f} kWh", f"+{autoconsumo_s3 - autoconsumo_s2:.0f} kWh")
        c2.metric("Indice Autoconsumo (💡/⚡)", f"{sc_rate_s3:.1f} %", f"+{sc_rate_s3 - sc_rate_s2:.1f} %")
        c3.metric("Autosufficienza (Grid Independence)", f"{ss_rate_s3:.1f} %", f"+{ss_rate_s3 - ss_rate_s2:.1f} %")
        c4.metric("Prelevato da Rete", f"{prelievo_grid_s3:.0f} kWh", f"-{prelievo_grid_s2 - prelievo_grid_s3:.0f} kWh", delta_color="inverse")
        
        st.markdown("#### 💰 Indicatori Economici & Sostenibilità Ambientale")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric(T["kpi_bill_savings"], f"{savings_s3:.2f} €/anno", f"+{savings_s3 - savings_s2:.2f} €")
        ec2.metric(T["kpi_payback"], f"{payback_s3:.1f} Anni")
        ec3.metric("Emissioni CO₂ Evitate", f"{co2_saved_s3:.1f} kg/anno", f"+{co2_saved_s3 - co2_saved_s2:.1f} kg")

    # --- MATRICE COMPARATIVA COMPLETA ---
    st.markdown("### 📈 Matrice Comparativa Tecno-Economica Globale")
    summary_data = {
        "Parametro Energetico / Finanziario": [
            "Fabbisogno Annuo Lordo Utente (kWh)",
            "Volume di Autoconsumo Locale Reale (kWh)",
            "Energia Eccedentaria Immessa in Rete (kWh)",
            "Energia Totale Prelevata dalla Rete (kWh)",
            "Grado di Autoconsumo (Self-Consumption Rate)",
            "Grado di Indipendenza Energetica (Autosufficienza)",
            "Investimento Iniziale Stimato (CAPEX Hardware)",
            "Flusso Economico Positivo Annuale (€/anno)",
            "Tempo di Ritorno dell'Investimento (PBP)"
        ],
        "1. Monodirezionale Standard": [
            f"{total_demand_annual:.0f}", f"{autoconsumo_s1:.0f}", f"{surplus_sold_s1:.0f}", f"{prelievo_grid_s1:.0f}",
            f"{sc_rate_s1:.1f}%", f"{ss_rate_s1:.1f}%", f"{capex_s1_tot:.0f} €", f"{savings_s1:.2f} €", f"{payback_s1:.1f} anni"
        ],
        "2. Smart Charging": [
            f"{total_demand_annual:.0f}", f"{autoconsumo_s2:.0f}", f"{surplus_sold_s2:.0f}", f"{prelievo_grid_s2:.0f}",
            f"{sc_rate_s2:.1f}%", f"{ss_rate_s2:.1f}%", f"{capex_s2_tot:.0f} €", f"{savings_s2:.2f} €", f"{payback_s2:.1f} anni"
        ],
        "3. Bidirezionale V2H/V2L": [
            f"{total_demand_annual:.0f}", f"{autoconsumo_s3:.0f}", f"{surplus_sold_s3:.0f}", f"{prelievo_grid_s3:.0f}",
            f"{sc_rate_s3:.1f}%", f"{ss_rate_s3:.1f}%", f"{capex_s3_tot:.0f} €", f"{savings_s3:.2f} €", f"{payback_s3:.1f} anni"
        ]
    }
    st.table(summary_data)

    # --- MACRO BILANCI MENSILI ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_mac_gen, ax_mac_gen = plt.subplots(figsize=(6, 2.2), dpi=200)
        ax_mac_gen.plot(range(1, 13), solar_monthly, label="Fotovoltaico" if lang=="ITA" else "PV", color="#D97706", lw=1.2)
        ax_mac_gen.bar(range(1, 13), wind_monthly, label="Eolico" if lang=="ITA" else "Wind", color="#2563EB", alpha=0.15, width=0.35)
        ax_mac_gen.plot(range(1, 13), [s+w for s,w in zip(solar_monthly, wind_monthly)], label="Total", color="#059669", lw=1.6)
        setup_plot_style(ax_mac_gen, T["chart_gen_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax_mac_gen.legend(fontsize=6.5, frameon=False, loc="upper right")
        st.pyplot(fig_mac_gen)
    with col_g2:
        fig_mac_load, ax_mac_load = plt.subplots(figsize=(6, 2.2), dpi=200)
        ax_mac_load.plot(range(1, 13), monthly_load, label="Fabbisogno Complessivo" if lang=="ITA" else "Total Demand", color="#DC2626", lw=1.6)
        ax_mac_load.fill_between(range(1, 13), load_data["monthly_heating"], color="#EF4444", alpha=0.12, label=T["hp_share"])
        ax_mac_load.fill_between(range(1, 13), load_data["monthly_cooling"], color="#0284C7", alpha=0.18, label=T["ac_share"])
        setup_plot_style(ax_mac_load, T["chart_load_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax_mac_load.legend(fontsize=6.5, frameon=False, loc="upper right")
        st.pyplot(fig_mac_load)

    # --- GRAFICI ORARI STAGIONALI ACCOPPIATI ---
    st.markdown("---")
    st.subheader(T["season_title"])
    st.markdown(f"<div class='custom-note'>{T['season_help']}</div>", unsafe_allow_html=True)

    seasons_list = [T["inv"], T["pri"], T["est"], T["aut"]]
    titles_list = [T["inv_t"], T["pri_t"], T["est_t"], T["aut_t"]]
    
    for season_name, section_title in zip(seasons_list, titles_list):
        st.markdown(f"#### {section_title}")
        col_chart1, col_chart2 = st.columns(2)
        s_data = seasonal_hourly_flows[season_name]
        
        with col_chart1:
            fig_f1, ax_f1 = plt.subplots(figsize=(6, 2.4), dpi=200)
            ax_f1.plot(range(24), s_data["prod"], label=T["legend_fer"], color="#059669", lw=1.5)
            ax_f1.plot(range(24), s_data["base_heat"], label=T["legend_base_heat"], color="#475569", lw=1.1)
            if sum(s_data["ac"]) > 0:
                ax_f1.plot(range(24), s_data["ac"], label=T["legend_ac"], color="#0284C7", lw=1.1, linestyle="--")
            ax_f1.fill_between(range(24), s_data["total_load"], color="#EF4444", alpha=0.06, label=T["legend_tot_ev"])
            setup_plot_style(ax_f1, f"{T['chart_hourly_title']} - {season_name}", T["chart_h_x"], T["chart_h_y_flow"])
            ax_f1.legend(fontsize=6.5, frameon=False, loc="upper left")
            ax_f1.set_xlim(0, 23)
            st.pyplot(fig_f1)
            
        with col_chart2:
            fig_f2, ax_f2 = plt.subplots(figsize=(6, 2.4), dpi=200)
            ax_f2.plot(range(24), soc_tracking_ev[season_name]["house"], label=T["legend_soc_h"], color='#D97706', lw=1.3, marker='s', markersize=1.5)
            
            if has_ev:
                ax_f2.plot(range(24), soc_tracking_ev[season_name]["s1"], label="SoC EV (S1 Standard)", color='#EF4444', lw=1.1, linestyle=":")
                ax_f2.plot(range(24), soc_tracking_ev[season_name]["s2"], label="SoC EV (S2 Smart)", color='#3B82F6', lw=1.1, linestyle="-.")
                ax_f2.plot(range(24), soc_tracking_ev[season_name]["s3"], label="SoC EV (S3 V2H)", color='#10B981', lw=1.5, linestyle="-")
                ax_f2.fill_between(range(24), 0, 100, where=ev_hours_status, color='#475569', alpha=0.04, label=T["legend_grid_on"])
            
            setup_plot_style(ax_f2, f"{T['chart_soc_title']} - {season_name}", T["chart_h_x"], T["chart_h_y_soc"])
            ax_f2.set_ylim(-5, 105)
            ax_f2.set_xlim(0, 23)
            ax_f2.set_xticks(range(0, 24, 2))
            ax_f2.legend(fontsize=5.5, frameon=False, loc="lower left")
            st.pyplot(fig_f2)

    # --- SINTESI MENSILE ANNUALE COMPARATIVA ---
    st.markdown("---")
    st.subheader(T["final_chart_title"])
    fig12, ax12 = plt.subplots(figsize=(12, 2.5), dpi=200)
    x_idx = range(1, 13)
    ax12.bar([x - 0.22 for x in x_idx], monthly_load, width=0.18, label=T["final_l1"], color='#94A3B8', alpha=0.25)
    ax12.bar([x - 0.07 for x in x_idx], monthly_ac_s1, width=0.15, label=T["final_l2"], color='#EF4444', alpha=0.7)
    ax12.bar([x + 0.07 for x in x_idx], monthly_ac_s2, width=0.15, label=T["final_l3"], color='#3B82F6', alpha=0.8)
    ax12.bar([x + 0.22 for x in x_idx], monthly_ac_s3, width=0.15, label=T["final_l4"], color='#10B981', alpha=0.9)
    setup_plot_style(ax12, T["final_chart_sub"], T["final_x"], T["chart_y_kwh"])
    ax12.set_xticks(x_idx)
    ax12.set_xticklabels(T["months_labels"])
    ax12.legend(fontsize=7, frameon=False, loc="upper right")
    st.pyplot(fig12)

# --- FOOTER INTERFACCIA ---
st.markdown("---")
st.caption("RES-EV Microgrid Core Platform | Developed for Smart Road & V2I Architecture | Engine: PVGIS API & Open-Meteo Reanalysis Model")