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
import os



# ── Groq AI Client Setup ───────────────────────────────────────────────────
try:
    from groq import Groq
    _groq_api_key ="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"
    groq_client = Groq(api_key=_groq_api_key) if _groq_api_key else None
except Exception:
    groq_client = None
def load_ai_skills():
    """Reads the skills blueprint file to inject into the AI system prompt."""
    skills_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.md")
    if os.path.exists(skills_path):
        with open(skills_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""  # Returns empty string if skills.md hasn't been created yet
# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="DataScrub – Data Cleaning Studio",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PROFESSIONAL DARK THEME - DEEP INDIGO + LIGHT TEXT ──────────────────────
st.markdown("""
<style>
    /* Main dark background */
    .stApp, .main, .stAppViewContainer {
        background-color: #0F172A !important;
    }
    
    .block-container {
        background-color: #0F172A !important;
    }
    
    /* ALL TEXT - FORCED TO BE LIGHT AND VISIBLE */
    p, span, div, label, .stMarkdown, .stText, .stCaption,
    .stAlert, .element-container, .stException, .stCodeBlock,
    [data-testid="stMarkdownContainer"], .stRadio label, .stCheckbox label {
        color: #E2E8F0 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6, .stHeading {
        color: #FFFFFF !important;
    }
    
    /* Sidebar - Dark but slightly lighter */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155 !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Buttons */
    .stButton > button {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        padding: 0.4rem 1rem !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background-color: #334155 !important;
        border-color: #00D4AA !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    
    /* Dataframes / Tables */
    .dataframe, .stDataFrame {
        background-color: #1E293B !important;
    }
    
    .dataframe th {
        background-color: #0F172A !important;
        color: #00D4AA !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #334155 !important;
    }
    
    .dataframe td {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border-bottom: 1px solid #334155 !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00D4AA !important;
        outline: none !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #1E293B !important;
        border-color: #334155 !important;
        color: #E2E8F0 !important;
    }
    
    /* File uploader */
    .uploadedFile, [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 1px dashed #334155 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem !important;
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8 !important;
        background-color: transparent !important;
        padding: 0.5rem 1rem !important;
        border-radius: 6px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #00D4AA !important;
        background-color: rgba(0, 212, 170, 0.1) !important;
    }
    
    /* Dividers */
    hr {
        border-color: #334155 !important;
    }
    
    /* Alert messages */
    .stAlert {
        background-color: #1E293B !important;
        border-radius: 8px !important;
        border-left: 4px solid #00D4AA !important;
        color: #E2E8F0 !important;
    }
    
    .stSuccess {
        border-left-color: #00D4AA !important;
    }
    
    .stWarning {
        border-left-color: #F59E0B !important;
    }
    
    .stError {
        border-left-color: #EF4444 !important;
    }
    
    .stInfo {
        border-left-color: #3B82F6 !important;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #00D4AA !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
    }
    
    /* Checkbox and Radio */
    .stCheckbox label, .stRadio label {
        color: #E2E8F0 !important;
    }
    
    /* Code blocks */
    code, .stCodeBlock {
        color: #00D4AA !important;
        background-color: #0F172A !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background-color: #00D4AA !important;
        color: #0F172A !important;
        border: none !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #00B4D8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Custom Header CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.main-header h1 {
    color: #00D4AA !important;
    margin: 0;
    font-size: 1.8rem;
}
.main-header p {
    color: #94A3B8 !important;
    margin: 0.25rem 0 0;
    font-size: 0.85rem;
}
.stat-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
}
.stat-card .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #00D4AA;
}
.stat-card .label {
    font-size: 0.7rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.sec {
    font-size: 0.75rem;
    color: #00D4AA;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.65rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #00D4AA;
}
.audit-entry {
    background: #1E293B;
    border-left: 3px solid #00D4AA;
    border-radius: 0 6px 6px 0;
    padding: 0.3rem 0.8rem;
    margin-bottom: 0.3rem;
    font-size: 0.8rem;
    color: #E2E8F0;
}
.bw, .bg {
    display: inline-block;
    background: #0F172A;
    border: 1px solid #00D4AA;
    color: #00D4AA;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: .72rem;
    font-weight: 600;
    margin: 2px;
}
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
        "chat_history": [],
        "ai_suggestions": [],
        "ignored_issues": set(),
        "ignored_quality": set(),
        "active_tab": 0,          # remembers which tab is open across reruns
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Undo/Redo Functions ────────────────────────────────────────────────────
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
        ws = w.sheets["Cleaned"]
        for col_idx, col_name in enumerate(df.columns, start=1):
            col_lower = str(col_name).lower()
            if any(token in col_lower for token in ("contact", "phone", "mobile", "email")):
                for row in range(2, ws.max_row + 1):
                    ws.cell(row=row, column=col_idx).number_format = "@"
    return buf.getvalue()


# ── AI Helper Functions ────────────────────────────────────────────────────

_NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}


def _clean_blank_values(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(r"^\s*$", np.nan, regex=True)


def _numeric_from_messy(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.lower()
    text = text.replace({
        "nan": pd.NA, "none": pd.NA, "null": pd.NA, "n/a": pd.NA,
        "na": pd.NA, "not available": pd.NA, "unknown": pd.NA,
    })
    text = text.replace(_NUMBER_WORDS)
    text = text.astype("string").str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(text, errors="coerce")


def _looks_numeric(series: pd.Series) -> bool:
    converted = _numeric_from_messy(series)
    non_blank = series.replace(r"^\s*$", np.nan, regex=True).notna().sum()
    return non_blank > 0 and converted.notna().sum() / non_blank >= 0.65


def _normalize_contact(value):
    if pd.isna(value):
        return np.nan
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 9 and digits.startswith("5"):
        digits = "0" + digits
    return digits if digits else np.nan


def _parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Parse common messy date formats while preserving year-first dates."""
    month_name_formats = ("%d-%b-%Y", "%d-%B-%Y", "%b %d %Y", "%B %d %Y")

    def parse_one(value):
        if pd.isna(value):
            return pd.NaT
        if isinstance(value, (pd.Timestamp, datetime, np.datetime64)):
            return pd.to_datetime(value, errors="coerce")
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null", "nat", "n/a", "na"}:
            return pd.NaT

        year_first = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", text)
        numeric_date = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", text)
        if year_first:
            year, month, day = map(int, year_first.groups())
            try:
                return pd.Timestamp(year=year, month=month, day=day)
            except ValueError:
                return pd.NaT

        if numeric_date:
            first, second, year = map(int, numeric_date.groups())
            if first > 12:
                day, month = first, second
            elif second > 12:
                month, day = first, second
            else:
                # Ambiguous values in this sample are listing dates; keep slash dates month-first
                # and dash dates day-first unless the numbers make that impossible.
                if "/" in text:
                    month, day = first, second
                else:
                    day, month = first, second
            try:
                return pd.Timestamp(year=year, month=month, day=day)
            except ValueError:
                return pd.NaT

        for fmt in month_name_formats:
            parsed = pd.to_datetime(text, errors="coerce", format=fmt)
            if pd.notna(parsed):
                return parsed

        return pd.to_datetime(text, errors="coerce", format="mixed")

    return series.apply(parse_one)


def auto_clean_dataframe(df: pd.DataFrame):
    """Deterministic high-quality cleaner used by the ai and one-click fixes."""
    cleaned = _clean_blank_values(df.copy())
    actions = []

    for col in cleaned.select_dtypes(include=["object", "string"]).columns:
        before = cleaned[col].copy()
        cleaned[col] = cleaned[col].astype("string").str.strip()
        cleaned[col] = cleaned[col].replace({
            "": pd.NA, "nan": pd.NA, "None": pd.NA, "none": pd.NA,
            "N/A": pd.NA, "n/a": pd.NA, "not available": pd.NA,
            "Not Available": pd.NA, "unknown": pd.NA, "Unknown": pd.NA,
        })
        if not before.equals(cleaned[col]):
            actions.append(f"Trimmed and normalized blanks in {col}")

    for col in cleaned.columns:
        col_lower = str(col).lower()
        if "contact" in col_lower or "phone" in col_lower or "mobile" in col_lower:
            cleaned[col] = cleaned[col].apply(_normalize_contact)
            actions.append(f"Standardized phone/contact values in {col}")
        elif "email" in col_lower:
            cleaned[col] = cleaned[col].astype("string").str.strip().str.lower()
            actions.append(f"Standardized emails in {col}")
        elif "date" in col_lower:
            parsed = _parse_mixed_dates(cleaned[col])
            if parsed.notna().any():
                cleaned[col] = parsed
                actions.append(f"Parsed dates in {col}")
        elif pd.api.types.is_object_dtype(cleaned[col]) or pd.api.types.is_string_dtype(cleaned[col]):
            if _looks_numeric(cleaned[col]):
                cleaned[col] = _numeric_from_messy(cleaned[col])
                actions.append(f"Converted {col} to numeric")

    for col in cleaned.select_dtypes(include=[np.number]).columns:
        if cleaned[col].isna().any():
            fill_value = cleaned[col].median()
            if pd.notna(fill_value):
                cleaned[col] = cleaned[col].fillna(fill_value)
                actions.append(f"Filled missing numeric values in {col} with median")

    for col in cleaned.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        if cleaned[col].isna().any() and cleaned[col].notna().any():
            fill_value = cleaned[col].dropna().median()
            cleaned[col] = cleaned[col].fillna(fill_value)
            actions.append(f"Filled invalid or missing dates in {col} with median date")

    for col in cleaned.select_dtypes(include=["object", "string"]).columns:
        if cleaned[col].isna().any():
            mode_value = cleaned[col].mode(dropna=True)
            fill_value = mode_value.iloc[0] if not mode_value.empty else "Unknown"
            cleaned[col] = cleaned[col].fillna(fill_value)
            actions.append(f"Filled missing text values in {col}")

    id_like = [c for c in cleaned.columns if str(c).lower().strip() in {"id", "property id", "record id"}]
    subset = [c for c in cleaned.columns if c not in id_like]
    if subset:
        before_rows = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
        dropped = before_rows - len(cleaned)
        if dropped:
            actions.append(f"Removed {dropped} duplicate listing row(s)")

    return cleaned, actions


def _rule_based_suggestions(df: pd.DataFrame):
    suggestions = [{
        "action": "auto_clean_dataset",
        "column": "",
        "reason": "Run the full deterministic cleanup: normalize blanks, convert messy numeric columns, parse dates, standardize contacts, fill gaps, and remove duplicate listings.",
    }]
    if df.duplicated().sum() > 0:
        suggestions.append({"action": "remove_duplicates", "column": "", "reason": "Exact duplicate rows found."})
    for col in df.columns:
        col_lower = str(col).lower()
        if df[col].isna().sum() > 0:
            action = "fill_missing_median" if pd.api.types.is_numeric_dtype(df[col]) or _looks_numeric(df[col]) else "fill_missing_mode"
            suggestions.append({"action": action, "column": col, "reason": f"{int(df[col].isna().sum())} missing value(s) detected."})
        if "date" in col_lower:
            suggestions.append({"action": "fix_dates", "column": col, "reason": "Date column may contain mixed or invalid formats."})
        if any(token in col_lower for token in ("contact", "phone", "mobile")):
            suggestions.append({"action": "fix_phone_numbers", "column": col, "reason": "Phone/contact values should be digits in one consistent format."})
        if "email" in col_lower:
            suggestions.append({"action": "fix_emails", "column": col, "reason": "Emails should be lowercase and trimmed."})
        if pd.api.types.is_object_dtype(df[col]) and _looks_numeric(df[col]):
            suggestions.append({"action": "convert_numeric", "column": col, "reason": "Column contains numeric values stored as messy text."})

    id_like = [c for c in df.columns if str(c).lower().strip() in {"id", "property id", "record id"}]
    subset = [c for c in df.columns if c not in id_like]
    if subset and df.duplicated(subset=subset).sum() > 0:
        suggestions.append({"action": "remove_business_duplicates", "column": "", "reason": "Duplicate records found when ID columns are ignored."})
    return suggestions


def get_ai_suggestions(df: pd.DataFrame):
    """Send df.head(10) to Groq and return structured JSON suggestions."""
    local_suggestions = _rule_based_suggestions(df)
    if groq_client is None:
        return local_suggestions
    try:
        sample = df.head(10).to_dict()
        prompt = (
            "You are a data quality expert. Analyze this dataset sample and return ONLY a JSON array "
            "(no markdown, no explanation) of cleaning suggestions. Each item must have: "
            "'action' (snake_case), 'column' (exact column name), 'reason' (short string). "
            "Supported actions: auto_clean_dataset, fix_dates, fix_phone_numbers, fill_missing_median, "
            "fill_missing_mode, remove_duplicates, remove_business_duplicates, convert_numeric, fix_emails. "
            f"Dataset sample:\n{json.dumps(sample, default=str)}"
        )
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        suggestions = json.loads(raw)
        if not isinstance(suggestions, list):
            suggestions = []
        seen = {(s.get("action"), s.get("column")) for s in suggestions if isinstance(s, dict)}
        for item in local_suggestions:
            key = (item.get("action"), item.get("column"))
            if key not in seen:
                suggestions.append(item)
                seen.add(key)
        return suggestions
    except Exception as e:
        return local_suggestions or [{"action": "error", "column": "N/A", "reason": f"AI error: {e}"}]


def ai_quality_score(df: pd.DataFrame) -> int:
    """Score the dataframe quality out of 100."""
    score = 100
    total_cells = df.size
    if total_cells > 0:
        missing_pct = df.isnull().sum().sum() / total_cells
        score -= int(missing_pct * 60)
    total_rows = len(df)
    if total_rows > 0:
        dup_pct = df.duplicated().sum() / total_rows
        score -= int(dup_pct * 40)
    return max(0, min(100, score))


def apply_ai_fix(df: pd.DataFrame, action: str, column: str) -> pd.DataFrame:
    """Apply a specific AI-suggested fix to the dataframe."""
    df = df.copy()
    if action == "auto_clean_dataset":
        df, _ = auto_clean_dataframe(df)
    elif action == "fix_dates":
        if column in df.columns:
            parsed = _parse_mixed_dates(df[column])
            df[column] = parsed
            if df[column].isna().any() and df[column].notna().any():
                df[column] = df[column].fillna(df[column].dropna().median())
    elif action == "fix_phone_numbers":
        if column in df.columns:
            df[column] = df[column].apply(_normalize_contact)
    elif action == "fill_missing_median":
        if column in df.columns and not pd.api.types.is_numeric_dtype(df[column]) and _looks_numeric(df[column]):
            df[column] = _numeric_from_messy(df[column])
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(df[column].median())
    elif action == "fill_missing_mode":
        if column in df.columns:
            mode_value = df[column].mode(dropna=True)
            fill_value = mode_value.iloc[0] if not mode_value.empty else "Unknown"
            df[column] = df[column].fillna(fill_value)
    elif action == "remove_duplicates":
        df = df.drop_duplicates()
    elif action == "remove_business_duplicates":
        id_like = [c for c in df.columns if str(c).lower().strip() in {"id", "property id", "record id"}]
        subset = [c for c in df.columns if c not in id_like]
        df = df.drop_duplicates(subset=subset or None, keep="first").reset_index(drop=True)
    elif action == "convert_numeric":
        if column in df.columns:
            df[column] = _numeric_from_messy(df[column])
    elif action == "fix_emails":
        if column in df.columns:
            df[column] = df[column].astype(str).str.lower().str.strip()
    return df


import textwrap as _textwrap


def _df_schema_summary(df: pd.DataFrame) -> str:
    """Compact schema string to include in AI prompts."""
    lines = [f"Shape: {df.shape[0]} rows × {df.shape[1]} cols", "Columns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isnull().sum())
        sample_vals = df[col].dropna().head(3).tolist()
        lines.append(f"  - {col!r} ({dtype}) | {nulls} nulls | sample: {sample_vals}")
    return "\n".join(lines)


def _safe_exec(code_str: str, df: pd.DataFrame):
    """
    Dedent the code, run it in a sandbox, and always return the resulting df.
    Handles both inplace mutations and reassignments like df = df.drop_duplicates().
    Returns (result_df, error_string_or_None).
    """
    # Dedent so model-indented code (leading spaces) doesn't cause IndentationError
    code_clean = _textwrap.dedent(code_str).strip()

    # Wrap any line that reassigns `df =` to also update a sentinel so we can retrieve it
    # We expose a mutable container so reassignment works too
    wrapper = f"""
_df_container[0] = df
{code_clean}
_df_container[0] = df
"""
    container = [df.copy()]
    sandbox = {
        "df": df,
        "pd": pd,
        "np": np,
        "re": re,
        "auto_clean_dataframe": auto_clean_dataframe,
        "_parse_mixed_dates": _parse_mixed_dates,
        "_df_container": container,
    }
    try:
        exec(compile(wrapper.strip(), "<ai>", "exec"), sandbox)  # noqa: S102
        # Prefer sandbox["df"] — covers both inplace and column-assignment cases
        result = sandbox.get("df", container[0])
        # If result is None or not a DataFrame (e.g. GroupBy object), fall back
        if result is None or not isinstance(result, pd.DataFrame):
            result = container[0]
        return result, None
    except Exception as err:
        return df, str(err)


def _parse_ai_payload(raw: str):
    """Accept strict JSON, JSON fenced in markdown, or a python code block as a best-effort fallback."""
    raw = raw.strip()
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        try:
            import ast
            parsed = ast.literal_eval(stripped)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        loose_action = re.search(
            r'"type"\s*:\s*"action".*?"explanation"\s*:\s*"(.*?)".*?"code"\s*:\s*"(.*)"\s*\}?\s*$',
            stripped,
            flags=re.DOTALL,
        )
        if loose_action:
            return {
                "type": "action",
                "explanation": loose_action.group(1).replace('\\"', '"').strip(),
                "code": loose_action.group(2).strip().strip('"').strip(),
            }

        loose_answer = re.search(
            r'"type"\s*:\s*"answer".*?"explanation"\s*:\s*"(.*)"\s*\}?\s*$',
            stripped,
            flags=re.DOTALL,
        )
        if loose_answer:
            return {
                "type": "answer",
                "explanation": loose_answer.group(1).replace('\\"', '"').strip(),
            }

        code_match = re.search(r"```python\s*(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
        if code_match:
            return {
                "type": "action",
                "explanation": "I generated and applied a pandas cleaning step.",
                "code": code_match.group(1).strip(),
            }
        return {"type": "answer", "explanation": raw}


def _is_direct_clean_request(user_message: str) -> bool:
    message = user_message.lower().strip()
    advice_markers = (
        "suggest", "recommend", "ways", "how should", "how can", "what should",
        "explain", "tell me", "show me", "list", "why", "what are",
    )
    if any(marker in message for marker in advice_markers):
        return False

    direct_clean_phrases = (
        "clean the data",
        "clean data",
        "clean dataset",
        "clean the dataset",
        "clean the whole dataset",
        "clean whole dataset",
        "fix all issues",
        "fix every issue",
        "fix everything",
        "auto clean",
        "prepare the file",
        "make it clean",
        "make it top notch",
        "top notch",
    )
    return any(phrase in message for phrase in direct_clean_phrases)


def _local_ai_response(user_message: str, df: pd.DataFrame):
    message = user_message.lower()
    if _is_direct_clean_request(user_message):
        cleaned, actions = auto_clean_dataframe(df)
        explanation = "Done. I cleaned the dataset with the built-in data-quality engine."
        if actions:
            explanation += "\n\nApplied:\n" + "\n".join(f"- {action}" for action in actions)
        return cleaned, explanation, "df, actions = auto_clean_dataframe(df)"

    if any(word in message for word in ("suggest", "recommend", "ways", "how should", "how can")) and "clean" in message:
        issues = detect_issues(df)
        suggestions = [
            "Start by converting messy numeric columns with `pd.to_numeric(..., errors='coerce')`, then fill numeric gaps with median values.",
            "Standardize text fields by trimming spaces and using consistent capitalization for city, location, and agent names.",
            "Normalize contact fields by removing non-digits and preserving leading zeroes as text in Excel exports.",
            "Parse mixed date formats into one datetime column, then review invalid dates before filling them.",
            "Check duplicate listings both as exact duplicates and as business duplicates where ID columns are ignored.",
            "Review outliers with domain context before capping or deleting them.",
        ]
        summary = (
            f"Current snapshot: {len(df):,} rows, {df.shape[1]:,} columns, "
            f"{int(df.isna().sum().sum()):,} missing cells, "
            f"{int(df.duplicated().sum()):,} exact duplicate rows."
        )
        if issues.get("missing"):
            missing_cols = ", ".join(issues["missing"].keys())
            summary += f"\n\nColumns with missing values: {missing_cols}."
        if issues.get("outliers"):
            outlier_cols = ", ".join(issues["outliers"].keys())
            summary += f"\n\nPossible outlier columns: {outlier_cols}."
        return df, summary + "\n\nRecommended cleaning plan:\n" + "\n".join(f"- {s}" for s in suggestions), None

    if ("missing" in message or "null" in message) and ("duplicate" in message or "dupe" in message):
        nulls = df.isna().sum()
        details = nulls[nulls > 0].sort_values(ascending=False)
        exact = int(df.duplicated().sum())
        id_like = [c for c in df.columns if str(c).lower().strip() in {"id", "property id", "record id"}]
        subset = [c for c in df.columns if c not in id_like]
        business = int(df.duplicated(subset=subset).sum()) if subset else exact
        missing_text = "No missing values found." if details.empty else details.to_markdown()
        return df, (
            f"Missing values:\n\n{missing_text}\n\n"
            f"Exact duplicate rows: {exact}\n\n"
            f"Duplicate business records ignoring ID columns: {business}"
        ), None

    if "missing" in message or "null" in message:
        nulls = df.isna().sum()
        details = nulls[nulls > 0].sort_values(ascending=False)
        if details.empty:
            return df, "No missing values were found in the current dataset.", None
        return df, "Missing values by column:\n\n" + details.to_markdown(), None

    if "duplicate" in message:
        exact = int(df.duplicated().sum())
        id_like = [c for c in df.columns if str(c).lower().strip() in {"id", "property id", "record id"}]
        subset = [c for c in df.columns if c not in id_like]
        business = int(df.duplicated(subset=subset).sum()) if subset else exact
        return df, f"Exact duplicate rows: {exact}\n\nDuplicate business records ignoring ID columns: {business}", None

    return df, (
        "I can answer basic quality questions locally. For richer natural-language transformations, "
        "configure `GROQ_API_KEY` in `.env`, `.venv`, or Streamlit secrets."
    ), None


def _escape_chat_html(value) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def ai_chat_response(user_message: str, df: pd.DataFrame, history: list):
    if _is_direct_clean_request(user_message):
        return _local_ai_response(user_message, df)

    if groq_client is None:
        return _local_ai_response(user_message, df)

    schema = _df_schema_summary(df)
    sample_json = df.head(5).to_json(orient="records", default_handler=str)
    
    # ─── 1. FETCH SKILLS HERE ───
    ai_skills = load_ai_skills()

    # ─── 2. INJECT IT INTO THE SYSTEM PROMPT ───
    system_prompt = f"""You are DataScrub AI — an expert data analyst and pandas engineer embedded in a Streamlit data cleaning app.

The user has a pandas DataFrame called `df`. Here is its current schema:
{schema}

Sample data (first 5 rows):
{sample_json}

📖 REUSABLE PYTHON SKILLS BLUEPRINTS:
Use the exact structures and logic patterns defined below when writing code:
{ai_skills}

YOUR JOB:
- Understand ANY natural language request about data cleaning, transformation, analysis, or questions.
- Always return exactly one valid JSON object. No markdown fences. No text outside JSON.
- Be concise, practical, and senior: name the issue, explain the tradeoff, and give the safest next step.
- For advice prompts, discuss missing values, inconsistent formatting, duplicate records, outliers, privacy, and scale when relevant to the dataset.
- Do not recommend deleting rows unless the quality benefit clearly outweighs information loss.
- Prefer reversible, auditable cleaning steps and mention when domain review is needed.
- For data changes, return:
  {{"type": "action", "explanation": "<short markdown explanation>", "code": "<python code>"}}
- For questions or analysis (not changing data), return:
  {{"type": "answer", "explanation": "<detailed markdown answer>"}}


    # ─── KEEP ALL THE REST OF YOUR ORIGINAL CODE BELOW THIS LINE ───
    # (The part that sets up messages, calls groq_client.chat.completions.create, 
    # handles the regex code block parsing, etc.)
  CODE RULES — very important:
  * Write code with NO leading indentation. Every line must start at column 0.
  * Reassign df for operations that return a new DataFrame:
      df = df.drop_duplicates()
      df = df.dropna(subset=['col'])
      df = df.sort_values('col')
  * Use direct assignment for column operations:
      df['col'] = df['col'].fillna(df['col'].mean())
      df['col'] = pd.to_numeric(df['col'], errors='coerce')
      df['date_col'] = _parse_mixed_dates(df['date_col'])
  * Never use inplace=True — it often returns None and breaks things.
  * Available globals: df, pd, np, re, auto_clean_dataframe, _parse_mixed_dates.
  * No imports, no file I/O, no os/sys.

CAPABILITIES (not limited to):
  - One-step full dataset cleanup: df, actions = auto_clean_dataframe(df)
  - Remove duplicates (all cols or subset)
  - Fill missing values: mean, median, mode, ffill, bfill, custom string, interpolate
  - Drop rows/columns by missing threshold
  - Type conversion: numeric, datetime, string, category
  - Rename, reorder, drop columns
  - Text standardisation: strip, lower, upper, title case, remove special chars
  - Fix phones (digits only), emails (lowercase+strip), dates (parse mixed formats)
  - Create derived columns (concatenate, extract, calculate)
  - Filter rows by conditions
  - Cap/remove outliers via IQR or Z-score
  - Sort, normalize, scale
  - Regex extraction and replacement
  - Statistical questions, null counts, distributions, correlations

Always return pure JSON. No markdown fences. No text outside the JSON object."""

    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-10:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            temperature=0.1,
            messages=messages,
        )
        raw = resp.choices[0].message.content.strip()
        parsed = _parse_ai_payload(raw)
    except json.JSONDecodeError:
        return df, f"🤖 {raw}", None
    except Exception as e:
        return df, f"❌ AI error: {e}", None

    response_type = parsed.get("type", "answer")
    explanation = parsed.get("explanation", "Done.")

    if response_type != "action":
        return df, explanation, None

    code_str = parsed.get("code", "").strip()
    if not code_str:
        return df, explanation, None

    # First execution attempt
    result_df, exec_err = _safe_exec(code_str, df)

    if exec_err is None:
        return result_df, explanation, code_str

    # ── Self-heal: send error back and ask for a fix ──────────────
    try:
        fix_resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": json.dumps(parsed)},
                {"role": "user", "content": (
                    f"That code raised this error: {exec_err}\n"
                    "Fix the code. Remember: no leading indentation, no inplace=True, "
                    "reassign df for operations that return a new frame. Return corrected JSON only."
                )},
            ],
        )
        fix_raw = fix_resp.choices[0].message.content.strip()
        fix_parsed = _parse_ai_payload(fix_raw)
        fixed_code = fix_parsed.get("code", "").strip()
        result_df2, exec_err2 = _safe_exec(fixed_code, df)
        if exec_err2 is None:
            return result_df2, fix_parsed.get("explanation", explanation), fixed_code
        # Both attempts failed — report clearly
        return df, (
            f"❌ **Could not apply the change.** The AI generated code but it failed to execute.\n\n"
            f"**Error:** `{exec_err2}`\n\n"
            f"Try rephrasing, e.g. *'fill missing Price with the column mean'* or specify the exact column name."
        ), None
    except Exception as e:
        return df, (
            f"❌ **Execution failed:** `{exec_err}`\n\n"
            f"Self-heal also failed: `{e}`\n\nTry rephrasing your request."
        ), None


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
                        elif action == "fill_missing":
                            df, _ = fill_missing(
                                st.session_state.df_working,
                                s["column"],
                                s["method"],
                                s.get("custom", ""),
                            )
                            st.session_state.df_working = df
                            log(f"[Recipe] Applied {action} on {s['column']}")
                        elif action == "drop_missing_rows":
                            before = len(st.session_state.df_working)
                            st.session_state.df_working = st.session_state.df_working.dropna(subset=[s["column"]])
                            log(f"[Recipe] Dropped {before - len(st.session_state.df_working)} rows with missing in {s['column']}")
                        elif action == "find_replace":
                            st.session_state.df_working = apply_fr(st.session_state.df_working, s["rule"])
                            log(f"[Recipe] Applied find/replace")
                        elif action == "cap_outliers":
                            st.session_state.df_working[s["column"]] = st.session_state.df_working[s["column"]].clip(s["lower"], s["upper"])
                            log(f"[Recipe] Capped outliers in {s['column']}")
                        elif action == "remove_outlier_rows":
                            before = len(st.session_state.df_working)
                            col = s["column"]
                            lower, upper = s["lower"], s["upper"]
                            st.session_state.df_working = st.session_state.df_working[
                                (st.session_state.df_working[col] >= lower) & (st.session_state.df_working[col] <= upper)
                            ]
                            log(f"[Recipe] Removed {before - len(st.session_state.df_working)} outlier rows from {col}")
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
    <div style="text-align:center;padding:4rem 2rem;">
        <div style="font-size:3.5rem">📊</div>
        <h3 style="color:#00D4AA;">No data loaded</h3>
        <p style="color:#94A3B8;">Upload a file from the sidebar to get started.<br>
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
    show_raw = st.checkbox("🔍 Show Original Raw Data")
    if show_raw != st.session_state.show_raw_data:
        st.session_state.show_raw_data = show_raw
        st.rerun()

if st.session_state.show_raw_data and st.session_state.df_original is not None:
    st.markdown("---")
    st.markdown('<div class="sec">📄 Original Raw Data (Before Any Cleaning)</div>', unsafe_allow_html=True)
    st.dataframe(st.session_state.df_original, use_container_width=True, height=400)
    st.markdown("---")

# ── Tab persistence: remember which tab is active ─────────────────
# Inject JS that clicks the stored tab index after every rerun
_tab_names = ["📊 Data Viewer","🔍 Issues & Fixes","🔧 Find & Replace","✅ Data Quality","📜 Audit","💾 Export","🤖 AI"]
_active = st.session_state.get("active_tab", 0)
st.markdown(f"""
<script>
(function() {{
    function clickTab(idx) {{
        var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
        if (tabs.length > idx) {{ tabs[idx].click(); }}
    }}
    // Try repeatedly because Streamlit can render tabs after script execution.
    clickTab({_active});
    setTimeout(function(){{ clickTab({_active}); }}, 250);
    setTimeout(function(){{ clickTab({_active}); }}, 750);
    setTimeout(function(){{ clickTab({_active}); }}, 1500);
    setTimeout(function(){{ clickTab({_active}); }}, 2500);
}})();
</script>
""", unsafe_allow_html=True)

# TABS - 7 tabs total
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Data Viewer", 
    "🔍 Issues & Fixes", 
    "🔧 Find & Replace", 
    "✅ Data Quality",
    "📜 Audit", 
    "💾 Export",
    "🤖 AI ",
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 - Data Viewer (KEEP YOUR ORIGINAL CODE HERE)
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.session_state.active_tab = 0
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

# TAB 2 through TAB 6 - PUT YOUR EXISTING CODE HERE (same as before)
# [The rest of your tabs remain exactly the same]


# ══════════════════════════════════════════════════════════════════
# TAB 2 - Issues & Fixes
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.session_state.active_tab = 1
    st.markdown('<div class="sec"> Detected Issues - Click buttons to fix or ignore</div>', unsafe_allow_html=True)

    with st.spinner("Analyzing data..."):
        issues = detect_issues(df)

    # Unignore controls
    if st.session_state.ignored_issues:
        with st.expander(f"🙈 {len(st.session_state.ignored_issues)} ignored issue(s) — click to restore"):
            for ig in sorted(st.session_state.ignored_issues):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"`{ig}`")
                if c2.button("Restore", key=f"restore_issue_{ig}"):
                    st.session_state.ignored_issues.discard(ig)
                    st.rerun()

    # Missing Values Section
    visible_missing = {c: v for c, v in issues['missing'].items() if c not in st.session_state.ignored_issues}
    if visible_missing:
        with st.expander(f" Missing Values ({len(visible_missing)} columns)", expanded=True):
            for col, info in visible_missing.items():
                hdr_c, ign_c = st.columns([5, 1])
                hdr_c.markdown(f"### Column: `{col}`")
                if ign_c.button("🙈 Ignore", key=f"ign_miss_{col}", help="Hide this issue"):
                    st.session_state.ignored_issues.add(col)
                    st.rerun()

                st.markdown(f"Missing: **{info['count']}** rows ({info['percentage']:.1f}%)")
                missing_sample = df[df[col].isnull()].head(3)
                if len(missing_sample) > 0:
                    st.markdown("**Sample rows with missing values:**")
                    st.dataframe(missing_sample, use_container_width=True)
                st.markdown("---")

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
                        if st.button(f" Fill with Mode ('{mode_display}')", key=f"fix_mode_{col}"):
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
                    custom_val = st.text_input("Custom value", key=f"custom_{col}", placeholder="Enter value", label_visibility="collapsed")
                    if st.button(f" Apply Custom", key=f"fix_custom_{col}"):
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
    dup_ignored = "__duplicates__" in st.session_state.ignored_issues
    if issues['duplicates'] > 0 and not dup_ignored:
        with st.expander(f"🔄 Duplicate Rows ({issues['duplicates']} found)", expanded=True):
            hdr_c, ign_c = st.columns([5, 1])
            hdr_c.warning(f"Found {issues['duplicates']} duplicate rows")
            if ign_c.button("🙈 Ignore", key="ign_dupes", help="Hide this issue"):
                st.session_state.ignored_issues.add("__duplicates__")
                st.rerun()
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
    visible_outliers = {c: v for c, v in issues['outliers'].items() if f"__outlier_{c}__" not in st.session_state.ignored_issues}
    if visible_outliers:
        with st.expander(f"📈 Statistical Outliers ({len(visible_outliers)} columns)", expanded=True):
            for col, info in visible_outliers.items():
                hdr_c, ign_c = st.columns([5, 1])
                hdr_c.markdown(f"### Column: `{col}`")
                if ign_c.button("🙈 Ignore", key=f"ign_out_{col}", help="Hide this issue"):
                    st.session_state.ignored_issues.add(f"__outlier_{col}__")
                    st.rerun()
                st.markdown(f"Outliers: **{info['count']}** rows ({info['percentage']:.1f}%) | Normal range: `[{info['lower']:.2f}, {info['upper']:.2f}]`")
                outlier_values = df[(df[col] < info['lower']) | (df[col] > info['upper'])][col].head(5)
                if len(outlier_values) > 0:
                    st.markdown("**Sample outlier values:** " + " · ".join(f"`{v}`" for v in outlier_values))
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

    if not visible_missing and not (issues['duplicates'] > 0 and not dup_ignored) and not visible_outliers:
        st.success("✅ No issues detected (or all have been resolved/ignored).")




