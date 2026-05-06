# DataScrub – Setup & Run Guide

Everything you need is in this folder. No GitHub, no cloud, just your machine.

---

## Folder contents

```
datascrub/
├── app.py              ← the Streamlit app
├── requirements.txt    ← Python packages needed
├── messy_users.csv     ← the sample messy dataset to test with
└── README.md           ← this file
```

---

## One-time setup (do this once)

### Step 1 — Make sure Python is installed
Open a terminal in VS Code (`Ctrl + backtick`) and run:
```
python --version
```
You need Python 3.9 or newer. If you don't have it: https://www.python.org/downloads/

---

### Step 2 — Install the required packages
In the VS Code terminal, make sure you are inside the `datascrub` folder:
```
cd path\to\datascrub
```
Then install dependencies:
```
pip install -r requirements.txt
```
This installs: streamlit, pandas, numpy, openpyxl.

---

## Running the app

Every time you want to launch the app, run this in the terminal:
```
streamlit run app.py
```

Your browser will open automatically at:
```
http://localhost:8501
```

If the browser doesn't open, copy that URL and paste it manually.

To stop the app: press `Ctrl + C` in the terminal.

---

## Using the app with the sample file

1. Click **Browse files** in the sidebar
2. Select `messy_users.csv` from this folder
3. The app loads the data — you will see row/column counts in the header
4. Work through each tab:
   - **Preview** — see the raw data and column types
   - **Issues** — auto-scan finds missing values, duplicates, outliers, spelling flags
   - **Clean** — fix missing values, remove duplicates, handle outliers
   - **Rules** — add find/replace rules (e.g. fix city casing, typos)
   - **Audit** — see every action taken + save as a recipe JSON
   - **Export** — download cleaned CSV or Excel, save the recipe

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Run `pip install streamlit` again, or use `python -m streamlit run app.py` |
| `ModuleNotFoundError: No module named 'openpyxl'` | Run `pip install openpyxl` |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |
| App opens but looks broken | Hard-refresh the browser with `Ctrl + Shift + R` |
