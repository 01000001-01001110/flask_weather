# Hurricane Tracker Flask App

This Flask application provides a dashboard for tracking hurricane-related weather data. It fetches data from the Open-Meteo API and visualizes various weather parameters such as temperature, humidity, wind speed, precipitation, and pressure.

## Features

- Location search using free geocoding service (Nominatim)
- Fetches weather data every 15 minutes
- Visualizes weather data in an interactive dashboard
- Provides current weather conditions
- Allows manual data fetching
- Includes a health check endpoint

## Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setting up a virtual environment

1. Open a terminal and navigate to your project directory.

2. Create a virtual environment:
   ```
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```
   - On Windows:
     ```
     venv\Scripts\activate
     ```

### Installing required packages

With your virtual environment activated, install the required packages using pip:

```
pip install flask openmeteo-requests requests-cache retry-requests pandas apscheduler plotly geopy
```

This command will install the following packages:
- Flask: Web framework
- openmeteo-requests: Client for Open-Meteo API
- requests-cache: Caching for HTTP requests
- retry-requests: Retry mechanism for HTTP requests
- pandas: Data manipulation library
- APScheduler: Advanced Python Scheduler
- plotly: Interactive plotting library
- geopy: Geocoding library

## Running the application

1. Make sure your virtual environment is activated.

2. Run the Flask app:
   ```
   python app.py
   ```

   Or, to specify a custom port:
   ```
   python app.py --port 5000
   ```

3. Open a web browser and navigate to `http://localhost:8080` (or the port you specified).

## Usage

- On the main page, enter a location (city, address, or landmark) to fetch weather data for that area.
- The visualization dashboard displays interactive charts of various weather parameters.
- To manually fetch new data, click the "Fetch New Data" button on the main page.
- The health check endpoint (`/health`) provides information about the application's status and data availability.

## File Structure

- `app.py`: The main Flask application file
- `templates/`:
  - `index.html`: Template for the main page
  - `visualize.html`: Template for the visualization dashboard
  - `error.html`: Template for error messages
- `weather_data_*.json`: JSON files containing fetched weather data

## Customization

To modify the default location or other parameters, edit the `params` dictionary in `app.py`.

## Troubleshooting

If you encounter any issues:
1. Ensure all required packages are installed correctly.
2. Check that the Open-Meteo API is accessible and responding.
3. Verify that you have write permissions in the directory for storing JSON data files.
4. If geocoding fails, try a different location or check your internet connection.

## Contributing

Contributions to improve the Hurricane Tracker Flask App are welcome. Please feel free to submit pull requests or open issues to discuss potential changes or enhancements, please make sure that you have tested your changes and provide quaily notes on the modifications you are suggesting. 

Remember to deactivate the virtual environment when you're done:
```
deactivate
```