# ══════════════════════════════════════════════════════════════════
# TAB 3 - FIND, SEARCH & REPLACE
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.session_state.active_tab = 2
    st.markdown('<div class="sec">🔧 Find, Search & Replace</div>', unsafe_allow_html=True)
    st.markdown("**Search the entire dataset or a specific column, then fix values individually or in bulk**")

    # ── Search scope toggle ──────────────────────────────────────
    search_scope = st.radio("Search in:", ["Entire Dataset", "Specific Column"], horizontal=True, key="search_scope")

    if search_scope == "Specific Column":
        col1, col2 = st.columns([1, 2])
        with col1:
            search_column = st.selectbox("Select column:", df.columns, key="search_col_main")
        with col2:
            search_term = st.text_input("Search for:", placeholder="e.g., 'gmail', '555', 'New York'", key="search_term_main")
        search_all_cols = False
    else:
        search_column = None
        search_term = st.text_input("Search entire dataset for:", placeholder="e.g., 'N/A', 'unknown', '0000'", key="search_term_global")
        search_all_cols = True

    if search_term:
        if search_all_cols:
            # Search every column, collect (row_idx, col, value) hits
            hit_rows = set()
            hit_details = []
            for c in df.columns:
                mask_c = df[c].astype(str).str.contains(search_term, case=False, na=False, regex=False)
                for idx in df[mask_c].index:
                    hit_rows.add(idx)
                    hit_details.append({"Row": idx, "Column": c, "Value": str(df.loc[idx, c])})

            matching_rows = df.loc[sorted(hit_rows)].copy() if hit_rows else pd.DataFrame()
            st.markdown(f"**Found matches in {len(hit_rows)} row(s) across {len(set(d['Column'] for d in hit_details))} column(s)**")

            if hit_details:
                with st.expander("📋 View all matches", expanded=True):
                    st.dataframe(pd.DataFrame(hit_details), hide_index=True, use_container_width=True)

                st.markdown("---")
                st.markdown("### 📦 Bulk Replace Across Entire Dataset")
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    global_replace_val = st.text_input("Replace ALL occurrences of the search term with:", key="global_replace_val", placeholder="New value")
                with col_b:
                    st.markdown("<div style='margin-top:1.8rem'></div>", unsafe_allow_html=True)
                    if st.button("✅ Replace All", key="global_replace_btn", use_container_width=True):
                        if global_replace_val is not None and global_replace_val != "":
                            save_state()
                            total_replaced = 0
                            for c in df.columns:
                                mask_c = df[c].astype(str).str.contains(search_term, case=False, na=False, regex=False)
                                count = mask_c.sum()
                                if count:
                                    df.loc[mask_c, c] = global_replace_val
                                    total_replaced += count
                            st.session_state.df_working = df
                            log(f"Global replace '{search_term}' → '{global_replace_val}' in {total_replaced} cells")
                            recipe_add({"action": "global_replace", "find": search_term, "replace": global_replace_val})
                            save_state()
                            st.success(f"✅ Replaced {total_replaced} cell(s) across the dataset!")
                            st.rerun()
                        else:
                            st.warning("Enter a replacement value")
            else:
                st.info(f"No cells found containing `{search_term}`")

        else:
            # Column-scoped search (original logic)
            mask = df[search_column].astype(str).str.contains(search_term, case=False, na=False)
            matching_rows = df[mask].copy()
            st.markdown(f"**Found {len(matching_rows)} matching row(s) in `{search_column}`**")

    if search_term and not search_all_cols:
        mask = df[search_column].astype(str).str.contains(search_term, case=False, na=False)
        matching_rows = df[mask].copy()
        if len(matching_rows) > 0:
            st.markdown("### Matching rows:")
            st.dataframe(matching_rows, use_container_width=True)
            st.markdown("---")
            st.markdown("### Fix Options:")
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("#### 📦 Fix ALL matching rows")
                new_value_all = st.text_input("Replace all with:", key="bulk_value", placeholder="Enter new value")
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
                row_display = {}
                for idx, row in matching_rows.iterrows():
                    row_display[f"Row {idx} - Current: {row[search_column]}"] = idx
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

            st.markdown("---")
            st.markdown("### ⚡ Quick Actions for this Column")
            col_a, col_b, col_c, col_d = st.columns(4)

            with col_a:
                if st.button("🔠 Title Case (All)", key="title_all_rows"):
                    save_state()
                    affected_count = sum(1 for idx in matching_rows.index if (new_v := str(df.loc[idx, search_column]).title()) != str(df.loc[idx, search_column]) and not df.__setitem__((search_column, idx), new_v) or True)
                    # simpler loop
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
                if st.button("🔡 Lower Case (All)", key="lower_all_rows"):
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
                if st.button("🔠 Upper Case (All)", key="upper_all_rows"):
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
                if st.button("✂️ Trim (All)", key="trim_all_rows"):
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

            st.markdown("---")
            st.markdown("#### Or apply case change to SELECTED row only:")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("🔠 Title Case (Selected Row)", key="title_selected"):
                    save_state()
                    old_val = df.loc[selected_idx, search_column]
                    df.loc[selected_idx, search_column] = str(old_val).title() if pd.notna(old_val) else old_val
                    st.session_state.df_working = df
                    log(f"Applied Title Case to row {selected_idx} in {search_column}")
                    save_state()
                    st.success(f"✅ Applied Title Case to row {selected_idx}!")
                    st.rerun()
            with col_b:
                if st.button("🔡 Lower Case (Selected Row)", key="lower_selected"):
                    save_state()
                    old_val = df.loc[selected_idx, search_column]
                    df.loc[selected_idx, search_column] = str(old_val).lower() if pd.notna(old_val) else old_val
                    st.session_state.df_working = df
                    log(f"Applied Lower Case to row {selected_idx} in {search_column}")
                    save_state()
                    st.success(f"✅ Applied Lower Case to row {selected_idx}!")
                    st.rerun()
            with col_c:
                if st.button("🔠 Upper Case (Selected Row)", key="upper_selected"):
                    save_state()
                    old_val = df.loc[selected_idx, search_column]
                    df.loc[selected_idx, search_column] = str(old_val).upper() if pd.notna(old_val) else old_val
                    st.session_state.df_working = df
                    log(f"Applied Upper Case to row {selected_idx} in {search_column}")
                    save_state()
                    st.success(f"✅ Applied Upper Case to row {selected_idx}!")
                    st.rerun()
        else:
            st.warning(f"No rows found containing '{search_term}' in column '{search_column}'")


