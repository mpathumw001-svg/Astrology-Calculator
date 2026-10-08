from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from datetime import datetime, timedelta

app = FastAPI()

# Nakshatra Names & Lords (Vimshottari Dasha Order)
NAKSHATRAS = [
    ("අස්විද", "Ketu", 7), ("බෙරණ", "Venus", 20), ("කැති", "Sun", 6),
    ("රෙහෙණ", "Moon", 10), ("මුවසිරස", "Mars", 7), ("අද", "Rahu", 18),
    ("පුනාවස", "Jupiter", 16), ("පුෂ", "Saturn", 19), ("අස්ලිස", "Mercury", 17),
    ("මා", "Ketu", 7), ("පුවපල්", "Venus", 20), ("උත්තරපල්", "Sun", 6),
    ("හත", "Moon", 10), ("සිත", "Mars", 7), ("සා", "Rahu", 18),
    ("විසා", "Jupiter", 16), ("අනුර", "Saturn", 19), ("දෙට", "Mercury", 17),
    ("මුල", "Ketu", 7), ("පුවසල", "Venus", 20), ("උත්තරසල", "Sun", 6),
    ("සැවණ", "Moon", 10), ("දෙනට", "Mars", 7), ("සියාවස", "Rahu", 18),
    ("පුවපුටුප", "Jupiter", 16), ("උත්තරපුටුප", "Saturn", 19), ("රේවතී", "Mercury", 17)
]

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

def get_dasha_info(moon_lon, birth_date_str):
    # 1 Nakshatra = 13.333333 degrees (13° 20')
    nak_index = int(moon_lon / 13.333333333333334)
    nak_name, lord, total_years = NAKSHATRAS[nak_index]
    
    # Calculate balance of dasha
    deg_in_nak = moon_lon % 13.333333333333334
    fraction_passed = deg_in_nak / 13.333333333333334
    years_remaining = total_years * (1 - fraction_passed)
    
    birth_dt = datetime.strptime(birth_date_str, "%Y/%m/%d")
    
    # Build timeline
    timeline = []
    current_date = birth_dt
    
    # First Dasha (Balance)
    end_date = current_date + timedelta(days=years_remaining * 365.25)
    timeline.append(f"<b>{lord} මහ දශාව (ශේෂය):</b> {current_date.strftime('%Y-%m-%d')} සිට {end_date.strftime('%Y-%m-%d')} දක්වා")
    current_date = end_date
    
    # Subsequent Dashas
    start_lord_idx = DASHA_ORDER.index(lord)
    for i in range(1, 9):
        next_lord = DASHA_ORDER[(start_lord_idx + i) % 9]
        dur = DASHA_YEARS[next_lord]
        end_date = current_date + timedelta(days=dur * 365.25)
        timeline.append(f"<b>{next_lord} මහ දශාව:</b> {current_date.strftime('%Y-%m-%d')} සිට {end_date.strftime('%Y-%m-%d')} දක්වා")
        current_date = end_date
        
    return nak_name, lord, years_remaining, timeline

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="si">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Astrology Engine</title>
        <style>
            body { font-family: sans-serif; background: #0f172a; color: #fff; padding: 20px; display: flex; justify-content: center; }
            .box { background: #1e293b; padding: 25px; border-radius: 12px; width: 100%; max-width: 480px; border: 1px solid #334155; }
            h2 { color: #38bdf8; text-align: center; margin-top: 0; }
            label { display: block; margin-top: 10px; color: #94a3b8; font-size: 14px; }
            input { width: 100%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
            button { width: 100%; margin-top: 20px; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
            button:hover { background: #0369a1; }
            #res { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 6px; border-left: 4px solid #38bdf8; display: none; }
            .timeline { font-size: 13px; line-height: 1.6; margin-top: 10px; color: #cbd5e1; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>ජ්‍යොතිෂ & දශා Calculator</h2>
            <label>උපන් දිනය (YYYY/MM/DD):</label>
            <input type="text" id="dt" value="1989/11/06">
            
            <label>උපන් වේලාව (HH:MM):</label>
            <input type="text" id="tm" value="07:42">
            
            <label>Latitude (අක්ෂාංශය):</label>
            <input type="text" id="lt" value="6.74">
            
            <label>Longitude (දේශාංශය):</label>
            <input type="text" id="ln" value="81.47">
            
            <button onclick="calc()">ගණනය කරන්න</button>

            <div id="res">
                <p>සඳු රාශිය: <b id="mSign" style="color:#38bdf8"></b></p>
                <p>උපන් නැකත: <b id="nak" style="color:#38bdf8"></b></p>
                <p>උපතේදී මහ දශාව: <b id="dLord" style="color:#38bdf8"></b></p>
                <p>දශා ශේෂය: <b id="dBal" style="color:#38bdf8"></b> වසර</p>
                <hr style="border-color:#334155;">
                <h4>මහ දශා කාලසීමාවන්:</h4>
                <div id="tline" class="timeline"></div>
            </div>
        </div>

        <script>
            async function calc() {
                const dt = document.getElementById('dt').value;
                const tm = document.getElementById('tm').value;
                const lt = document.getElementById('lt').value;
                const ln = document.getElementById('ln').value;

                try {
                    const r = await fetch(`/calculate?date=${encodeURIComponent(dt)}&time=${encodeURIComponent(tm)}&lat=${lt}&lon=${ln}`);
                    const d = await r.json();

                    if(d.moon_sign) {
                        document.getElementById('mSign').innerText = d.moon_sign;
                        document.getElementById('nak').innerText = d.nakshatra;
                        document.getElementById('dLord').innerText = d.dasha_lord;
                        document.getElementById('dBal').innerText = Number(d.balance_years).toFixed(2);
                        
                        let html = '';
                        d.timeline.forEach(item => {
                            html += `<div>• ${item}</div>`;
                        });
                        document.getElementById('tline').innerHTML = html;
                        
                        document.getElementById('res').style.display = 'block';
                    } else {
                        alert('Error: ' + (d.error || 'ගණනය කිරීමේ දෝෂයක් ඇත!'));
                    }
                } catch(e) {
                    alert('Error Connecting to Server!');
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/calculate")
def calculate(date: str, time: str, lat: float, lon: float):
    try:
        formatted_date = date.replace("-", "/")
        dt = Datetime(formatted_date, time, '+05:30')
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)
        
        moon = chart.get(const.MOON)
        sun = chart.get(const.SUN)
        
        nak_name, lord, years_rem, timeline = get_dasha_info(moon.lon, formatted_date)
        
        return {
            "moon_sign": moon.sign,
            "moon_lon": moon.lon,
            "sun_sign": sun.sign,
            "nakshatra": nak_name,
            "dasha_lord": lord,
            "balance_years": years_rem,
            "timeline": timeline
        }
    except Exception as e:
        return {"error": str(e)}
