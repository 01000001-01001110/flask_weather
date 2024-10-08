from flask import Flask, jsonify, render_template, redirect, url_for, request
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import json
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

app = Flask(__name__)

# Setup geocoder
geolocator = Nominatim(user_agent="hurricane_tracker_app")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# API configuration
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 29.2858,
    "longitude": -81.0559,
    "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "rain", "showers", "cloud_cover", "pressure_msl", "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
    "hourly": ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature", "precipitation", "rain", "showers", "pressure_msl", "surface_pressure", "cloud_cover", "wind_speed_10m", "wind_speed_80m", "wind_direction_10m", "wind_direction_80m", "wind_gusts_10m", "temperature_80m", "surface_temperature"],
    "temperature_unit": "fahrenheit",
    "wind_speed_unit": "mph",
    "precipitation_unit": "inch",
    "timezone": "America/New_York",
    "forecast_days": 3
}

def fetch_weather_data(latitude, longitude):
    try:
        params["latitude"] = latitude
        params["longitude"] = longitude
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # Process current data
        current = response.Current()
        current_data = {}
        for idx, var in enumerate(params["current"]):
            try:
                current_data[var] = current.Variables(idx).Value()
            except IndexError:
                print(f"Warning: {var} not found in current data")
        
        # Process hourly data
        hourly = response.Hourly()
        hourly_data = {
            "time": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            ).astype(str).tolist()
        }
        for idx, var in enumerate(params["hourly"]):
            try:
                hourly_data[var] = hourly.Variables(idx).ValuesAsNumpy().tolist()
            except IndexError:
                print(f"Warning: {var} not found in hourly data")
        
        # Combine data
        weather_data = {
            "current": current_data,
            "hourly": hourly_data
        }
        
        # Store the data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_data_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(weather_data, f)
        print(f"Data fetched and stored in {filename}")
    except Exception as e:
        print(f"Error fetching data: {str(e)}")

# Schedule the data fetching task
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: fetch_weather_data(params["latitude"], params["longitude"]), trigger="interval", minutes=15)
scheduler.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        location = request.form['location']
        try:
            location_data = geolocator.geocode(location)
            if location_data:
                lat = location_data.latitude
                lng = location_data.longitude
                params["latitude"] = lat
                params["longitude"] = lng
                fetch_weather_data(lat, lng)
                return redirect(url_for('visualize'))
            else:
                error = "Location not found. Please try again."
                return render_template('index.html', error=error)
        except (GeocoderTimedOut, GeocoderUnavailable):
            error = "Geocoding service is currently unavailable. Please try again later."
            return render_template('index.html', error=error)
    health_data = get_health_data()
    return render_template('index.html', health_data=health_data)

