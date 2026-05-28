# FEREnergySim.py
import streamlit as st
import requests
import matplotlib.pyplot as plt
import folium
import math
from streamlit_folium import st_folium

# --- CONFIGURAZIONE INTERFACCIA ED ESTETICA ---
st.set_page_config(page_title="RES-Based Home & EV Simulator", layout="wide")

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
        padding: 0.5rem 0.75rem; border-radius: 0.25rem; font-size: 0.8rem; 
        background-color: #F8FAFC; color: #475569; border-left: 3px solid #3B82F6; margin-bottom: 0.6rem; line-height: 1.3;
    }
    .custom-note-result { 
        padding: 0.6rem 0.75rem; border-radius: 0.25rem; font-size: 0.82rem; 
        background-color: #F0FDF4; color: #166534; border-left: 3px solid #22C55E; margin-bottom: 0.8rem;
    }
    div[data-testid="column"] { padding: 0px 1px !important; }
    </style>
""", unsafe_allow_html=True)

# --- DIZIONARIO DI TRADUZIONE BILINGUE (ITA / ENG) ---
LANG_DICT = {
    "ITA": {
        "title": "🌍 RES-Based Home & EV Mobility Simulator (V2H / V2L Beta)",
        "subtitle": "Modellazione avanzata micro-reti con integrazione di ricarica Unidirezionale, Smart Charging e Bidirezionale V2H/V2L.",
        "params_title": "🎛️ Configurazione Parametri Tecnici ed Economici",
        "pv_title": "☀️ Fotovoltaico (Max 20 kWp)",
        "pv_help": "💡 **PV**: Inclinazione ottimale in Italia: 30°-35°. Azimuth: 0° Sud, -90° Est, 90° Ovest.",
        "pv_p": "Potenza Impianto (kWp)",
        "pv_t": "Tilt Angle (°)",
        "pv_az": "Azimuth Angle (°)",
        "pv_eff": "Rendimento Modulo (%)",
        "wind_title": "🌬️ Micro-Eolico",
        "wind_help": "💡 **WT**: Estrapola la velocità del vento all'altezza del mozzo mediante legge di potenza esponenziale.",
        "wind_p": "Potenza Nominale (kW)",
        "wind_h": "Altezza Mozzo (m)",
        "batt_title": "🔋 Accumulo Elettrochimico Casa",
        "batt_help": "💡 **BESS**: Capacità stazionaria fissa installata a parete all'interno dell'abitazione.",
        "batt_c": "Capacità Nominale (kWh)",
        "batt_eff": "Efficienza Round-Trip (%)",
        "batt_dod": "DoD Massimo (%)",
        "load_title": "🏠 Profilo Utenza & EV",
        "load_help": "💡 **Loads**: Calcola la firma termica dell'edificio incrociando i dati GIS di temperatura oraria storici.",
        "load_area": "Superficie Calpestabile (m²)",
        "load_class": "Classe Energetica",
        "load_occ": "Numero Occupanti",
        "load_cop": "COP/EER Medio Pompa Calore",
        "load_ev_check": "Abilita Veicolo Elettrico (EV)",
        "eco_title": "💰 Parametri Economici & CAPEX",
        "eco_help": "💡 **Financial**: Parametri di costo dell'energia preimpostati sui contratti domestici standard.",
        "eco_capex_pv": "CAPEX Fotovoltaico (€/kWp)",
        "eco_capex_wind": "CAPEX Micro-Eolico (€/kW)",
        "eco_capex_batt": "CAPEX Accumulo Casa (€/kWh)",
        "eco_capex_v2h": "CAPEX Hardware V2H/V2L (€ - fisso)",
        "eco_price_buy": "Costo Energia Prelevata (€/kWh)",
        "eco_price_sell": "Tariffa di Scambio/Vendita (€/kWh)",
        "ev_section_title": "🚗 Configurazione Mobilità Elettrica & Logiche di Ricarica",
        "ev_help": "💡 **EV Config**: Spunta le ore in cui l'auto è connessa alla wallbox di casa. Nelle ore non spuntate l'auto viaggia consumando energia.",
        "ev_cap": "Capacità Batteria EV (kWh)",
        "ev_km": "Distanza Giornaliera (km)",
        "ev_whkm": "Consumo Specifico (Wh/km)",
        "ev_v2hp": "Potenza Massima Wallbox (kW)",
        "ev_v2heff": "Efficienza Convertitore (%)",
        "ev_grid_matrix": "Matrice Oraria Connessione Auto (Spuntato = Connesso a Casa | Default: Notturno 20h-08h)",
        "gis_title": "📍 Posizionamento Geografico Impianto",
        "gis_search": "Cerca Comune o Coordinate",
        "gis_btn": "🔍 Aggiorna Mappa Sito",
        "gis_active": "**Sito Attivo:**",
        "run_btn": "⚡ Esegui Simulazione Energetica Dinamica",
        "results_title": "📊 Analisi Output e Confronto Strategie di Integrazione EV",
        "results_help": "🔬 **Scenari a Confronto**: \n1. **Monodirezionale Standard**: L'auto carica subito al massimo appena connessa.\n2. **Monodirezionale Smart**: L'auto carica solo se c'è surplus FER.\n3. **Bidirezionale V2H/V2L**: L'auto assorbe surplus e scarica verso i carichi di casa quando serve.",
        "c1_title": "##### 🛑 1. Monodirezionale Standard (Immediate)",
        "c2_title": "##### ☀️ 2. Monodirezionale Smart (Surplus)",
        "c3_title": "##### 🔄 3. Bidirezionale V2H + V2L Completo",
        "kpi_ac": "Autoconsumo",
        "kpi_ssp": "Autosufficienza (SSP)",
        "kpi_sc": "Quota Rinnovabile (SC)",
        "kpi_bill_savings": "Risparmio Annuo",
        "kpi_tot_capex": "CAPEX Investimento",
        "kpi_payback": "Tempo di Payback",
        "chart_gen_title": "Profili di Generazione Mensile",
        "chart_load_title": "Profili di Fabbisogno Mensile (Riscaldamento vs Condizionamento)",
        "chart_eco_title": "Analisi Finanziaria Comparativa degli Scenari",
        "chart_x_month": "Mese",
        "chart_y_kwh": "Energia [kWh]",
        "chart_y_eur": "Valore Economico [€]",
        "season_title": "📈 Dinamica Oraria dello Stato di Carica (SoC) nelle Tre Strategie",
        "season_help": "🔬 **Analisi dei Grafici**: Osserva come lo scenario Bidirezionale V2H/V2L (linea verde tratteggiata) utilizzi l'auto come generatore di supporto scaricandola per coprire i picchi domestici.",
        "inv": "Inverno", "pri": "Primavera", "est": "Estate", "aut": "Autunno",
        "inv_t": "❄️ Giorno Tipico Invernale (Gennaio)", "pri_t": "🌱 Giorno Tipico Primavera (Aprile)", "est_t": "☀️ Giorno Tipico Estivo (Luglio)", "aut_t": "🍂 Giorno Tipico Autunnale (Ottobre)",
        "chart_hourly_title": "Bilancio di Potenza Orario",
        "chart_soc_title": "Confronto Curve SoC Batteria Auto EV",
        "chart_h_x": "Ora del Giorno [h]",
        "chart_h_y_flow": "Energia Oraria [kWh]",
        "chart_h_y_soc": "State of Charge EV [%]",
        "legend_fer": "Generazione FER", 
        "legend_base_heat": "Carico Base + Riscaldamento",
        "legend_ac": "Carico Condizionamento (AC)",
        "legend_tot_ev": "Carico Totale + Ricarica EV",
        "legend_soc_s1": "SoC S1: Monodirezionale Standard",
        "legend_soc_s2": "SoC S2: Smart Charging Surplus",
        "legend_soc_s3": "SoC S3: Bidirezionale V2H/V2L",
        "legend_grid_on": "Auto Connessa alla Rete di Casa",
        "final_chart_title": "📊 Analisi Comparativa dell'Autoconsumo Mensile Effettivo",
        "final_chart_sub": "Quota di energia coperta localmente nelle 3 configurazioni",
        "final_x": "Mese dell'Anno", "final_l1": "Fabbisogno Lordo", "final_l2": "Autoconsumo Standard", "final_l3": "Autoconsumo Smart", "final_l4": "Autoconsumo V2H/V2L",
        "months_labels": ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'],
        "hp_share": "Quota Riscaldamento",
        "ac_share": "Quota Condizionamento (AC)"
    },
    "ENG": {
        "title": "🌍 RES-Based Home & EV Mobility Simulator (V2H / V2L Beta)",
        "subtitle": "Advanced micro-grid modeling with integration of Unidirectional, Smart Charging, and Bidirectional V2H/V2L profiles.",
        "params_title": "🎛️ Technical & Economic Parameters Configuration",
        "pv_title": "☀️ Photovoltaic (Max 20 kWp)",
        "pv_help": "💡 **PV**: Optimal Tilt in Italy: 30°-35°. Azimuth: 0° South, -90° East, 90° West.",
        "pv_p": "System Power (kWp)",
        "pv_t": "Tilt Angle (°)",
        "pv_az": "Azimuth Angle (°)",
        "pv_eff": "Module Efficiency (%)",
        "wind_title": "🌬️ Micro-Wind",
        "wind_help": "💡 **WT**: Extrapolates wind speed at hub height using power law exponential coefficient.",
        "wind_p": "Nominal Power (kW)",
        "wind_h": "Hub Height (m)",
        "batt_title": "🔋 Home Stationary Storage",
        "batt_help": "💡 **BESS**: Stationary battery capacity installed inside the house.",
        "batt_c": "Nominal Capacity (kWh)",
        "batt_eff": "Round-Trip Efficiency (%)",
        "batt_dod": "Max DoD (%)",
        "load_title": "🏠 Load Profile & EV",
        "load_help": "💡 **Loads**: Dynamically computes thermal signature from GIS hourly data.",
        "load_area": "Floor Area (m²)",
        "load_class": "Energy Class",
        "load_occ": "Occupants Number",
        "load_cop": "Heat Pump Average COP/EER",
        "load_ev_check": "Enable Electric Vehicle (EV)",
        "eco_title": "💰 Financial Parameters & CAPEX",
        "eco_help": "💡 **Financial**: Energy prices pre-set on standard household baseline contracts.",
        "eco_capex_pv": "PV CAPEX (€/kWp)",
        "eco_capex_wind": "Micro-Wind CAPEX (€/kW)",
        "eco_capex_batt": "Home BESS CAPEX (€/kWh)",
        "eco_capex_v2h": "V2H/V2L Hardware CAPEX (€ - fixed)",
        "eco_price_buy": "Electricity Import Cost (€/kWh)",
        "eco_price_sell": "Electricity Export Rate (€/kWh)",
        "ev_section_title": "🚗 EV Mobility & Charging Strategy Settings",
        "ev_help": "💡 **EV Config**: Check hours when the car is plugged into the home wallbox. During unchecked slots, the vehicle travels draining battery.",
        "ev_cap": "EV Battery Capacity (kWh)",
        "ev_km": "Daily Distance (km)",
        "ev_whkm": "Specific Consumption (Wh/km)",
        "ev_v2hp": "Max Wallbox Power (kW)",
        "ev_v2heff": "Converter Efficiency (%)",
        "ev_grid_matrix": "Hourly Connection Matrix (Checked = Plugged at Home | Default: Overnight 20h-08h)",
        "gis_title": "📍 GIS Site Localization",
        "gis_search": "Search Municipality or Coordinates",
        "gis_btn": "🔍 Update Site Map",
        "gis_active": "**Active Site:**",
        "run_btn": "⚡ Run Dynamic Energy Simulation",
        "results_title": "📊 Simulation Output & EV Strategy Comparison",
        "results_help": "🔬 **Scenarios Breakdown**: \n1. **Standard Unidirectional**: Car charges immediately at max speed when plugged.\n2. **Smart Unidirectional**: Car charges only if local RES surplus is detected.\n3. **Bidirectional V2H/V2L**: Car absorbs surplus and discharges to feed home loads when needed.",
        "c1_title": "##### 🛑 1. Standard Unidirectional (Immediate)",
        "c2_title": "##### ☀️ 2. Smart Unidirectional (Surplus)",
        "c3_title": "##### 🔄 3. Bidirectional V2H + V2L Complete",
        "kpi_ac": "Self-Consumption",
        "kpi_ssp": "Self-Sufficiency (SSP)",
        "kpi_sc": "Renewable Share (SC)",
        "kpi_bill_savings": "Annual Savings",
        "kpi_tot_capex": "Total CAPEX",
        "kpi_payback": "Payback Period",
        "chart_gen_title": "Monthly Generation Profiles",
        "chart_load_title": "Monthly Demand Profiles (Heating vs Cooling)",
        "chart_eco_title": "Comparative Financial and Economic Analysis",
        "chart_x_month": "Month",
        "chart_y_kwh": "Energy [kWh]",
        "chart_y_eur": "Economic Value [€]",
        "season_title": "📈 Hourly State of Charge (SoC) Dynamics Across Strategies",
        "season_help": "🔬 **Chart Insight**: Observe how Bidirectional V2H/V2L (green dashed line) utilizes the vehicle as a grid-forming support asset, discharging to offset domestic peaks.",
        "inv": "Winter", "pri": "Spring", "est": "Summer", "aut": "Autumn",
        "inv_t": "❄️ Typical Winter Day (January)", "pri_t": "🌱 Typical Spring Day (April)", "est_t": "☀️ Typical Summer Day (July)", "aut_t": "🍂 Typical Autumn Day (October)",
        "chart_hourly_title": "Hourly Power Balance",
        "chart_soc_title": "EV Battery SoC Curves Comparison",
        "chart_h_x": "Time of Day [h]",
        "chart_h_y_flow": "Hourly Energy [kWh]",
        "chart_h_y_soc": "EV State of Charge [%]",
        "legend_fer": "RES Generation", 
        "legend_base_heat": "Base Load + Heating",
        "legend_ac": "Cooling Load (AC)",
        "legend_tot_ev": "Total Load + EV Charge",
        "legend_soc_s1": "SoC S1: Standard Unidirectional",
        "legend_soc_s2": "SoC S2: Smart Charging Surplus",
        "legend_soc_s3": "SoC S3: Bidirectional V2H/V2L",
        "legend_grid_on": "EV Connected to Home Grid",
        "final_chart_title": "📊 Comparative Analysis of Effective Monthly Self-Consumption",
        "final_chart_sub": "Share of local load covered internally across the 3 configurations",
        "final_x": "Month of the Year", "final_l1": "Gross Demand", "final_l2": "Standard Self-Cons", "final_l3": "Smart Self-Cons", "final_l4": "V2H/V2L Self-Cons",
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

# --- PANNELLO DI CONTROLLO Parametri ---
st.markdown(f"## {T['params_title']}")
exp_pv, exp_wind, exp_batt, exp_load = st.columns(4)

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
    battery_capacity_kwh = st.slider(T["batt_c"], 0, 50, 10)
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
    has_ev = st.checkbox(T["load_ev_check"], value=True) # ATTIVO DI DEFAULT

# --- ESPANDER VALUTAZIONE ECONOMICA ---
st.markdown("---")
with st.expander(T["eco_title"], expanded=False):
    st.markdown(f"<div class='custom-note'>{T['eco_help']}</div>", unsafe_allow_html=True)
    col_eco1, col_eco2, col_eco3 = st.columns(3)
    
    capex_pv_unit = col_eco1.number_input(T["eco_capex_pv"], min_value=100, max_value=5000, value=1500, step=50)
    capex_wind_unit = col_eco1.number_input(T["eco_capex_wind"], min_value=200, max_value=8000, value=2500, step=100)
    
    capex_batt_unit = col_eco2.number_input(T["eco_capex_batt"], min_value=100, max_value=3000, value=600, step=50)
    capex_v2h_fixed = col_eco2.number_input(T["eco_capex_v2h"], min_value=0, max_value=10000, value=2000, step=100)
    
    energy_buy_price = col_eco3.slider(T["eco_price_buy"], 0.05, 0.80, 0.24, step=0.01)
    energy_sell_price = col_eco3.slider(T["eco_price_sell"], 0.01, 0.40, 0.08, step=0.01)

# Sezione EV e Matrice oraria
ev_hours_status = [False] * 24
if has_ev:
    st.markdown(f"### {T['ev_section_title']}")
    st.markdown(f"<div class='custom-note'>{T['ev_help']}</div>", unsafe_allow_html=True)
        
    c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)
    ev_capacity_kwh = c_p1.slider(T["ev_cap"], 20, 120, 60)
    ev_km_day = c_p2.slider(T["ev_km"], 5, 200, 45) # PERMETTE LA MODIFICA DEI KM GIORNALIERI
    ev_efficiency_wh_km = c_p3.slider(T["ev_whkm"], 120, 250, 150)
    v2h_power_kw = c_p4.slider(T["ev_v2hp"], 3.0, 22.0, 7.4)
    v2h_eff = c_p5.slider(T["ev_v2heff"], 70, 100, 92) / 100.0
    
    daily_ev_demand_kwh = (ev_km_day * ev_efficiency_wh_km) / 1000.0
    ev_soc_min_reserve = ev_capacity_kwh * 0.20 # Riserva 20% minima invariabile
    
    st.markdown(f"**{T['ev_grid_matrix']}**")
    cols_grid = st.columns(24)
    for h_idx in range(24):
        default_state = (h_idx >= 19 or h_idx < 8) # default connesso la sera e notte
        ev_hours_status[h_idx] = cols_grid[h_idx].checkbox(f"{h_idx:02d}", value=default_state)
else:
    daily_ev_demand_kwh = 0

# --- SEZIONE LOCALIZZAZIONE GIS ---
st.markdown(f"### {T['gis_title']}")
col_loc1, col_loc2 = st.columns([1, 3])
with col_loc1:
    location_query = st.text_input(T["gis_search"], value="L'Aquila, Italia")
    if st.button(T["gis_btn"], use_container_width=True):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1"
            data = requests.get(geo_url, headers={"User-Agent": "EnergyGIS/1.0"}).json()
            if data: st.session_state.lat, st.session_state.lon = float(data[0]["lat"]), float(data[0]["lon"])
        except: pass
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

# --- CALCOLO CORE PROFILI ---
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
    rotor_area = math.pi * (80 / 2) ** 2
    average_power_kw = min((0.5 * 1.225 * rotor_area * 0.42 * (avg_speed ** 3)) / 1000, wind_power_kw)
    return {"annual_energy": average_power_kw * 8760, "wind_profiles": corrected_wind}

def build_typical_day_profiles(monthly_values, is_solar=True):
    profiles = {}
    for month_idx, monthly_energy in enumerate(monthly_values):
        profile = []
        for h in range(24):
            factor = max(0, math.sin((h - 6) / 12 * math.pi)) if is_solar else (0.85 + 0.3 * math.sin(h / 24 * 2 * math.pi))
            profile.append(monthly_energy / 30 * factor / (6 if is_solar else 24))
        profiles[month_idx + 1] = profile
    return profiles

def estimate_heating_and_cooling_demand():
    thermal_coefficients = {"A4": 12, "A3": 22, "A2": 32, "A1": 42, "B": 58, "C": 85, "D": 120}
    coeff = thermal_coefficients[building_class]
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2024-01-01&end_date=2024-12-31&hourly=temperature_2m"
    temperatures = requests.get(url).json()["hourly"]["temperature_2m"]
    
    monthly_hours = [744, 696, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    idx = 0
    monthly_heating, monthly_cooling = [], []
    for hours in monthly_hours:
        m_heat, m_cool = 0, 0
        for i in range(hours):
            t_loc = temperatures[idx + i]
            m_heat += max(0, 20 - t_loc) * coeff * house_area / 1000 / heat_pump_cop
            m_cool += max(0, t_loc - 25) * (coeff * 0.6) * house_area / 1000 / (heat_pump_cop * 0.9)
        monthly_heating.append(m_heat)
        monthly_cooling.append(m_cool)
        idx += hours
    monthly_base = [(1100 + occupants * 700) / 12] * 12
    return {"monthly_heating": monthly_heating, "monthly_cooling": monthly_cooling, "monthly_base": monthly_base}

# --- SIMULAZIONE ---
if st.button(T["run_btn"], type="primary", use_container_width=True):
    solar_monthly, wind_monthly = [0]*12, [0]*12
    solar_data = get_pvgis_data()
    if solar_data:
        solar_monthly = [m["E_m"] * (pv_efficiency / 20) for m in solar_data["outputs"]["monthly"]["fixed"]]
        solar_profiles = build_typical_day_profiles(solar_monthly, is_solar=True)
    wind_data = get_wind_data()
    if wind_data:
        wind_monthly = [(wind_data["annual_energy"] / 12 * (0.85 + 0.25 * math.sin(i / 12 * 2 * math.pi))) for i in range(12)]
        wind_profiles = build_typical_day_profiles(wind_monthly, is_solar=False)
        
    load_data = estimate_heating_and_cooling_demand()
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Costruzione profili base orari per mese
    hourly_prod, hourly_house_load, hourly_base_heat, hourly_ac = {}, {}, {}, {}
    for month in range(1, 13):
        p_p, l_p, bh_p, ac_p = [], [], [], []
        m_h = load_data["monthly_heating"][month-1]
        m_c = load_data["monthly_cooling"][month-1]
        m_b = load_data["monthly_base"][month-1]
        for h in range(24):
            prod = solar_profiles[month][h] + wind_profiles[month][h]
            ac_f = 1.2 * math.exp(-((h - 15) ** 2) / 6) if month in [6,7,8,9] else 0.0
            heat_f = (1.2 + 0.4 * math.exp(-((h - 7) ** 2) / 4) + 0.6 * math.exp(-((h - 20) ** 2) / 8)) if month in [1,2,3,10,11,12] else 0.0
            base_f = (0.8 + 0.5 * math.exp(-((h - 20) ** 2) / 12))
            
            hb = (m_b / 30 / 24) * base_f
            h_heat = (m_h / 30 / 24) * heat_f
            h_cool = (m_c / 30 / 24) * ac_f
            
            p_p.append(prod)
            l_p.append(hb + h_heat + h_cool)
            bh_p.append(hb + h_heat)
            ac_p.append(h_cool)
        hourly_prod[month] = p_p
        hourly_house_load[month] = l_p
        hourly_base_heat[month] = bh_p
        hourly_ac[month] = ac_p

    # --- SIMULAZIONE DELLE 3 STRATEGIE DI INTEGRAZIONE EV ---
    seasons_mapping = {T["inv"]: 1, T["pri"]: 4, T["est"]: 7, T["aut"]: 10}
    soc_tracking_ev = {s: {"s1": [], "s2": [], "s3": []} for s in seasons_mapping}
    
    # Inizializzazioni contatori annuali
    autoconsumo_s1, autoconsumo_s2, autoconsumo_s3 = 0, 0, 0
    surplus_sold_s1, surplus_sold_s2, surplus_sold_s3 = 0, 0, 0
    prelievo_grid_s1, prelievo_grid_s2, prelievo_grid_s3 = 0, 0, 0
    total_annual_load_s1, total_annual_load_s2, total_annual_load_s3 = 0, 0, 0
    
    monthly_ac_s1, monthly_ac_s2, monthly_ac_s3 = [], [], []
    monthly_gross_load_all = []

    # Condizioni iniziali SoC accumulatori fisici di casa (comuni)
    soc_house_s1, soc_house_s2, soc_house_s3 = soc_min, soc_min, soc_min
    # Condizioni iniziali SoC Auto EV
    soc_ev_s1, soc_ev_s2, soc_ev_s3 = ev_capacity_kwh, ev_capacity_kwh, ev_capacity_kwh

    for month in range(1, 13):
        days = days_in_months[month - 1]
        m_ac_s1, m_ac_s2, m_ac_s3 = 0, 0, 0
        m_gross_load = 0
        
        hours_outside = ev_hours_status.count(False)
        ev_hourly_travel_drain = daily_ev_demand_kwh / (hours_outside if hours_outside > 0 else 24) if has_ev else 0
        
        for day in range(days):
            for h in range(24):
                p_h = hourly_prod[month][h]
                l_house_h = hourly_house_load[month][h]
                connected = has_ev and ev_hours_status[h]
                
                # Scarica per viaggio (fuori casa)
                if has_ev and not connected:
                    soc_ev_s1 = max(ev_soc_min_reserve, soc_ev_s1 - ev_hourly_travel_drain)
                    soc_ev_s2 = max(ev_soc_min_reserve, soc_ev_s2 - ev_hourly_travel_drain)
                    soc_ev_s3 = max(ev_soc_min_reserve, soc_ev_s3 - ev_hourly_travel_drain)

                # ----------------------------------------------------
                # SCENARIO 1: Monodirezionale Standard (Ricarica Immediata)
                # ----------------------------------------------------
                ev_charge_demand_s1 = 0
                if connected and soc_ev_s1 < ev_capacity_kwh:
                    # Carica subito al massimo della potenza della colonnina fino a riempimento
                    ev_charge_demand_s1 = min(v2h_power_kw, (ev_capacity_kwh - soc_ev_s1) / v2h_eff)
                
                total_load_s1 = l_house_h + ev_charge_demand_s1
                m_gross_load += total_load_s1 if day==0 else 0 # traccia profilo mensile indicativo
                
                dir_s1 = min(p_h, total_load_s1)
                m_ac_s1 += dir_s1
                surp_s1, def_s1 = p_h - dir_s1, total_load_s1 - dir_s1
                
                if surp_s1 > 0 and battery_capacity_kwh > 0:
                    ch_h1 = min(surp_s1 * battery_eff, soc_max - soc_house_s1)
                    soc_house_s1 += ch_h1
                    surplus_sold_s1 += (surp_s1 - (ch_h1 / battery_eff))
                else: surplus_sold_s1 += surp_s1
                
                if def_s1 > 0 and battery_capacity_kwh > 0:
                    dis_h1 = min(def_s1, (soc_house_s1 - soc_min) * battery_eff)
                    soc_house_s1 -= (dis_h1 / battery_eff)
                    m_ac_s1 += dis_h1
                    prelievo_grid_s1 += (def_s1 - dis_h1)
                else: prelievo_grid_s1 += def_s1
                
                if connected and ev_charge_demand_s1 > 0:
                    # L'energia assorbita incrementa il SoC dell'auto
                    # se coperto da diretto o rete non importa alla logica, assorbe comunque
                    soc_ev_s1 = min(ev_capacity_kwh, soc_ev_s1 + (ev_charge_demand_s1 * v2h_eff))

                # ----------------------------------------------------
                # SCENARIO 2: Monodirezionale Smart (Solo su Surplus)
                # ----------------------------------------------------
                # Carico casa soddisfatto prioritariamente
                dir_house_s2 = min(p_h, l_house_h)
                m_ac_s2 += dir_house_s2
                surp_s2, def_s2 = p_h - dir_house_s2, l_house_h - dir_house_s2
                
                # Gestione batteria stazionaria casa prima dell'auto
                if surp_s2 > 0 and battery_capacity_kwh > 0:
                    ch_h2 = min(surp_s2 * battery_eff, soc_max - soc_house_s2)
                    soc_house_s2 += ch_h2
                    surp_s2 -= (ch_h2 / battery_eff)
                
                # Ricarica EV Intelligente solo se avanza surplus FER
                ev_charge_demand_s2 = 0
                if connected and surp_s2 > 0 and soc_ev_s2 < ev_capacity_kwh:
                    ev_charge_demand_s2 = min(min(v2h_power_kw, surp_s2), (ev_capacity_kwh - soc_ev_s2) / v2h_eff)
                    soc_ev_s2 = min(ev_capacity_kwh, soc_ev_s2 + (ev_charge_demand_s2 * v2h_eff))
                    m_ac_s2 += ev_charge_demand_s2
                    surp_s2 -= ev_charge_demand_s2
                
                # Se a fine giornata l'auto è ancora scarica sotto il livello di sicurezza dei km quotidiani, forza la ricarica da rete
                if connected and h == 23 and soc_ev_s2 < (ev_soc_min_reserve + daily_ev_demand_kwh):
                    forza_ch = (ev_soc_min_reserve + daily_ev_demand_kwh) - soc_ev_s2
                    soc_ev_s2 += forza_ch
                    prelievo_grid_s2 += (forza_ch / v2h_eff)
                    
                surplus_sold_s2 += surp_s2
                
                if def_s2 > 0:
                    if battery_capacity_kwh > 0 and soc_house_s2 > soc_min:
                        dis_h2 = min(def_s2, (soc_house_s2 - soc_min) * battery_eff)
                        soc_house_s2 -= (dis_h2 / battery_eff)
                        m_ac_s2 += dis_h2
                        def_s2 -= dis_h2
                    prelievo_grid_s2 += def_s2

                # ----------------------------------------------------
                # SCENARIO 3: Bidirezionale V2H + V2L Completo
                # ----------------------------------------------------
                dir_house_s3 = min(p_h, l_house_h)
                m_ac_s3 += dir_house_s3
                surp_s3, def_s3 = p_h - dir_house_s3, l_house_h - dir_house_s3
                
                # 1. Se c'è surplus carica prima casa e poi l'auto (V2H Charging)
                if surp_s3 > 0:
                    if battery_capacity_kwh > 0 and soc_house_s3 < soc_max:
                        ch_h3 = min(surp_s3 * battery_eff, soc_max - soc_house_s3)
                        soc_house_s3 += ch_h3
                        surp_s3 -= (ch_h3 / battery_eff)
                    if connected and surp_s3 > 0 and soc_ev_s3 < ev_capacity_kwh:
                        ch_ev3 = min(min(v2h_power_kw, surp_s3), (ev_capacity_kwh - soc_ev_s3) / v2h_eff)
                        soc_ev_s3 = min(ev_capacity_kwh, soc_ev_s3 + (ch_ev3 * v2h_eff))
                        m_ac_s3 += ch_ev3
                        surp_s3 -= ch_ev3
                    surplus_sold_s3 += surp_s3
                
                # 2. Se c'è deficit l'auto supporta la casa erogando potenza (Logica V2L / V2H Discharging)
                elif def_s3 > 0:
                    if connected and soc_ev_s3 > (ev_soc_min_reserve + 5): # Mantiene margine di sicurezza
                        dis_ev3 = min(min(v2h_power_kw, def_s3), (soc_ev_s3 - ev_soc_min_reserve) * v2h_eff)
                        soc_ev_s3 -= (dis_ev3 / v2h_eff)
                        def_s3 -= dis_ev3
                        m_ac_s3 += dis_ev3
                    if def_s3 > 0 and battery_capacity_kwh > 0 and soc_house_s3 > soc_min:
                        dis_h3 = min(def_s3, (soc_house_s3 - soc_min) * battery_eff)
                        soc_house_s3 -= (dis_h3 / battery_eff)
                        m_ac_s3 += dis_h3
                        def_s3 -= dis_h3
                    prelievo_grid_s3 += def_s3

                # Tracciamento stagionale orario dei SoC dell'auto
                for season_name, season_month in seasons_mapping.items():
                    if month == season_month and day == days - 1:
                        soc_tracking_ev[season_name]["s1"].append(soc_ev_s1 / ev_capacity_kwh * 100)
                        soc_tracking_ev[season_name]["s2"].append(soc_ev_s2 / ev_capacity_kwh * 100)
                        soc_tracking_ev[season_name]["s3"].append(soc_ev_s3 / ev_capacity_kwh * 100)

        autoconsumo_s1 += m_ac_s1
        autoconsumo_s2 += m_ac_s2
        autoconsumo_s3 += m_ac_s3
        
        monthly_ac_s1.append(m_ac_s1)
        monthly_ac_s2.append(m_ac_s2)
        monthly_ac_s3.append(m_ac_s3)
        monthly_gr_load = sum(hourly_house_load[month]) * days + (daily_ev_demand_kwh * days if has_ev else 0)
        monthly_gross_load_all.append(monthly_gr_load)

    # --- CALCOLO FINANZIARIO ---
    capex_base = (pv_power * capex_pv_unit) + (wind_power_kw * capex_wind_unit) + (battery_capacity_kwh * capex_batt_unit)
    capex_s1_tot = capex_base
    capex_s2_tot = capex_base
    capex_s3_tot = capex_base + capex_v2h_fixed
    
    savings_s1 = (autoconsumo_s1 * energy_buy_price) + (surplus_sold_s1 * energy_sell_price)
    savings_s2 = (autoconsumo_s2 * energy_buy_price) + (surplus_sold_s2 * energy_sell_price)
    savings_s3 = (autoconsumo_s3 * energy_buy_price) + (surplus_sold_s3 * energy_sell_price)
    
    payback_s1 = capex_s1_tot / savings_s1 if savings_s1 > 0 else 0
    payback_s2 = capex_s2_tot / savings_s2 if savings_s2 > 0 else 0
    payback_s3 = capex_s3_tot / savings_s3 if savings_s3 > 0 else 0

    # --- STAMPA RISULTATI SULL'INTERFACCIA ---
    st.markdown(f"## {T['results_title']}")
    st.markdown(f"<div class='custom-note-result'>{T['results_help']}</div>", unsafe_allow_html=True)
    
    col_sc1, col_sc2, col_sc3 = st.columns(3)
    
    with col_sc1:
        st.markdown(T["c1_title"])
        st.metric(T["kpi_ac"], f"{autoconsumo_s1:.0f} kWh")
        st.metric(T["kpi_bill_savings"], f"{savings_s1:.0f} €/anno")
        st.metric(T["kpi_payback"], f"{payback_s1:.1f} {T['chart_x_month']}i" if lang=="ITA" else f"{payback_s1:.1f} Years")
        
    with col_sc2:
        st.markdown(T["c2_title"])
        st.metric(T["kpi_ac"], f"{autoconsumo_s2:.0f} kWh", f"+{autoconsumo_s2-autoconsumo_s1:.0f} kWh")
        st.metric(T["kpi_bill_savings"], f"{savings_s2:.0f} €/anno", f"+{savings_s2-savings_s1:.0f} €")
        st.metric(T["kpi_payback"], f"{payback_s2:.1f} {T['chart_x_month']}i" if lang=="ITA" else f"{payback_s2:.1f} Years")
        
    with col_sc3:
        st.markdown(T["c3_title"])
        st.metric(T["kpi_ac"], f"{autoconsumo_s3:.0f} kWh", f"+{autoconsumo_s3-autoconsumo_s2:.0f} kWh")
        st.metric(T["kpi_bill_savings"], f"{savings_s3:.0f} €/anno", f"+{savings_s3-savings_s2:.0f} €")
        st.metric(T["kpi_payback"], f"{payback_s3:.1f} {T['chart_x_month']}i" if lang=="ITA" else f"{payback_s3:.1f} Years")

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