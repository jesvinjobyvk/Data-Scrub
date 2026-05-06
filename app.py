"""
DataScrub – Interactive Data Cleaning Studio
============================================
Run locally:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import json, io
import re
from datetime import datetime
from collections import deque

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="DataScrub – Data Cleaning Studio",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html,body,[class*="css"]  { font-family:'DM Sans',sans-serif; }
h1,h2,h3                  { font-family:'Space Mono',monospace; }

.main-header{
    background:linear-gradient(135deg,#1a1f2e 0%,#0f1117 100%);
    border:1px solid #2a3040;border-radius:12px;
    padding:1.6rem 2rem;margin-bottom:1.2rem;
    position:relative;overflow:hidden;
}
.main-header::before{
    content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,#00d4aa,#7c6af7,#ff6b6b);
}
.main-header h1{color:#00d4aa;margin:0;font-size:1.8rem;letter-spacing:-1px;}
.main-header p {color:#6b7fa3;margin:.25rem 0 0;font-size:.88rem;}

.stat-card{background:#1a1f2e;border:1px solid #2a3040;border-radius:10px;
           padding:.8rem 1rem;text-align:center;}
.stat-card .value{font-family:'Space Mono',monospace;font-size:1.65rem;color:#00d4aa;}
.stat-card .label{font-size:.72rem;color:#6b7fa3;text-transform:uppercase;letter-spacing:1px;}

.audit-entry{background:#1a1f2e;border-left:3px solid #00d4aa;
             border-radius:0 8px 8px 0;padding:.4rem .85rem;
             margin-bottom:.3rem;font-size:.82rem;color:#c8d0e0;}
.audit-entry .ts{color:#6b7fa3;font-size:.7rem;font-family:'Space Mono',monospace;}

.bw{display:inline-block;background:#2a1f30;border:1px solid #7c3f5a;
    color:#ff8fab;border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:600;margin:2px;}
.bg{display:inline-block;background:#1a2e25;border:1px solid #1f6b45;
    color:#00d4aa; border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:600;margin:2px;}

.sec{font-family:'Space Mono',monospace;font-size:.78rem;color:#7c6af7;
     text-transform:uppercase;letter-spacing:2px;
     margin-bottom:.65rem;padding-bottom:.3rem;border-bottom:1px solid #2a3040;}

.stButton>button{background:#00d4aa;color:#0f1117;border:none;border-radius:8px;
    font-family:'Space Mono',monospace;font-weight:700;font-size:.8rem;
    padding:.42rem 1rem;transition:all .2s;}
.stButton>button:hover{background:#00b894;transform:translateY(-1px);}

.undo-btn>button{background:#6c5ce7;color:#fff;}
.undo-btn>button:hover{background:#5b4bc4;}
.redo-btn>button{background:#fdcb6e;color:#1a1f2e;}
.redo-btn>button:hover{background:#f9ca24;}

.stDownloadButton>button{background:#7c6af7;color:#fff;border:none;border-radius:8px;
    font-family:'Space Mono',monospace;font-weight:700;font-size:.8rem;}
.stDownloadButton>button:hover{background:#6c5ce7;}
div[data-testid="stExpander"]{background:#1a1f2e;border:1px solid #2a3040;
    border-radius:10px;margin-bottom:.65rem;}

.preview-box{background:#1a2e25;border:1px solid #00d4aa;border-radius:5px;padding:10px;margin:10px 0;}
.type-error{background-color:#ff6b6b22;border-left:3px solid #ff6b6b;padding:8px;margin:5px 0;border-radius:4px;}
.type-success{background-color:#00d4aa22;border-left:3px solid #00d4aa;padding:8px;margin:5px 0;border-radius:4px;}
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────
def _init():
    for k, v in {
        "df_original": None,
        "df_working":  None,
        "filename":    None,
        "audit_log":   [],
        "recipe":      [],
        "data_loaded": False,
        "history":     deque(maxlen=50),
        "history_index": -1,
        "show_raw_data": False,
        "fr_rules": [],
        "show_preview": {},
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Undo/Redo Functions (FIXED) ────────────────────────────────────────────
def save_state():
    if st.session_state.df_working is not None:
        current_state = st.session_state.df_working.copy()
        if st.session_state.history_index < len(st.session_state.history) - 1:
            while len(st.session_state.history) > st.session_state.history_index + 1:
                st.session_state.history.pop()
        st.session_state.history.append(current_state)
        st.session_state.history_index = len(st.session_state.history) - 1

def undo():
    if can_undo():
        st.session_state.history_index -= 1
        st.session_state.df_working = st.session_state.history[st.session_state.history_index].copy()
        log("↩️ Undid last action")
        return True
    return False

def redo():
    if can_redo():
        st.session_state.history_index += 1
        st.session_state.df_working = st.session_state.history[st.session_state.history_index].copy()
        log("↪️ Redid last action")
        return True
    return False

def can_undo():
    return (st.session_state.df_working is not None and 
            len(st.session_state.history) > 0 and
            st.session_state.history_index > 0)

def can_redo():
    return (st.session_state.df_working is not None and 
            len(st.session_state.history) > 0 and
            st.session_state.history_index < len(st.session_state.history) - 1)


# ── Helper Functions ────────────────────────────────────────────────────────
def log(msg):
    st.session_state.audit_log.append({"ts": datetime.now().strftime("%H:%M:%S"), "msg": msg})

def recipe_add(step):
    st.session_state.recipe.append(step)

def read_file(f) -> pd.DataFrame:
    n = f.name.lower()
    if n.endswith((".csv", ".txt")):
        try:
            df = pd.read_csv(f)
        except Exception:
            f.seek(0)
            df = pd.read_csv(f, on_bad_lines="skip", engine="python")
    elif n.endswith((".xlsx", ".xls")): 
        df = pd.read_excel(f)
    elif n.endswith(".json"):           
        df = pd.read_json(f)
    else:
        raise ValueError("Unsupported type — use CSV, Excel, or JSON.")
    df = df.replace(r'^\s*$', np.nan, regex=True)
    return df

def detect_issues(df):
    df_clean = df.replace(r'^\s*$', np.nan, regex=True)
    
    miss = {}
    for col in df_clean.columns:
        missing_count = df_clean[col].isnull().sum()
        if missing_count > 0:
            miss[col] = {
                "count": missing_count, 
                "percentage": (missing_count/len(df))*100
            }
    
    dupes = int(df_clean.duplicated().sum())
    
    outliers = {}
    for col in df_clean.select_dtypes(include=[np.number]).columns:
        s = df_clean[col].dropna()
        if len(s) >= 4:
            mu, sd = s.mean(), s.std()
            if sd > 0:
                lower, upper = mu - 3*sd, mu + 3*sd
                mask = (df_clean[col] < lower) | (df_clean[col] > upper)
                n = int(mask.sum())
                if n:
                    outliers[col] = {
                        "count": n, 
                        "percentage": (n/len(df))*100, 
                        "lower": lower, 
                        "upper": upper
                    }
    
    return {"missing": miss, "duplicates": dupes, "outliers": outliers}

def fill_missing(df, col, method, custom=""):
    df = df.copy()
    if col in df.columns:
        df[col] = df[col].replace(r'^\s*$', np.nan, regex=True)
        
        if method == "mean" and pd.api.types.is_numeric_dtype(df[col]):
            fill_value = df[col].mean()
            df[col] = df[col].fillna(fill_value)
            return df, fill_value
        elif method == "median" and pd.api.types.is_numeric_dtype(df[col]):
            fill_value = df[col].median()
            df[col] = df[col].fillna(fill_value)
            return df, fill_value
        elif method == "mode":
            mode_values = df[col].mode()
            if not mode_values.empty:
                fill_value = mode_values[0]
                df[col] = df[col].fillna(fill_value)
                return df, fill_value
        elif method == "custom":
            df[col] = df[col].fillna(custom)
            return df, custom
        elif method == "drop":
            df = df.dropna(subset=[col])
            return df, None
    return df, None

def apply_fr(df, rule):
    df = df.copy()
    tcols = list(df.select_dtypes(include=["object","string"]).columns)
    targets = tcols if rule["columns"] == ["__ALL__"] \
              else [c for c in rule["columns"] if c in df.columns]
    for c in targets:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace(
                rule["find"], rule["replace"], regex=False)
    return df

def to_csv(df):  
    return df.to_csv(index=False).encode("utf-8")

def to_xlsx(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Cleaned")
    return buf.getvalue()


# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🧹 DataScrub</h1>
  <p>Interactive Data Cleaning Studio — upload · detect · fix · export</p>
</div>""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sec">📂 Upload Dataset</div>', unsafe_allow_html=True)
    up = st.file_uploader("CSV · Excel · JSON · TXT",
                          type=["csv","txt","xlsx","xls","json"],
                          key="file_uploader_main")
    
    if up is not None:
        if st.session_state.filename != up.name or not st.session_state.data_loaded:
            try:
                with st.spinner("Reading file..."):
                    raw = read_file(up)
                st.session_state.df_original = raw.copy()
                st.session_state.df_working = raw.copy()
                st.session_state.filename = up.name
                st.session_state.audit_log = []
                st.session_state.recipe = []
                st.session_state.fr_rules = []
                st.session_state.data_loaded = True
                
                st.session_state.history.clear()
                st.session_state.history.append(raw.copy())
                st.session_state.history_index = 0
                
                log(f"✅ Loaded '{up.name}' - {len(raw):,} rows x {len(raw.columns)} cols")
                st.success(f"**{up.name}**\n{len(raw):,} rows · {len(raw.columns)} cols")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")
                st.session_state.data_loaded = False
    
    st.divider()
    
    # ========== LOAD RECIPE SECTION ==========
    st.markdown('<div class="sec">📋 Load Recipe</div>', unsafe_allow_html=True)
    rfile = st.file_uploader("Apply a saved recipe (.json)",
                             type=["json"], 
                             key="recipe_uploader")
    if rfile is not None:
        if st.button("📥 Apply Recipe", key="apply_recipe_btn", use_container_width=True):
            try:
                recipe_data = json.load(rfile)
                steps = recipe_data.get("steps", [])
                if steps:
                    save_state()
                    for s in steps:
                        action = s.get("action")
                        if action == "fill_missing":
                            df, _ = fill_missing(st.session_state.df_working, s["column"], s["method"], s.get("custom", ""))
                            st.session_state.df_working = df
                            log(f"[Recipe] Applied {action} on {s['column']}")
                        elif action == "drop_duplicates":
                            st.session_state.df_working = st.session_state.df_working.drop_duplicates()
                            log(f"[Recipe] Removed duplicates")
                        elif action == "find_replace":
                            st.session_state.df_working = apply_fr(st.session_state.df_working, s["rule"])
                            log(f"[Recipe] Applied find/replace")
                        elif action == "cap_outliers":
                            st.session_state.df_working[s["column"]] = st.session_state.df_working[s["column"]].clip(s["lower"], s["upper"])
                            log(f"[Recipe] Capped outliers in {s['column']}")
                    st.session_state.recipe.extend(steps)
                    save_state()
                    st.success(f"✅ Applied {len(steps)} recipe steps!")
                    st.rerun()
                else:
                    st.warning("No steps found in recipe file")
            except Exception as e:
                st.error(f"Recipe error: {e}")
    
    st.divider()
    
    # ========== UNDO/REDO SECTION ==========
    if st.session_state.df_working is not None:
        st.markdown('<div class="sec">↩️ Undo / Redo</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↩️ Undo", key="undo_btn", use_container_width=True, disabled=not can_undo()):
                if undo():
                    st.rerun()
        with col2:
            if st.button("↪️ Redo", key="redo_btn", use_container_width=True, disabled=not can_redo()):
                if redo():
                    st.rerun()
        
        st.caption(f"History: {st.session_state.history_index + 1}/{len(st.session_state.history)}")
        st.divider()
        
        # ========== RESET BUTTON ==========
        if st.button("🔄 Reset to Original", key="reset_btn", use_container_width=True):
            if st.session_state.df_original is not None:
                save_state()
                st.session_state.df_working = st.session_state.df_original.copy()
                st.session_state.audit_log = []
                st.session_state.recipe = []
                st.session_state.fr_rules = []
                log("🔄 Reset to original data")
                save_state()
                st.rerun()

# ── Main content ──────────────────────────────────────────────────────────
if st.session_state.df_working is None or not st.session_state.data_loaded:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#6b7fa3;">
        <div style="font-size:3.5rem">📊</div>
        <h3 style="font-family:'Space Mono',monospace;color:#2a3040">No data loaded</h3>
        <p>Upload a file from the sidebar to get started.<br>
           The file <strong>messy_users.csv</strong> is included — try it!</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

# Get current working data
df = st.session_state.df_working.copy()
df = df.replace(r'^\s*$', np.nan, regex=True)
st.session_state.df_working = df

# Stats bar
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="stat-card"><div class="value">{len(df):,}</div><div class="label">Rows</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><div class="value">{len(df.columns)}</div><div class="label">Columns</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-card"><div class="value">{int(df.isnull().sum().sum()):,}</div><div class="label">Missing</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-card"><div class="value">{int(df.duplicated().sum()):,}</div><div class="label">Duplicates</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="stat-card"><div class="value">{len(st.session_state.history)}</div><div class="label">History</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Raw Data Toggle
col1, col2 = st.columns([1, 3])
with col1:
    show_raw = st.checkbox("🔍 Show Original Raw Data", value=st.session_state.show_raw_data)
    if show_raw != st.session_state.show_raw_data:
        st.session_state.show_raw_data = show_raw
        st.rerun()

if st.session_state.show_raw_data and st.session_state.df_original is not None:
    st.markdown("---")
    st.markdown('<div class="sec">📄 Original Raw Data (Before Any Cleaning)</div>', unsafe_allow_html=True)
    st.dataframe(st.session_state.df_original, use_container_width=True, height=400)
    st.markdown("---")

# TABS - 8 tabs total (your original 7 + Data Quality as 8th)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Data Viewer", "🔍 Issues & Fixes", "🔧 Find & Replace", "✅ Data Quality", "📜 Audit", "💾 Export"
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 - Data Viewer
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="sec">📊 Current Data (After Cleaning)</div>', unsafe_allow_html=True)
    
    view_option = st.radio("View:", ["Sample (first 20 rows)", "Full Dataset", "Column Details"], horizontal=True)
    
    if view_option == "Sample (first 20 rows)":
        st.dataframe(df.head(20), use_container_width=True, height=500)
    elif view_option == "Full Dataset":
        st.dataframe(df, use_container_width=True, height=500)
    else:
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.notnull().sum().values,
            "Null %": (df.isnull().sum() / len(df) * 100).round(1).values,
            "Unique": [df[c].nunique() for c in df.columns],
        })
        st.dataframe(col_info, hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# TAB 2 - Issues & Fixes (YOUR ORIGINAL VERSION - KEPT AS IS)
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec">🔍 Detected Issues - Click buttons to fix</div>', unsafe_allow_html=True)
    
    with st.spinner("Analyzing data..."):
        issues = detect_issues(df)
    
    # Missing Values Section
    if issues['missing']:
        with st.expander(f"📊 Missing Values ({len(issues['missing'])} columns)", expanded=True):
            for col, info in issues['missing'].items():
                st.markdown(f"### Column: `{col}`")
                st.markdown(f"Missing: **{info['count']}** rows ({info['percentage']:.1f}%)")
                
                # Show sample of missing rows
                missing_sample = df[df[col].isnull()].head(3)
                if len(missing_sample) > 0:
                    st.markdown("**Sample rows with missing values:**")
                    st.dataframe(missing_sample, use_container_width=True)
                
                st.markdown("---")
                
                # Fix buttons in a row
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        mean_val = df[col].mean()
                        if st.button(f"📊 Fill with Mean ({mean_val:.2f})", key=f"fix_mean_{col}"):
                            save_state()
                            df, val = fill_missing(df, col, "mean")
                            st.session_state.df_working = df
                            log(f"Filled {info['count']} missing in {col} with mean ({val:.2f})")
                            recipe_add({"action": "fill_missing", "column": col, "method": "mean"})
                            save_state()
                            st.success(f"✅ Filled missing values in {col} with mean ({val:.2f})")
                            st.rerun()
                    
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        mode_display = mode_val[0]
                        if st.button(f"⭐ Fill with Mode ('{mode_display}')", key=f"fix_mode_{col}"):
                            save_state()
                            df, val = fill_missing(df, col, "mode")
                            st.session_state.df_working = df
                            log(f"Filled {info['count']} missing in {col} with mode ({val})")
                            recipe_add({"action": "fill_missing", "column": col, "method": "mode"})
                            save_state()
                            st.success(f"✅ Filled missing values in {col} with mode ('{val}')")
                            st.rerun()
                
                with col2:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        median_val = df[col].median()
                        if st.button(f"📈 Fill with Median ({median_val:.2f})", key=f"fix_median_{col}"):
                            save_state()
                            df, val = fill_missing(df, col, "median")
                            st.session_state.df_working = df
                            log(f"Filled {info['count']} missing in {col} with median ({val:.2f})")
                            recipe_add({"action": "fill_missing", "column": col, "method": "median"})
                            save_state()
                            st.success(f"✅ Filled missing values in {col} with median ({val:.2f})")
                            st.rerun()
                    
                    if st.button(f"🗑️ Drop Rows with Missing {col}", key=f"fix_drop_{col}"):
                        save_state()
                        before = len(df)
                        df = df.dropna(subset=[col])
                        st.session_state.df_working = df
                        log(f"Dropped {before - len(df)} rows with missing {col}")
                        recipe_add({"action": "drop_missing_rows", "column": col})
                        save_state()
                        st.success(f"✅ Dropped {before - len(df)} rows with missing values in {col}")
                        st.rerun()
                
                with col3:
                    st.markdown("**Custom Value:**")
                    custom_val = st.text_input(f"", key=f"custom_{col}", placeholder="Enter value", label_visibility="collapsed")
                    if st.button(f"✏️ Apply Custom", key=f"fix_custom_{col}"):
                        if custom_val:
                            save_state()
                            df, val = fill_missing(df, col, "custom", custom_val)
                            st.session_state.df_working = df
                            log(f"Filled {info['count']} missing in {col} with custom value: {custom_val}")
                            recipe_add({"action": "fill_missing", "column": col, "method": "custom", "custom": custom_val})
                            save_state()
                            st.success(f"✅ Filled missing values in {col} with '{custom_val}'")
                            st.rerun()
                        else:
                            st.warning("Please enter a value")
                
                st.markdown("---")
    
    # Duplicates Section
    if issues['duplicates'] > 0:
        with st.expander(f"🔄 Duplicate Rows ({issues['duplicates']} found)", expanded=True):
            st.warning(f"Found {issues['duplicates']} duplicate rows")
            
            # Show duplicate preview
            dupes = df[df.duplicated(keep=False)]
            if len(dupes) > 0:
                st.markdown("**Duplicate rows preview:**")
                st.dataframe(dupes.head(10), use_container_width=True)
            
            if st.button("🗑️ Remove All Duplicate Rows", key="remove_dupes_main"):
                save_state()
                before = len(df)
                df = df.drop_duplicates()
                st.session_state.df_working = df
                log(f"Removed {before - len(df)} duplicate rows")
                recipe_add({"action": "drop_duplicates"})
                save_state()
                st.success(f"✅ Removed {before - len(df)} duplicate rows")
                st.rerun()
    
    # Outliers Section
    if issues['outliers']:
        with st.expander(f"📈 Statistical Outliers ({len(issues['outliers'])} columns)", expanded=True):
            for col, info in issues['outliers'].items():
                st.markdown(f"### Column: `{col}`")
                st.markdown(f"Outliers: **{info['count']}** rows ({info['percentage']:.1f}%)")
                st.markdown(f"Normal range: `[{info['lower']:.2f}, {info['upper']:.2f}]`")
                
                # Show outlier values
                outlier_values = df[(df[col] < info['lower']) | (df[col] > info['upper'])][col].head(5)
                if len(outlier_values) > 0:
                    st.markdown("**Sample outlier values:**")
                    for val in outlier_values:
                        st.markdown(f"- `{val}`")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📏 Cap Outliers in {col}", key=f"cap_{col}"):
                        save_state()
                        df[col] = df[col].clip(info['lower'], info['upper'])
                        st.session_state.df_working = df
                        log(f"Capped {info['count']} outliers in {col}")
                        recipe_add({"action": "cap_outliers", "column": col, "lower": info['lower'], "upper": info['upper']})
                        save_state()
                        st.success(f"✅ Capped {info['count']} outliers in {col}")
                        st.rerun()
                
                with col2:
                    if st.button(f"❌ Remove Outlier Rows in {col}", key=f"remove_out_{col}"):
                        save_state()
                        before = len(df)
                        df = df[(df[col] >= info['lower']) & (df[col] <= info['upper'])]
                        st.session_state.df_working = df
                        log(f"Removed {before - len(df)} outlier rows from {col}")
                        recipe_add({"action": "remove_outlier_rows", "column": col, "lower": info['lower'], "upper": info['upper']})
                        save_state()
                        st.success(f"✅ Removed {before - len(df)} outlier rows from {col}")
                        st.rerun()
                
                st.markdown("---")


# ══════════════════════════════════════════════════════════════════
# TAB 3 - FIND & REPLACE (Consolidated: Batch Rules + Search & Row Editor)
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec">🔧 Find & Replace - Batch Rules & Search Editor</div>', unsafe_allow_html=True)
    
    # Create sub-tabs within this tab
    sub_tab1, sub_tab2 = st.tabs(["📋 Batch Rules", "🔍 Search & Row Editor"])
    
    # ========== SUB-TAB 1: BATCH RULES ==========
    with sub_tab1:
        st.markdown("**Create multiple find/replace rules and apply them together**")
        st.caption("Add rules to fix typos, standardize text, etc. - all applied in one click")
        
        # Form to add new rule
        with st.form("batch_rule_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                find_rule = st.text_input("Find:", placeholder='e.g., "dgos"', key="batch_find")
            with col_b:
                replace_rule = st.text_input("Replace with:", placeholder='e.g., "dogs"', key="batch_replace")
            
            tcols = ["All Text Columns"] + list(df.select_dtypes(include=["object", "string"]).columns)
            rule_cols = st.multiselect("Apply to column(s):", tcols, default=["All Text Columns"], key="batch_cols")
            
            if st.form_submit_button("➕ Add Rule"):
                if find_rule.strip():
                    st.session_state.fr_rules.append({
                        "find": find_rule,
                        "replace": replace_rule,
                        "columns": ["__ALL__"] if "All Text Columns" in rule_cols else rule_cols,
                    })
                    st.toast(f"Rule added: '{find_rule}' → '{replace_rule}'")
                    st.rerun()
                else:
                    st.warning("Please enter text to find")
        
        # Display pending rules
        if st.session_state.fr_rules:
            st.markdown("#### Pending Rules")
            for i, rule in enumerate(st.session_state.fr_rules):
                cl = ("All Text Columns" if rule["columns"] == ["__ALL__"] else ", ".join(rule["columns"]))
                col_a, col_b, col_c = st.columns([4, 2, 1])
                with col_a:
                    st.markdown(f'<span class="bw">Rule {i+1}</span> `{rule["find"]}` → `{rule["replace"]}` in *{cl}*', unsafe_allow_html=True)
                with col_b:
                    # Preview count for this rule
                    preview_df = df.copy()
                    tlist = (list(preview_df.select_dtypes(include=["object", "string"]).columns)
                             if rule["columns"] == ["__ALL__"]
                             else [c for c in rule["columns"] if c in preview_df.columns])
                    affected = sum(preview_df[c].astype(str).str.contains(rule["find"], regex=False, na=False).sum() for c in tlist)
                    st.markdown(f"📊 {affected} rows affected")
                with col_c:
                    if st.button("🗑️", key=f"del_batch_{i}"):
                        st.session_state.fr_rules.pop(i)
                        st.rerun()
            
            # Apply all rules button
            if st.button("✅ Apply All Rules", key="apply_batch_rules"):
                save_state()
                prog = st.progress(0)
                for j, rule in enumerate(st.session_state.fr_rules):
                    df = apply_fr(df, rule)
                    log(f"Batch Rule: '{rule['find']}' → '{rule['replace']}'")
                    recipe_add({"action": "find_replace", "rule": rule})
                    prog.progress((j+1)/len(st.session_state.fr_rules))
                st.session_state.df_working = df
                st.session_state.fr_rules = []
                save_state()
                st.success(f"✅ Applied all rules!")
                st.rerun()
        else:
            st.info("No pending rules. Add rules above to create a batch.")
    
    # ========== SUB-TAB 2: SEARCH & ROW EDITOR (with Case Conversion) ==========
    with sub_tab2:
        st.markdown("**Search for specific values, then fix them individually, in bulk, or change case**")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            search_column = st.selectbox("Select column to search:", df.columns, key="search_col_main")
        with col2:
            search_term = st.text_input("Enter value to search for:", placeholder="e.g., 'gmail', '555', 'New York'", key="search_term_main")
        
        if search_term:
            # Find matching rows
            mask = df[search_column].astype(str).str.contains(search_term, case=False, na=False)
            matching_rows = df[mask].copy()
            
            st.markdown(f"**Found {len(matching_rows)} matching row(s)**")
            
            if len(matching_rows) > 0:
                st.markdown("### Matching rows:")
                st.dataframe(matching_rows, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Fix Options:")
                
                # Option 1: Bulk replace all
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("#### 📦 Fix ALL matching rows")
                    new_value_all = st.text_input("Replace all with:", key="bulk_value", placeholder="Enter new value for all matching rows")
                    if st.button("✅ Apply to ALL matching rows", key="bulk_apply", use_container_width=True):
                        if new_value_all:
                            save_state()
                            affected_count = mask.sum()
                            df.loc[mask, search_column] = new_value_all
                            st.session_state.df_working = df
                            log(f"Replaced '{search_term}' → '{new_value_all}' in ALL {affected_count} rows of {search_column}")
                            recipe_add({"action": "bulk_replace", "column": search_column, "find": search_term, "replace": new_value_all})
                            save_state()
                            st.success(f"✅ Updated ALL {affected_count} rows!")
                            st.rerun()
                        else:
                            st.warning("Please enter a value")
                
                with col_b:
                    st.markdown("#### 🎯 Fix ONE ROW AT A TIME")
                    st.caption("Select a specific row to fix individually")
                    
                    # Radio buttons for row selection
                    row_display = {}
                    for idx, row in matching_rows.iterrows():
                        display_text = f"Row {idx} - Current: {row[search_column]}"
                        row_display[display_text] = idx
                    
                    selected_label = st.radio("Select row to fix:", list(row_display.keys()), key="row_select")
                    selected_idx = row_display[selected_label]
                    
                    new_value_single = st.text_input("Replace with:", key="single_value", placeholder="Enter new value for this row")
                    
                    if st.button("✅ Apply to SELECTED row only", key="single_apply", use_container_width=True):
                        if new_value_single:
                            save_state()
                            old_value = df.loc[selected_idx, search_column]
                            df.loc[selected_idx, search_column] = new_value_single
                            st.session_state.df_working = df
                            log(f"Row {selected_idx}: Replaced '{old_value}' → '{new_value_single}' in {search_column}")
                            recipe_add({"action": "single_row_replace", "column": search_column, "row": int(selected_idx), "old": old_value, "new": new_value_single})
                            save_state()
                            st.success(f"✅ Updated row {selected_idx}!")
                            st.rerun()
                        else:
                            st.warning("Please enter a value")
                
                # ========== CASE CONVERSION & QUICK ACTIONS ==========
                st.markdown("---")
                st.markdown("### ⚡ Quick Actions for this Column")
                st.caption("Apply case changes to ALL matching rows or just SELECTED row")
                
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    # Title Case - All matching rows
                    if st.button(f"🔠 Title Case (All)", key="title_all_rows"):
                        save_state()
                        affected_count = 0
                        for idx in matching_rows.index:
                            old_val = df.loc[idx, search_column]
                            new_val = str(old_val).title() if pd.notna(old_val) else old_val
                            if new_val != old_val:
                                df.loc[idx, search_column] = new_val
                                affected_count += 1
                        st.session_state.df_working = df
                        log(f"Applied Title Case to {affected_count} rows in {search_column}")
                        save_state()
                        st.success(f"✅ Applied Title Case to {affected_count} rows!")
                        st.rerun()
                
                with col_b:
                    # Lower Case - All matching rows
                    if st.button(f"🔡 Lower Case (All)", key="lower_all_rows"):
                        save_state()
                        affected_count = 0
                        for idx in matching_rows.index:
                            old_val = df.loc[idx, search_column]
                            new_val = str(old_val).lower() if pd.notna(old_val) else old_val
                            if new_val != old_val:
                                df.loc[idx, search_column] = new_val
                                affected_count += 1
                        st.session_state.df_working = df
                        log(f"Applied Lower Case to {affected_count} rows in {search_column}")
                        save_state()
                        st.success(f"✅ Applied Lower Case to {affected_count} rows!")
                        st.rerun()
                
                with col_c:
                    # Upper Case - All matching rows
                    if st.button(f"🔠 Upper Case (All)", key="upper_all_rows"):
                        save_state()
                        affected_count = 0
                        for idx in matching_rows.index:
                            old_val = df.loc[idx, search_column]
                            new_val = str(old_val).upper() if pd.notna(old_val) else old_val
                            if new_val != old_val:
                                df.loc[idx, search_column] = new_val
                                affected_count += 1
                        st.session_state.df_working = df
                        log(f"Applied Upper Case to {affected_count} rows in {search_column}")
                        save_state()
                        st.success(f"✅ Applied Upper Case to {affected_count} rows!")
                        st.rerun()
                
                with col_d:
                    # Trim whitespace - All matching rows
                    if st.button(f"✂️ Trim (All)", key="trim_all_rows"):
                        save_state()
                        affected_count = 0
                        for idx in matching_rows.index:
                            old_val = df.loc[idx, search_column]
                            new_val = str(old_val).strip() if pd.notna(old_val) else old_val
                            if new_val != old_val:
                                df.loc[idx, search_column] = new_val
                                affected_count += 1
                        st.session_state.df_working = df
                        log(f"Trimmed whitespace from {affected_count} rows in {search_column}")
                        save_state()
                        st.success(f"✅ Trimmed {affected_count} rows!")
                        st.rerun()
                
                # Individual row case conversion
                st.markdown("---")
                st.markdown("#### Or apply case change to SELECTED row only:")
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    # Title Case - Selected row only
                    if st.button(f"🔠 Title Case (Selected Row)", key="title_selected"):
                        save_state()
                        old_val = df.loc[selected_idx, search_column]
                        new_val = str(old_val).title() if pd.notna(old_val) else old_val
                        df.loc[selected_idx, search_column] = new_val
                        st.session_state.df_working = df
                        log(f"Applied Title Case to row {selected_idx} in {search_column}: '{old_val}' → '{new_val}'")
                        save_state()
                        st.success(f"✅ Applied Title Case to row {selected_idx}!")
                        st.rerun()
                
                with col_b:
                    # Lower Case - Selected row only
                    if st.button(f"🔡 Lower Case (Selected Row)", key="lower_selected"):
                        save_state()
                        old_val = df.loc[selected_idx, search_column]
                        new_val = str(old_val).lower() if pd.notna(old_val) else old_val
                        df.loc[selected_idx, search_column] = new_val
                        st.session_state.df_working = df
                        log(f"Applied Lower Case to row {selected_idx} in {search_column}: '{old_val}' → '{new_val}'")
                        save_state()
                        st.success(f"✅ Applied Lower Case to row {selected_idx}!")
                        st.rerun()
                
                with col_c:
                    # Upper Case - Selected row only
                    if st.button(f"🔠 Upper Case (Selected Row)", key="upper_selected"):
                        save_state()
                        old_val = df.loc[selected_idx, search_column]
                        new_val = str(old_val).upper() if pd.notna(old_val) else old_val
                        df.loc[selected_idx, search_column] = new_val
                        st.session_state.df_working = df
                        log(f"Applied Upper Case to row {selected_idx} in {search_column}: '{old_val}' → '{new_val}'")
                        save_state()
                        st.success(f"✅ Applied Upper Case to row {selected_idx}!")
                        st.rerun()
            else:
                st.warning(f"No rows found containing '{search_term}' in column '{search_column}'")
        else:
            st.info("👆 Enter a search term above to find rows to fix")


# ══════════════════════════════════════════════════════════════════
# TAB 4 - DATA QUALITY (FULLY FIXED with Proper Refresh)
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec">✅ Data Quality - Type Validation & Format Checking</div>', unsafe_allow_html=True)
    
    st.info("🔍 Fix data type issues - after fixing, click 'Refresh Issues' to re-scan your data")
    
    # Add a refresh button at the top
    if st.button("🔄 Refresh Issues (Scan current data)", key="refresh_quality"):
        st.rerun()
    
    st.markdown("---")
    
    # ========== SIMPLIFIED VALIDATION ==========
    def get_suggested_fix(value, expected_type):
        """Return suggested fix for a value"""
        if pd.isna(value) or value == '':
            return value
        
        value_str = str(value).strip()
        
        if expected_type == 'phone':
            digits = re.sub(r'\D', '', value_str)
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) > 10:
                digits = digits[-10:]
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            return value_str
        
        elif expected_type == 'email':
            if '@' not in value_str:
                return value_str + '@email.com'
            if '.' not in value_str.split('@')[1]:
                return value_str + '.com'
            return value_str.replace('gmial.com', 'gmail.com').replace('gmal.com', 'gmail.com')
        
        elif expected_type == 'date':
            numbers = re.findall(r'\d+', value_str)
            if len(numbers) == 3:
                return f"{numbers[2]}-{numbers[0].zfill(2)}-{numbers[1].zfill(2)}"
            return value_str
        
        elif expected_type == 'numeric':
            numbers = re.findall(r'\d+(?:\.\d+)?', value_str)
            if numbers:
                return float(numbers[0])
            return value_str
        
        return value_str

    def detect_type_issues(df):
        """Detect columns with type issues - uses current df_working"""
        issues = []
        
        # Columns to SKIP (should be text, not validated)
        skip_columns = ['name', 'full name', 'agent', 'agent name', 'city', 'state', 'country', 
                       'address', 'notes', 'description', 'comments', 'status', 'type', 'category']
        
        for col in df.columns:
            col_lower = col.lower()
            
            # SKIP text columns that shouldn't be validated
            if any(skip_word in col_lower for skip_word in skip_columns):
                continue
            
            # Determine expected type
            if any(w in col_lower for w in ['phone', 'mobile', 'contact']):
                expected = 'phone'
            elif any(w in col_lower for w in ['email']):
                expected = 'email'
            elif any(w in col_lower for w in ['date', 'created', 'birth', 'registration', 'active']):
                expected = 'date'
            elif any(w in col_lower for w in ['age', 'year', 'price', 'amount', 'total', 'spent', 'cost', 'salary', 'id', 'code']):
                expected = 'numeric'
            else:
                continue  # Skip columns without clear type
            
            # Find invalid rows
            invalid_rows = []
            for idx, val in df[col].items():
                if pd.isna(val) or val == '' or str(val).strip() == '':
                    continue
                
                is_valid = False
                if expected == 'phone':
                    digits = re.sub(r'\D', '', str(val))
                    is_valid = len(digits) == 10
                elif expected == 'email':
                    email_str = str(val)
                    is_valid = '@' in email_str and '.' in email_str.split('@')[-1] and len(email_str.split('@')[0]) > 0
                elif expected == 'date':
                    numbers = re.findall(r'\d+', str(val))
                    is_valid = len(numbers) == 3
                elif expected == 'numeric':
                    try:
                        float(re.sub(r'[$,%]', '', str(val)))
                        is_valid = True
                    except:
                        is_valid = False
                
                if not is_valid:
                    invalid_rows.append({
                        'row': idx,
                        'current': val,
                        'suggested': get_suggested_fix(val, expected)
                    })
            
            if invalid_rows:
                issues.append({
                    'column': col,
                    'expected_type': expected,
                    'invalid_rows': invalid_rows
                })
        
        return issues
    
    # Get current data and detect issues
    current_df = st.session_state.df_working.copy()
    issues = detect_type_issues(current_df)
    
    if not issues:
        st.success("✅ No data type issues found! All columns have correct formats.")
    else:
        for col_idx, issue in enumerate(issues):
            st.markdown(f"### 📍 Column: `{issue['column']}` (Expected: {issue['expected_type'].upper()})")
            st.markdown(f"Found **{len(issue['invalid_rows'])}** problematic values")
            
            # Create display dataframe
            fix_data = []
            for inv in issue['invalid_rows']:
                fix_data.append({
                    'Row': inv['row'],
                    'Current Value': str(inv['current']),
                    'Suggested Fix': str(inv['suggested']),
                    'New Value': str(inv['suggested'])
                })
            
            fix_df = pd.DataFrame(fix_data)
            
            # Display the table
            st.markdown("**Edit values directly in the table below:**")
            edited_df = st.data_editor(
                fix_df,
                column_config={
                    'Row': st.column_config.NumberColumn('Row', disabled=True),
                    'Current Value': st.column_config.TextColumn('Current Value', disabled=True),
                    'Suggested Fix': st.column_config.TextColumn('Suggested Fix', disabled=True),
                    'New Value': st.column_config.TextColumn('New Value', help='Edit this column to fix values')
                },
                hide_index=True,
                use_container_width=True,
                key=f"quality_editor_{col_idx}_{issue['column'].replace(' ', '_')}"
            )
            
            # Row selection for custom value
            st.markdown("---")
            st.markdown("**Custom Value Options:**")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Custom value input
                custom_val = st.text_input(
                    "Enter custom value:", 
                    key=f"custom_val_{col_idx}_{issue['column'].replace(' ', '_')}", 
                    placeholder="e.g., 'Unknown' or 'N/A'"
                )
            
            with col2:
                # Select which rows to apply to
                row_options = [f"Row {inv['row']}" for inv in issue['invalid_rows']]
                selected_rows = st.multiselect(
                    "Select rows to apply custom value to:",
                    options=row_options,
                    default=row_options,
                    key=f"selected_rows_{col_idx}_{issue['column'].replace(' ', '_')}"
                )
            
            with col3:
                if st.button(f"📝 Apply to Selected", key=f"apply_selected_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    if custom_val:
                        save_state()
                        applied_count = 0
                        for row_label in selected_rows:
                            row_num = int(row_label.split(' ')[1])
                            current_df.at[row_num, issue['column']] = custom_val
                            applied_count += 1
                        st.session_state.df_working = current_df
                        log(f"Applied custom value '{custom_val}' to {applied_count} selected rows in {issue['column']}")
                        save_state()
                        st.success(f"✅ Applied custom value to {applied_count} selected rows! Click 'Refresh Issues' to see updated list.")
                        st.rerun()
                    else:
                        st.warning("Please enter a custom value")
            
            # Action buttons row
            st.markdown("---")
            st.markdown("**Bulk Actions:**")
            
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                # Apply Changes button (saves edits from table)
                if st.button(f"💾 Save Table Edits", key=f"save_edits_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    save_state()
                    changes_made = 0
                    for _, row in edited_df.iterrows():
                        row_idx = int(row['Row'])
                        new_val = row['New Value']
                        current_val = str(row['Current Value'])
                        if new_val != current_val:
                            current_df.at[row_idx, issue['column']] = new_val
                            changes_made += 1
                    st.session_state.df_working = current_df
                    log(f"Saved {changes_made} edits in {issue['column']}")
                    save_state()
                    st.success(f"✅ Saved {changes_made} changes to '{issue['column']}'! Click 'Refresh Issues' to see updated list.")
                    st.rerun()
            
            with col_b:
                # Use All Suggested button
                if st.button(f"✨ Apply All Suggested", key=f"apply_suggested_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    save_state()
                    for inv in issue['invalid_rows']:
                        current_df.at[inv['row'], issue['column']] = inv['suggested']
                    st.session_state.df_working = current_df
                    log(f"Applied suggested fixes to all {len(issue['invalid_rows'])} rows in {issue['column']}")
                    save_state()
                    st.success(f"✅ Applied suggested fixes to all {len(issue['invalid_rows'])} rows! Click 'Refresh Issues' to see updated list.")
                    st.rerun()
            
            with col_c:
                # Apply to All with custom value
                if st.button(f"📝 Apply Custom to All", key=f"custom_all_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    if custom_val:
                        save_state()
                        for inv in issue['invalid_rows']:
                            current_df.at[inv['row'], issue['column']] = custom_val
                        st.session_state.df_working = current_df
                        log(f"Applied custom value '{custom_val}' to all {len(issue['invalid_rows'])} rows in {issue['column']}")
                        save_state()
                        st.success(f"✅ Applied custom value to all {len(issue['invalid_rows'])} rows! Click 'Refresh Issues' to see updated list.")
                        st.rerun()
                    else:
                        st.warning("Please enter a custom value first")
            
            with col_d:
                # Clear all button
                if st.button(f"🗑️ Clear All Values", key=f"clear_all_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    save_state()
                    for inv in issue['invalid_rows']:
                        current_df.at[inv['row'], issue['column']] = ""
                    st.session_state.df_working = current_df
                    log(f"Cleared all {len(issue['invalid_rows'])} invalid values in {issue['column']}")
                    save_state()
                    st.success(f"✅ Cleared all {len(issue['invalid_rows'])} values! Click 'Refresh Issues' to see updated list.")
                    st.rerun()
            
            st.markdown("---")


# ══════════════════════════════════════════════════════════════════
# TAB 5 - Audit (YOUR ORIGINAL VERSION)
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="sec">📜 Cleaning Audit Log</div>', unsafe_allow_html=True)
    
    if not st.session_state.audit_log:
        st.info("No cleaning actions have been performed yet.")
    else:
        for entry in reversed(st.session_state.audit_log[-30:]):
            st.markdown(
                f'<div class="audit-entry">'
                f'<span class="ts">{entry["ts"]}</span>&nbsp;&nbsp;{entry["msg"]}'
                f'</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<div class="sec">💾 Save Recipe</div>', unsafe_allow_html=True)
    
    if st.session_state.recipe:
        recipe_json = json.dumps({"steps": st.session_state.recipe, "filename": st.session_state.filename}, indent=2)
        st.download_button(
            label="📥 Download Cleaning Recipe",
            data=recipe_json,
            file_name=f"{st.session_state.filename.split('.')[0]}_recipe.json",
            mime="application/json",
            key="download_recipe"
        )
        st.caption(f"Recipe contains {len(st.session_state.recipe)} cleaning steps")


# ══════════════════════════════════════════════════════════════════
# TAB 6 - Export (YOUR ORIGINAL VERSION)
# ══════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="sec">💾 Export Cleaned Data</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Data**")
        if st.session_state.df_original is not None:
            st.metric("Rows", len(st.session_state.df_original))
            st.metric("Missing", st.session_state.df_original.isnull().sum().sum())
    
    with col2:
        st.markdown("**Cleaned Data**")
        st.metric("Rows", len(df))
        st.metric("Missing", df.isnull().sum().sum())
    
    st.markdown("---")
    st.dataframe(df.head(10), use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download CSV", data=to_csv(df), 
                          file_name=f"{st.session_state.filename.split('.')[0]}_cleaned.csv", 
                          mime="text/csv", key="export_csv")
    with col2:
        st.download_button("Download Excel", data=to_xlsx(df),
                          file_name=f"{st.session_state.filename.split('.')[0]}_cleaned.xlsx",
                          key="export_excel")

