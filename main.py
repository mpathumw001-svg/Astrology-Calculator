from fastapi import FastAPI
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Astrology Calculation Engine Active"}

@app.get("/calculate")
def calculate(date: str, time: str, lat: float, lon: float):
    # Format: date="YYYY/MM/DD", time="HH:MM"
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
