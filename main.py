from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()

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
            .box { background: #1e293b; padding: 25px; border-radius: 12px; width: 100%; max-width: 400px; border: 1px solid #334155; }
            h2 { color: #38bdf8; text-align: center; margin-top: 0; }
            label { display: block; margin-top: 10px; color: #94a3b8; font-size: 14px; }
            input { width: 100%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
            button { width: 100%; margin-top: 20px; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
            button:hover { background: #0369a1; }
            #res { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 6px; border-left: 4px solid #38bdf8; display: none; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>ජ්‍යොතිෂ Calculator</h2>
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
                <p>සඳු Longitude: <b id="mLon" style="color:#38bdf8"></b>°</p>
                <p>රාශි අංශකය: <b id="mDeg" style="color:#38bdf8"></b>°</p>
                <p>හිරු රාශිය: <b id="sSign" style="color:#38bdf8"></b></p>
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
                        document.getElementById('mLon').innerText = Number(d.moon_lon).toFixed(2);
                        document.getElementById('mDeg').innerText = Number(d.moon_deg_in_sign).toFixed(2);
                        document.getElementById('sSign').innerText = d.sun_sign;
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
        
        # Build chart using default ephemeris
        chart = Chart(dt, pos)
        
        moon = chart.get(const.MOON)
        sun = chart.get(const.SUN)
        
        return {
            "moon_sign": moon.sign,
            "moon_lon": moon.lon,
            "moon_deg_in_sign": moon.lon % 30,
            "sun_sign": sun.sign,
            "sun_lon": sun.lon
        }
    except Exception as e:
        return {"error": str(e)}
