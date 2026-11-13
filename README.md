# Smart Control Tower · Press Shop Daily Review

An operational analytics workspace and performance review dashboard designed for Amber PR & R (Press Shop).

---

## Architecture & Project Structure

The project is intentionally minimal and modular:

```
Smart Control Tower/
├── public/                    # THE WEBSITE (only copy) — served locally and by Vercel
│   ├── index.html             # UI + formula engine + charts
│   └── assets/                # Logo, favicon, AI avatar
│
├── server.py                  # Local server + AI proxy (python server.py)
├── api/index.py               # Vercel's AI endpoint; reuses server.py
│
├── data/                      # INPUT: client Excel files (private)
│   ├── Fw__PRESS_SHOP_OEE_REPORT_AND_REJECTION_DOWNTIME_REPORT_ (1)/
│   ├── Fw__Downtime_data_from_Nov'25_to_Mar'26/
│   ├── Fw__REJECTION/
│   └── analysis/              # OUTPUT: audit & diagnostics workbooks
│
├── docs/                      # Project documents (not used by the website)
│   ├── Project_One_Pager.pdf / .html
│   ├── HISTORICAL_DATA_AUDIT_REPORT.md
│   ├── checkpoints/           # Session checkpoints
│   └── images/                # OEE formula sheet, screenshots
│
├── tests/formula_check.js     # Verifies KPI math (node tests/formula_check.js)
├── .env                       # API keys (Groq / OpenAI / Mistral), not in git
├── .env.example               # Template for .env
├── vercel.json                # Routes /api/* → Python
├── requirements.txt / pyproject.toml / uv.lock
└── README.md
```

Rule: edit `public/index.html` directly. There is no second copy to keep in sync.

---

## Running the Application

### 1. Install optional helper dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional for AI)
Add your API key to `.env`:
```ini
GROQ_API_KEY=your_key_here
# or OPENAI_API_KEY=...
# or MISTRAL_API_KEY=...
```

### 3. Start the Server
```powershell
python server.py
```
Open **`http://localhost:4173/`** in your browser.

To share across the factory Wi-Fi / local plant office:
```powershell
$env:SMART_TOWER_HOST="0.0.0.0"
python server.py
```
Open `http://<your-computer-ip>:4173/` from any phone or PC on the network.
