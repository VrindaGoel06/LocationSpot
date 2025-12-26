import uvicorn
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()
# ================= CONFIGURATION =================
OT_HOST = os.getenv("OT_HOST")
OT_USER = os.getenv("OT_USER")
OT_DEVICE = os.getenv("OT_DEVICE")
CACHE_FILE = os.getenv("CACHE_FILE")    
NTFY_URL = os.getenv("NTFY_URL")
# =================================================

app = FastAPI()

# Load Cache
try:
    with open(CACHE_FILE, 'r') as f:
        aqi_cache = json.load(f)
except FileNotFoundError:
    aqi_cache = {}

def save_cache():
    """Sync save is fine as it happens rarely at end of request"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(aqi_cache, f)

async def run_mask_alert_loop():
    print("--- 😷 Mask Alert System Started ---")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # 1. Get MOST RECENT location
                # We ask for "last" API from OwnTracks
                ot_url = f"{OT_HOST}/api/0/last"
                async with session.get(ot_url) as resp:
                    data = await resp.json()
                
                # OwnTracks 'last' usually returns a list or a single dict depending on version
                # We handle list format:
                if isinstance(data, list):
                    # Filter for our specific user/device
                    target = next((x for x in data if x['username'] == OT_USER and x['device'] == OT_DEVICE), None)
                else:
                    target = data

                if target:
                    lat, lon, tst = target['lat'], target['lon'], target['tst']
                    
                    # 2. Check AQI
                    # (Re-using your existing function)
                    pm25 = await get_aqi_data(session, lat, lon, tst)

                    if pm25 and pm25 > 100:
                        print(f"⚠️ High Pollution Detected: {pm25}")
                        
                        # 3. Send Notification to ntfy
                        msg = f"Mask Up! Current PM2.5 is {pm25} at your location."
                        try:
                            # ntfy accepts raw string body as the message
                            async with session.post(NTFY_URL, data=msg) as ntfy_resp:
                                print("   -> Ntfy sent status:", ntfy_resp.status)
                        except Exception as e:
                            print("   -> Ntfy failed:", e)
                    else:
                        print(f"✅ Air Safe (PM2.5: {pm25})")

            except Exception as e:
                print(f"Alert Loop Error: {e}")

            # Wait 15 minutes before checking again to avoid spam
            await asyncio.sleep(900)
async def fetch_open_meteo(session, lat, lon, date_str):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat, "longitude": lon, "hourly": "pm2_5",
        "start_date": date_str, "end_date": date_str, "timezone": "auto"
    }
    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200: return await resp.json()
    except Exception: pass
    return None

async def get_aqi_data(session, lat, lon, timestamp):
    dt_obj = datetime.fromtimestamp(timestamp)
    date_str = dt_obj.strftime("%Y-%m-%d")
    hour_index = dt_obj.hour
    key = f"{round(lat, 2)}_{round(lon, 2)}_{date_str}"

    if key in aqi_cache:
        try: return aqi_cache[key][hour_index]
        except: return None

    data = await fetch_open_meteo(session, lat, lon, date_str)
    if data and "hourly" in data and "pm2_5" in data["hourly"]:
        aqi_cache[key] = data["hourly"]["pm2_5"]
        return aqi_cache[key][hour_index]
    return None

@app.get("/api/tracks")
async def get_tracks(hours: int = 24):
    now = datetime.now()
    past = now - timedelta(hours=hours)
    
    # Fetch OwnTracks
    async with aiohttp.ClientSession() as session:
        try:
            ot_url = f"{OT_HOST}/api/0/locations?user={OT_USER}&device={OT_DEVICE}&from={past.strftime('%Y-%m-%dT%H:%M')}&to={now.strftime('%Y-%m-%dT%H:%M')}"
            async with session.get(ot_url) as resp:
                ot_res = await resp.json()
        except Exception: return []
        ot_res = ot_res['data']

        if not isinstance(ot_res, list): return []

        processed = []
        # Sort by time just in case
        ot_res.sort(key=lambda x: x['tst'])

        # Process points (Take all points for smooth animation, don't skip)
        points_to_process = [p for p in ot_res if p.get('acc', 0) <= 200]
        
        for loc in points_to_process:
            lat, lon, tst = loc['lat'], loc['lon'], loc['tst']
            pm25 = await get_aqi_data(session, lat, lon, tst)
            
            # Allow None, we can interpolate/hold previous value in frontend
            processed.append({
                "lat": lat,
                "lon": lon,
                "tst": tst, # Keep generic timestamp for JS math
                "time_str": datetime.fromtimestamp(tst).strftime("%H:%M"),
                "pm2_5": pm25 if pm25 is not None else 0
            })

    save_cache()
    return processed

# --- FRONTEND (Animated Map) ---
@app.get("/", response_class=HTMLResponse)
async def serve_map():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delhi AQI Replay</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.motion/dist/leaflet.motion.min.js"></script>
        <style>
            body { margin: 0; padding: 0; background: #1a1a1a; font-family: 'Segoe UI', sans-serif; color: #ddd; }
            #map { height: 100vh; width: 100%; }
            
            #controls { 
                position: absolute; top: 10px; right: 10px; z-index: 1000; 
                background: rgba(30, 30, 30, 0.9); padding: 20px; 
                border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
                width: 250px; backdrop-filter: blur(5px);
            }
            
            .info-row { margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;}
            h2 { margin: 0 0 5px 0; font-size: 18px; color: #fff;}
            .big-stat { font-size: 32px; font-weight: bold; color: #fff; }
            .sub-stat { font-size: 14px; color: #aaa; }
            
            #time-display { font-family: monospace; font-size: 16px; color: #00e400; }
            
            button {
                width: 100%; padding: 10px; border: none; border-radius: 6px;
                background: #007bff; color: white; font-weight: bold; cursor: pointer;
                transition: background 0.2s;
            }
            button:hover { background: #0056b3; }
            button:disabled { background: #555; cursor: not-allowed; }

            .legend { background: rgba(30,30,30,0.8); padding: 10px; position: absolute; bottom: 20px; left: 20px; z-index: 1000; border-radius: 4px; font-size: 12px;}
            .dot { height: 10px; width: 10px; display: inline-block; border-radius: 50%; margin-right: 5px; }

            /* Dynamic Ring around the tracker */
            .pulse-ring {
                border: 3px solid rgba(255, 255, 255, 0.8);
                border-radius: 50%;
                height: 100%; width: 100%;
                animation: pulsate 1s ease-out;
                animation-iteration-count: infinite; 
            }
            @keyframes pulsate {
                0% { transform: scale(0.1, 0.1); opacity: 0.0; }
                50% { opacity: 1.0; }
                100% { transform: scale(1.2, 1.2); opacity: 0.0; }
            }
        </style>
    </head>
    <body>
        <div id="controls">
            <h2>Delhi Activity Replay</h2>
            <div class="info-row">
                <div>
                    <div id="aqi-val" class="big-stat">--</div>
                    <div class="sub-stat">PM 2.5 µg/m³</div>
                </div>
                <div style="text-align:right">
                    <div id="time-display">--:--</div>
                    <div class="sub-stat">Time</div>
                </div>
            </div>
            
            <div id="progress-container" style="background:#444; height:4px; margin-bottom:15px; border-radius:2px;">
                <div id="progress-bar" style="background:#007bff; height:100%; width:0%;"></div>
            </div>

            <button id="playBtn" onclick="togglePlay()">Loading Data...</button>
        </div>
        
        <div id="map"></div>
        
        <div class="legend">
            <b>PM 2.5 Levels</b><br>
            <span class="dot" style="background: #00e400;"></span> 0-30 Good<br>
            <span class="dot" style="background: #ffff00;"></span> 30-60 Sat.<br>
            <span class="dot" style="background: #ff7e00;"></span> 60-90 Mod.<br>
            <span class="dot" style="background: #ff0000;"></span> 90-120 Poor<br>
            <span class="dot" style="background: #99004c;"></span> 120-250 V.Poor<br>
            <span class="dot" style="background: #7e0023;"></span> 250+ Severe
        </div>

        <script>
            // === MAP SETUP ===
            var map = L.map('map').setView([28.6139, 77.2090], 12);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

            // Global State
            var points = [];
            var currentIndex = 0;
            var isPlaying = false;
            var animationSpeed = 1000; // ms per point
            var marker = null;
            var pathLine = null;
            var polylinePoints = [];

            // === COLORS ===
            function getDelhiColor(pm25) {
                if (pm25 >= 250) return '#7e0023'; 
                if (pm25 >= 120) return '#99004c'; 
                if (pm25 >= 90)  return '#ff0000';  
                if (pm25 >= 60)  return '#ff7e00';  
                if (pm25 >= 30)  return '#ffff00';  
                return '#00e400';                 
            }

            // === DATA FETCH ===
            fetch('/api/tracks?hours=24')
                .then(res => res.json())
                .then(data => {
                    points = data;
                    document.getElementById('playBtn').innerText = "▶ PLAY REPLAY";
                    
                    if(points.length > 0) {
                        // Set map start view
                        map.setView([points[0].lat, points[0].lon], 13);
                        updateStats(0);
                    }
                });

            // === ANIMATION LOOP ===
            function togglePlay() {
                if (points.length === 0) return;
                
                if (isPlaying) {
                    isPlaying = false;
                    document.getElementById('playBtn').innerText = "▶ RESUME";
                } else {
                    isPlaying = true;
                    document.getElementById('playBtn').innerText = "⏸ PAUSE";
                    
                    // Reset if finished
                    if (currentIndex >= points.length - 1) {
                        currentIndex = 0;
                        if(pathLine) map.removeLayer(pathLine); 
                        polylinePoints = [];
                    }
                    animate();
                }
            }

            function animate() {
                if (!isPlaying || currentIndex >= points.length) {
                    if (currentIndex >= points.length) {
                        isPlaying = false;
                        document.getElementById('playBtn').innerText = "↺ REPLAY";
                    }
                    return;
                }

                var p = points[currentIndex];
                var color = getDelhiColor(p.pm2_5);

                // 1. Move/Create Marker
                if (!marker) {
                    marker = L.circleMarker([p.lat, p.lon], {
                        radius: 8, fillColor: color, color: "#fff", weight: 2, fillOpacity: 1
                    }).addTo(map);
                } else {
                    marker.setLatLng([p.lat, p.lon]);
                    marker.setStyle({ fillColor: color });
                }

                // 2. Draw Trail (History)
                // We add segments individually to color them differently
                if (currentIndex > 0) {
                    var prev = points[currentIndex - 1];
                    L.polyline([[prev.lat, prev.lon], [p.lat, p.lon]], {
                        color: getDelhiColor(prev.pm2_5), // Color line by previous point's AQI
                        weight: 4,
                        opacity: 0.7
                    }).addTo(map);
                }

                // 3. Update UI Stats
                updateStats(currentIndex);

                // 4. Pan map if marker leaves bounds
                if (!map.getBounds().contains([p.lat, p.lon])) {
                    map.panTo([p.lat, p.lon]);
                }

                // Next Frame
                currentIndex++;
                
                // Smart Speed Control: 
                // If the next point is far away in time, speed up. If close, slow down.
                setTimeout(animate, animationSpeed);
            }

            function updateStats(index) {
                var p = points[index];
                var color = getDelhiColor(p.pm2_5);
                
                document.getElementById('aqi-val').innerText = Math.round(p.pm2_5);
                document.getElementById('aqi-val').style.color = color;
                
                document.getElementById('time-display').innerText = p.time_str;
                document.getElementById('time-display').style.color = color;
                
                var percent = (index / points.length) * 100;
                document.getElementById('progress-bar').style.width = percent + "%";
                document.getElementById('progress-bar').style.background = color;
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(run_mask_alert_loop())
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    