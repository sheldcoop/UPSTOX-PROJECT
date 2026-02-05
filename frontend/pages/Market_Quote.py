import streamlit as st
import pandas as pd
import requests
import sys
import os
import time

# Add project root to path for imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.components.stock_search import stock_search_component

st.set_page_config(page_title="Market Quote Intelligence", layout="wide")

API_BASE_URL = "http://localhost:5000/api/market-quote"

st.title("📊 Market Quote Intelligence")

# Tabs for Universes
tab1, tab2, tab5, tab3, tab4 = st.tabs(["🌎 Universe View", "🔍 Deep Search", "📊 Index Monitor", "📈 SME Monitor", "⚡ F&O Radar"])

def fetch_universe_data(universe_type):
    try:
        response = requests.get(f"{API_BASE_URL}/universe/{universe_type}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def fetch_indices_list():
    try:
        return requests.get(f"{API_BASE_URL}/indices").json()
    except:
        return []

def fetch_index_data(index_name):
    try:
        return requests.get(f"{API_BASE_URL}/index/{index_name}").json()
    except:
        return None

# --- TAB 1: Universe View ---
with tab1:
    st.header("Whole Universe Snapshot")
    universe_select = st.selectbox("Select Universe", ["NSE500", "SME", "FNO"])
    
    if st.button("Refresh Snapshot"):
        with st.spinner(f"Fetching {universe_select} data..."):
            data = fetch_universe_data(universe_select.lower())
            
            if data and data['data']:
                df = pd.DataFrame(data['data'])
                st.metric("Total Instruments", data['count'], f"Updated: {data['timestamp']}")
                
                # Key Metrics Display
                st.dataframe(df[[
                    'trading_symbol' if 'trading_symbol' in df.columns else 'instrument_key', 
                    'close', 'volume', 'total_buy_quantity', 'total_sell_quantity'
                ]].style.highlight_max(axis=0), use_container_width=True)
            else:
                st.warning("No data found or API offline.")

# --- TAB 2: Deep Search ---
with tab2:
    st.header("Individual Stock Deep Dive")
    selected_stock = stock_search_component(key="deep_dive_search")
    
    if selected_stock:
        key = selected_stock['instrument_key']
        st.info(f"Fetching Quote for {selected_stock['trading_symbol']}...")
        
        try:
            resp = requests.get(f"{API_BASE_URL}/snapshot/{key}")
            if resp.status_code == 200:
                quote = resp.json()
                
                # Display Top Line
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Price", quote.get('close'), f"{quote.get('volume', 0):,} Vol")
                col2.metric("Buying Pressure", quote.get('total_buy_quantity'), delta_color="normal")
                col3.metric("Selling Pressure", quote.get('total_sell_quantity'), delta_color="inverse")
                col4.metric("OI", quote.get('oi', 'N/A'))
                
                # Market Depth Table
                st.subheader("Market Depth")
                depth_data = []
                for i in range(1, 6):
                    depth_data.append({
                        "Bid Qty": quote.get(f'bid_qty_{i}'),
                        "Bid Price": quote.get(f'bid_price_{i}'),
                        "Ask Price": quote.get(f'ask_price_{i}'),
                        "Ask Qty": quote.get(f'ask_qty_{i}')
                    })
                st.table(pd.DataFrame(depth_data))
                
            else:
                st.error("Quote not found in monitored tables.")
        except Exception as e:
            st.error(f"API Error: {e}")

# --- TAB 5: Index Monitor ---
with tab5:
    st.header("Thematic Index Tracker")
    indices = fetch_indices_list()
    
    if indices:
        selected_index = st.selectbox("Select Index", indices)
        if st.button("Load Index Constituents"):
            with st.spinner(f"Loading {selected_index}..."):
                idx_data = fetch_index_data(selected_index)
                if idx_data and idx_data.get('data'):
                    df = pd.DataFrame(idx_data['data'])
                    st.metric("Constituents", idx_data['count'], f"Updated: {idx_data['timestamp']}")
                    
                    st.dataframe(df[[
                        'instrument_key', 'close', 'open', 'high', 'low', 'volume', 'total_buy_quantity'
                    ]].style.highlight_max(axis=0), use_container_width=True)
                else:
                    st.warning("No data found or constituents not in active feed.")
    else:
        st.warning("No indices found. Run import_indices.py?")

# --- TAB 3: SME Monitor ---
with tab3:
    st.subheader("SME Liquidity Tracker")
    # Quick view for SMEs specifically
    if st.button("Load SME Data"):
         data = fetch_universe_data('sme')
         if data and data['data']:
             df = pd.DataFrame(data['data'])
             # Calculate Pressure Ratio
             df['Pressure'] = df['total_buy_quantity'] / (df['total_sell_quantity'] + 1)
             st.dataframe(df.sort_values(by='Pressure', ascending=False).head(50))

# --- TAB 4: F&O Radar ---
with tab4:
    st.subheader("F&O Active Instruments")
    if st.button("Load F&O Data"):
         data = fetch_universe_data('fno')
         if data and data['data']:
             df = pd.DataFrame(data['data'])
             st.dataframe(df)

st.markdown("---")
st.caption("Data sourced from Upstox Market Quote API (5-min snapshot).")
