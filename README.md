# EMS Expense Portal - Mobile Web App

A modern, mobile-friendly Web Application designed to make submitting corporate expenses to the EMS portal (`http://122.170.117.118/ems/`) seamless from any smartphone (iOS / Android) or desktop browser.

---

## ⚡ Direct Access Options

### 1. Instant Worldwide Public Access (HTTPS)
When running locally, the app automatically establishes a secure **Cloudflare Tunnel** giving you a live HTTPS URL (e.g. `https://<unique-name>.trycloudflare.com`).
- **No port forwarding or VPN needed**
- Accessible from any smartphone on cellular data (4G/5G) anywhere in the world
- Shows a dynamic QR code on screen for 1-second mobile scanning

### 2. 24/7 Cloud Hosting (No PC Needed)
You can deploy this repository to free cloud platforms with 1 click:
- **[Render.com](https://render.com/)**: Connect this GitHub repo -> New Web Service -> Select Python -> Start Command: `gunicorn app:app`.
- **[Railway.app](https://railway.app/)**: Connect GitHub repo -> 1-click automatic build via Dockerfile.
- **[PythonAnywhere](https://www.pythonanywhere.com/)**: Free Python WSGI hosting.

---

## 🚀 Quick Start (Local PC)

1. Double-click **`start_expense_app.bat`** (or `Start Expense Mobile App.bat`).
2. The browser will open **`http://localhost:5000`**.
3. Scan the **QR Code** on screen with your phone camera to open on mobile immediately.

---

## 📱 Features

- **📸 Camera & File Upload:** Snap physical receipts directly with your phone's camera (`capture="environment"`), or upload PDF, PNG, or JPG receipts.
- **⚡ Auto JPG Conversion:** High-resolution multi-page PDF or PNG receipts are automatically converted into compressed JPGs compliant with the EMS portal requirements.
- **🧠 Auto Text & Date Parsing:** Automatically detects dates, total amounts, and ride/meal descriptions from Rapido, Uber, or restaurant bills.
- **🚗 Quick Preset Chips:** 1-tap fill for **Rapido**, **Uber**, **Lunch**, **Dinner**, **Hotel**, or **Other**.
- **🏢 Direct Portal Submission:** Authenticates with the EMS portal, passes ViewState session tokens, uploads multipart form data, and confirms registration.
- **📋 Live Portal History:** Real-time sync with the EMS portal to view recent expense claims and approval statuses (`In Process`, `Paid`).

---

## 📂 Project Structure

```
├── app.py                # Main Flask backend server (EMS login, upload, parse, submit)
├── templates/
│   └── index.html        # Responsive mobile-first UI with camera capture, QR & presets
├── requirements.txt      # Python dependencies (Flask, requests, pillow, pymupdf, gunicorn)
├── Procfile              # Cloud process command for Render/Heroku/Railway
├── render.yaml           # 1-click blueprint for Render.com
├── Dockerfile            # Container image definition
├── start_expense_app.bat # Windows desktop launcher
└── README.md             # Documentation
```
