# app.py
import streamlit as st
import requests
import matplotlib.pyplot as plt
import folium
import math
from streamlit_folium import st_folium

# --- CONFIGURAZIONE INTERFACCIA ED ESTETICA ---
st.set_page_config(page_title="RES-Bsed Home Simulator", layout="wide")

# CSS Avanzato per layout ultra-compatto, font professionale e griglia orizzontale EV micro
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
    
    /* Stile Note Sempre Visibili - Più compatte e sobrie */
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
    
    /* Ottimizzazione micro-spazi per la griglia orizzontale 24h dell'EV */
    div[data-testid="column"] { padding: 0px 1px !important; }
    .stCheckbox { margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# --- DIZIONARIO DI TRADUZIONE BILINGUE (ITA / ENG) ---
LANG_DICT = {
    "ITA": {
        "title": "🌍 RES-Based Home Simulator by Prof. Eng. C. Villante - University of L'Aquila (Beta Version)",
        "subtitle": "Analisi quantitativa e modellazione geospaziale per micro-reti, accumuli stazionari ed ecosistemi V2H.",
        "params_title": "🎛️ Configurazione Parametri Tecnici",
        "pv_title": "☀️ Fotovoltaico (Max 20 kWp)",
        "pv_help": "💡 **PV**: 1 kWp occupa ~5-7 m². Tilt ottimale (inclinazione) in Italia: 30°-35°. Azimuth: 0° Sud, -90° Est, 90° Ovest.",
        "pv_p": "Potenza Impianto (kWp)",
        "pv_t": "Tilt Angle (°)",
        "pv_az": "Azimuth Angle (°)",
        "pv_eff": "Rendimento Modulo (%)",
        "wind_title": "🌬️ Micro-Eolico",
        "wind_help": "💡 **WT**: Si ipotizza di utilizzare per fini individuali una quota di potenza di un generatore da 2 MW di grande taglia. Estrapola la velocità del vento all'altezza del mozzo mediante legge di potenza dal dataset Open-Meteo.",
        "wind_p": "Potenza Nominale (kW)",
        "wind_h": "Altezza Mozzo (m)",
        "batt_title": "🔋 Accumulo Elettrochimico",
        "batt_help": "💡 **BESS**: Il DoD Max (profondità di scarica) preserva il ciclo di vita vincolando la capacità minima residua.",
        "batt_c": "Capacità Nominale (kWh)",
        "batt_eff": "Efficienza Round-Trip (%)",
        "batt_dod": "DoD Massimo (%)",
        "load_title": "🏠 Profilo Utenza & EV",
        "load_help": "💡 **Loads**: Calcola dinamicamente la firma termica invernale e il carico estivo di condizionamento (AC) incrociando la classe dell'edificio con le temperature storiche GIS locali.",
        "load_area": "Superficie Calpestabile (m²)",
        "load_class": "Classe Energetica",
        "load_occ": "Numero Occupanti",
        "load_cop": "COP/EER Medio Pompa Calore",
        "load_ev_check": "Abilita Veicolo Elettrico (EV)",
        "ev_section_title": "🚗 Integrazione e Profilo di Connessione V2H",
        "ev_help": "💡 **V2H Grid**: Riga temporale di disponibilità (00-23h). Nei periodi non smarcati, il veicolo è disconnesso ed applica il consumo dei km giornalieri.",
        "ev_cap": "Capacità Batteria EV (kWh)",
        "ev_km": "Distanza Giornaliera (km)",
        "ev_whkm": "Consumo Specifico (Wh/km)",
        "ev_v2hp": "Potenza Inverter V2H (kW)",
        "ev_v2heff": "Efficienza Convertitore (%)",
        "ev_grid_matrix": "Matrice di Disponibilità Oraria (Spuntato = Connesso V2H | Default: 20h-08h)",
        "gis_title": "📍 Posizionamento Geografico Impianto",
        "gis_search": "Cerca Comune o Coordinate",
        "gis_btn": "🔍 Aggiorna Mappa Sito",
        "gis_active": "**Sito Attivo:**",
        "run_btn": "⚡ Esegui Simulazione Energetica Dinamica",
        "results_title": "📊 Analisi Output e Indicatori di Performance",
        "results_help": "🔬 **Interpretazione KPI**:\n- **Autoconsumo**: Energia prodotta consumata localmente o salvata in batteria.\n- **Autosufficienza (SSP)**: % di carico coperto da autogenerazione. Abbassa la bolletta.\n- **Quota Rinnovabile (SC)**: % di produzione sfruttata in loco anziché immessa in rete.",
        "c1_title": "##### 🏛️ Analisi KPI Energetici",
        "c1_title_v2h": "##### 🏛️ Configurazione 1: Standard BESS (Casa)",
        "c2_title": "##### 🚗 Configurazione 2: Smart V2H Integrato",
        "kpi_ac": "Autoconsumo Complessivo",
        "kpi_ssp": "Autosufficienza (SSP)",
        "kpi_sc": "Quota Rinnovabile (SC)",
        "v2h_note": "🏅 **Analisi V2H**: L'integrazione bidirezionale trasforma l'auto in un accumulo domestico aggiuntivo, assorbendo il surplus diurno e supportando i carichi di condizionamento pomeridiani e i picchi serali.",
        "chart_gen_title": "Profili di Generazione Mensile",
        "chart_load_title": "Profili di Fabbisogno Mensile (Riscaldamento vs Condizionamento)",
        "chart_x_month": "Mese",
        "chart_y_kwh": "Energia [kWh]",
        "season_title": "📈 Dinamica Oraria Stagionale sui Giorni Medi",
        "season_help": "🔬 **Interpretazione Grafici Orari**:\n- I carichi termici di **Riscaldamento** e **Condizionamento (AC)** sono scorporati per evidenziare l'impatto specifico di ciascun vettore sul bilancio di potenza locale.",
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
        "legend_tot_no_ev": "Carico Totale Domestico",
        "legend_soc_h": "SoC Batteria Casa", "legend_soc_ev": "SoC Batteria EV (V2H)", "legend_grid_on": "Accoppiamento V2H Attivo",
        "final_chart_title": "📊 Analisi Energetica Mensile",
        "final_chart_sub": "Copertura Energetica ed Autoconsumo Mensile Effettivo",
        "final_x": "Mese dell'Anno", "final_l1": "Fabbisogno Utenza Lordo", "final_l2": "Autoconsumo Effettivo", "final_l2_bess": "Autoconsumo con BESS Standard", "final_l3": "Autoconsumo Integrato V2H",
        "months_labels": ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'],
        "hp_share": "Quota Riscaldamento",
        "ac_share": "Quota Condizionamento (AC)"
    },
    "ENG": {
        "title": "🌍 Energy GIS Simulator",
        "subtitle": "Quantitative analysis and geospatial modeling for micro-grids, stationary storage, and V2H ecosystems.",
        "params_title": "🎛️ Technical Parameters Configuration",
        "pv_title": "☀️ Photovoltaic (Max 20 kWp)",
        "pv_help": "💡 **PV**: 1 kWp requires ~5-7 m². Optimal Tilt in Italy: 30°-35°. Azimuth: 0° South, -90° East, 90° West.",
        "pv_p": "System Power (kWp)",
        "pv_t": "Tilt Angle (°)",
        "pv_az": "Azimuth Angle (°)",
        "pv_eff": "Module Efficiency (%)",
        "wind_title": "🌬️ Micro-Wind",
        "wind_help": "💡 **WT**: Hypotesis is made to uindividually use a power fraction of a big-size 2MW wind generator. Extrapolates wind speed at hub height using power law from the Open-Meteo reanalysis dataset.",
        "wind_p": "Nominal Power (kW)",
        "wind_d": "Rotor Diameter (m)",
	"wind_h": "Hub height (m)",
        "batt_title": "🔋 Electrochemical Storage (BESS)",
        "batt_help": "💡 **BESS**: Max DoD (Depth of Discharge) preserves battery cycle life by setting a minimum residual energy constraint.",
        "batt_c": "Nominal Capacity (kWh)",
        "batt_eff": "Round-Trip Efficiency (%)",
        "batt_dod": "Max DoD (%)",
        "load_title": "🏠 Load Profile & EV",
        "load_help": "💡 **Loads**: Dynamically computes winter heating and summer cooling (AC) demands by intersecting the building class with historical local GIS temperature data.",
        "load_area": "Floor Area (m²)",
        "load_class": "Energy Class",
        "load_occ": "Occupants Number",
        "load_cop": "Heat Pump Average COP/EER",
        "load_ev_check": "Enable Electric Vehicle (EV)",
        "ev_section_title": "🚗 V2H Integration & Connection Profile",
        "ev_help": "💡 **V2H Grid**: Timeline availability grid (00-23h). During unchecked periods, the vehicle is traveling and drains power based on daily km.",
        "ev_cap": "EV Battery Capacity (kWh)",
        "ev_km": "Daily Distance (km)",
        "ev_whkm": "Specific Consumption (Wh/km)",
        "ev_v2hp": "V2H Inverter Power (kW)",
        "ev_v2heff": "Converter Efficiency (%)",
        "ev_grid_matrix": "Hourly Availability Matrix (Checked = V2H Grid Tied | Default: 20h-08h)",
        "gis_title": "📍 GIS Site Localization",
        "gis_search": "Search Municipality or Coordinates",
        "gis_btn": "🔍 Update Site Map",
        "gis_active": "**Active Site:**",
        "run_btn": "⚡ Run Dynamic Energy Simulation",
        "results_title": "📊 Simulation Output & Performance Indicators",
        "results_help": "🔬 **KPI Interpretation**:\n- **Self-Consumption**: Generated energy consumed locally or stored in batteries.\n- **Self-Sufficiency (SSP)**: % of total load covered by self-generation. Reduces electricity bills.\n- **Renewable Share (SC)**: % of total generation utilized locally instead of being fed into the grid.",
        "c1_title": "##### 🏛️ Energy KPI Analysis",
        "c1_title_v2h": "##### 🏛️ Configuration 1: Standard BESS (Home)",
        "c2_title": "##### 🚗 Configuration 2: Smart Integrated V2H",
        "kpi_ac": "Total Self-Consumption",
        "kpi_ssp": "Self-Sufficiency (SSP)",
        "kpi_sc": "Renewable Share (SC)",
        "v2h_note": "🏅 **V2H Analysis**: Bidirectional coupling transforms the EV into an automated mobile BESS, buffering midday solar surplus, powering afternoon cooling loads, and discharging during evening peaks.",
        "chart_gen_title": "Monthly Generation Profiles",
        "chart_load_title": "Monthly Demand Profiles (Heating vs Cooling)",
        "chart_x_month": "Month",
        "chart_y_kwh": "Energy [kWh]",
        "season_title": "📈 Hourly Seasonal Dynamics on Average Days",
        "season_help": "🔬 **Hourly Charts Interpretation**:\n- **Heating** and **Cooling (AC)** loads are uncoupled to highlight the unique impact of each thermal vector on the net power balance.",
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
        "legend_tot_no_ev": "Total Household Load",
        "legend_soc_h": "Home BESS SoC", "legend_soc_ev": "EV Battery SoC (V2H)", "legend_grid_on": "V2H Grid Tied Active",
        "final_chart_title": "📊 Monthly Energy Analysis",
        "final_chart_sub": "Energy Coverage and Effective Monthly Self-Consumption",
        "final_x": "Month of the Year", "final_l1": "Gross Load", "final_l2": "Effective Self-Consumption", "final_l2_bess": "Self-Consumption with Standard BESS", "final_l3": "V2H Integrated Self-Consumption",
        "months_labels": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dic'],
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

# --- PANNELLO DI CONTROLLO IN ALTO ---
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
    battery_capacity_kwh = st.slider(T["batt_c"], 0, 100, 20)
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
    has_ev = st.checkbox(T["load_ev_check"], value=False)

# Configurazione EV & Matrice Oraria Orrizzontale disposta SOTTO ai prompt
ev_hours_status = [False] * 24
if has_ev:
    st.markdown(f"### {T['ev_section_title']}")
    st.markdown(f"<div class='custom-note'>{T['ev_help']}</div>", unsafe_allow_html=True)
        
    c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)
    ev_capacity_kwh = c_p1.slider(T["ev_cap"], 20, 150, 50)
    ev_km_day = c_p2.slider(T["ev_km"], 10, 150, 40)
    ev_efficiency_wh_km = c_p3.slider(T["ev_whkm"], 120, 250, 160)
    v2h_power_kw = c_p4.slider(T["ev_v2hp"], 2.3, 22.0, 6.0)
    v2h_eff = c_p5.slider(T["ev_v2heff"], 70, 100, 90) / 100.0
    
    daily_ev_demand_kwh = (ev_km_day * ev_efficiency_wh_km) / 1000.0
    annual_ev_kwh = daily_ev_demand_kwh * 365
    ev_soc_travel_min = daily_ev_demand_kwh + (ev_capacity_kwh * 0.2)
        
    st.markdown(f"**{T['ev_grid_matrix']}**")
    cols_grid = st.columns(24)
    for h_idx in range(24):
        default_state = (h_idx >= 20 or h_idx < 8)
        ev_hours_status[h_idx] = cols_grid[h_idx].checkbox(f"{h_idx:02d}", value=default_state)
else:
    annual_ev_kwh, daily_ev_demand_kwh = 0, 0

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
            else: st.error("Error location" if lang=="ENG" else "Località non trovata")
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
    rotor_diameter = 80
    rotor_area = math.pi * (rotor_diameter / 2) ** 2
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
    thermal_coefficients = {"A4": 15, "A3": 25, "A2": 35, "A1": 45, "B": 60, "C": 90, "D": 130}
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
            # Riscaldamento (Inverno T < 20°C)
            m_heat += max(0, 20 - t_loc) * coeff * house_area / 1000 / heat_pump_cop
            # Raffrescamento (Estate T > 25°C)
            m_cool += max(0, t_loc - 25) * (coeff * 0.6) * house_area / 1000 / (heat_pump_cop * 0.9)
            
        monthly_heating.append(m_heat)
        monthly_cooling.append(m_cool)
        idx += hours
        
    monthly_base = [(1200 + occupants * 750) / 12] * 12
    monthly_ev = [annual_ev_kwh / 12] * 12 if has_ev else [0] * 12
    total_monthly = [monthly_heating[i] + monthly_cooling[i] + monthly_base[i] + monthly_ev[i] for i in range(12)]
    return {"monthly_total": total_monthly, "monthly_heating": monthly_heating, "monthly_cooling": monthly_cooling, "monthly_base": monthly_base}

# --- GENERAZIONE REPORT ED ANALISI ---
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
    monthly_load = load_data["monthly_total"]
    total_annual_load = sum(monthly_load)
    total_monthly_prod = [s + w for s, w in zip(solar_monthly, wind_monthly)]
    total_annual_prod = sum(total_monthly_prod)

    st.markdown(f"## {T['results_title']}")
    st.markdown(f"<div class='custom-note-result'>{T['results_help']}</div>", unsafe_allow_html=True)

    # --- CALCOLO MODELLI DI ACCUMULO ---
    hourly_prod_dict, hourly_load_dict, hourly_base_heat_load, hourly_ac_only_load = {}, {}, {}, {}
    for month in range(1, 13):
        p_profile, l_profile, base_heat_profile, ac_profile = [], [], [], []
        
        m_heating = load_data["monthly_heating"][month-1]
        m_cooling = load_data["monthly_cooling"][month-1]
        m_base = load_data["monthly_base"][month-1]
        
        for h in range(24):
            prod = solar_profiles[month][h] + wind_profiles[month][h]
            
            # Profilazione oraria distinta dei carichi termici
            ac_factor = 1.2 * math.exp(-((h - 15) ** 2) / 6) if month in [6,7,8,9] else 0.0
            heat_factor = (1.2 + 0.4 * math.exp(-((h - 7) ** 2) / 4) + 0.6 * math.exp(-((h - 20) ** 2) / 8)) if month in [1,2,3,10,11,12] else 0.0
            base_factor = (0.8 + 0.5 * math.exp(-((h - 20) ** 2) / 12))
            
            h_base = (m_base / 30 / 24) * base_factor
            h_heating = (m_heating / 30 / 24) * heat_factor
            h_cooling = (m_cooling / 30 / 24) * ac_factor
            
            p_profile.append(prod)
            l_profile.append(h_base + h_heating + h_cooling + (annual_ev_kwh / 12 / 30 / 24 if has_ev else 0))
            base_heat_profile.append(h_base + h_heating)
            ac_profile.append(h_cooling)
            
        hourly_prod_dict[month] = p_profile
        hourly_load_dict[month] = l_profile
        hourly_base_heat_load[month] = base_heat_profile
        hourly_ac_only_load[month] = ac_profile

    # STRATEGIA 1: Standard BESS
    current_soc_house_s1 = soc_min
    total_autoconsumo_s1 = 0
    monthly_autoconsumo_s1 = []
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Mappatura per il tracciamento orario stagionale della sola strategia BESS Standard (quando has_ev è False)
    seasons_mapping = {T["inv"]: 1, T["pri"]: 4, T["est"]: 7, T["aut"]: 10}
    seasonal_hourly_data_s1 = {s: {"soc_house": [], "prod": [], "load_base_heat": [], "load_ac": [], "load_total": []} for s in seasons_mapping}

    for month in range(1, 13):
        m_direct, m_batt, days = 0, 0, days_in_months[month - 1]
        for day in range(days):
            for h in range(24):
                prod_h, load_h = hourly_prod_dict[month][h], hourly_load_dict[month][h]
                diretto = min(prod_h, load_h)
                m_direct += diretto
                surplus, deficit = prod_h - diretto, load_h - diretto
                if surplus > 0 and battery_capacity_kwh > 0:
                    charge = min(surplus * battery_eff, soc_max - current_soc_house_s1)
                    current_soc_house_s1 += charge
                elif deficit > 0 and battery_capacity_kwh > 0:
                    discharge = min(deficit, (current_soc_house_s1 - soc_min) * battery_eff)
                    current_soc_house_s1 -= (discharge / battery_eff)
                    m_batt += discharge
                
                # Salva i dati orari dell'ultimo giorno del mese per i grafici (usati solo se non c'è l'EV)
                if not has_ev:
                    for season_name, season_month in seasons_mapping.items():
                        if month == season_month and day == days - 1:
                            seasonal_hourly_data_s1[season_name]["soc_house"].append(current_soc_house_s1)
                            seasonal_hourly_data_s1[season_name]["prod"].append(prod_h)
                            seasonal_hourly_data_s1[season_name]["load_base_heat"].append(hourly_base_heat_load[month][h])
                            seasonal_hourly_data_s1[season_name]["load_ac"].append(hourly_ac_only_load[month][h])
                            seasonal_hourly_data_s1[season_name]["load_total"].append(load_h)
                            
        monthly_autoconsumo_s1.append(m_direct + m_batt)
        total_autoconsumo_s1 += (m_direct + m_batt)

    ssp_s1 = (total_autoconsumo_s1 / total_annual_load) * 100
    sc_s1 = (total_autoconsumo_s1 / total_annual_prod) * 100

    if has_ev:
        # STRATEGIA 2: V2H Ottimizzato (Eseguito solo se l'EV è abilitato)
        current_soc_house_s2 = soc_min
        current_soc_ev = ev_capacity_kwh
        total_autoconsumo_s2 = 0
        monthly_autoconsumo_s2 = []
        seasonal_hourly_data = {s: {"soc_house": [], "soc_ev": [], "prod": [], "load_base_heat": [], "load_ac": [], "load_total_with_ev_charge": []} for s in seasons_mapping}
        
        for month in range(1, 13):
            m_direct, m_storage, days = 0, 0, days_in_months[month - 1]
            for day in range(days):
                hours_outside = ev_hours_status.count(False)
                ev_hourly_travel_drain = daily_ev_demand_kwh / (hours_outside if hours_outside > 0 else 24)
                    
                for h in range(24):
                    prod_h = hourly_prod_dict[month][h]
                    load_house_pure = hourly_load_dict[month][h]
                    connected = ev_hours_status[h]
                    if not connected:
                        current_soc_ev = max(0.0, current_soc_ev - ev_hourly_travel_drain)
                    
                    diretto = min(prod_h, load_house_pure)
                    m_direct += diretto
                    surplus, deficit = prod_h - diretto, load_house_pure - diretto
                    initial_ev_soc_for_tracking = current_soc_ev
                    
                    if surplus > 0:
                        if battery_capacity_kwh > 0 and current_soc_house_s2 < soc_max:
                            charge_h = min(surplus * battery_eff, soc_max - current_soc_house_s2)
                            current_soc_house_s2 += charge_h
                            surplus -= (charge_h / battery_eff)
                        if connected and surplus > 0 and current_soc_ev < ev_capacity_kwh:
                            charge_ev = min(min(v2h_power_kw, surplus) * v2h_eff, ev_capacity_kwh - current_soc_ev)
                            current_soc_ev += charge_ev
                    elif deficit > 0:
                        if connected and current_soc_ev > ev_soc_travel_min:
                            discharge_ev = min(min(v2h_power_kw, deficit), (current_soc_ev - ev_soc_travel_min) * v2h_eff)
                            current_soc_ev -= (discharge_ev / v2h_eff)
                            deficit -= discharge_ev
                            m_storage += discharge_ev
                        if deficit > 0 and battery_capacity_kwh > 0 and current_soc_house_s2 > soc_min:
                            discharge_h = min(deficit, (current_soc_house_s2 - soc_min) * battery_eff)
                            current_soc_house_s2 -= (discharge_h / battery_eff)
                            m_storage += discharge_h
                            
                    if connected and current_soc_ev < ev_capacity_kwh:
                        hours_to_go = sum(1 for future_h in range(h, 24) if ev_hours_status[future_h])
                        if hours_to_go <= 3 or (ev_capacity_kwh - current_soc_ev) >= (hours_to_go * v2h_power_kw * v2h_eff):
                            actual_ev_charge = min(min(v2h_power_kw, (ev_capacity_kwh - current_soc_ev) / v2h_eff) * v2h_eff, ev_capacity_kwh - current_soc_ev)
                            current_soc_ev += actual_ev_charge
                    
                    ev_net_charge_demand = max(0.0, (current_soc_ev - initial_ev_soc_for_tracking) / v2h_eff) if connected else 0.0
                    instantaneous_total_load = load_house_pure + ev_net_charge_demand
                    
                    for season_name, season_month in seasons_mapping.items():
                        if month == season_month and day == days - 1:
                            seasonal_hourly_data[season_name]["soc_house"].append(current_soc_house_s2)
                            seasonal_hourly_data[season_name]["soc_ev"].append(current_soc_ev)
                            seasonal_hourly_data[season_name]["prod"].append(prod_h)
                            seasonal_hourly_data[season_name]["load_base_heat"].append(hourly_base_heat_load[month][h])
                            seasonal_hourly_data[season_name]["load_ac"].append(hourly_ac_only_load[month][h])
                            seasonal_hourly_data[season_name]["load_total_with_ev_charge"].append(instantaneous_total_load)
                            
            monthly_autoconsumo_s2.append(m_direct + m_storage)
            total_autoconsumo_s2 += (m_direct + m_storage)

        ssp_s2 = (total_autoconsumo_s2 / total_annual_load) * 100
        sc_s2 = (total_autoconsumo_s2 / total_annual_prod) * 100

        # METRICHE DI CONFRONTO A DUE COLONNE (EV Abilitato)
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(T["c1_title_v2h"])
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric(T["kpi_ac"], f"{total_autoconsumo_s1:.0f} kWh")
            c_m2.metric(T["kpi_ssp"], f"{ssp_s1:.1f} %")
            c_m3.metric(T["kpi_sc"], f"{sc_s1:.1f} %")
        with col_m2:
            st.markdown(T["c2_title"])
            c_m4, c_m5, c_m6 = st.columns(3)
            c_m4.metric(T["kpi_ac"], f"{total_autoconsumo_s2:.0f} kWh", f"+{total_autoconsumo_s2 - total_autoconsumo_s1:.0f} kWh")
            c_m5.metric(T["kpi_ssp"], f"{ssp_s2:.1f} %", f"{ssp_s2 - ssp_s1:.1f} %")
            c_m6.metric(T["kpi_sc"], f"{sc_s2:.1f} %", f"{sc_s2 - sc_s1:.1f} %")
            
        st.markdown(f"<div class='custom-note-result'>{T['v2h_note']}</div>", unsafe_allow_html=True)
    else:
        # METRICHE SINGOLE COMPATTE (EV Disabilitato)
        st.markdown(T["c1_title"])
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric(T["kpi_ac"], f"{total_autoconsumo_s1:.0f} kWh")
        c_m2.metric(T["kpi_ssp"], f"{ssp_s1:.1f} %")
        c_m3.metric(T["kpi_sc"], f"{sc_s1:.1f} %")

    # --- MACRO BILANCI MENSILI ANNUALE ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig, ax = plt.subplots(figsize=(6, 2.2), dpi=200)
        ax.plot(range(1, 13), solar_monthly, label="PV" if lang=="ENG" else "Fotovoltaico", color="#D97706", lw=1.2)
        ax.bar(range(1, 13), wind_monthly, label="Wind" if lang=="ENG" else "Eolico", color="#2563EB", alpha=0.15, width=0.35)
        ax.plot(range(1, 13), total_monthly_prod, label="Total" if lang=="ENG" else "Generazione Totale", color="#059669", lw=1.6)
        setup_plot_style(ax, T["chart_gen_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax.legend(fontsize=6.5, frameon=False, loc="upper right")
        st.pyplot(fig)
    with col_g2:
        fig, ax = plt.subplots(figsize=(6, 2.2), dpi=200)
        ax.plot(range(1, 13), monthly_load, label="Total Demand" if lang=="ENG" else "Fabbisogno Complessivo", color="#DC2626", lw=1.6)
        ax.fill_between(range(1, 13), load_data["monthly_heating"], color="#EF4444", alpha=0.12, label=T["hp_share"])
        ax.fill_between(range(1, 13), load_data["monthly_cooling"], color="#0284C7", alpha=0.18, label=T["ac_share"])
        setup_plot_style(ax, T["chart_load_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax.legend(fontsize=6.5, frameon=False, loc="upper right")
        st.pyplot(fig)

    # --- ANALISI IN CASCATA DELLE SIMULAZIONI STAGIONALI ---
    st.markdown("---")
    st.subheader(T["season_title"])
    st.markdown(f"<div class='custom-note'>{T['season_help']}</div>", unsafe_allow_html=True)

    seasons_list = [T["inv"], T["pri"], T["est"], T["aut"]]
    titles_list = [T["inv_t"], T["pri_t"], T["est_t"], T["aut_t"]]
    
    for season_name, section_title in zip(seasons_list, titles_list):
        st.markdown(f"#### {section_title}")
        col_chart1, col_chart2 = st.columns(2)
        
        # Recupera il dizionario dati corretto a seconda dello scenario EV attivo o no
        s_data = seasonal_hourly_data[season_name] if has_ev else seasonal_hourly_data_s1[season_name]
        
        with col_chart1:
            fig_f1, ax_f1 = plt.subplots(figsize=(6, 2.4), dpi=200)
            ax_f1.plot(range(24), s_data["prod"], label=T["legend_fer"], color="#059669", lw=1.5)
            ax_f1.plot(range(24), s_data["load_base_heat"], label=T["legend_base_heat"], color="#475569", lw=1.1)
            
            if sum(s_data["load_ac"]) > 0:
                ax_f1.plot(range(24), s_data["load_ac"], label=T["legend_ac"], color="#0284C7", lw=1.1, linestyle="--")
                
            if has_ev:
                ax_f1.fill_between(range(24), s_data["load_total_with_ev_charge"], color="#EF4444", alpha=0.06, label=T["legend_tot_ev"])
            else:
                ax_f1.fill_between(range(24), s_data["load_total"], color="#EF4444", alpha=0.06, label=T["legend_tot_no_ev"])
                
            setup_plot_style(ax_f1, f"{T['chart_hourly_title']} - {season_name}", T["chart_h_x"], T["chart_h_y_flow"])
            ax_f1.legend(fontsize=6.5, frameon=False, loc="upper left")
            ax_f1.set_xlim(0, 23)
            st.pyplot(fig_f1)
            
        with col_chart2:
            fig_f2, ax_f2 = plt.subplots(figsize=(6, 2.4), dpi=200)
            soc_h_pct = [v / battery_capacity_kwh * 100 if battery_capacity_kwh > 0 else 0 for v in s_data["soc_house"]]
            ax_f2.plot(range(24), soc_h_pct, label=T["legend_soc_h"], color='#D97706', lw=1.3, marker='s', markersize=1.5)
            
            if has_ev:
                soc_e_pct = [v / ev_capacity_kwh * 100 for v in s_data["soc_ev"]]
                ax_f2.plot(range(24), soc_e_pct, label=T["legend_soc_ev"], color='#0F766E', lw=1.3, marker='o', markersize=1.5)
                ax_f2.fill_between(range(24), 0, 100, where=ev_hours_status, color='#10B981', alpha=0.03, label=T["legend_grid_on"])
            
            setup_plot_style(ax_f2, f"{T['chart_soc_title']} - {season_name}", T["chart_h_x"], T["chart_h_y_soc"])
            ax_f2.set_ylim(-5, 105)
            ax_f2.set_xlim(0, 23)
            ax_f2.set_xticks(range(0, 24, 2))
            ax_f2.legend(fontsize=6.5, frameon=False, loc="lower left")
            st.pyplot(fig_f2)

    # --- SINTESI MENSILE SULL'ANNO ---
    st.markdown("---")
    st.subheader(T["final_chart_title"])
    fig12, ax12 = plt.subplots(figsize=(12, 2.4), dpi=200)
    x_idx = range(1, 13)
    
    if has_ev:
        ax12.bar([x - 0.18 for x in x_idx], monthly_load, width=0.22, label=T["final_l1"], color='#94A3B8', alpha=0.3)
        ax12.bar([x for x in x_idx], monthly_autoconsumo_s1, width=0.22, label=T["final_l2_bess"], color='#EA580C', alpha=0.8)
        ax12.bar([x + 0.18 for x in x_idx], monthly_autoconsumo_s2, width=0.22, label=T["final_l3"], color='#0D9488', alpha=0.9)
    else:
        ax12.bar([x - 0.11 for x in x_idx], monthly_load, width=0.22, label=T["final_l1"], color='#94A3B8', alpha=0.3)
        ax12.bar([x + 0.11 for x in x_idx], monthly_autoconsumo_s1, width=0.22, label=T["final_l2"], color='#EA580C', alpha=0.8)
        
    setup_plot_style(ax12, T["final_chart_sub"], T["final_x"], T["chart_y_kwh"])
    ax12.set_xticks(x_idx)
    ax12.set_xticklabels(T["months_labels"])
    ax12.legend(fontsize=7, frameon=False, loc="upper right")
    st.pyplot(fig12)

# --- FOOTER INTERFACCIA ---
st.markdown("---")
st.caption("Engine: PVGIS API & Open-Meteo Reanalysis Model | Geocoding: Nominatim OSM | Frontend: Streamlit Clean Core Dual-Lang")