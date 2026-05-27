# app.py
import streamlit as st
import requests
import matplotlib.pyplot as plt
import folium
import math
from streamlit_folium import st_folium

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="Energy GIS Simulator", layout="wide")

# CSS personalizzato per affinare i font, ridurre i margini e rendere l'interfaccia compatta
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 2.2rem !important; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    h2 { font-size: 1.4rem !important; font-weight: 600; color: #2563EB; margin-top: 1.5rem; margin-bottom: 0.8rem; border-bottom: 1px solid #E5E7EB; padding-bottom: 0.3rem; }
    h3 { font-size: 1.1rem !important; font-weight: 600; color: #374151; }
    .stSlider > label, .stSelectbox > label, .stTextInput > label { font-size: 0.85rem !important; font-weight: 500; }
    .stMetric { background-color: #F8FAFC; padding: 0.6rem; border-radius: 0.4rem; border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

st.title("🌍 Energy GIS Simulator")
st.caption("Piattaforma avanzata per la simulazione e ottimizzazione di sistemi energetici locali, accumuli stazionari e integrazione V2H.")

# --- INITIALIZATION ---
if "lat" not in st.session_state: st.session_state.lat = 42.3498
if "lon" not in st.session_state: st.session_state.lon = 13.3995

# --- BARRA LATERALE: CONFIGURAZIONE PARAMETRI ---
st.sidebar.markdown("### 🎛️ Pannello di Controllo")

with st.sidebar.expander("☀️ Configurazione Fotovoltaico", expanded=True):
    pv_power = st.slider("Potenza Impianto (kWp)", 1, 100, 5)
    c1, c2 = st.columns(2)
    pv_tilt = c1.slider("Tilt (°)", 0, 90, 35)
    pv_azimuth = c2.slider("Azimuth (°)", -180, 180, 0, help="0=Sud | -90=Est | 90=Ovest")
    pv_efficiency = st.slider("Rendimento Pannelli (%)", 10, 30, 20)

with st.sidebar.expander("🌬️ Configurazione Eolico", expanded=False):
    wind_power_kw = st.slider("Quota Potenza (kW)", 1, 100, 2)
    c3, c4 = st.columns(2)
    hub_height = c3.slider("Altezza Mozzo (m)", 10, 200, 80)
    rotor_diameter = c4.slider("Diametro Rotore (m)", 10, 200, 80)

with st.sidebar.expander("🔋 Accumulo Stazionario Casa", expanded=True):
    battery_capacity_kwh = st.slider("Capacità Batteria (kWh)", 0, 100, 10)
    c5, c6 = st.columns(2)
    battery_eff = c5.slider("Efficienza (%)", 70, 100, 92) / 100.0
    dod_limit = c6.slider("DoD Max (%)", 50, 100, 80)
    soc_min = battery_capacity_kwh * (1 - (dod_limit / 100.0))
    soc_max = battery_capacity_kwh

with st.sidebar.expander("🏠 Carichi Elettrici & Veicolo (EV)", expanded=True):
    c7, c8 = st.columns(2)
    house_area = c7.slider("Superficie (m²)", 40, 300, 120)
    building_class = c8.selectbox("Classe", ["A4", "A3", "A2", "A1", "B", "C", "D"])
    occupants = st.slider("Occupanti", 1, 8, 3)
    heat_pump_cop = st.slider("COP Pompa di Calore", 2.0, 5.0, 3.5)
    
    has_ev = st.checkbox("Integra Auto Elettrica (EV)", value=False)
    if has_ev:
        st.markdown("---")
        ev_capacity_kwh = st.slider("Batteria Auto (kWh)", 20, 150, 50)
        c9, c10 = st.columns(2)
        ev_km_day = c9.slider("Km/Giorno", 10, 150, 40)
        ev_efficiency_wh_km = c10.slider("Wh/km", 120, 250, 160)
        daily_ev_demand_kwh = (ev_km_day * ev_efficiency_wh_km) / 1000.0
        annual_ev_kwh = daily_ev_demand_kwh * 365
        
        st.markdown("**Profilo Connessione V2H**")
        c11, c12 = st.columns(2)
        ev_plug_in = c11.slider("Ora Allaccio", 0, 23, 18)
        ev_plug_out = c12.slider("Ora Distacco", 0, 23, 7)
        v2h_power_kw = st.slider("Potenza Inverter V2H (kW)", 2.3, 22.0, 6.0)
        v2h_eff = st.slider("Efficienza Caricatore (%)", 70, 100, 90) / 100.0
        ev_soc_travel_min = daily_ev_demand_kwh + (ev_capacity_kwh * 0.2)
    else:
        annual_ev_kwh, daily_ev_demand_kwh = 0, 0

st.sidebar.markdown("### 📍 Localizzazione")
location_query = st.sidebar.text_input("Località", value="L'Aquila, Italia", label_visibility="collapsed")
if st.sidebar.button("🔍 Centra Mappa", use_container_width=True):
    try:
        geo_url = f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1"
        data = requests.get(geo_url, headers={"User-Agent": "EnergyGIS/1.0"}).json()
        if data:
            st.session_state.lat, st.session_state.lon = float(data[0]["lat"]), float(data[0]["lon"])
            st.sidebar.success(f"Trovata: {data[0]['display_name'][:30]}...")
        else: st.sidebar.error("Località non trovata")
    except Exception as e: st.sidebar.error(f"Errore geocoding")

# --- SEZIONE MAPPA ---
st.subheader("🗺️ Inquadramento Territoriale dell'Impianto")
m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=6)
folium.Marker([st.session_state.lat, st.session_state.lon], tooltip="Sito Selezionato").add_to(m)
map_data = st_folium(m, width="100%", height=320)

if map_data["last_clicked"] is not None:
    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

lat, lon = st.session_state.lat, st.session_state.lon
st.info(f"📍 **Coordinate di calcolo attive:** Latitudine {lat:.4f}° | Longitudine {lon:.4f}°")

# --- FUNZIONI DI SUPPORTO GRAFICI (STILE PROFESSIONALE COMPATTO) ---
def setup_plot_style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=10, fontweight='600', color='#1E3A8A', loc='left', pad=10)
    ax.set_xlabel(xlabel, fontsize=8, color='#4B5563')
    ax.set_ylabel(ylabel, fontsize=8, color='#4B5563')
    ax.tick_params(axis='both', which='major', labelsize=8, labelcolor='#4B5563')
    ax.grid(True, linestyle='--', alpha=0.3, color='#9CA3AF')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')

# --- CONFIGURAZIONE CHIAMATE API ---
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

def estimate_heating_demand():
    thermal_coefficients = {"A4": 15, "A3": 25, "A2": 35, "A1": 45, "B": 60, "C": 90, "D": 130}
    coeff = thermal_coefficients[building_class]
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2024-01-01&end_date=2024-12-31&hourly=temperature_2m"
    temperatures = requests.get(url).json()["hourly"]["temperature_2m"]
    
    monthly_hours = [744, 696, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    idx, monthly_heating = 0, []
    for hours in monthly_hours:
        m_energy = sum([max(0, 20 - temperatures[idx + i]) * coeff * house_area / 1000 / heat_pump_cop for i in range(hours)])
        monthly_heating.append(m_energy)
        idx += hours
        
    monthly_base = [(1200 + occupants * 750) / 12] * 12
    monthly_ev = [annual_ev_kwh / 12] * 12 if has_ev else [0] * 12
    total_monthly = [monthly_heating[i] + monthly_base[i] + monthly_ev[i] for i in range(12)]
    return {"monthly_total": total_monthly, "monthly_heating": monthly_heating, "monthly_base": monthly_base}

# --- PROCESSO DI ANALISI ---
if st.button("⚡ Elabora Simulazione Energetica Avanzata", type="primary", use_container_width=True):
    solar_monthly, wind_monthly = [0]*12, [0]*12
    
    # FETCH DATI
    solar_data = get_pvgis_data()
    if solar_data:
        solar_monthly = [m["E_m"] * (pv_efficiency / 20) for m in solar_data["outputs"]["monthly"]["fixed"]]
        solar_profiles = build_typical_day_profiles(solar_monthly, is_solar=True)
        
    wind_data = get_wind_data()
    if wind_data:
        wind_monthly = [(wind_data["annual_energy"] / 12 * (0.85 + 0.25 * math.sin(i / 12 * 2 * math.pi))) for i in range(12)]
        wind_profiles = build_typical_day_profiles(wind_monthly, is_solar=False)
        
    load_data = estimate_heating_demand()
    monthly_load = load_data["monthly_total"]
    total_annual_load = sum(monthly_load)
    total_monthly_prod = [s + w for s, w in zip(solar_monthly, wind_monthly)]
    total_annual_prod = sum(total_monthly_prod)

    # LAYOUT COLONNE PER GENERAZIONE E CARICHI MENSILE
    st.subheader("📊 Bilancio Energetico e Sostenibilità")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig, ax = plt.subplots(figsize=(6, 2.5))
        ax.plot(range(1, 13), solar_monthly, label="Fotovoltaico", color="#F59E0B", lw=1.5)
        ax.bar(range(1, 13), wind_monthly, label="Eolico", color="#3B82F6", alpha=0.6, width=0.4)
        ax.plot(range(1, 13), total_monthly_prod, label="Produzione Totale", color="#10B981", lw=2)
        setup_plot_style(ax, "Produzione Mensile Stimata", "Mese", "kWh")
        ax.legend(fontsize=7, frameon=False)
        st.pyplot(fig)
        
    with col_g2:
        fig, ax = plt.subplots(figsize=(6, 2.5))
        ax.plot(range(1, 13), monthly_load, label="Consumo Totale", color="#EF4444", lw=2)
        ax.fill_between(range(1, 13), load_data["monthly_heating"], label="Riscaldamento", color="#FCA5A5", alpha=0.4)
        setup_plot_style(ax, "Profilo di Consumo dell'Abitazione", "Mese", "kWh")
        ax.legend(fontsize=7, frameon=False)
        st.pyplot(fig)

    # COSTRUZIONE PROFILI GIORNALIERI ORARI DI DETTAGLIO
    hourly_prod_dict, hourly_load_dict, hourly_house_pure_load = {}, {}, {}
    for month in range(1, 13):
        p_profile, l_profile, pure_profile = [], [], []
        total_house_pure_month = load_data["monthly_heating"][month-1] + load_data["monthly_base"][month-1]
        for h in range(24):
            prod = solar_profiles[month][h] + wind_profiles[month][h]
            evening_peak = (1.1 + 0.5 * math.exp(-((h - 20) ** 2) / 12))
            
            p_profile.append(prod)
            l_profile.append((monthly_load[month - 1] / 30 / 24 * evening_peak))
            pure_profile.append((total_house_pure_month / 30 / 24 * evening_peak))
        hourly_prod_dict[month] = p_profile
        hourly_load_dict[month] = l_profile
        hourly_house_pure_load[month] = pure_profile

    # --- SIMULAZIONE ALGORITMO ACCUMULO STAZIONARIO (STRATEGIA 1) ---
    current_soc_house_s1 = soc_min
    total_autoconsumo_s1 = 0
    monthly_autoconsumo_s1 = []
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
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
        monthly_autoconsumo_s1.append(m_direct + m_batt)
        total_autoconsumo_s1 += (m_direct + m_batt)

    # --- SIMULAZIONE ALGORITMO ACCUMULO COMPLESSO V2H (STRATEGIA 2) ---
    current_soc_house_s2 = soc_min
    current_soc_ev = ev_capacity_kwh if has_ev else 0.0
    total_autoconsumo_s2 = 0
    monthly_autoconsumo_s2 = []
    
    # Dizionari per salvare l'andamento orario dell'ultimo giorno delle 4 stagioni
    seasons_mapping = {"Inverno": 1, "Primavera": 4, "Estate": 7, "Autunno": 10}
    seasonal_hourly_data = {s: {"soc_house": [], "soc_ev": [], "prod": [], "load_pure": [], "load_total_with_ev_charge": []} for s in seasons_mapping}
    
    def is_ev_connected(hour, p_in, p_out):
        return hour >= p_in or hour < p_out if p_in > p_out else p_in <= hour < p_out

    for month in range(1, 13):
        m_direct, m_storage, days = 0, 0, days_in_months[month - 1]
        for day in range(days):
            if has_ev:
                hours_outside = 24 - ((ev_plug_out - ev_plug_in) % 24 if ev_plug_in != ev_plug_out else 24)
                ev_hourly_travel_drain = daily_ev_demand_kwh / (hours_outside if hours_outside > 0 else 24)
            else: ev_hourly_travel_drain = 0
                
            for h in range(24):
                prod_h, load_house_h = hourly_prod_dict[month][h], hourly_house_pure_load[month][h]
                connected = has_ev and is_ev_connected(h, ev_plug_in, ev_plug_out)
                
                if has_ev and not connected:
                    current_soc_ev = max(0.0, current_soc_ev - ev_hourly_travel_drain)
                
                diretto = min(prod_h, load_house_h)
                m_direct += diretto
                surplus, deficit = prod_h - diretto, load_house_h - diretto
                
                initial_ev_soc_for_tracking = current_soc_ev
                
                # CARICA SMART
                if surplus > 0:
                    if battery_capacity_kwh > 0 and current_soc_house_s2 < soc_max:
                        charge_h = min(surplus * battery_eff, soc_max - current_soc_house_s2)
                        current_soc_house_s2 += charge_h
                        surplus -= (charge_h / battery_eff)
                    if connected and surplus > 0 and current_soc_ev < ev_capacity_kwh:
                        charge_ev = min(min(v2h_power_kw, surplus) * v2h_eff, ev_capacity_kwh - current_soc_ev)
                        current_soc_ev += charge_ev
                
                # SCARICA SMART (V2H prioritario)
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
                
                # RE-INTEGRO OBBLIGATORIO AUTOMOBILE
                if connected and current_soc_ev < ev_capacity_kwh:
                    hours_to_go = ev_plug_out - h if ev_plug_out > h else (24 - h) + ev_plug_out
                    if (ev_capacity_kwh - current_soc_ev) >= (hours_to_go * v2h_power_kw * v2h_eff) or hours_to_go <= 3:
                        actual_ev_charge = min(min(v2h_power_kw, (ev_capacity_kwh - current_soc_ev) / v2h_eff) * v2h_eff, ev_capacity_kwh - current_soc_ev)
                        current_soc_ev += actual_ev_charge
                
                # Calcolo del carico totale istantaneo includendo i prelievi effettivi dell'EV
                ev_net_charge_demand = max(0.0, (current_soc_ev - initial_ev_soc_for_tracking) / v2h_eff) if connected else 0.0
                instantaneous_total_load = load_house_h + ev_net_charge_demand
                
                # Salvataggio dati orari per le analisi stagionali
                for season_name, season_month in seasons_mapping.items():
                    if month == season_month and day == days - 1:
                        seasonal_hourly_data[season_name]["soc_house"].append(current_soc_house_s2)
                        seasonal_hourly_data[season_name]["soc_ev"].append(current_soc_ev)
                        seasonal_hourly_data[season_name]["prod"].append(prod_h)
                        seasonal_hourly_data[season_name]["load_pure"].append(load_house_h)
                        seasonal_hourly_data[season_name]["load_total_with_ev_charge"].append(instantaneous_total_load)
                        
        monthly_autoconsumo_s2.append(m_direct + m_storage)
        total_autoconsumo_s2 += (m_direct + m_storage)

    # SCALATURA INDICI DI PRESTAZIONE (KPI)
    ssp_s1, ssp_s2 = (total_autoconsumo_s1 / total_annual_load) * 100, (total_autoconsumo_s2 / total_annual_load) * 100
    sc_s1, sc_s2 = (total_autoconsumo_s1 / total_annual_prod) * 100, (total_autoconsumo_s2 / total_annual_prod) * 100

    # --- SEZIONE CRITICA CONFRONTI (UI / METRICS) ---
    st.subheader("🔋 Analisi Comparativa dell'Accumulo ed Efficientamento Locali")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("##### 🏛️ Configurazione 1: Carica Standard + Batteria Casa")
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Autoconsumo", f"{total_autoconsumo_s1:.0f} kWh")
        c_m2.metric("Autosufficienza (SSP)", f"{ssp_s1:.1f} %")
        c_m3.metric("Quota Rinnovabile (SC)", f"{sc_s1:.1f} %")
        
    with col_m2:
        st.markdown("##### 🚗 Configurazione 2: Sistema Intelligente V2H Bidirezionale")
        c_m4, c_m5, c_m6 = st.columns(3)
        c_m4.metric("Autoconsumo", f"{total_autoconsumo_s2:.0f} kWh", f"+{total_autoconsumo_s2 - total_autoconsumo_s1:.0f} kWh")
        c_m5.metric("Autosufficienza (SSP)", f"{ssp_s2:.1f} %", f"{ssp_s2 - ssp_s1:.1f} %")
        c_m6.metric("Quota Rinnovabile (SC)", f"{sc_s2:.1f} %", f"{sc_s2 - sc_s1:.1f} %")

    # --- NUOVA SEZIONE DI DETTAGLIO ORARIO STAGIONALE (GIORNI MEDI TIPICI) ---
    st.subheader("📈 Analisi Oraria di Dettaglio per Stagione (Giornate Medie)")
    st.markdown("Seleziona una delle schede stagionali per analizzare la dinamica simultanea tra producibilità FER, carichi interni e risposte dei sistemi di accumulo stazionario e mobile (V2H).")
    
    tabs = st.tabs(["❄️ Giorno Medio Invernale", "🌱 Giorno Medio Primavera", "☀️ Giorno Medio Estivo", "🍂 Giorno Medio Autunnale"])
    seasons_list = ["Inverno", "Primavera", "Estate", "Autunno"]
    
    for tab, season_name in zip(tabs, seasons_list):
        with tab:
            col_chart1, col_chart2 = st.columns(2)
            s_data = seasonal_hourly_data[season_name]
            
            with col_chart1:
                # Grafico 1: Bilancio flussi di potenza (Produzione vs Consumi)
                fig_f1, ax_f1 = plt.subplots(figsize=(6, 2.8))
                ax_f1.plot(range(24), s_data["prod"], label="Producibilità FER Totale", color="#10B981", lw=2)
                ax_f1.plot(range(24), s_data["load_pure"], label="Carico Abitazione Puro", color="#EF4444", lw=1.5, linestyle="--")
                ax_f1.fill_between(range(24), s_data["load_total_with_ev_charge"], color="#EF4444", alpha=0.15, label="Fabbisogno Totale (+Carica EV)")
                setup_plot_style(ax_f1, f"Flussi di Energia - {season_name}", "Ora del Giorno", "Energia Oraria (kWh)")
                ax_f1.legend(fontsize=7, frameon=False, loc="upper left")
                st.pyplot(fig_f1)
                
            with col_chart2:
                # Grafico 2: Dinamica dello stato di carica degli accumuli (SoC)
                fig_f2, ax_f2 = plt.subplots(figsize=(6, 2.8))
                soc_h_pct = [v / battery_capacity_kwh * 100 if battery_capacity_kwh > 0 else 0 for v in s_data["soc_house"]]
                ax_f2.plot(range(24), soc_h_pct, label="SoC % Accumulo Casa", color='#D97706', lw=1.8, marker='s', markersize=2)
                
                if has_ev:
                    soc_e_pct = [v / ev_capacity_kwh * 100 for v in s_data["soc_ev"]]
                    ax_f2.plot(range(24), soc_e_pct, label="SoC % Batteria EV (V2H)", color='#0D9488', lw=1.8, marker='o', markersize=2)
                    c_mask = [is_ev_connected(h, ev_plug_in, ev_plug_out) for h in range(24)]
                    ax_f2.fill_between(range(24), 0, 100, where=c_mask, color='#10B981', alpha=0.05, label='Fascia Allaccio EV')
                
                setup_plot_style(ax_f2, f"Stato di Carica (SoC) Sistemi di Accumulo - {season_name}", "Ora del Giorno", "Stato di Carica (%)")
                ax_f2.set_ylim(-5, 105)
                ax_f2.set_xticks(range(0, 24, 2))
                ax_f2.legend(fontsize=7, frameon=False, loc="lower left")
                st.pyplot(fig_f2)

    # GRAFICO DI SINTESI MENSILE SULL'ANNO
    st.markdown("---")
    st.subheader("📊 Sintesi dell'Autoconsumo su Base Mensile")
    fig12, ax12 = plt.subplots(figsize=(12, 2.5))
    x_idx = range(1, 13)
    ax12.bar([x - 0.15 for x in x_idx], monthly_load, width=0.25, label='Carico Domestico Annuo', color='#9CA3AF', alpha=0.4)
    ax12.bar([x for x in x_idx], monthly_autoconsumo_s1, width=0.25, label='Autoconsumo Stazionario Standard', color='#F59E0B')
    ax12.bar([x + 0.15 for x in x_idx], monthly_autoconsumo_s2, width=0.25, label='Autoconsumo + Ottimizzazione V2H', color='#0D9488')
    setup_plot_style(ax12, "Confronto della Copertura dell'Autoconsumo Mensile", "Mese", "kWh")
    ax12.set_xticks(x_idx)
    ax12.legend(fontsize=7, frameon=False)
    st.pyplot(fig12)

# --- FOOTER INTERFACCIA ---
st.markdown("---")
st.caption("Engine: PVGIS & Open-Meteo API | Geocoding: Nominatim OSM | Sviluppato con Streamlit Professional Layout")