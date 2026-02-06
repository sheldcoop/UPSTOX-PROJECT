import streamlit as st
import requests
import pandas as pd
from typing import Optional, Dict

# API Config
API_BASE_URL = "http://localhost:5000/api/market-quote"

def stock_search_component(key: str = "stock_search") -> Optional[Dict]:
    """
    Reusable Stock Search Component.
    Returns the selected stock dictionary if selected, else None.
    """
    st.markdown("### 🔍 Search Stocks")
    
    # Session state initialization for cache
    if f"{key}_options" not in st.session_state:
        st.session_state[f"{key}_options"] = []
    
    query = st.text_input("Enter Symbol or Name", key=f"{key}_input")
    
    if query and len(query) >= 2:
        try:
            response = requests.get(f"{API_BASE_URL}/search", params={'q': query, 'limit': 10})
            if response.status_code == 200:
                results = response.json()
                st.session_state[f"{key}_options"] = results
            else:
                st.error("Search API failed")
        except Exception as e:
            st.error(f"Connection error: {e}")
            
    options = st.session_state[f"{key}_options"]
    
    if not options:
        return None
        
    # Format options for selectbox: "SYMBOL (Name)"
    option_map = {f"{row['trading_symbol']} ({row['name']})": row for row in options}
    
    selected_label = st.selectbox("Select Instrument", list(option_map.keys()), key=f"{key}_select")
    
    if selected_label:
        return option_map[selected_label]
    
    return None
