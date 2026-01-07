import re
import json
import pandas as pd
import numpy as np
import streamlit as st
import global_state_lib as gsl

# Do NOT call st.set_page_config() here — main.py sets it once for the app.
st.title("Saved CO2 for product")

global_state = gsl.get_global_state()

# Access global_state via the GlobalState API (it doesn't implement dict.get)
if 'status' not in global_state.get_key_names() or global_state['status'] != 'OK':
    st.info("No product loaded — open 'Enter Product ID' in the sidebar and load a product (e.g. Product ID = 1).")
    if st.checkbox("Show global state keys (debug)"):
        st.write(global_state.get_key_names())
    st.stop()

product_id = global_state['product_id'] if 'product_id' in global_state.get_key_names() else None
st.write(f"Product ID: {product_id}")

st.markdown("---")

# Helper: robustly compare product ids (handles '1', 1, 1.0, '1.0')
def pid_equals(a, b):
    try:
        return float(str(a)) == float(str(b))
    except Exception:
        return str(a) == str(b)

# 1) Find dynamic dataframe(s) in metadata
pages_meta = global_state['metadata_data_content_pages'] if 'metadata_data_content_pages' in global_state.get_key_names() else {}
dynamic_dfs = []
for page_name, meta in pages_meta.items():
    values = meta.get('values', {})
    for sub, val in values.items():
        if isinstance(val, pd.DataFrame):
            dynamic_dfs.append((page_name, sub, val))

if not dynamic_dfs:
    st.warning('No dynamic data tables found in metadata; unable to compute CO2.')
    st.stop()

# 2) Locate CO2-like columns and rows for the selected product
co2_cols = []
matched_rows = pd.DataFrame()
for page_name, sub, df in dynamic_dfs:
    # make a copy to avoid mutating shared state
    df_copy = df.copy()
    # Normalize column names for searching
    cols = df_copy.columns.tolist()
    for c in cols:
        cl = c.lower()
        if ('co2' in cl and 'save' in cl) or ('co2 saving' in cl) or ('co2' in cl and 'recoat' in cl) or ('co2 footprint' in cl):
            co2_cols.append((page_name, sub, c))
    # If there are CO2 columns, filter rows for product id
    if any(pid for pid in [product_id]):
        # Build mask by comparing Product ID values robustly
        if 'Product ID' in df_copy.columns:
            mask = df_copy['Product ID'].apply(lambda x: pid_equals(x, product_id))
        else:
            # Try to infer product id column if named differently
            pid_col = None
            for candidate in df_copy.columns:
                if 'product' in candidate.lower() and 'id' in candidate.lower():
                    pid_col = candidate
                    break
            if pid_col:
                mask = df_copy[pid_col].apply(lambda x: pid_equals(x, product_id))
            else:
                mask = pd.Series([False]*len(df_copy))
        rows = df_copy[mask]
        if len(rows) > 0:
            matched_rows = pd.concat([matched_rows, rows], ignore_index=True)

if matched_rows.empty:
    st.info('No dynamic rows found for this Product ID. The CO2 metric may be on another page or the Product ID mismatch.')
    st.stop()

# Determine the CO2 column to use (prefer columns found earlier, else search within matched_rows)
selected_co2_cols = []
if co2_cols:
    # use the column names collected (may come from multiple pages)
    selected_co2_cols = list({c for (_, _, c) in co2_cols})
else:
    # fallback: look for any column name containing 'co2' in matched_rows
    selected_co2_cols = [c for c in matched_rows.columns if 'co2' in c.lower()]

if not selected_co2_cols:
    st.warning('No CO2-like columns found for this product.')
    st.write('Available columns in dynamic table:', matched_rows.columns.tolist())
    st.stop()

# Extract numeric CO2 values and sum them
co2_values = []
for c in selected_co2_cols:
    vals = pd.to_numeric(matched_rows[c], errors='coerce')
    vals = vals.dropna()
    if not vals.empty:
        co2_values.extend(vals.tolist())

total_co2 = float(np.nansum(co2_values)) if co2_values else 0.0

st.metric(label='CO2 saved', value=f"{total_co2:,.2f} kg")

st.markdown('### Contribution details')
if not matched_rows.empty:
    # show relevant columns: Product ID, Update ID, Historic (if present), CO2 columns
    cols_to_show = [c for c in ['Product ID', 'Update ID', 'Historic'] if c in matched_rows.columns]
    cols_to_show += selected_co2_cols
    # avoid duplicate columns
    cols_to_show = [c for i, c in enumerate(cols_to_show) if c not in cols_to_show[:i]]
    st.dataframe(matched_rows[cols_to_show].reset_index(drop=True))

# 3) Try to extract Diameter from static metadata
diameter = None
for page_name, meta in pages_meta.items():
    headers = meta.get('headers', {})
    values = meta.get('values', {})
    for sub, val in values.items():
        # static string lists
        if isinstance(val, list):
            hdrs = headers.get(sub, [])
            for i, h in enumerate(hdrs):
                if 'dimension' in h.lower() or 'diameter' in h.lower():
                    try:
                        candidate = str(val[i])
                    except Exception:
                        candidate = str(val)
                    m = re.search(r'Diameter\s*:??\s*(\d+(?:\.\d+)?)\s*cm', candidate, flags=re.IGNORECASE)
                    if m:
                        diameter = float(m.group(1))
                        break
        # static df possibility
        if isinstance(val, pd.DataFrame):
            if 'Dimensions' in val.columns:
                # try match product row
                df_val = val.copy()
                if 'Product ID' in df_val.columns:
                    for idx, r in df_val.iterrows():
                        if pid_equals(r['Product ID'], product_id):
                            candidate = str(r['Dimensions'])
                            m = re.search(r'Diameter\s*:??\s*(\d+(?:\.\d+)?)\s*cm', candidate, flags=re.IGNORECASE)
                            if m:
                                diameter = float(m.group(1))
                                break
    if diameter is not None:
        break

if diameter is not None:
    st.markdown(f"**Diameter (from static metadata):** {diameter} cm")
else:
    st.info('Diameter could not be extracted from static metadata for this product.')
