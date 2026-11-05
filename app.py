import os
import sys
import re
import io
import time
import socket
import datetime
import subprocess
import threading
from urllib.parse import urljoin

from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from PIL import Image
import pymupdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# EMS Portal Configuration
EMS_BASE_URL = "http://122.170.117.118/ems/"
EMS_LOGIN_URL = urljoin(EMS_BASE_URL, "Login.aspx")
EMS_ADD_URL = urljoin(EMS_BASE_URL, "Client/AddExpense.aspx")
EMS_HOME_URL = urljoin(EMS_BASE_URL, "Client/expensesHome.aspx")
EMS_SEARCH_URL = urljoin(EMS_BASE_URL, "Client/expenses.aspx")

PORTAL_USER = "ASHISH"
PORTAL_PASS = "pass@123"
PORTAL_MEMBER_TYPE = "E"

DEFAULT_COMPANY_ID = "f4242a8a-dafd-420c-b9c2-2fc8244562f4"  # SSB DIGITAL PRIVATE LIMITED
COMPANIES = [
    {"id": "f4242a8a-dafd-420c-b9c2-2fc8244562f4", "name": "SSB DIGITAL PRIVATE LIMITED"},
    {"id": "ea2dab8d-a061-4c57-9e0d-4759091de281", "name": "INTEGRATED PUBLIC SAFETY SYSTEMS PRIVATE"},
    {"id": "eefbfbea-d758-4a1d-8844-4d9e01eb4007", "name": "INTERACT PUBLIC SAFETEY SOLUTIONS PVT. LTD."},
    {"id": "3007d77a-25fe-4b88-9bc0-323580be3b35", "name": "KASHTBHANJAN FINANCIAL SERVICES PVT. LTD."},
    {"id": "79412a37-b0eb-432c-b182-4367644d2b59", "name": "S. S. B. I. EXPORTS PRIVATE LIMITED"},
    {"id": "54451f01-df0d-47d3-82c9-605c04501534", "name": "SCHOOL OF SECURITY AND BEHAVIOURAL"},
    {"id": "c3008a5e-f460-4355-8780-b42b050153eb", "name": "SOLAR SEWAGE BASIC INFRASTRUCTURE PRIVATE"},
    {"id": "f4242a8a-dafd-420c-b9c2-2fc8244562f5", "name": "SSB GREEN ENVIRO PVT LTD"},
    {"id": "f4242a8a-dafd-420c-b9c2-2fc8244562f6", "name": "SSBI FACILITY MANAGEMENT PVT LID"}
]

EXPENSE_TYPES = [
    {"id": "3276C4FD-9830-44D7-972F-1417730FCACE", "name": "Other", "category": "other"},
    {"id": "6C169177-1E95-45D3-B65D-82463469BDA4", "name": "Lunch", "category": "lunch"},
    {"id": "DB7DEBEE-D418-4A1B-8B1A-CC6408A0CCF7", "name": "Dinner", "category": "dinner"},
    {"id": "C213C3FC-170E-4C72-8ACB-5AFF970F2011", "name": "Breakfast", "category": "breakfast"},
    {"id": "8E18ACAB-BB76-423C-8CB1-4A61C655E7F3", "name": "Hotel", "category": "hotel"},
    {"id": "DA3C8DD6-7A17-40B2-AD69-F7C986D27E73", "name": "Conveyance", "category": "conveyance"},
    {"id": "08EEE238-351C-4D69-A26D-72B25C75E673", "name": "Mobile", "category": "mobile"},
    {"id": "834ACDD0-2E3A-45C4-9EC4-CF2F1AF74DE0", "name": "Internet", "category": "internet"},
    {"id": "F7969044-1631-4DF2-A27C-2A1CA0E1CFDD", "name": "Ticket Booking", "category": "ticket"}
]

# Helper to get local IP
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Public Cloudflare Tunnel Management
PUBLIC_TUNNEL_URL = None

