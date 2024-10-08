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
from dateutil import parser as date_parser
import argparse

app = Flask(__name__)

# Setup geocoder
geolocator = Nominatim(user_agent="weather_dashboard_app")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# API configuration
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 29.3014,
    "longitude": -81.1134,
    "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "rain", "showers", "snowfall", "weather_code", "cloud_cover", "pressure_msl", "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
    "hourly": ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature", "precipitation", "rain", "showers", "pressure_msl", "surface_pressure", "cloud_cover", "wind_speed_10m", "wind_speed_80m", "wind_direction_10m", "wind_direction_80m", "wind_gusts_10m", "temperature_80m", "surface_temperature"],
    "temperature_unit": "fahrenheit",
    "wind_speed_unit": "mph",
    "precipitation_unit": "inch",
    "timezone": "America/New_York",
    "past_days": 1,
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
        current_data_dict = {
            "temperature": current.Variables(0).Value(),
            "relative_humidity": current.Variables(1).Value(),
            "apparent_temperature": current.Variables(2).Value(),
            "is_day": current.Variables(3).Value(),
            "precipitation": current.Variables(4).Value(),
            "rain": current.Variables(5).Value(),
            "showers": current.Variables(6).Value(),
            "snowfall": current.Variables(7).Value(),
            "weather_code": current.Variables(8).Value(),
            "cloud_cover": current.Variables(9).Value(),
            "pressure_msl": current.Variables(10).Value(),
            "surface_pressure": current.Variables(11).Value(),
            "wind_speed": current.Variables(12).Value(),
            "wind_direction": current.Variables(13).Value(),
            "wind_gusts": current.Variables(14).Value()
        }
        
        # Process hourly data
        hourly = response.Hourly()
        hourly_data = {"time": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ).astype(str).tolist()}
        
        for i, var in enumerate(params["hourly"]):
            hourly_data[var] = hourly.Variables(i).ValuesAsNumpy().tolist()
        
        # Combine data
        weather_data = {
            "current": current_data_dict,
            "hourly": hourly_data,
            "latitude": latitude,
            "longitude": longitude
        }
        
        # Store the data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_data_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(weather_data, f)
        print(f"Data fetched and stored in {filename}")
        return weather_data
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

# Schedule the data fetching task
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: fetch_weather_data(params["latitude"], params["longitude"]), trigger="interval", minutes=15)
scheduler.start()

# Fetch initial weather data
fetch_weather_data(params["latitude"], params["longitude"])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
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
            else:
                error = "Location not found. Please try again."
                return render_template('index.html', error=error)
        except (GeocoderTimedOut, GeocoderUnavailable):
            error = "Geocoding service is currently unavailable. Please try again later."
            return render_template('index.html', error=error)
    
    files = [f for f in os.listdir('.') if f.startswith('weather_data_')]
    if not files:
        # If no data is available, try to fetch it
        data = fetch_weather_data(params["latitude"], params["longitude"])
        if not data:
            return render_template('visualize.html', error="Failed to fetch weather data. Please try again later.")
    else:
        latest_file = max(files)
        with open(latest_file, 'r') as f:
            data = json.load(f)
    
    try:
        hourly_data = data['hourly']
        current_data = data['current']
        
        # Convert time to datetime objects using dateutil.parser
        time = [date_parser.parse(t) for t in hourly_data['time']]
        
        # Prepare data for charts
        temp_humidity_data = [
            go.Scatter(x=time, y=hourly_data['temperature_2m'], name="Temperature"),
            go.Scatter(x=time, y=hourly_data['relative_humidity_2m'], name="Humidity", yaxis="y2")
        ]
        
        wind_data = [
            go.Scatter(x=time, y=hourly_data['wind_speed_10m'], name="Wind Speed"),
            go.Scatter(x=time, y=hourly_data['wind_direction_10m'], name="Wind Direction", yaxis="y2")
        ]
        
        precipitation_data = [go.Bar(x=time, y=hourly_data['precipitation'], name="Precipitation")]
        
        dew_point_apparent_temp_data = [
            go.Scatter(x=time, y=hourly_data['dew_point_2m'], name="Dew Point"),
            go.Scatter(x=time, y=hourly_data['apparent_temperature'], name="Apparent Temperature")
        ]
        
        cloud_pressure_data = [
            go.Scatter(x=time, y=hourly_data['cloud_cover'], name="Cloud Cover"),
            go.Scatter(x=time, y=hourly_data['pressure_msl'], name="Pressure", yaxis="y2")
        ]
        
        # Prepare data for wind rose diagram
        wind_speeds = hourly_data['wind_speed_10m']
        wind_directions = hourly_data['wind_direction_10m']
        
        # Convert the plot data to JSON for rendering in the template
        plot_json = json.dumps({
            'temp_humidity_data': temp_humidity_data,
            'wind_data': wind_data,
            'precipitation_data': precipitation_data,
            'dew_point_apparent_temp_data': dew_point_apparent_temp_data,
            'cloud_pressure_data': cloud_pressure_data,
            'wind_speeds': wind_speeds,
            'wind_directions': wind_directions,
            'current_weather': current_data,
            'latitude': data['latitude'],
            'longitude': data['longitude']
        }, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('visualize.html', plot_json=plot_json, latitude=data['latitude'], longitude=data['longitude'])
    except KeyError as e:
        return render_template('visualize.html', error=f"Error processing weather data: {str(e)}. Please try again later.")

@app.route('/maps')
def maps():
    return render_template('maps.html')

@app.route('/status')
def status():
    health_data = get_health_data()
    return render_template('status.html', health_data=health_data)

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

@app.route('/fetch', methods=['GET'])
def manual_fetch():
    data = fetch_weather_data(params["latitude"], params["longitude"])
    if data:
        return redirect(url_for('status'))
    else:
        return render_template('status.html', error="Failed to fetch weather data. Please try again later.")

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 8080))
    app.run(host='0.0.0.0', port=port)