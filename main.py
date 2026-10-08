from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="si">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Astrology Calculator Engine</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .card { background-color: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%; max-width: 450px; border: 1px solid #334155; }
            h2 { text-align: center; color: #38bdf8; margin-bottom: 24px; }
            label { font-size: 14px; color: #94a3b8; display: block; margin-top: 12px; margin-bottom: 6px; }
            input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #475569; background-color: #0f172a; color: #fff; box-sizing: border-box; font-size: 15px; }
            button { width: 100%; margin-top: 24px; padding: 14px; background-color: #0284c7; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; transition: 0.2s; }
            button:hover { background-color: #0369a1; }
            .result { margin-top: 24px; padding: 16px; background-color: #0f172a; border-radius: 8px; border-left: 4px solid #38bdf8; display: none; }
            .result-item { margin-bottom: 8px; font-size: 15px; }
            .result-item span { color: #38bdf8; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>ජ්‍යොතිෂ ගණක යන්ත්‍රය</h2>
            <form id="astroForm">
                <label>උපන් දිනය (YYYY/MM/DD):</label>
                <input type="text" id="date" value="1989/11/06" required>
                
                <label>උපන් වේලාව (HH:MM - 24 Hours):</label>
                <input type="text" id="time" value="07:42" required>
                
                <label>Latitude (අක්ෂාංශය):</label>
                <input type="text" id="lat" value="6.74" required>
                
                <label>Longitude (දේශාංශය):</label>
                <input type="text" id="lon" value="81.47" required>
                
                <button type="submit">ගණනය කරන්න</button>
            </form>

            <div id="result" class="result">
                <div class="result-item">සඳු සිටින රාශිය: <span id="moonSign"></span></div>
                <div class="result-item">සඳුගේ Exact Longitude: <span id="moonLon"></span>°</div>
                <div class="result-item">රාශියේ අංශක ප්‍රමාණය: <span id="moonDeg"></span>°</div>
                <div class="result-item">හිරු සිටින රාශිය: <span id="sunSign"></span></div>
            </div>
        </div>

        <script>
            document.getElementById('astroForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const date = document.getElementById('date').value;
                const time = document.getElementById('time').value;
                const lat = document.getElementById('lat').value;
                const lon = document.getElementById('lon').value;

                const response = await fetch(`/calculate?date=${date}&time=${time}&lat=${lat}&lon=${lon}`);
                const data = await response.json();

                document.getElementById('moonSign').innerText = data.moon_sign;
                document.getElementById('moonLon').innerText = data.moon_lon.toFixed(2);
                document.getElementById('moonDeg').innerText = data.moon_deg_in_sign.toFixed(2);
                document.getElementById('sunSign').innerText = data.sun_sign;

                document.getElementById('result').style.display = 'block';
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/calculate")
def calculate(date: str, time: str, lat: float, lon: float):
    dt = Datetime(date, time, '+05:30')
    pos = GeoPos(lat, lon)
    chart = Chart(dt, pos, IDs=const.LIST_OBJECTS, sys=const.HOUSES_PLACIDUS)
    
    moon = chart.get(const.MOON)
    sun = chart.get(const.SUN)
    
    return {
        "moon_sign": moon.sign,
        "moon_lon": moon.lon,
        "moon_deg_in_sign": moon.lon % 30,
        "sun_sign": sun.sign,
        "sun_lon": sun.lon
    }