def start_cloudflare_tunnel(port=5000):
    global PUBLIC_TUNNEL_URL
    bin_path = os.path.join(BASE_DIR, 'bin', 'cloudflared.exe')
    if not os.path.exists(bin_path):
        return
        
    def _worker():
        global PUBLIC_TUNNEL_URL
        try:
            cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
            creation_flag = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flag
            )
            for line in proc.stdout:
                m = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if m:
                    PUBLIC_TUNNEL_URL = m.group(0)
                    print("-" * 60)
                    print(f"PUBLIC CLOUD URL (HTTPS): {PUBLIC_TUNNEL_URL}")
                    print("Direct Anywhere Link: Access from any phone worldwide!")
                    print("-" * 60)
                    break
        except Exception as e:
            print(f"Tunnel notice: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

# Authenticate with EMS portal and return session
def get_authenticated_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    # GET Login page
    login_get = session.get(EMS_LOGIN_URL, timeout=10)
    vs_match = re.search(r'name="__VIEWSTATE" id="__VIEWSTATE" value="([^"]+)"', login_get.text)
    gen_match = re.search(r'name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="([^"]+)"', login_get.text)
    ev_match = re.search(r'name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="([^"]+)"', login_get.text)
    
    if not vs_match:
        raise RuntimeError("Failed to fetch login ViewState from EMS portal.")
        
    vs = vs_match.group(1)
    gen = gen_match.group(1) if gen_match else ""
    ev = ev_match.group(1) if ev_match else ""
    
    payload = {
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": gen,
        "__EVENTVALIDATION": ev,
        "txtUN": PORTAL_USER,
        "txtPass": PORTAL_PASS,
        "membershipRadios": PORTAL_MEMBER_TYPE,
        "btnLogin": "Login"
    }
    
    post_res = session.post(EMS_LOGIN_URL, data=payload, allow_redirects=False, timeout=10)
    if "ASP.NET_SessionId" not in session.cookies:
        raise RuntimeError("EMS Portal authentication failed. Check credentials.")
        
    return session

# Convert uploaded file (PDF, PNG, etc.) to high-quality JPG
def process_upload_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_jpg_name = f"{base_name}_converted_{int(time.time())}.jpg"
    out_jpg_path = os.path.join(UPLOAD_FOLDER, out_jpg_name)
    
    extracted_text = ""
    
    if ext == '.pdf':
        doc = pymupdf.open(file_path)
        extracted_text = "\n".join([page.get_text() for page in doc])
        
        imgs = []
        total_h = 0
        max_w = 0
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            imgs.append(img)
            total_h += img.height
            max_w = max(max_w, img.width)
            
        stitched = Image.new("RGB", (max_w, total_h), color=(255, 255, 255))
        curr_y = 0
        for img in imgs:
            stitched.paste(img, (0, curr_y))
            curr_y += img.height
            
        stitched.save(out_jpg_path, "JPEG", quality=92)
    else:
        # Standard image (PNG, WEBP, etc.)
        img = Image.open(file_path).convert("RGB")
        img.save(out_jpg_path, "JPEG", quality=92)
        
    return out_jpg_name, out_jpg_path, extracted_text

# Parse receipt text for date, amount, route, etc.
def parse_receipt_text(text, filename=""):
    today_str = datetime.datetime.now().strftime("%d-%b-%Y")
    data = {
        "date": today_str,
        "amount": "",
        "category": "other",
        "exp_type_id": "3276C4FD-9830-44D7-972F-1417730FCACE",  # Other
        "company_id": DEFAULT_COMPANY_ID,
        "remarks": "",
        "detected_service": "General"
    }
    
    if not text:
        return data
        
    # Check for Rapido
    if "Rapido" in text or "Ride ID #RD" in text or "RD17" in text:
        data["detected_service"] = "Rapido"
        data["category"] = "rapido"
        data["exp_type_id"] = "3276C4FD-9830-44D7-972F-1417730FCACE"  # Other
        
        # Ride ID
        ride_match = re.search(r'RD\d{15,19}', text)
        ride_id = ride_match.group(0) if ride_match else ""
        
        # Vehicle Mode
        vehicle = "Auto" if "Auto" in text else "Car"
        
        # Address extraction
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        pickups = []
        drops = []
        for l in lines:
            if any(k in l for k in ["Thane", "Ahmedabad", "Vasai", "Kolshet", "Rajivnagar", "Lodha", "Ambawadi", "Terminal"]):
                if len(pickups) == 0:
                    pickups.append(l)
                elif len(drops) == 0 and l != pickups[0]:
                    drops.append(l)
                    
        p_str = pickups[0][:50] if pickups else "Pickup location"
        d_str = drops[0][:50] if drops else "Drop location"
        data["remarks"] = f"{p_str} to {d_str}"
        
        # Amount
        price_match = re.search(r'Selected Price\s*[\r\n]+\s*(?:Rs\.?|₹)?\s*(\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if not price_match:
            price_match = re.search(r'(?:Total Fare|Suggested Fare|₹|Rs\.?)\s*(\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if price_match:
            data["amount"] = price_match.group(1)
            
        # Date
        # e.g. Aug 18th 2026 or 26 Oct 2026 or 07/08/26
        dt_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\s+(\d{4})', text)
        if dt_match:
            day, month_str, year = dt_match.groups()
            try:
                dt_obj = datetime.datetime.strptime(f"{day} {month_str[:3]} {year}", "%d %b %Y")
                data["date"] = dt_obj.strftime("%d-%b-%Y")
            except Exception:
                pass
                
    # Check for Uber
    elif "Uber" in text or "Thanks for riding" in text:
        data["detected_service"] = "Uber"
        data["category"] = "uber"
        data["exp_type_id"] = "3276C4FD-9830-44D7-972F-1417730FCACE"  # Other
        
        # Amount
        amt_match = re.search(r'Total\s*[\r\n]+\s*(?:Rs\.?|₹|\?)?\s*(\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if amt_match:
            data["amount"] = amt_match.group(1)
            
        # Date e.g. 25 Aug 2026 or 7 Aug 2026
        dt_match = re.search(r'(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})', text)
        if dt_match:
            day, month_str, year = dt_match.groups()
            try:
                dt_obj = datetime.datetime.strptime(f"{day} {month_str[:3]} {year}", "%d %b %Y")
                data["date"] = dt_obj.strftime("%d-%b-%Y")
            except Exception:
                pass
                
        # Remarks
        if "Bassein" in text or "Vasai" in text:
            data["remarks"] = "Vasai West (Bassein Bank) to Lodha Business District Thane West - Returning from Bassein Bank visit booked by Rohan with me (Uber)"
        else:
            data["remarks"] = "Uber cab travel for office visit"
            
    # Check for Food / Restaurant
    elif any(k in text.lower() for k in ["kitchen", "restaurant", "dine in", "food", "veg", "chicken", "biryani", "gstin"]):
        data["detected_service"] = "Food"
        data["category"] = "lunch"
        data["exp_type_id"] = "6C169177-1E95-45D3-B65D-82463469BDA4"  # Lunch
        
        # Grand total
        amt_match = re.search(r'(?:Grand Total|Total|Sub Total|Net Amount)\s*[:₹\s]*\s*(\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if amt_match:
            data["amount"] = amt_match.group(1)
            
        # Date e.g. 07/08/26 or 07-08-2026
        dt_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', text)
        if dt_match:
            d, m, y = dt_match.groups()
            if len(y) == 2:
                y = "20" + y
            try:
                dt_obj = datetime.datetime(int(y), int(m), int(d))
                data["date"] = dt_obj.strftime("%d-%b-%Y")
            except Exception:
                pass
                
        data["remarks"] = "Lunch / food expenses during bank client visit"

    return data


# --- Routes ---

@app.route('/')
def index():
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    host_url = request.host_url.rstrip('/')
    public_url = PUBLIC_TUNNEL_URL or (host_url if 'localhost' not in host_url and '127.0.0.1' not in host_url else None)
    return render_template(
        'index.html',
        local_ip=local_ip,
        port=port,
        public_url=public_url,
        companies=COMPANIES,
        expense_types=EXPENSE_TYPES
    )

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/info')
def api_info():
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    host_url = request.host_url.rstrip('/')
    public_url = PUBLIC_TUNNEL_URL or (host_url if 'localhost' not in host_url and '127.0.0.1' not in host_url else None)
    mobile_url = f"http://{local_ip}:{port}"
    active_url = public_url if public_url else mobile_url
    return jsonify({
        "status": "online",
        "local_ip": local_ip,
        "port": port,
        "mobile_url": mobile_url,
        "public_url": public_url,
        "active_url": active_url,
        "portal_user": PORTAL_USER,
        "portal_url": EMS_BASE_URL
    })

@app.route('/api/upload-parse', methods=['POST'])
def api_upload_parse():
    if 'receipt' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
        
    file = request.files['receipt']
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
    timestamp = int(time.time())
    dest_name = f"{timestamp}_{safe_name}"
    dest_path = os.path.join(UPLOAD_FOLDER, dest_name)
    file.save(dest_path)
    
    try:
        jpg_name, jpg_path, extracted_text = process_upload_file(dest_path)
        parsed = parse_receipt_text(extracted_text, filename=file.filename)
        
        return jsonify({
            "success": True,
            "filename": jpg_name,
            "preview_url": f"/uploads/{jpg_name}",
            "parsed": parsed,
            "extracted_text_preview": extracted_text[:300] if extracted_text else ""
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to process receipt: {str(e)}"}), 500

@app.route('/api/submit-portal', methods=['POST'])
def api_submit_portal():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON body"}), 400
        
    filename = data.get("filename")
    date_str = data.get("date")  # DD-MMM-YYYY
    amount = str(data.get("amount", "")).strip()
    com_id = data.get("company_id", DEFAULT_COMPANY_ID)
    exp_type_id = data.get("exp_type_id", "3276C4FD-9830-44D7-972F-1417730FCACE")
    note = (data.get("remarks") or "")[:245]
    
    if not filename or not date_str or not amount:
        return jsonify({"success": False, "error": "Date, Amount, and Receipt file are required."}), 400
        
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": f"File {filename} not found on server."}), 404
        
    try:
        # Step 1: Login
        session = get_authenticated_session()
        
        # Step 2: Fetch AddExpense.aspx tokens
        add_get = session.get(EMS_ADD_URL, timeout=10)
        vs = re.search(r'name="__VIEWSTATE" id="__VIEWSTATE" value="([^"]+)"', add_get.text).group(1)
        gen = (re.search(r'name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="([^"]+)"', add_get.text) or ["", ""])[1]
        ev = (re.search(r'name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="([^"]+)"', add_get.text) or ["", ""])[1]
        
        # Step 3: Prepare multipart upload
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
            
        files = {
            'ctl00$ContentPlaceHolder1$fuImg': (filename, file_bytes, 'image/jpeg')
        }
        
        form_data = {
            '__VIEWSTATE': vs,
            '__VIEWSTATEGENERATOR': gen,
            '__EVENTVALIDATION': ev,
            'ctl00$ContentPlaceHolder1$hdnExpID': '',
            'ctl00$ContentPlaceHolder1$ddlComName': com_id,
            'ctl00$ContentPlaceHolder1$ddlExpType': exp_type_id,
            'ctl00$ContentPlaceHolder1$txtDate': date_str,
            'ctl00$ContentPlaceHolder1$txtAmt': amount,
            'ctl00$ContentPlaceHolder1$ddlCurrency': 'INR',
            'ctl00$ContentPlaceHolder1$txtNote': note,
            'ctl00$ContentPlaceHolder1$btnSubmit': 'Submit',
            'ctl00$hdnChangeComId': '',
            'ctl00$hdnChangeExpId': '',
            'ctl00$HiddenField1': '',
            'ctl00$txtNewPass': '',
            'ctl00$txtConPass': ''
        }
        
        post_res = session.post(EMS_ADD_URL, data=form_data, files=files, allow_redirects=False, timeout=15)
        
        time.sleep(1)
        
        # Step 4: Verification
        home_res = session.get(EMS_HOME_URL, timeout=10)
        verified = (date_str in home_res.text and amount in home_res.text)
        
        return jsonify({
            "success": True,
            "message": "Expense successfully uploaded to EMS portal!",
            "details": {
                "date": date_str,
                "amount": f"₹{amount}",
                "remarks": note,
                "verified_on_portal": verified,
                "status": "In Process"
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Portal error: {str(e)}"}), 500

@app.route('/api/portal-expenses')
def api_portal_expenses():
    try:
        session = get_authenticated_session()
        home_res = session.get(EMS_HOME_URL, timeout=10)
        
        table_match = re.search(r'<table[^>]+id="[^"]*grdExp"[^>]*>([\s\S]*?)</table>', home_res.text, re.IGNORECASE)
        if not table_match:
            return jsonify({"success": True, "expenses": [], "total_count": 0})
            
        rows = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', table_match.group(1), re.IGNORECASE)
        expenses = []
        for r in rows[1:]:
            if 'Page$' in r:
                continue
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>([\s\S]*?)</td>', r, re.IGNORECASE)]
            if len(cells) >= 7:
                expenses.append({
                    "upload_date": cells[0],
                    "company": cells[1],
                    "date": cells[2],
                    "type": cells[3],
                    "amount": cells[4],
                    "note": cells[5],
                    "status": cells[6]
                })
                
        return jsonify({
            "success": True,
            "expenses": expenses,
            "total_count": len(expenses)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    local_ip = get_local_ip()
    
    # Start Cloudflare Tunnel in background if binary exists
    start_cloudflare_tunnel(port)
    
    print("=" * 60)
    print("EXPENSE PORTAL MOBILE APP SERVER STARTED")
    print(f"Desktop URL      : http://localhost:{port}")
    print(f"Local Wi-Fi URL  : http://{local_ip}:{port}")
    print("Starting Cloudflare Tunnel for worldwide HTTPS access...")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
