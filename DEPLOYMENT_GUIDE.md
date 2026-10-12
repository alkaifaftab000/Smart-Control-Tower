# Smart Control Tower · Always-On Deployment Guide

## 1. Why Render Goes to Sleep (And The Fix)
* **The Problem:** Render's free tier spins down into "sleep mode" after 15 minutes of inactivity. When someone opens it later, it takes 50–90 seconds to wake up.
* **The Two Fixes:**
  1. **Deploy on Vercel (Recommended):** Vercel **never sleeps**. The dashboard loads in 0.1s worldwide, 24/7.
  2. **Keep Render Awake 24/7 with a Free Ping:** If you use Render, add a free 10-minute ping monitor (instructions below).

---

## 2. Option A (Recommended): Deploy to Vercel (100% Always-On, Never Sleeps)

Vercel serves the HTML dashboard from its global CDN instantly and runs the AI proxy on-demand.

### 3-Step Vercel Setup:
1. Push this folder to a GitHub repository.
2. Go to **[vercel.com](https://vercel.com) &rarr; Add New &rarr; Project**:
   * Select your repository.
   * Vercel will automatically detect [`vercel.json`](file:///D:/HMC/Amber%20All/Soma%20ji/Smart%20Control%20Tower/vercel.json) and [`api/index.py`](file:///D:/HMC/Amber%20All/Soma%20ji/Smart%20Control%20Tower/api/index.py).
3. Under **Environment Variables**, add:
   * `GROQ_API_KEY` = `your_groq_api_key` (or `OPENAI_API_KEY`)
4. Click **Deploy**.
   * You will get an instant, permanent link: `https://your-project.vercel.app`
   * **Result:** 0.1-second page loads, zero cold-starts, zero sleeping!

---

## 3. Option B: Keep Render Awake 24/7 (Free Trick)

If you already have or prefer Render:
1. Deploy via [`render.yaml`](file:///D:/HMC/Amber%20All/Soma%20ji/Smart%20Control%20Tower/render.yaml) on [Render.com](https://render.com).
2. Go to **[Cron-job.org](https://cron-job.org)** or **[UptimeRobot.com](https://uptimerobot.com)** (both 100% free).
3. Create a simple HTTP monitor:
   * **URL:** `https://your-app.onrender.com/api/status`
   * **Interval:** Every 10 minutes.
4. **Result:** Because Render receives a heartbeat ping every 10 minutes, **it never goes to sleep** and stays running 24/7.

---

## 4. Option C: Plant Office / Local WiFi Sharing (Zero Cloud)

If your team is in the plant and you don't even want to use cloud providers:
1. Start the server on your computer:
   ```powershell
   $env:SMART_TOWER_HOST="0.0.0.0"
   python ai_local_server.py
   ```
2. Find your local IP via `ipconfig` (e.g. `192.168.1.45`).
3. Anyone on the factory WiFi or office network can open:
   `http://192.168.1.45:4173/`
   and upload their files directly from their desk!
