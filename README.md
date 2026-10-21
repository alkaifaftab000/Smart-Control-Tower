# Smart Control Tower · Press Shop Daily Review

An operational analytics workspace and performance review dashboard designed for Amber PR & R (Press Shop).

---

## Architecture & Project Structure

The project is intentionally minimal and modular:

```
Smart Control Tower/
├── assets/                    # Static UI branding & images
│   ├── ai-assistant-avatar.png
│   └── amber_logo.png
│
├── data/                      # Client's plant operational Excel files (private)
│   ├── DFOS  Dashboard (1).xlsx
│   ├── Fw__Downtime_data_from_Nov'25_to_Mar'26/
│   ├── Fw__PRESS_SHOP_OEE_REPORT_AND_REJECTION_DOWNTIME_REPORT_ (1)/
│   └── Fw__REJECTION/
│
├── .env                       # Local API credentials (OpenAI / Mistral / Groq)
├── .env.example               # Template environment configuration
├── .gitignore                 # Standard git ignores
├── index.html                 # The complete web dashboard application
├── requirements.txt           # Python dependencies (openpyxl)
├── README.md                  # Project overview
└── server.py                  # Standalone Python local server & AI API proxy
```

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
