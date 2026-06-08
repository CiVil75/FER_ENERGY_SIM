import streamlit as st

# 1. Configurazione della pagina
st.set_page_config(page_title="RES-Based Home Simulator 8760", layout="wide")

# 2. CSS per distruggere la barra laterale, il menu e la toolbar di navigazione file
st.markdown("""
    <style>
    /* Nasconde completamente la barra laterale delle pagine */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    /* Rimuove l'header superiore dove compare il menu e il pulsante dei file */
    header {
        visibility: hidden !important;
        display: none !important;
    }
    /* Rimuove il footer in basso */
    footer {
        visibility: hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Rimanda subito alla pagina reale
st.switch_page("pages/app_principale.py")
