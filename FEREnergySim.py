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
    .stNumberInput > label, .stSelectbox > label, .stTextInput > label, .stCheckbox > label { font-size: 0.78rem !important; font-weight: 500; color: #475569; }
    .stMetric { background-color: #F8FAFC; padding: 0.4rem 0.6rem; border-radius: 0.375rem; border: 1px solid #E2E8F0; }
    div[data-testid="stExpander"] { border: 1px solid #E2E8F0 !important; box-shadow: none !important; margin-bottom: 0.4rem; }
    .custom-note { padding: 0.5rem 0.75rem; border-radius: 0.25rem; font-size: 0.8rem; background-color: #F8FAFC; color: #475569; border-left: 3px solid #3B82F6; margin-bottom: 0.6rem; line-height: 1.3; }
    .custom-note-result { padding: 0.6rem 0.75rem; border-radius: 0.25rem; font-size: 0.82rem; background-color: #F0FDF4; color: #166534; border-left: 3px solid #22C55E; margin-bottom: 0.8rem; }
    div[data-testid="column"] { padding: 0px 1px !important; }
    
    .compare-card { background: #FFFFFF; border: 1px solid #E2E8F0; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem; width: 100%; display: block; }
    .compare-item { margin-bottom: 0.6rem; }
    .compare-label { font-size: 0.82rem; font-weight: 600; color: #334155; margin-bottom: 0.4rem; }
    .compare-bar-container { background: #E2E8F0; border-radius: 0.25rem; height: 10px; width: 100%; position: relative; margin-top: 0.1rem; margin-bottom: 0.1rem; }
    .compare-bar-fill { height: 100%; border-radius: 0.25rem; }
    .compare-val { font-size: 0.85rem; font-weight: 700; color: #0F172A; text-align: right; margin-top: 0.1rem; }
    </style>
""", unsafe_allow_html=True)

LANG_DICT = {
    "ITA": {
        "title": "🌍 Simulatore Residenziale FER (8760h continuo) - Prof. Ing. C. Villante",
        "subtitle": "Modellazione dinamica oraria su base annua (8760 punti) per micro-reti accoppiate a sistemi BESS e V2H.",
        "doc_expander_title": "📖 Spiegazione Architettura del Codice e Flussi Dati a 8760 ore (Technical Documentation)",
        "doc_global_text": "Questo simulatore esegue un'analisi energetica dinamica oraria sequenziale su 8760 ore continuative.",
        "guide_metrics_title": "📊 Guida all'Interpretazione dei KPI e Indicatori Finanziari",
        "guide_metrics_text": "Fornisce indicazioni chiare su Autoconsumo, Autosufficienza e tempo di ammortamento semplice (Payback Period).",
        "guide_macro_charts_title": "📉 Guida ai Grafici di Sintesi Mensile (Macro Bilanci)",
        "guide_macro_charts_text": "Grafici aggregati di generazione e fabbisogno su base mensile con scorporo dei sottocarichi termici.",
        "guide_hourly_charts_title": "⏱️ Analisi dinamica oraria.",
        "guide_8760_charts_title": "📈 Guida all'Analisi delle Curve Continue Annuali (8760 ore Interattive)",
        "guide_8760_charts_text": "Visualizzazione continua oraria sull'intero anno con possibilità di zoom interattivo tramite lo slider.",
        "params_title": "🎛️ Configurazione Parametri Tecnici ed Economici",
        "pv_title": "☀️ Fotovoltaico (Max 20 kWp)",
        "pv_help": "💡 1 kWp occupa ~5-7 m². Inclinazione ottimale in Italia: 30°-35°.",
        "wind_title": "🌬️ Micro-Eolico",
        "wind_help": "💡 Profilo orario a 8760 punti riscalato con la legge logaritmica sull'altezza mozzo.",
        "batt_title": "🔋 Accumulo Stazionario (BESS)",
        "batt_help": "💡 Il DoD Max preserva la vita dell'accumulo vincolando la carica minima oraria residua.",
        "load_title": "🏠 Profilo Utenza & Edificio",
        "load_help": "💡 Calcola la firma termica oraria integrando i dati storici ambientali Open-Meteo.",
        "eco_title": "💰 Parametri Economici & Tariffe Grid",
        "eco_help": "💡 Inserisci i costi per valutare il tempo di ammortamento semplice.",
        "load_ev_check": "Abilita Veicolo Elettrico (EV)",
        "ev_section_title": "🚗 Configurazione Connessione & Infrastruttura di Ricarica EV (Algoritmo Predittivo orario)",
        "ev_help": "💡 Convenzione Oraria: Il veicolo si intende connesso alla Wallbox a partire dal primo minuto dell'ora di inizio indicata, fino all'ultimo minuto dell'ora di fine.",
        "pv_p": "Potenza Impianto (kWp)", "pv_t": "Tilt Angle (°)", "pv_az": "Azimuth Angle (°)", "pv_eff": "Rendimento Modulo (%)",
        "wind_p": "Potenza Nominale (kW)", "wind_h": "Altezza Mozzo (m)",
        "batt_c": "Capacità Nominale (kWh)", "batt_eff": "Efficienza Round-Trip (%)", "batt_dod": "DoD Massimo (%)",
        "load_area": "Superficie Calpestabile (m²)", "load_class": "Classe Energetica", "load_occ": "Numero Occupanti", "load_cop": "COP/EER Medio Pompa Calore",
        "eco_cost": "Costo Energia Prelevata (€/kWh)", "eco_sell": "Tariffa Immissione / RID (€/kWh)", "eco_capex": "CAPEX Impianto Base (PV+Wind) (€)",
        "ev_cap": "Capacità Batteria EV (kWh)", "ev_km": "Distanza Giornaliera (km)", "ev_whkm": "Consumo Specifico (Wh/km)",
        "ev_v2hp": "Potenza Wallbox / Inverter V2H (kW)", "ev_v2heff": "Efficienza Convertitore (%)", "ev_soc_min": "SoC Minimo di Sicurezza per Viaggio (%)",
        "ev_capex_s1": "Costo Aggiuntivo Wallbox S1 Standard (€)", "ev_capex_s2": "Costo Aggiuntivo Smart Wallbox S2 (€)", "ev_capex_s3": "Costo Aggiuntivo Stazione Bidirezionale V2H S3 (€)",
        "gis_title": "📍 Posizionamento Geografico Impianto", "gis_search": "Cerca Comune o Coordinate", "gis_btn": "🔍 Aggiorna Mappa Sito", "gis_active": "**Sito Attivo:**",
        "run_btn": "⚡ Esegui Simulazione Energetica Dinamica (8760 Punti)",
        "results_title": "📊 Analisi Output e Indicatori di Performance Annuali",
        "results_help": "🔬 Risultati consolidati sull'orizzonte temporale continuo di 8760 ore annuali.",
        "kpi_ac": "Autoconsumo", "kpi_bill_savings": "Risparmio Economico", "kpi_payback": "Tempo di Ritorno",
        "chart_gen_title": "Profili di Generazione Mensile Integrata", "chart_load_title": "Profili di Fabbisogno Mensile Integrato (Dettaglio Sottocarichi Domestici)",
        "chart_x_month": "Mese", "chart_y_kwh": "Energia [kWh]",
        "season_title": "📈 Dinamica Oraria Dettagliata sui Giorni Tipici Reali Selezionati",
        "inv": "Inverno (15 Gennaio - Lunedì)", "pri": "Primavera (15 Aprile - Lunedì)", "est": "Estate (15 Luglio - Lunedì)", "aut": "Autunno (15 Ottobre - Martedì)",
        "chart_hourly_title": "Bilancio di Potenza Orario", "chart_soc_title": "Stato di Carica (SoC)",
        "chart_h_x": "Ora del Giorno [h]", "final_chart_title": "📊 Analisi Comparativa delle Strategie di Autoconsumo sull'Anno",
        "final_chart_sub": "Copertura Energetica ed Autoconsumo Mensile Effettivo nelle Strategie Simulation",
        "final_x": "Mese dell'Anno", "final_l1": "Fabbisogno Utenza Lordo", "final_l2": "S1: Monodirezionale Standard", "final_l3": "S2: Smart Charging", "final_l4": "S3: Bidirectional V2H/V2L",
        "months_labels": ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    }
}

lang = "ITA"
T = LANG_DICT[lang]

# Definizione globale dei giorni dei mesi per renderli accessibili in tutto lo script
days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

if "lat" not in st.session_state: st.session_state.lat = 42.3498
if "lon" not in st.session_state: st.session_state.lon = 13.3995
if "sim_data" not in st.session_state: st.session_state.sim_data = None

# --- PANNELLO PARAMETRI ---
st.markdown(f"## {T['params_title']}")
exp_pv, exp_wind, exp_batt, exp_load, exp_eco = st.columns(5)

with exp_pv.expander(T["pv_title"], expanded=False):
    pv_power = st.number_input(T["pv_p"], min_value=1, max_value=20, value=6, step=1)
    pv_tilt = st.number_input(T["pv_t"], min_value=0, max_value=90, value=35, step=5)
    pv_azimuth = st.number_input(T["pv_az"], min_value=-180, max_value=180, value=0, step=5)
    pv_efficiency = st.number_input(T["pv_eff"], min_value=10, max_value=30, value=20, step=1)

with exp_wind.expander(T["wind_title"], expanded=False):
    wind_power_kw = st.number_input(T["wind_p"], min_value=1, max_value=20, value=3, step=1)
    hub_height = st.number_input(T["wind_h"], min_value=10, max_value=200, value=25, step=5)

with exp_batt.expander(T["batt_title"], expanded=False):
    battery_capacity_kwh = st.number_input(T["batt_c"], min_value=0, max_value=100, value=15, step=1)
    battery_eff = st.number_input(T["batt_eff"], min_value=70, max_value=100, value=92, step=1) / 100.0
    dod_limit = st.number_input(T["batt_dod"], min_value=50, max_value=100, value=80, step=5)
    soc_min = battery_capacity_kwh * (1 - (dod_limit / 100.0))
    soc_max = battery_capacity_kwh

with exp_load.expander(T["load_title"], expanded=False):
    house_area = st.number_input(T["load_area"], min_value=40, max_value=300, value=130, step=10)
    building_class = st.selectbox(T["load_class"], ["A4", "A3", "A2", "A1", "B", "C", "D"], index=4)
    occupants = st.number_input(T["load_occ"], min_value=1, max_value=8, value=4, step=1)
    heat_pump_cop = st.number_input(T["load_cop"], min_value=2.0, max_value=5.0, value=3.6, step=0.1, format="%.1f")
    has_ev = st.checkbox(T["load_ev_check"], value=True)

with exp_eco.expander(T["eco_title"], expanded=False):
    cost_electricity = st.number_input(T["eco_cost"], min_value=0.01, max_value=2.00, value=0.30, step=0.01, format="%.2f")
    val_injection = st.number_input(T["eco_sell"], min_value=0.00, max_value=2.00, value=0.09, step=0.01, format="%.2f")
    capex_base = st.number_input(T["eco_capex"], min_value=1000, max_value=100000, value=11000, step=500)

# INTERFACCIA DI CONNESSIONE EV
ev_hours_status = [False] * 24
if has_ev:
    st.markdown(f"### {T['ev_section_title']}")
    st.markdown(f"<div class='custom-note'>{T['ev_help']}</div>", unsafe_allow_html=True)
    
    c_p1, c_p2, c_p3, c_p4, c_p5, c_p6 = st.columns(6)
    ev_capacity_kwh = c_p1.number_input(T["ev_cap"], min_value=20, max_value=150, value=60, step=5)
    ev_km_day = c_p2.number_input(T["ev_km"], min_value=10, max_value=150, value=50, step=5)
    ev_efficiency_wh_km = c_p3.number_input(T["ev_whkm"], min_value=120, max_value=250, value=160, step=5)
    v2h_power_kw = c_p4.number_input(T["ev_v2hp"], min_value=2.3, max_value=22.0, value=7.4, step=0.1, format="%.1f")
    v2h_eff = c_p5.number_input(T["ev_v2heff"], min_value=70, max_value=100, value=90, step=1) / 100.0
    ev_soc_min_pct = c_p6.number_input(T["ev_soc_min"], min_value=10, max_value=50, value=20, step=5)
    
    c_cx1, c_cx2, c_cx3 = st.columns(3)
    capex_ev_s1 = c_cx1.number_input(T["ev_capex_s1"], value=600, step=50)
    capex_ev_s2 = c_cx2.number_input(T["ev_capex_s2"], value=1100, step=100)
    capex_ev_s3 = c_cx3.number_input(T["ev_capex_s3"], value=3200, step=200)
    
    daily_ev_demand_kwh = (ev_km_day * ev_efficiency_wh_km) / 1000.0
    ev_soc_travel_min = ev_capacity_kwh * (ev_soc_min_pct / 100.0)
    
    cc1, cc2, cc3 = st.columns(3)
    conn_type = cc1.radio("Tipologia di connessione alla rete domestica", ["Overnight (A cavallo della mezzanotte)", "Diurna (Stessa giornata solare)"], index=0)
    start_conn_h = cc2.number_input("Ora Inizio Connessione", min_value=0, max_value=23, value=20, step=1)
    end_conn_h = cc3.number_input("Ora Fine Connessione", min_value=0, max_value=23, value=8, step=1)
    
    if "Overnight" in conn_type:
        for h in range(24):
            if h >= start_conn_h or h <= end_conn_h: ev_hours_status[h] = True
    else:
        for h in range(24):
            if start_conn_h <= h <= end_conn_h: ev_hours_status[h] = True
else:
    daily_ev_demand_kwh, ev_capacity_kwh = 0, 0
    capex_ev_s1, capex_ev_s2, capex_ev_s3 = 0, 0, 0

# --- LOCALIZZAZIONE GIS RESILIENTE ---
st.markdown(f"### {T['gis_title']}")
col_loc1, col_loc2 = st.columns([1, 3])
with col_loc1:
    location_query = st.text_input(T["gis_search"], value="L'Aquila, Italia")
    if st.button(T["gis_btn"], use_container_width=True):
        headers = {"User-Agent": "FEREnergySim_v2_AcademicApplication/1.1 (prof.villante.simulation@univaq.it)"}
        geo_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(location_query)}&format=json&limit=1"
        try:
            res = requests.get(headers=headers, url=geo_url, timeout=5)
            data = res.json()
            if data and len(data) > 0: 
                st.session_state.lat = float(data[0]["lat"])
                st.session_state.lon = float(data[0]["lon"])
                st.rerun()
        except:
            fallback_db = {"l'aquila": (42.3498, 13.3995), "roma": (41.9028, 12.4964), "milano": (45.4642, 9.1900)}
            q_clean = location_query.lower().split(",")[0].strip()
            if q_clean in fallback_db:
                st.session_state.lat, st.session_state.lon = fallback_db[q_clean]
                st.rerun()
            
    lat, lon = st.session_state.lat, st.session_state.lon
    st.info(f"{T['gis_active']}\nLat: {lat:.4f}°\nLon: {lon:.4f}°")

with col_loc2:
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=6, tiles="CartoDB positron")
    # Sostituito con CircleMarker per prevenire i bug grafici di visibilità delle icone marker standard in Streamlit
    folium.CircleMarker(
        location=[st.session_state.lat, st.session_state.lon],
        radius=8,
        color="#EF4444",
        fill=True,
        fill_color="#EF4444",
        fill_opacity=0.9,
        popup="Sito Selezionato"
    ).add_to(m)
    map_data = st_folium(m, width="100%", height=150, key=f"map_widget_{st.session_state.lat}_{st.session_state.lon}")

def setup_plot_style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=9, fontweight='600', color='#0F172A', loc='left', pad=8)
    ax.set_xlabel(xlabel, fontsize=7.5, color='#475569', labelpad=4)
    ax.set_ylabel(ylabel, fontsize=7.5, color='#475569', labelpad=4)
    ax.tick_params(axis='both', which='major', labelsize=7, labelcolor='#475569')
    ax.grid(True, linestyle='--', alpha=0.4, color='#CBD5E1', lw=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def get_8760_profiles():
    pvgis_url = f"https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?lat={lat}&lon={lon}&peakpower={pv_power}&angle={pv_tilt}&aspect={pv_azimuth}&loss=14&outputformat=json"
    sol_m = [0]*12
    try:
        sol_data = requests.get(pvgis_url, timeout=5).json()
        sol_m = [m["E_m"] * (pv_efficiency / 20) for m in sol_data["outputs"]["monthly"]["fixed"]]
    except:
        sol_m = [pv_power * 110] * 12
        
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
        meteo_res = requests.get(open_meteo_url, timeout=5).json()
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
        p_heat = max(0, 20 - t_ext) * coeff * house_area / 1000 / heat_pump_cop / 24
        p_cool = max(0, t_ext - 25) * (coeff * 0.5) * house_area / 1000 / (heat_pump_cop * 0.9) / 24
        base_8760.append(p_base)
        heating_8760.append(p_heat)
        cooling_8760.append(p_cool)
        load_8760.append(p_base + p_heat + p_cool)

    return {
        "pv": pv_8760, "wt": wt_8760, "fer": [pv_8760[i] + wt_8760[i] for i in range(8760)],
        "load": load_8760, "heating": heating_8760, "cooling": cooling_8760, "base": base_8760,
        "temp": temp_2m, "wind": wind_10m
    }

# --- GRUPPO DI CALCOLO SIMULAZIONE ---
if st.button(T["run_btn"], type="primary", use_container_width=True):
    sim = get_8760_profiles()
    hours_indices = {
        T["inv"]: list(range(336, 360)),    
        T["pri"]: list(range(2520, 2544)),  
        T["est"]: list(range(4680, 4704)),  
        T["aut"]: list(range(6888, 6912))   
    }

    conn_annual = [ev_hours_status[h % 24] if has_ev else False for h in range(8760)]
    
    def get_remaining_connected_hours(current_index):
        count = 0
        idx = current_index
        while idx < 8760 and conn_annual[idx]:
            count += 1
            idx += 1
        return count

    # --- STRATEGIA S1: Monodirezionale Standard ---
    soc_h_s1 = soc_min
    current_ev_soc_s1 = ev_capacity_kwh if has_ev else 0
    ac_s1, grid_s1, sell_s1 = 0, 0, 0
    soc_track_h_s1, soc_track_ev_s1 = [], []
    total_load_with_ev_s1 = [0.0] * 8760
    ac_s1_hourly = [0.0] * 8760

    for i in range(8760):
        is_connected = conn_annual[i]
        
        if has_ev and not is_connected and (i == 0 or conn_annual[i-1]):
            current_ev_soc_s1 = max(0.0, current_ev_soc_s1 - daily_ev_demand_kwh)

        soc_track_ev_s1.append(current_ev_soc_s1 if is_connected else np.nan)
        soc_track_h_s1.append(soc_h_s1)

        ev_charge_demand = 0.0
        if has_ev and is_connected and current_ev_soc_s1 < ev_capacity_kwh:
            ev_charge_demand = min(v2h_power_kw, (ev_capacity_kwh - current_ev_soc_s1) / v2h_eff)
            current_ev_soc_s1 += ev_charge_demand * v2h_eff

        tot_load = sim["load"][i] + ev_charge_demand
        total_load_with_ev_s1[i] = tot_load
        prod = sim["fer"][i]
        
        diretto = min(prod, tot_load)
        local_ac = directo
        surplus, deficit = prod - directo, tot_load - directo
        
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
        ac_s1_hourly[i] = local_ac
        ac_s1 += local_ac

    # --- STRATEGIA S2: Smart Charging Predittivo ---
    soc_h_s2 = soc_min
    current_ev_soc_s2 = ev_capacity_kwh if has_ev else 0
    ac_s2, grid_s2, sell_s2 = 0, 0, 0
    soc_track_h_s2, soc_track_ev_s2 = [], []
    ac_s2_hourly = [0.0] * 8760

    for i in range(8760):
        is_connected = conn_annual[i]
        if has_ev and not is_connected and (i == 0 or conn_annual[i-1]):
            current_ev_soc_s2 = max(0.0, current_ev_soc_s2 - daily_ev_demand_kwh)

        soc_track_ev_s2.append(current_ev_soc_s2 if is_connected else np.nan)
        soc_track_h_s2.append(soc_h_s2)

        prod, house_load = sim["fer"][i], sim["load"][i]
        diretto = min(prod, house_load)
        local_ac = diretto
        surplus = prod - diretto
        deficit = house_load - diretto

        ev_charge_power = 0.0
        if has_ev and is_connected and current_ev_soc_s2 < ev_capacity_kwh:
            needed_energy = ev_capacity_kwh - current_ev_soc_s2
            needed_hours = math.ceil(needed_energy / (v2h_power_kw * v2h_eff))
            rem_hours = get_remaining_connected_hours(i)
            
            if rem_hours <= needed_hours:
                ev_charge_power = min(v2h_power_kw, needed_energy / v2h_eff)
                deficit += ev_charge_power
                current_ev_soc_s2 += ev_charge_power * v2h_eff
            elif surplus > 0:
                ev_charge_power = min(min(v2h_power_kw, surplus), needed_energy / v2h_eff)
                surplus -= ev_charge_power
                local_ac += ev_charge_power
                current_ev_soc_s2 += ev_charge_power * v2h_eff

        if surplus > 0 and battery_capacity_kwh > 0:
            ch = min(surplus * battery_eff, soc_max - soc_h_s2)
            soc_h_s2 += ch
            surplus -= (ch / battery_eff)
            local_ac += ch
        sell_s2 += surplus

        if deficit > 0 and battery_capacity_kwh > 0:
            dh = min(deficit, (soc_h_s2 - soc_min) * battery_eff)
            soc_h_s2 -= (dh / battery_eff)
            local_ac += dh
            deficit -= dh
        grid_s2 += deficit
        ac_s2_hourly[i] = local_ac
        ac_s2 += local_ac

    # --- STRATEGIA S3: Vehicle-to-Home Cooperativo ---
    soc_h_s3 = soc_min
    current_ev_soc_s3 = ev_capacity_kwh if has_ev else 0
    ac_s3, grid_s3, sell_s3 = 0, 0, 0
    soc_track_h_s3, soc_track_ev_s3 = [], []
    ac_s3_hourly = [0.0] * 8760

    for i in range(8760):
        is_connected = conn_annual[i]
        if has_ev and not is_connected and (i == 0 or conn_annual[i-1]):
            current_ev_soc_s3 = max(0.0, current_ev_soc_s3 - daily_ev_demand_kwh)

        soc_track_ev_s3.append(current_ev_soc_s3 if is_connected else np.nan)
        soc_track_h_s3.append(soc_h_s3)

        prod, house_load = sim["fer"][i], sim["load"][i]
        diretto = min(prod, house_load)
        local_ac = diretto
        surplus = prod - diretto
        deficit = house_load - diretto

        if has_ev and is_connected:
            needed_energy = ev_capacity_kwh - current_ev_soc_s3
            needed_hours = math.ceil(needed_energy / (v2h_power_kw * v2h_eff))
            rem_hours = get_remaining_connected_hours(i)
            
            if rem_hours <= needed_hours:
                ev_charge_power = min(v2h_power_kw, needed_energy / v2h_eff)
                deficit += ev_charge_power
                current_ev_soc_s3 += ev_charge_power * v2h_eff
            else:
                if deficit > 0 and current_ev_soc_s3 > ev_soc_travel_min:
                    v2h_discharge = min(min(v2h_power_kw, deficit), (current_ev_soc_s3 - ev_soc_travel_min) * v2h_eff)
                    current_ev_soc_s3 -= (v2h_discharge / v2h_eff)
                    deficit -= v2h_discharge
                    local_ac += v2h_discharge
                if surplus > 0 and current_ev_soc_s3 < ev_capacity_kwh:
                    ev_charge_power = min(min(v2h_power_kw, surplus), needed_energy / v2h_eff)
                    surplus -= ev_charge_power
                    local_ac += ev_charge_power
                    current_ev_soc_s3 += ev_charge_power * v2h_eff

        if surplus > 0 and battery_capacity_kwh > 0:
            ch = min(surplus * battery_eff, soc_max - soc_h_s3)
            soc_h_s3 += ch
            surplus -= (ch / battery_eff)
            local_ac += ch
        sell_s3 += surplus

        if deficit > 0 and battery_capacity_kwh > 0:
            dh = min(deficit, (soc_h_s3 - soc_min) * battery_eff)
            soc_h_s3 -= (dh / battery_eff)
            local_ac += dh
            deficit -= dh
        grid_s3 += deficit
        ac_s3_hourly[i] = local_ac
        ac_s3 += local_ac

    annual_ev_kwh = (daily_ev_demand_kwh * 365) if has_ev else 0.0
    total_demand_annual = sum(sim["load"]) + annual_ev_kwh
    total_generation_annual = sum(sim["fer"])

    monthly_load_with_ev_s1_agg = [0]*12
    monthly_ac_s1_agg, monthly_ac_s2_agg, monthly_ac_s3_agg = [0]*12, [0]*12, [0]*12
    monthly_sol_agg, monthly_wind_agg = [0]*12, [0]*12
    monthly_base_agg, monthly_heat_agg, monthly_cool_agg = [0]*12, [0]*12, [0]*12
    
    c_idx = 0
    for m in range(12):
        h_count = days_in_months[m] * 24
        monthly_load_with_ev_s1_agg[m] = sum(total_load_with_ev_s1[c_idx : c_idx + h_count])
        monthly_sol_agg[m] = sum(sim["pv"][c_idx : c_idx + h_count])
        monthly_wind_agg[m] = sum(sim["wt"][c_idx : c_idx + h_count])
        monthly_base_agg[m] = sum(sim["base"][c_idx : c_idx + h_count])
        monthly_heat_agg[m] = sum(sim["heating"][c_idx : c_idx + h_count])
        monthly_cool_agg[m] = sum(sim["cooling"][c_idx : c_idx + h_count])
        
        monthly_ac_s1_agg[m] = sum(ac_s1_hourly[c_idx : c_idx + h_count])
        if has_ev:
            monthly_ac_s2_agg[m] = sum(ac_s2_hourly[c_idx : c_idx + h_count])
            monthly_ac_s3_agg[m] = sum(ac_s3_hourly[c_idx : c_idx + h_count])
        c_idx += h_count

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
    else:
        savings_s2, savings_s3, capex_s2_tot, capex_s3_tot, payback_s2, payback_s3 = 0,0,0,0,0,0

    st.session_state.sim_data = {
        "sim": sim, "hours_indices": hours_indices, "has_ev": has_ev, "ev_hours_status": ev_hours_status,
        "total_demand_annual": total_demand_annual, "total_generation_annual": total_generation_annual,
        "ac_s1": ac_s1, "grid_s1": grid_s1, "sell_s1": sell_s1, "savings_s1": savings_s1, "capex_s1_tot": capex_s1_tot, "payback_s1": payback_s1,
        "ac_s2": ac_s2, "grid_s2": grid_s2, "sell_s2": sell_s2, "savings_s2": savings_s2, "capex_s2_tot": capex_s2_tot, "payback_s2": payback_s2,
        "ac_s3": ac_s3, "grid_s3": grid_s3, "sell_s3": sell_s3, "savings_s3": savings_s3, "capex_s3_tot": capex_s3_tot, "payback_s3": payback_s3,
        "monthly_load_with_ev_s1_agg": monthly_load_with_ev_s1_agg, "monthly_ac_s1_agg": monthly_ac_s1_agg,
        "monthly_ac_s2_agg": monthly_ac_s2_agg, "monthly_ac_s3_agg": monthly_ac_s3_agg,
        "monthly_sol_agg": monthly_sol_agg, "monthly_wind_agg": monthly_wind_agg,
        "monthly_base_agg": monthly_base_agg, "monthly_heat_agg": monthly_heat_agg, "monthly_cool_agg": monthly_cool_agg,
        "soc_track_h_s1": soc_track_h_s1, "soc_track_ev_s1": soc_track_ev_s1,
        "soc_track_h_s2": soc_track_h_s2, "soc_track_ev_s2": soc_track_ev_s2,
        "soc_track_h_s3": soc_track_h_s3, "soc_track_ev_s3": soc_track_ev_s3,
        "total_load_with_ev_s1": total_load_with_ev_s1
    }

# --- RENDERING ORDINATO DELLE SEZIONI DI REPORT ---
if st.session_state.sim_data is not None:
    sd = st.session_state.sim_data
    sim = sd["sim"]
    hours_indices = sd["hours_indices"]
    has_ev = sd["has_ev"]
    ev_hours_status = sd["ev_hours_status"]
    
    sc_rate_s1 = (sd["ac_s1"] / sd["total_generation_annual"]) * 100 if sd["total_generation_annual"] > 0 else 0
    ss_rate_s1 = (sd["ac_s1"] / sd["total_demand_annual"]) * 100 if sd["total_demand_annual"] > 0 else 0
    if has_ev:
        sc_rate_s2 = (sd["ac_s2"] / sd["total_generation_annual"]) * 100 if sd["total_generation_annual"] > 0 else 0
        ss_rate_s2 = (sd["ac_s2"] / sd["total_demand_annual"]) * 100 if sd["total_demand_annual"] > 0 else 0
        sc_rate_s3 = (sd["ac_s3"] / sd["total_generation_annual"]) * 100 if sd["total_generation_annual"] > 0 else 0
        ss_rate_s3 = (sd["ac_s3"] / sd["total_demand_annual"]) * 100 if sd["total_demand_annual"] > 0 else 0
    else:
        ss_rate_s2, ss_rate_s3 = 0, 0

    # --- 1ª SEZIONE: ISTOGRAMMA COMPARATIVO ANNUALE MENSILI ---
    st.markdown(f"### {T['final_chart_title']}")
    fig12, ax12 = plt.subplots(figsize=(12, 2.4), dpi=200)
    x_idx = range(1, 13)
    ax12.bar([x - 0.22 for x in x_idx], sd["monthly_load_with_ev_s1_agg"], width=0.18, label=T["final_l1"], color='#94A3B8', alpha=0.25)
    ax12.bar([x - 0.07 for x in x_idx], sd["monthly_ac_s1_agg"], width=0.15, label=T["final_l2"] if has_ev else "Autoconsumo S1", color='#EF4444', alpha=0.7)
    if has_ev:
        ax12.bar([x + 0.07 for x in x_idx], sd["monthly_ac_s2_agg"], width=0.15, label=T["final_l3"], color='#3B82F6', alpha=0.8)
        ax12.bar([x + 0.22 for x in x_idx], sd["monthly_ac_s3_agg"], width=0.15, label=T["final_l4"], color='#10B981', alpha=0.9)
    setup_plot_style(ax12, T["final_chart_sub"], T["final_x"], T["chart_y_kwh"])
    ax12.set_xticks(x_idx)
    ax12.set_xticklabels(T["months_labels"])
    ax12.legend(fontsize=7, frameon=False, loc="upper right")
    st.pyplot(fig12)

    # --- 2ª SEZIONE: PROSPETTO COMPARATIVO PERFORMANCE BARRE CSS ---
    st.markdown("### 📊 Prospetto Comparativo delle Performance Inter-Strategia")
    if has_ev:
        col_bar1, col_bar2, col_bar3, col_bar4 = st.columns(4)
        
        with col_bar1:
            # Risolto l'overflow impostando un tetto dinamico basato sul valore massimo registrato (anche se > 100%)
            max_ss = max(100.0, ss_rate_s1, ss_rate_s2, ss_rate_s3)
            st.markdown(f"""
            <div class='compare-card'>
                <div class='compare-label'>Grado di Autosufficienza [%]</div>
                <div class='compare-item'><small>S1 Standard</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(ss_rate_s1/max_ss)*100}%; background: #EF4444;'></div></div><div class='compare-val'>{ss_rate_s1:.1f} %</div></div>
                <div class='compare-item'><small>S2 Smart</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(ss_rate_s2/max_ss)*100}%; background: #3B82F6;'></div></div><div class='compare-val'>{ss_rate_s2:.1f} %</div></div>
                <div class='compare-item'><small>S3 V2H</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(ss_rate_s3/max_ss)*100}%; background: #10B981;'></div></div><div class='compare-val'>{ss_rate_s3:.1f} %</div></div>
            </div>
            """, unsafe_allow_html=True)

        with col_bar2:
            max_savings = max(sd["savings_s1"], sd["savings_s2"], sd["savings_s3"]) if max(sd["savings_s1"], sd["savings_s2"], sd["savings_s3"]) > 0 else 1
            st.markdown(f"""
            <div class='compare-card'>
                <div class='compare-label'>Risparmio Economico Annuale [€/anno]</div>
                <div class='compare-item'><small>S1 Standard</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(sd["savings_s1"]/max_savings)*100}%; background: #EF4444;'></div></div><div class='compare-val'>{sd["savings_s1"]:.2f} €</div></div>
                <div class='compare-item'><small>S2 Smart</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(sd["savings_s2"]/max_savings)*100}%; background: #3B82F6;'></div></div><div class='compare-val'>{sd["savings_s2"]:.2f} €</div></div>
                <div class='compare-item'><small>S3 V2H</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(sd["savings_s3"]/max_savings)*100}%; background: #10B981;'></div></div><div class='compare-val'>{sd["savings_s3"]:.2f} €</div></div>
            </div>
            """, unsafe_allow_html=True)

        with col_bar3:
            max_capex = max(sd["capex_s1_tot"], sd["capex_s2_tot"], sd["capex_s3_tot"]) if max(sd["capex_s1_tot"], sd["capex_s2_tot"], sd["capex_s3_tot"]) > 0 else 1
            st.markdown(f"""
            <div class='compare-card'>
                <div class='compare-label'>Investimento Iniziale (CAPEX) [€]</div>
                <div class='compare-item'><small>S1 Standard</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(sd["capex_s1_tot"]/max_capex)*100}%; background: #EF4444;'></div></div><div class='compare-val'>{sd["capex_s1_tot"]:.0f} €</div></div>
                <div class='compare-item'><small>S2 Smart</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(sd["capex_s2_tot"]/max_capex)*100}%; background: #3B82F6;'></div></div><div class='compare-val'>{sd["capex_s2_tot"]:.0f} €</div></div>
                <div class='compare-item'><small>S3 V2H</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {(sd["capex_s3_tot"]/max_capex)*100}%; background: #10B981;'></div></div><div class='compare-val'>{sd["capex_s3_tot"]:.0f} €</div></div>
            </div>
            """, unsafe_allow_html=True)

        with col_bar4:
            st.markdown(f"""
            <div class='compare-card'>
                <div class='compare-label'>Tempo di Ritorno Ammortamento [Anni]</div>
                <div class='compare-item'><small>S1 Standard</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {min(100, (sd["payback_s1"]/15)*100)}%; background: #EF4444;'></div></div><div class='compare-val'>{sd["payback_s1"]:.1f} anni</div></div>
                <div class='compare-item'><small>S2 Smart</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {min(100, (sd["payback_s2"]/15)*100)}%; background: #3B82F6;'></div></div><div class='compare-val'>{sd["payback_s2"]:.1f} anni</div></div>
                <div class='compare-item'><small>S3 V2H</small><div class='compare-bar-container'><div class='compare-bar-fill' style='width: {min(100, (sd["payback_s3"]/15)*100)}%; background: #10B981;'></div></div><div class='compare-val'>{sd["payback_s3"]:.1f} anni</div></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Abilita il veicolo elettrico (EV) nei parametri per sbloccare l'analisi delle performance.")

    # --- 3ª SEZIONE: MACRO BILANCI MENSILI DETTAGLIATI ---
    st.markdown("### 📊 Macro Bilanci Energetici su Base Mensile")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        # Modificato in grafico a barre cumulate: FV sotto, Eolico sopra
        fig_mac_gen, ax_mac_gen = plt.subplots(figsize=(6, 2.3), dpi=200)
        ax_mac_gen.bar(range(1, 13), sd["monthly_sol_agg"], label="Fotovoltaico (API PVGIS)", color="#D97706", alpha=0.8, width=0.5)
        ax_mac_gen.bar(range(1, 13), sd["monthly_wind_agg"], bottom=sd["monthly_sol_agg"], label="Eolico (Open-Meteo)", color="#2563EB", alpha=0.7, width=0.5)
        setup_plot_style(ax_mac_gen, T["chart_gen_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax_mac_gen.legend(fontsize=6.5, frameon=False, loc="upper right")
        st.pyplot(fig_mac_gen)
        
    with col_m2:
        # Modificato in barre interamente cumulate (EV -> Base -> Riscaldamento -> Climatizzazione)
        fig_mac_load, ax_mac_load = plt.subplots(figsize=(6, 2.3), dpi=200)
        
        # Scorporo della quota EV mensile
        monthly_ev_agg = [sd["monthly_load_with_ev_s1_agg"][k] - (sd["monthly_base_agg"][k] + sd["monthly_heat_agg"][k] + sd["monthly_cool_agg"][k]) for k in range(12)]
        
        # 1. Ricarica EV (Base)
        ax_mac_load.bar(range(1, 13), monthly_ev_agg, label="Ricarica EV", color="#E11D48", alpha=0.7, width=0.5)
        
        # 2. Carichi base sopra EV
        bottom_base = monthly_ev_agg
        ax_mac_load.bar(range(1, 13), sd["monthly_base_agg"], bottom=bottom_base, label="Carichi Elettrici Base", color="#475569", alpha=0.4, width=0.5)
        
        # 3. Riscaldamento sopra Base+EV
        bottom_heat = [monthly_ev_agg[k] + sd["monthly_base_agg"][k] for k in range(12)]
        ax_mac_load.bar(range(1, 13), sd["monthly_heat_agg"], bottom=bottom_heat, label="Riscaldamento (Pompa Calore)", color="#DC2626", alpha=0.6, width=0.5)
        
        # 4. Climatizzazione sopra Riscaldamento+Base+EV (Raggiunge il Fabbisogno Lordo Totale)
        bottom_cool = [monthly_ev_agg[k] + sd["monthly_base_agg"][k] + sd["monthly_heat_agg"][k] for k in range(12)]
        ax_mac_load.bar(range(1, 13), sd["monthly_cool_agg"], bottom=bottom_cool, label="Rinfrescamento (AC)", color="#3B82F6", alpha=0.6, width=0.5)
        
        setup_plot_style(ax_mac_load, T["chart_load_title"], T["chart_x_month"], T["chart_y_kwh"])
        ax_mac_load.legend(fontsize=6, frameon=False, loc="upper right")
        st.pyplot(fig_mac_load)

    # --- 4ª SEZIONE: SCHEDE DETTAGLIO STRATEGIE ---
    st.markdown("### 📋 Dettaglio Analitico delle Singole Strategie")
    if has_ev:
        tab1, tab2, tab3 = st.tabs(["🛑 Scenario 1: Standard Monodirezionale", "☀️ Scenario 2: Smart Charging", "🔄 Scenario 3: Bidirectional V2H"])
    else:
        tab1, = st.tabs(["🏠 Configurazione Impianto Base (Senza EV)"])

    def plot_strategy_pies(ac, grid, sell):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5, 2.1), dpi=150)
        ax1.pie([ac, grid], labels=['Autoconsumo', 'Rete'], colors=['#10B981', '#EF4444'], autopct='%1.1f%%', startangle=90, textprops={'fontsize':6})
        ax1.set_title("Copertura Fabbisogno", fontsize=7, fontweight='600')
        ax2.pie([ac, sell], labels=['Autoconsumo', 'Immissione'], colors=['#10B981', '#3B82F6'], autopct='%1.1f%%', startangle=90, textprops={'fontsize':6})
        ax2.set_title("Destinazione FER", fontsize=7, fontweight='600')
        st.pyplot(fig)

    with tab1:
        mc1, mc2 = st.columns([3, 2])
        with mc1:
            c1, c2 = st.columns(2); c1.metric("Autoconsumo Effettivo", f"{sd['ac_s1']:.0f} kWh"); c2.metric("Grado di Autoconsumo", f"{sc_rate_s1:.1f} %")
            c3, c4 = st.columns(2); c3.metric("Autosufficienza Nodo", f"{ss_rate_s1:.1f} %"); c4.metric("Prelievo Totale da Rete", f"{sd['grid_s1']:.0f} kWh")
            c5, c6 = st.columns(2); c5.metric("Energia Immessa in Rete", f"{sd['sell_s1']:.0f} kWh"); c6.metric("Fabbisogno Annuo Lordo", f"{sd['total_demand_annual']:.0f} kWh")
            st.divider()
            f1, f2 = st.columns(2); f1.metric("Risparmio Economico", f"{sd['savings_s1']:.2f} €/anno"); f2.metric("Tempo di Ritorno (PBP)", f"{sd['payback_s1']:.1f} Anni")
        with mc2: plot_strategy_pies(sd['ac_s1'], sd['grid_s1'], sd['sell_s1'])
    
    if has_ev:
        with tab2:
            mc1, mc2 = st.columns([3, 2])
            with mc1:
                c1, c2 = st.columns(2); c1.metric("Autoconsumo Effettivo", f"{sd['ac_s2']:.0f} kWh"); c2.metric("Grado di Autoconsumo", f"{sc_rate_s2:.1f} %")
                c3, c4 = st.columns(2); c3.metric("Autosufficienza Nodo", f"{ss_rate_s2:.1f} %"); c4.metric("Prelievo Totale da Rete", f"{sd['grid_s2']:.0f} kWh")
                c5, c6 = st.columns(2); c5.metric("Energia Immessa in Rete", f"{sd['sell_s2']:.0f} kWh"); c6.metric("Fabbisogno Annuo Lordo", f"{sd['total_demand_annual']:.0f} kWh")
                st.divider()
                f1, f2 = st.columns(2); f1.metric("Risparmio Economico", f"{sd['savings_s2']:.2f} €/anno"); f2.metric("Tempo di Ritorno (PBP)", f"{sd['payback_s2']:.1f} Anni")
            with mc2: plot_strategy_pies(sd['ac_s2'], sd['grid_s2'], sd['sell_s2'])
                
        with tab3:
            mc1, mc2 = st.columns([3, 2])
            with mc1:
                c1, c2 = st.columns(2); c1.metric("Autoconsumo Effettivo", f"{sd['ac_s3']:.0f} kWh"); c2.metric("Grado di Autoconsumo", f"{sc_rate_s3:.1f} %")
                c3, c4 = st.columns(2); c3.metric("Autosufficienza Nodo", f"{ss_rate_s3:.1f} %"); c4.metric("Prelievo Totale da Rete", f"{sd['grid_s3']:.0f} kWh")
                c5, c6 = st.columns(2); c5.metric("Energia Immessa in Rete", f"{sd['sell_s3']:.0f} kWh"); c6.metric("Fabbisogno Annuo Lordo", f"{sd['total_demand_annual']:.0f} kWh")
                st.divider()
                f1, f2 = st.columns(2); f1.metric("Risparmio Economico", f"{sd['savings_s3']:.2f} €/anno"); f2.metric("Tempo di Ritorno (PBP)", f"{sd['payback_s3']:.1f} Anni")
            with mc2: plot_strategy_pies(sd['ac_s3'], sd['grid_s3'], sd['sell_s3'])

    # --- 5ª SEZIONE: ANALISI DINAMICA ORARIA ---
    st.markdown("---")
    st.subheader("⏱ Analisi Energetica Dinamica Oraria Intra-Giornaliera")
    for season_name, idx_list in hours_indices.items():
        st.markdown(f"#### {season_name}")
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_f1, ax_f1 = plt.subplots(figsize=(6, 2.5), dpi=200)
            ax_f1.plot(range(24), [sim["fer"][idx] for idx in idx_list], label="FER", color="#059669", lw=1.5)
            ax_f1.plot(range(24), [sim["load"][idx] for idx in idx_list], label="Carico", color="#475569", lw=1.2, linestyle="--")
            ax_meteo = ax_f1.twinx()
            ax_meteo.plot(range(24), [sim["temp"][idx] for idx in idx_list], color="#F59E0B", lw=1, linestyle=":")
            setup_plot_style(ax_f1, f"{T['chart_hourly_title']}", T["chart_h_x"], "kW")
            st.pyplot(fig_f1)
            
        with col_chart2:
            if has_ev:
                # S1
                fig_f2_s1, ax_f2_s1 = plt.subplots(figsize=(6, 1.4), dpi=200)
                for h in range(24):
                    if ev_hours_status[h]: ax_f2_s1.axvspan(h-0.5, h+0.5, color='#E0F2FE', alpha=0.4, lw=0)
                h_soc_pct_s1 = [(sd["soc_track_h_s1"][idx] / battery_capacity_kwh * 100) if battery_capacity_kwh > 0 else 0 for idx in idx_list]
                ev_soc_pct_s1 = [(sd["soc_track_ev_s1"][idx] / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for idx in idx_list]
                ax_f2_s1.plot(range(24), h_soc_pct_s1, label="SoC BESS Casa", color='#D97706', lw=1.3)
                ax_f2_s1.plot(range(24), ev_soc_pct_s1, label="SoC EV (Connesso)", color='#EF4444', lw=1.3, marker='o', markersize=2)
                setup_plot_style(ax_f2_s1, "S1: Standard Monodirezionale", T["chart_h_x"], "SoC [%]")
                ax_f2_s1.set_ylim(-5, 105); ax_f2_s1.legend(fontsize=5.5, loc="lower left"); st.pyplot(fig_f2_s1)
                # S2
                fig_f2_s2, ax_f2_s2 = plt.subplots(figsize=(6, 1.4), dpi=200)
                for h in range(24):
                    if ev_hours_status[h]: ax_f2_s2.axvspan(h-0.5, h+0.5, color='#E0F2FE', alpha=0.4, lw=0)
                h_soc_pct_s2 = [(sd["soc_track_h_s2"][idx] / battery_capacity_kwh * 100) if battery_capacity_kwh > 0 else 0 for idx in idx_list]
                ev_soc_pct_s2 = [(sd["soc_track_ev_s2"][idx] / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for idx in idx_list]
                ax_f2_s2.plot(range(24), h_soc_pct_s2, label="SoC BESS Casa", color='#B45309', lw=1.3)
                ax_f2_s2.plot(range(24), ev_soc_pct_s2, label="SoC EV (Connesso)", color='#3B82F6', lw=1.3, marker='o', markersize=2)
                setup_plot_style(ax_f2_s2, "S2: Smart Charging", T["chart_h_x"], "SoC [%]")
                ax_f2_s2.set_ylim(-5, 105); ax_f2_s2.legend(fontsize=5.5, loc="lower left"); st.pyplot(fig_f2_s2)
                # S3
                fig_f2_s3, ax_f2_s3 = plt.subplots(figsize=(6, 1.4), dpi=200)
                for h in range(24):
                    if ev_hours_status[h]: ax_f2_s3.axvspan(h-0.5, h+0.5, color='#E0F2FE', alpha=0.4, lw=0)
                h_soc_pct_s3 = [(sd["soc_track_h_s3"][idx] / battery_capacity_kwh * 100) if battery_capacity_kwh > 0 else 0 for idx in idx_list]
                ev_soc_pct_s3 = [(sd["soc_track_ev_s3"][idx] / ev_capacity_kwh * 100) if ev_capacity_kwh > 0 else 0 for idx in idx_list]
                ax_f2_s3.plot(range(24), h_soc_pct_s3, label="SoC BESS Casa", color='#78350F', lw=1.3)
                ax_f2_s3.plot(range(24), ev_soc_pct_s3, label="SoC EV (Connesso)", color='#10B981', lw=1.3, marker='o', markersize=2)
                setup_plot_style(ax_f2_s3, "S3: Bidirezionale V2H", "SoC [%]", "SoC [%]")
                ax_f2_s3.set_ylim(-5, 105); ax_f2_s3.legend(fontsize=5.5, loc="lower left"); st.pyplot(fig_f2_s3)
            else:
                fig_f2, ax_f2 = plt.subplots(figsize=(6, 2.5), dpi=200)
                ax_f2.plot(range(24), [(sd["soc_track_h_s1"][idx] / battery_capacity_kwh * 100) for idx in idx_list], label="SoC Casa", color='#D97706', lw=1.5)
                setup_plot_style(ax_f2, T["chart_soc_title"], T["chart_h_x"], "SoC [%]")
                ax_f2.set_ylim(-5, 105); ax_f2.legend(fontsize=6, loc="lower right"); st.pyplot(fig_f2)

    st.markdown("---")
    st.subheader(T["guide_8760_charts_title"])
    start_hour, end_hour = st.slider("Seleziona la finestra oraria da analizzare (Zoom asse orario condiviso)", min_value=1, max_value=8760, value=(1, 8760), step=1)
    s_idx, e_idx = start_hour - 1, end_hour
    t_range = range(start_hour, end_hour + 1) if (end_hour - start_hour) > 0 else [start_hour]
    
    col_ann1, col_ann2 = st.columns(2)
    with col_ann1:
        fig_ann_flows, ax_ann_flows = plt.subplots(figsize=(7, 2.5), dpi=200)
        ax_ann_flows.plot(t_range, sim["fer"][s_idx:e_idx], color="#10B981", alpha=0.6, lw=0.6, label="Generazione FER")
        ax_ann_flows.plot(t_range, sd["total_load_with_ev_s1"][s_idx:e_idx], color="#EF4444", alpha=0.5, lw=0.6, label="Carico Lordo")
        setup_plot_style(ax_ann_flows, "Andamento Potenze nel Periodo Selezionato", "Ore dell'Anno", "kW")
        ax_ann_flows.legend(fontsize=6, loc="upper right"); st.pyplot(fig_ann_flows)
        
    with col_ann2:
        if has_ev:
            conn_mask = [100 if ev_hours_status[h % 24] else np.nan for h in range(start_hour, end_hour + 1)]
            # S1 continuo
            fig_ann_soc_s1, ax_ann_soc_s1 = plt.subplots(figsize=(7, 1.4), dpi=200)
            ax_ann_soc_s1.plot(t_range, [(v / battery_capacity_kwh * 100) for v in sd["soc_track_h_s1"][s_idx:e_idx]], label="SoC BESS Casa", color="#D97706", lw=0.6)
            ax_ann_soc_s1.plot(t_range, [(v / ev_capacity_kwh * 100) for v in sd["soc_track_ev_s1"][s_idx:e_idx]], label="SoC EV", color="#EF4444", lw=0.6, alpha=0.8)
            ax_ann_soc_s1.plot(t_range, conn_mask, label="Fascia Connessione", color="#E0F2FE", lw=2.5, alpha=0.4)
            setup_plot_style(ax_ann_soc_s1, "S1: Standard Monodirezionale", "Ore dell'Anno", "SoC [%]")
            ax_ann_soc_s1.set_ylim(-5, 105); ax_ann_soc_s1.legend(fontsize=6, loc="lower left"); st.pyplot(fig_ann_soc_s1)
            
            # S2 continuo
            fig_ann_soc_s2, ax_ann_soc_s2 = plt.subplots(figsize=(7, 1.4), dpi=200)
            ax_ann_soc_s2.plot(t_range, [(v / battery_capacity_kwh * 100) for v in sd["soc_track_h_s2"][s_idx:e_idx]], label="SoC BESS Casa", color="#B45309", lw=0.6)
            ax_ann_soc_s2.plot(t_range, [(v / ev_capacity_kwh * 100) for v in sd["soc_track_ev_s2"][s_idx:e_idx]], label="SoC EV", color="#3B82F6", lw=0.6, alpha=0.8)
            ax_ann_soc_s2.plot(t_range, conn_mask, label="Fascia Connessione", color="#E0F2FE", lw=2.5, alpha=0.4)
            setup_plot_style(ax_ann_soc_s2, "S2: Smart Charging", "Ore dell'Anno", "SoC [%]")
            ax_ann_soc_s2.set_ylim(-5, 105); ax_ann_soc_s2.legend(fontsize=6, loc="lower left"); st.pyplot(fig_ann_soc_s2)
            
            # S3 continuo
            fig_ann_soc_s3, ax_ann_soc_s3 = plt.subplots(figsize=(7, 1.4), dpi=200)
            ax_ann_soc_s3.plot(t_range, [(v / battery_capacity_kwh * 100) for v in sd["soc_track_h_s3"][s_idx:e_idx]], label="SoC BESS Casa", color="#78350F", lw=0.6)
            ax_ann_soc_s3.plot(t_range, [(v / ev_capacity_kwh * 100) for v in sd["soc_track_ev_s3"][s_idx:e_idx]], label="SoC EV", color="#10B981", lw=0.6, alpha=0.8)
            ax_ann_soc_s3.plot(t_range, conn_mask, label="Fascia Connessione", color="#E0F2FE", lw=2.5, alpha=0.4)
            setup_plot_style(ax_ann_soc_s3, "S3: Bidirezionale V2H", "Ore dell'Anno", "SoC [%]")
            ax_ann_soc_s3.set_ylim(-5, 105); ax_ann_soc_s3.legend(fontsize=6, loc="lower left"); st.pyplot(fig_ann_soc_s3)
        else:
            fig_ann_soc, ax_ann_soc = plt.subplots(figsize=(7, 2.5), dpi=200)
            ax_ann_soc.plot(t_range, [(v / battery_capacity_kwh * 100) for v in sd["soc_track_h_s1"][s_idx:e_idx]], label="SoC Casa", color="#D97706", lw=0.6)
            setup_plot_style(ax_ann_soc, "Evoluzione dello Stato di Carica nel Periodo Selezionato", "Ore dell'Anno", "SoC [%]")
            ax_ann_soc.set_ylim(-5, 105); ax_ann_soc.legend(fontsize=6.5, loc="lower left"); st.pyplot(fig_ann_soc)

st.markdown("---")
st.caption("RES-EV Microgrid Core Platform | 8760-Hour Chronological Solver | Engine: PVGIS API & Open-Meteo Weather Dataset")