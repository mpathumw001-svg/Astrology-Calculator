from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from flatlib import ayanamsa
from datetime import datetime, timedelta

app = FastAPI()

# Set Sidereal / Lahiri Ayanamsa for Vedic Astrology
ayanamsa.setMode(const.AYANAMSA_LAHIRI)

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

def calculate_antardashas(major_lord, start_dt, dasha_duration_years):
    antardashas = []
    curr_dt = start_dt
    start_idx = DASHA_ORDER.index(major_lord)
    
    for i in range(9):
        sub_lord = DASHA_ORDER[(start_idx + i) % 9]
        sub_years = (DASHA_YEARS[major_lord] * DASHA_YEARS[sub_lord]) / 120.0
        actual_sub_years = sub_years * (dasha_duration_years / DASHA_YEARS[major_lord])
        
        end_dt = curr_dt + timedelta(days=actual_sub_years * 365.2422)
        antardashas.append({
            "sub_lord": sub_lord,
            "start": curr_dt.strftime('%Y-%m-%d'),
            "end": end_dt.strftime('%Y-%m-%d')
        })
        curr_dt = end_dt
        
    return antardashas

def get_dasha_info(sidereal_moon_lon, birth_date_str):
    nak_index = int(sidereal_moon_lon / 13.333333333333334)
    nak_index = min(nak_index, 26)
    nak_name, lord, total_years = NAKSHATRAS[nak_index]
    
    deg_in_nak = sidereal_moon_lon % 13.333333333333334
    fraction_passed = deg_in_nak / 13.333333333333334
    years_remaining = total_years * (1 - fraction_passed)
    
    birth_dt = datetime.strptime(birth_date_str, "%Y/%m/%d")
    
    timeline = []
    current_date = birth_dt
    
    end_date = current_date + timedelta(days=years_remaining * 365.2422)
    subs = calculate_antardashas(lord, current_date, years_remaining)
    timeline.append({
        "major_lord": f"{lord} (ශේෂය)",
        "start": current_date.strftime('%Y-%m-%d'),
        "end": end_date.strftime('%Y-%m-%d'),
        "sub_dashas": subs
    })
    current_date = end_date
    
    start_lord_idx = DASHA_ORDER.index(lord)
    for i in range(1, 9):
        next_lord = DASHA_ORDER[(start_lord_idx + i) % 9]
        dur = DASHA_YEARS[next_lord]
        end_date = current_date + timedelta(days=dur * 365.2422)
        subs = calculate_antardashas(next_lord, current_date, dur)
        timeline.append({
            "major_lord": next_lord,
            "start": current_date.strftime('%Y-%m-%d'),
            "end": end_date.strftime('%Y-%m-%d'),
            "sub_dashas": subs
        })
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
        <title>Vedic Astrology Engine</title>
        <style>
            body { font-family: sans-serif; background: #0f172a; color: #fff; padding: 20px; display: flex; justify-content: center; }
            .box { background: #1e293b; padding: 25px; border-radius: 12px; width: 100%; max-width: 550px; border: 1px solid #334155; }
            h2 { color: #38bdf8; text-align: center; margin-top: 0; }
            label { display: block; margin-top: 10px; color: #94a3b8; font-size: 14px; }
            input, select { width: 100%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
            button { width: 100%; margin-top: 20px; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
            button:hover { background: #0369a1; }
            #res { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 6px; border-left: 4px solid #38bdf8; display: none; }
            details { margin-bottom: 8px; background: #1e293b; padding: 8px; border-radius: 6px; }
            summary { cursor: pointer; font-weight: bold; color: #38bdf8; }
            .sub-list { margin-top: 8px; padding-left: 15px; font-size: 13px; color: #cbd5e1; }
            .sub-item { margin-bottom: 4px; }
            .row { display: flex; gap: 10px; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>වෛදික ජ්‍යොතිෂ & දශා Calculator</h2>
            <label>උපන් දිනය (YYYY/MM/DD):</label>
            <input type="text" id="dt" value="1989/11/06">
            
            <label>උපන් වේලාව (HH:MM):</label>
            <input type="text" id="tm" value="07:42">
            
            <label>දිස්ත්‍රික්කය තෝරන්න:</label>
            <select id="district" onchange="updateCoords()">
                <option value="6.9271,79.8612">කොළඹ (Colombo)</option>
                <option value="7.0840,79.9925">ගම්පහ (Gampaha)</option>
                <option value="6.5854,79.9607">කළුතර (Kalutara)</option>
                <option value="7.2906,80.6337">මහනුවර (Kandy)</option>
                <option value="7.4675,80.6234">මාතලේ (Matale)</option>
                <option value="6.8935,80.5027">නුවරඑළිය (Nuwara Eliya)</option>
                <option value="6.0535,80.2210">ගාල්ල (Galle)</option>
                <option value="5.9485,80.5353">මාතර (Matara)</option>
                <option value="6.1246,81.1185">හම්බන්තොට (Hambantota)</option>
                <option value="9.6615,80.0255">යාපනය (Jaffna)</option>
                <option value="9.3803,80.3770">කිලිනොච්චිය (Kilinochchi)</option>
                <option value="8.8855,80.4982">මන්නාරම (Mannar)</option>
                <option value="8.7542,80.4982">වවුනියාව (Vavuniya)</option>
                <option value="9.2671,80.8142">මුලතිව් (Mullaitivu)</option>
                <option value="7.7170,81.7000">මඩකලපුව (Batticaloa)</option>
                <option value="8.5874,81.2152">ත්‍රිකුණාමලය (Trincomalee)</option>
                <option value="7.2820,81.6738">අම්පාර (Ampara)</option>
                <option value="7.4863,80.3623">කුරුණෑගල (Kurunegala)</option>
                <option value="8.0362,79.8283">පුත්තලම (Puttalam)</option>
                <option value="8.3114,80.4037">අනුරාධපුරය (Anuradhapura)</option>
                <option value="7.9403,81.0188">පොළොන්නරුව (Polonnaruwa)</option>
                <option value="6.9934,81.0550">බදුල්ල (Badulla)</option>
                <option value="6.8720,81.3510" selected>මොණරාගල (Monaragala)</option>
                <option value="6.6828,80.3992">රත්නපුරය (Ratnapura)</option>
                <option value="7.2513,80.3464">කෑගල්ල (Kegalle)</option>
                <option value="custom">වෙනත් නගරයක් Search කරන්න...</option>
            </select>

            <div id="searchBox" style="display:none;">
                <label>නගරය/ගම Type කරන්න:</label>
                <div class="row">
                    <input type="text" id="placeName" placeholder="Enter city name">
                    <button type="button" style="width: 30%; margin-top:5px;" onclick="searchLocation()">Search</button>
                </div>
            </div>

            <input type="hidden" id="lt" value="6.8720">
            <input type="hidden" id="ln" value="81.3510">
            
            <button onclick="calc()">ගණනය කරන්න</button>

            <div id="res">
                <p>සඳු රාශිය (Nirayana/Sidereal): <b id="mSign" style="color:#38bdf8"></b></p>
                <p>උපන් නැකත: <b id="nak" style="color:#38bdf8"></b></p>
                <p>උපතේදී මහ දශාව: <b id="dLord" style="color:#38bdf8"></b></p>
                <p>දශා ශේෂය: <b id="dBal" style="color:#38bdf8"></b> වසර</p>
                <hr style="border-color:#334155;">
                <h4>මහ දශා සහ අන්තර දශාවන්:</h4>
                <div id="tline"></div>
            </div>
        </div>

        <script>
            function updateCoords() {
                const val = document.getElementById('district').value;
                if(val === 'custom') {
                    document.getElementById('searchBox').style.display = 'block';
                } else {
                    document.getElementById('searchBox').style.display = 'none';
                    const parts = val.split(',');
                    document.getElementById('lt').value = parts[0];
                    document.getElementById('ln').value = parts[1];
                }
            }

            async function searchLocation() {
                const q = document.getElementById('placeName').value;
                if(!q) return alert('කරුණාකර නගරයේ නම ඇතුළත් කරන්න');
                try {
                    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`);
                    const data = await res.json();
                    if(data && data.length > 0) {
                        document.getElementById('lt').value = data[0].lat;
                        document.getElementById('ln').value = data[0].lon;
                        alert(`ස්ථානය සොයාගන්නා ලදී: ${data[0].display_name}`);
                    } else {
                        alert('ස්ථානය සොයාගත නොහැකි විය.');
                    }
                } catch(e) { alert('Location Search Error!'); }
            }

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
                            html += `<details>`;
                            html += `<summary>${item.major_lord} මහ දශාව: ${item.start} සිට ${item.end}</summary>`;
                            html += `<div class="sub-list">`;
                            item.sub_dashas.forEach(sub => {
                                html += `<div class="sub-item">• <b>${sub.sub_lord} අන්තරය:</b> ${sub.start} සිට ${sub.end}</div>`;
                            });
                            html += `</div></details>`;
                        });
                        document.getElementById('tline').innerHTML = html;
                        
                        document.getElementById('res').style.display = 'block';
                    } else { alert('Error: ' + (d.error || 'ගණනය කිරීමේ දෝෂයක් ඇත!')); }
                } catch(e) { alert('Error Connecting to Server!'); }
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
        chart = Chart(dt, pos, mode=const.AYANAMSA_LAHIRI)
        
        moon = chart.get(const.MOON)
        
        # Calculate Sidereal Longitude using Lahiri Ayanamsa
        ay_val = ayanamsa.get(dt, const.AYANAMSA_LAHIRI)
        sidereal_moon_lon = (moon.lon - ay_val) % 360
        
        nak_name, lord, years_rem, timeline = get_dasha_info(sidereal_moon_lon, formatted_date)
        
        return {
            "moon_sign": moon.sign,
            "sidereal_moon_lon": sidereal_moon_lon,
            "nakshatra": nak_name,
            "dasha_lord": lord,
            "balance_years": years_rem,
            "timeline": timeline
        }
    except Exception as e:
        return {"error": str(e)}