# ══════════════════════════════════════════════════════════════════
# TAB 4 - DATA QUALITY 
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.session_state.active_tab = 3
    st.markdown('<div class="sec"> Data Quality - Type Validation & Format Checking</div>', unsafe_allow_html=True)
    
    st.info(" Fix data type issues - edits are saved automatically when you click 'Refresh Issues'")
    
    # Initialize refresh flag if not exists
    if 'quality_refresh' not in st.session_state:
        st.session_state.quality_refresh = False
    
    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh Issues", key="refresh_quality_btn"):
            st.session_state.quality_refresh = True
            st.rerun()
    
    # If refresh flag is set, clear it and re-run to reload data
    if st.session_state.quality_refresh:
        st.session_state.quality_refresh = False
    
    st.markdown("---")
    
    # ========== HELPER FUNCTIONS ==========
    def safe_set_value(df, row_idx, col, value):
        """Safely set a value, converting types if needed"""
        try:
            col_dtype = df[col].dtype
            
            if pd.api.types.is_numeric_dtype(col_dtype):
                try:
                    if isinstance(value, str):
                        numbers = re.findall(r'\d+(?:\.\d+)?', value)
                        if numbers:
                            value = float(numbers[0])
                        else:
                            value = None
                    else:
                        value = float(value)
                except (ValueError, TypeError):
                    value = None
            
            if value is None:
                df.at[row_idx, col] = None
            else:
                df.at[row_idx, col] = value
            return True
        except Exception:
            return False

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
            return 0
        
        return value_str

    def detect_type_issues(df):
        """Detect columns with type issues - always uses current df"""
        issues = []
        
        skip_columns = ['name', 'full name', 'agent', 'agent name', 'city', 'state', 'country', 
                       'address', 'notes', 'description', 'comments', 'status', 'type', 'category', 
                       'user id', 'id', 'full name', 'user id']
        
        for col in df.columns:
            col_lower = col.lower()
            
            if any(skip_word in col_lower for skip_word in skip_columns):
                continue
            
            if any(w in col_lower for w in ['phone', 'mobile', 'contact']):
                expected = 'phone'
            elif any(w in col_lower for w in ['email']):
                expected = 'email'
            elif any(w in col_lower for w in ['date', 'created', 'birth', 'registration', 'active']):
                expected = 'date'
            elif any(w in col_lower for w in ['age', 'year', 'price', 'amount', 'total', 'spent', 'cost', 'salary']):
                expected = 'numeric'
            else:
                continue
            
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
                    is_valid = '@' in email_str and '.' in email_str.split('@')[-1]
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
                    'invalid_rows': invalid_rows,
                    'current_dtype': str(df[col].dtype)
                })
        
        return issues
    
    # Get FRESH current data EVERY TIME the tab loads
    current_df = st.session_state.df_working.copy()
    issues = detect_type_issues(current_df)

    # Unignore controls
    if st.session_state.ignored_quality:
        with st.expander(f"🙈 {len(st.session_state.ignored_quality)} ignored quality issue(s) — click to restore"):
            for ig in sorted(st.session_state.ignored_quality):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"`{ig}`")
                if c2.button("Restore", key=f"restore_q_{ig}"):
                    st.session_state.ignored_quality.discard(ig)
                    st.rerun()

    visible_issues = [iss for iss in issues if iss['column'] not in st.session_state.ignored_quality]

    if not visible_issues:
        st.success("✅ No data quality issues found (or all have been resolved/ignored).")
    else:
        for col_idx, issue in enumerate(visible_issues):
            hdr_c, ign_c = st.columns([5, 1])
            hdr_c.markdown(f"###  Column: `{issue['column']}` (Expected: {issue['expected_type'].upper()})")
            if ign_c.button("🙈 Ignore", key=f"ign_q_{col_idx}_{issue['column'].replace(' ','_')}", help="Hide this issue"):
                st.session_state.ignored_quality.add(issue['column'])
                st.rerun()
            st.markdown(f"Current data type: `{issue['current_dtype']}`")
            st.markdown(f"Found **{len(issue['invalid_rows'])}** problematic values")
            
            if issue['expected_type'] == 'numeric' and 'int' in issue['current_dtype']:
                st.warning(f"⚠️ This is a numeric column. Only numbers are allowed.")
            
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
            
            # Display editable table
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
            
            st.markdown("---")
            st.markdown("**Bulk Actions:**")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                # Apply Table Edits button
                if st.button(f" Apply Table Edits", key=f"save_edits_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    save_state()
                    changes_made = 0
                    for _, row in edited_df.iterrows():
                        row_idx = int(row['Row'])
                        new_val = row['New Value']
                        current_val = str(row['Current Value'])
                        if new_val != current_val:
                            if safe_set_value(current_df, row_idx, issue['column'], new_val):
                                changes_made += 1
                    if changes_made > 0:
                        st.session_state.df_working = current_df
                        log(f"Applied {changes_made} edits to {issue['column']}")
                        save_state()
                        st.success(f"✅ Applied {changes_made} changes! Click 'Refresh Issues' to see updated list.")
                        st.session_state.quality_refresh = True
                        st.rerun()
                    else:
                        st.warning("No valid changes detected")
            
            with col_b:
                # Apply All Suggested button
                if st.button(f" Apply All Suggested", key=f"apply_suggested_{col_idx}_{issue['column'].replace(' ', '_')}"):
                    save_state()
                    changes_made = 0
                    for inv in issue['invalid_rows']:
                        if safe_set_value(current_df, inv['row'], issue['column'], inv['suggested']):
                            changes_made += 1
                    if changes_made > 0:
                        st.session_state.df_working = current_df
                        log(f"Applied suggested fixes to {changes_made} rows in {issue['column']}")
                        save_state()
                        st.success(f"✅ Applied fixes to {changes_made} rows! Click 'Refresh Issues' to see updated list.")
                        st.session_state.quality_refresh = True
                        st.rerun()
                    else:
                        st.warning("No valid fixes could be applied")
            
            with col_c:
                # Custom value
                custom_val = st.text_input(
                    "Custom value:", 
                    key=f"custom_val_{col_idx}_{issue['column'].replace(' ', '_')}", 
                    placeholder="Enter value..."
                )
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button(f" Apply to All", key=f"custom_all_{col_idx}_{issue['column'].replace(' ', '_')}"):
                        if custom_val:
                            save_state()
                            applied_count = 0
                            for inv in issue['invalid_rows']:
                                if safe_set_value(current_df, inv['row'], issue['column'], custom_val):
                                    applied_count += 1
                            if applied_count > 0:
                                st.session_state.df_working = current_df
                                log(f"Applied custom value '{custom_val}' to {applied_count} rows in {issue['column']}")
                                save_state()
                                st.success(f"✅ Applied to {applied_count} rows! Click 'Refresh Issues' to see updated list.")
                                st.session_state.quality_refresh = True
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to apply. For numeric columns, use numbers only.")
                        else:
                            st.warning("Enter a value first")
                
                with col_c2:
                    if st.button(f"🗑️ Clear All", key=f"clear_all_{col_idx}_{issue['column'].replace(' ', '_')}"):
                        save_state()
                        for inv in issue['invalid_rows']:
                            safe_set_value(current_df, inv['row'], issue['column'], "")
                        st.session_state.df_working = current_df
                        log(f"Cleared {len(issue['invalid_rows'])} values in {issue['column']}")
                        save_state()
                        st.success(f"✅ Cleared all values! Click 'Refresh Issues' to see updated list.")
                        st.session_state.quality_refresh = True
                        st.rerun()
            
            st.markdown("---")
# ══════════════════════════════════════════════════════════════════
# TAB 5 - Audit (YOUR ORIGINAL VERSION)
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.session_state.active_tab = 4
    st.markdown('<div class="sec"> Cleaning Audit Log</div>', unsafe_allow_html=True)
    
    if not st.session_state.audit_log:
        st.info("No cleaning actions have been performed yet.")
    else:
        for entry in reversed(st.session_state.audit_log[-30:]):
            st.markdown(
                f'<div class="audit-entry">'
                f'<span class="ts">{entry["ts"]}</span>&nbsp;&nbsp;{entry["msg"]}'
                f'</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<div class="sec"> Save Recipe</div>', unsafe_allow_html=True)
    
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
    st.session_state.active_tab = 5
    st.markdown('<div class="sec"> Export Cleaned Data</div>', unsafe_allow_html=True)
    
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

# ══════════════════════════════════════════════════════════════════
# TAB 7 - AI  (FULL INTELLIGENCE UPGRADE)
# ══════════════════════════════════════════════════════════════════
with tab7:
    st.session_state.active_tab = 6
    st.markdown('<div class="sec">🤖 AI — Intelligent Data Cleaning Assistant</div>', unsafe_allow_html=True)

    if groq_client is None:
        st.info(
            "AI is running in local cleaning mode. Add `GROQ_API_KEY` to `.env`, `.venv`, or Streamlit secrets for full natural-language AI.\n\n"
            "Get a free key at [console.groq.com](https://console.groq.com)"
        )
    else:
        st.markdown(
            '<div style="background:linear-gradient(90deg,#0F172A,#1E293B);border:1px solid #00D4AA;border-radius:8px;'
            'padding:0.6rem 1rem;margin-bottom:0.5rem;display:flex;align-items:center;gap:0.5rem;">'
            '<span style="font-size:1.1rem;">🟢</span>'
            '<span style="color:#00D4AA;font-weight:600;">AI Active</span>'
            '<span style="color:#94A3B8;font-size:0.8rem;margin-left:0.5rem;">— llama-3.3-70b-versatile via Groq · '
            'Ask anything about your data</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── AI Quality Score ─────────────────────────────────────────
    score = ai_quality_score(df)
    score_color = "#00D4AA" if score >= 80 else "#F59E0B" if score >= 50 else "#EF4444"
    col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
    with col_s1:
        st.metric("🏆 AI Quality Score", f"{score}/100")
    with col_s2:
        st.markdown(
            f'<div style="margin-top:0.6rem;font-size:1.4rem;color:{score_color};">'
            f'{"🟢 Excellent" if score >= 80 else "🟡 Needs Work" if score >= 50 else "🔴 Poor"}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_s3:
        missing_pen = min(60, int(df.isnull().sum().sum() / max(df.size, 1) * 60))
        dup_pen = min(40, int(df.duplicated().sum() / max(len(df), 1) * 40))
        st.markdown(
            f'<div style="background:#1E293B;border:1px solid #334155;border-radius:8px;padding:0.6rem 1rem;">'
            f'<span style="color:#94A3B8;font-size:0.75rem;">SCORE BREAKDOWN</span><br>'
            f'<span style="color:#E2E8F0;font-size:0.8rem;">Missing values penalty: -{missing_pen} pts</span><br>'
            f'<span style="color:#E2E8F0;font-size:0.8rem;">Duplicates penalty: -{dup_pen} pts</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── AI Dataset Analyzer ──────────────────────────────────────
    st.markdown("### 🔍 AI Dataset Analyzer")
    st.caption("One-click deep scan — AI inspects your data and suggests targeted fixes")

    if st.button("🔍 Analyze Dataset with AI", key="ai_analyze_btn"):
        with st.spinner("🤖 Scanning your dataset…"):
            suggestions = get_ai_suggestions(df)
            st.session_state.ai_suggestions = suggestions

    if st.session_state.ai_suggestions:
        valid_suggestions = [s for s in st.session_state.ai_suggestions if s.get("action") != "error"]
        error_suggestions = [s for s in st.session_state.ai_suggestions if s.get("action") == "error"]

        if error_suggestions:
            st.error(error_suggestions[0]["reason"])

        if valid_suggestions:
            st.markdown(f"**AI found {len(valid_suggestions)} suggestion(s):**")
            for i, sug in enumerate(valid_suggestions):
                action = sug.get("action", "")
                column = sug.get("column", "")
                col_exists = column in df.columns or action in ("remove_duplicates", "remove_business_duplicates", "auto_clean_dataset")
                c_card, c_btn = st.columns([4, 1])
                with c_card:
                    st.markdown(
                        f'<div style="background:#1E293B;border-left:3px solid #00D4AA;'
                        f'border-radius:0 6px 6px 0;padding:0.5rem 0.9rem;margin-bottom:0.3rem;">'
                        f'<span style="color:#00D4AA;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">'
                        f'{action.replace("_"," ")}</span>'
                        f'{"" if col_exists else " <span style=color:#EF4444;font-size:0.7rem;>(column not found)</span>"}'
                        f'<br><span style="color:#E2E8F0;font-size:0.85rem;">📌 <code>{column}</code></span><br>'
                        f'<span style="color:#94A3B8;font-size:0.8rem;">{sug.get("reason","")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with c_btn:
                    st.markdown("<div style='margin-top:0.4rem'></div>", unsafe_allow_html=True)
                    if st.button("⚡ Apply", key=f"ai_fix_{i}_{action}", disabled=(not col_exists)):
                        save_state()
                        st.session_state.df_working = apply_ai_fix(st.session_state.df_working, action, column)
                        log(f"[AI Analyzer] Applied '{action}' on '{column}'")
                        recipe_add({"action": action, "column": column, "source": "ai_suggestion"})
                        save_state()
                        st.success(f"✅ Applied **{action}** on `{column}`")
                        st.rerun()
        else:
            st.info("No actionable suggestions returned.")
    else:
        st.info("Click **🔍 Analyze Dataset with AI** above to get AI-powered suggestions.")

    st.markdown("---")

    # ── Full AI Chat ─────────────────────────────────────
    st.markdown("### 💬 AI Chat")
    st.markdown(
        '<div style="background:#1E293B;border:1px solid #334155;border-radius:8px;padding:0.7rem 1rem;margin-bottom:1rem;">'
        '<span style="color:#94A3B8;font-size:0.8rem;">💡 <strong style="color:#E2E8F0;">Ask anything.</strong> '
        'Examples: &nbsp;'
        '<code>fill missing ages with the median</code> &nbsp;·&nbsp; '
        '<code>remove duplicates keeping the last occurrence</code> &nbsp;·&nbsp; '
        '<code>convert the Date column to datetime</code> &nbsp;·&nbsp; '
        '<code>standardize all emails to lowercase</code> &nbsp;·&nbsp; '
        '<code>create a full_name column from first and last</code> &nbsp;·&nbsp; '
        '<code>which columns have the most nulls?</code> &nbsp;·&nbsp; '
        '<code>cap outliers in salary using IQR</code>'
        '</span></div>',
        unsafe_allow_html=True,
    )

    # ── Chat input pinned at top, history scrollable below ──────
    # Inject CSS for the scrollable chat window
    st.markdown("""
    <style>
    .chat-scroll-window {
        height: 480px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        padding: 0.5rem 0.2rem;
        border: 1px solid #1E293B;
        border-radius: 10px;
        background: #0F172A;
        margin-bottom: 0.5rem;
    }
    /* Auto-scroll anchor */
    .chat-scroll-anchor { height: 1px; }
    </style>
    <script>
    // Auto-scroll to bottom of chat window on load
    function scrollChat() {
        var wins = window.parent.document.querySelectorAll('.chat-scroll-window');
        wins.forEach(function(w){ w.scrollTop = 0; });
    }
    window.addEventListener('load', scrollChat);
    setTimeout(scrollChat, 400);
    </script>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="background:#111827;border:1px solid #334155;border-radius:8px;'
        'padding:0.75rem 0.9rem;margin-bottom:0.75rem;">'
        '<span style="color:#00D4AA;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;">'
        'AI Prompt</span>'
        '<div style="color:#94A3B8;font-size:0.78rem;margin-top:0.25rem;">'
        'Type naturally. Cleanup commands are applied directly; analysis questions stay as answers.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("Clean Whole Dataset", key="ai_quick_clean", use_container_width=True):
            st.session_state.ai_pending_prompt = "clean the whole dataset"
    with q2:
        if st.button("Find Issues", key="ai_quick_issues", use_container_width=True):
            st.session_state.ai_pending_prompt = "suggest me ways to clean the data"
    with q3:
        if st.button("Missing + Duplicates", key="ai_quick_quality", use_container_width=True):
            st.session_state.ai_pending_prompt = "show missing values and duplicates"

    with st.form("ai_prompt_form", clear_on_submit=True):
        typed_prompt = st.text_area(
            "Prompt",
            placeholder="Example: clean the whole dataset, fix all issues, explain remaining quality problems...",
            height=95,
            label_visibility="collapsed",
            key="ai_prompt_text_area",
        )
        send_prompt = st.form_submit_button("Send to AI", use_container_width=True)

    user_input = None
    if send_prompt and typed_prompt.strip():
        user_input = typed_prompt.strip()
    elif st.session_state.get("ai_pending_prompt"):
        user_input = st.session_state.pop("ai_pending_prompt")

    # Scrollable history window via HTML container, newest exchange first.
    history_parts = []
    exchanges = []
    chat_turns = st.session_state.chat_history
    i = 0
    while i < len(chat_turns):
        if chat_turns[i].get("role") == "user":
            exchange = [chat_turns[i]]
            if i + 1 < len(chat_turns) and chat_turns[i + 1].get("role") == "assistant":
                exchange.append(chat_turns[i + 1])
                i += 2
            else:
                i += 1
            exchanges.append(exchange)
        else:
            exchanges.append([chat_turns[i]])
            i += 1

    for exchange in reversed(exchanges):
        for turn in exchange:
            role = turn["role"]
            content = turn["content"]
            if role == "user":
                safe_content = _escape_chat_html(content)
                bubble = (
                    f'<div style="display:flex;justify-content:flex-end;margin:4px 0">'
                    f'<div style="background:#1D4ED8;color:#fff;padding:0.55rem 0.9rem;'
                    f'border-radius:14px 14px 2px 14px;max-width:78%;font-size:0.88rem;'
                    f'white-space:pre-wrap;word-break:break-word;">{safe_content}</div></div>'
                )
            else:
                safe_content = _escape_chat_html(content)
                bubble = (
                    f'<div style="display:flex;justify-content:flex-start;margin:4px 0 14px 0">'
                    f'<div style="background:#1E293B;color:#E2E8F0;padding:0.55rem 0.9rem;'
                    f'border-radius:14px 14px 14px 2px;max-width:86%;font-size:0.88rem;'
                    f'white-space:pre-wrap;word-break:break-word;">'
                    f'<span style="font-size:0.75rem;color:#00D4AA;font-weight:600;">AI</span><br>'
                    f'{safe_content}</div></div>'
                )
            history_parts.append(bubble)

    scroll_html = (
        '<div class="chat-scroll-window">'
        + ("".join(history_parts) if history_parts else
           '<div style="color:#475569;font-size:0.85rem;text-align:center;margin-top:2rem;">'
           '💬 No messages yet — type below to get started</div>')
        + '<div class="chat-scroll-anchor"></div>'
        + '</div>'
    )
    st.markdown(scroll_html, unsafe_allow_html=True)

    # Also render proper st.chat_message bubbles for the LATEST exchange only
    # (so code expanders and markdown render properly for new messages)
    if st.session_state.chat_history and len(st.session_state.chat_history) >= 2:
        last_two = st.session_state.chat_history[-2:]
        if last_two[-1]["role"] == "assistant" and last_two[-1].get("code"):
            with st.expander("🧪 View generated code from last response", expanded=False):
                st.code(last_two[-1]["code"], language="python")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("🤖 Thinking…"):
            df_before = st.session_state.df_working.copy()
            updated_df, explanation, code_str = ai_chat_response(
                user_input,
                st.session_state.df_working.copy(),
                st.session_state.chat_history[:-1],
            )

        data_changed = False
        if code_str is not None:
            if not isinstance(updated_df, pd.DataFrame):
                updated_df = df_before.copy()

            rows_before = len(df_before)
            nulls_before = int(df_before.isnull().sum().sum())
            rows_after = len(updated_df)
            nulls_after = int(updated_df.isnull().sum().sum())
            cols_before = set(df_before.columns)
            cols_after = set(updated_df.columns)
            shape_changed = df_before.shape != updated_df.shape
            nulls_changed = nulls_before != nulls_after
            cols_changed = cols_before != cols_after
            try:
                values_changed = not df_before.equals(updated_df)
            except Exception:
                values_changed = True
            data_changed = shape_changed or nulls_changed or cols_changed or values_changed

            if data_changed:
                save_state()
                st.session_state.df_working = updated_df
                save_state()
                log(f"[AI] {user_input[:80]}")
                recipe_add({"action": "ai", "command": user_input, "code": code_str})

                delta_lines = []
                if rows_before != rows_after:
                    delta_lines.append(f"Rows: {rows_before:,} → {rows_after:,} ({rows_after - rows_before:+,})")
                if nulls_changed:
                    delta_lines.append(f"Nulls: {nulls_before:,} → {nulls_after:,} ({nulls_after - nulls_before:+,})")
                new_cols = cols_after - cols_before
                if new_cols:
                    delta_lines.append(f"New cols: {', '.join(new_cols)}")
                dropped_cols = cols_before - cols_after
                if dropped_cols:
                    delta_lines.append(f"Dropped: {', '.join(dropped_cols)}")
                if delta_lines:
                    explanation += "\n\n✅ **Applied:** " + " · ".join(delta_lines)
            else:
                explanation += "\n\n⚠️ Code ran but data unchanged (operation may have had no effect)."

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": explanation,
            "code": code_str,
        })

        # Show code expander inline (outside scroll window so it renders properly)
        if code_str:
            with st.expander("🧪 View generated code", expanded=False):
                st.code(code_str, language="python")

        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