@app.route('/latest', methods=['GET'])
def get_latest_data():
    files = [f for f in os.listdir('.') if f.startswith('weather_data_')]
    if not files:
        return jsonify({"error": "No data available"}), 404
    latest_file = max(files)
    with open(latest_file, 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/visualize')
def visualize():
    files = [f for f in os.listdir('.') if f.startswith('weather_data_')]
    if not files:
        return render_template('error.html', message="No weather data available. Please wait for the first data fetch.")
    
    latest_file = max(files)
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    hourly_data = data['hourly']
    current_data = data['current']
    
    # Convert time to datetime objects
    time = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S%z") for t in hourly_data['time']]
    
    # Create a more comprehensive dashboard
    fig = make_subplots(rows=3, cols=2, 
                        subplot_titles=("Temperature & Humidity", "Wind Speed & Gusts", 
                                        "Precipitation", "Pressure",
                                        "Cloud Cover", "Current Conditions"),
                        specs=[[{"secondary_y": True}, {"secondary_y": True}],
                               [{"secondary_y": False}, {"secondary_y": False}],
                               [{"secondary_y": False}, {"type": "table"}]])
    
    # Temperature & Humidity
    if 'temperature_2m' in hourly_data:
        fig.add_trace(go.Scatter(x=time, y=hourly_data['temperature_2m'], name="Temperature"), row=1, col=1)
    if 'relative_humidity_2m' in hourly_data:
        fig.add_trace(go.Scatter(x=time, y=hourly_data['relative_humidity_2m'], name="Humidity"), row=1, col=1, secondary_y=True)
    
    # Wind Speed & Gusts
    if 'wind_speed_10m' in hourly_data:
        fig.add_trace(go.Scatter(x=time, y=hourly_data['wind_speed_10m'], name="Wind Speed"), row=1, col=2)
    if 'wind_gusts_10m' in hourly_data:
        fig.add_trace(go.Scatter(x=time, y=hourly_data['wind_gusts_10m'], name="Wind Gusts"), row=1, col=2, secondary_y=True)
    
    # Precipitation
    if 'precipitation' in hourly_data:
        fig.add_trace(go.Bar(x=time, y=hourly_data['precipitation'], name="Precipitation"), row=2, col=1)
    
    # Pressure
    if 'pressure_msl' in hourly_data:
        fig.add_trace(go.Scatter(x=time, y=hourly_data['pressure_msl'], name="Sea Level Pressure"), row=2, col=2)
    
    # Cloud Cover
    if 'cloud_cover' in hourly_data:
        fig.add_trace(go.Scatter(x=time, y=hourly_data['cloud_cover'], name="Cloud Cover"), row=3, col=1)
    
    # Current Conditions Table
    current_conditions = go.Table(
        header=dict(values=["Parameter", "Value"]),
        cells=dict(values=[
            ["Temperature", "Humidity", "Wind Speed", "Wind Direction", "Precipitation", "Pressure"],
            [f"{current_data.get('temperature_2m', 'N/A')}°F", 
             f"{current_data.get('relative_humidity_2m', 'N/A')}%", 
             f"{current_data.get('wind_speed_10m', 'N/A')} mph", 
             f"{current_data.get('wind_direction_10m', 'N/A')}°", 
             f"{current_data.get('precipitation', 'N/A')} in", 
             f"{current_data.get('pressure_msl', 'N/A')} hPa"]
        ])
    )
    fig.add_trace(current_conditions, row=3, col=2)
    
    # Update layout
    fig.update_layout(height=1200, width=1000, title_text="Weather Dashboard")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Temperature (°F)", secondary_y=False, row=1, col=1)
    fig.update_yaxes(title_text="Humidity (%)", secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text="Wind Speed (mph)", secondary_y=False, row=1, col=2)
    fig.update_yaxes(title_text="Wind Gusts (mph)", secondary_y=True, row=1, col=2)
    fig.update_yaxes(title_text="Precipitation (in)", row=2, col=1)
    fig.update_yaxes(title_text="Pressure (hPa)", row=2, col=2)
    fig.update_yaxes(title_text="Cloud Cover (%)", row=3, col=1)
    
    # Convert the plot to JSON for rendering in the template
    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('visualize.html', plot_json=plot_json)

def get_health_data():
    files = [f for f in os.listdir('.') if f.startswith('weather_data_')]
    if files:
        latest_file = max(files)
        last_update = datetime.fromtimestamp(os.path.getmtime(latest_file))
        time_since_update = datetime.now() - last_update
        status = "healthy" if time_since_update.total_seconds() < 1800 else "stale"
    else:
        status = "no data"
        last_update = None
    return {
        "status": status,
        "last_update": last_update.isoformat() if last_update else None,
        "data_files": files
    }

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(get_health_data())

@app.route('/fetch', methods=['GET'])
def manual_fetch():
    fetch_weather_data(params["latitude"], params["longitude"])
    return redirect(url_for('index'))

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Hurricane Tracker Flask App")
    parser.add_argument('--port', type=int, default=8080, help="Port to run the Flask app on (default: 8080)")
    args = parser.parse_args()
    
    print(f"Starting Flask app on port {args.port}")
    app.run(debug=True, port=args.port)
