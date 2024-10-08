# Weather Dashboard Flask App

This Flask application provides a comprehensive weather dashboard with interactive visualizations, maps, and real-time data from the Open-Meteo API. It offers detailed weather forecasts, current conditions, and various weather parameters for any location.

## Features

- Location-based weather data retrieval using geocoding (Nominatim)
- Fetches forecast and current weather data from Open-Meteo API
- Interactive weather forecast visualization with Plotly
- Current weather conditions display
- Weather maps integration (OpenStreetMap and Windy)
- Nearby webcams display using Windy API
- Wind rose diagram for wind direction and speed analysis
- Manual data refresh option
- Scheduled background data updates (every 15 minutes)
- Health check endpoint for monitoring application status
- Responsive design with Tailwind CSS
- Discord community link and GitHub repository link in the footer

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

## Docker Setup and Usage

To run the Weather Dashboard Flask App using Docker, follow these steps:

1. Make sure you have Docker installed on your system.

2. Build the Docker image:
   ```
   docker build -t weather-dashboard .
   ```

3. Run the Docker container:
   ```
   docker run -p 8080:8080 weather-dashboard
   ```

   This command maps port 8080 from the container to port 8080 on your host machine.

4. Open a web browser and navigate to `http://localhost:8080` to access the application.

To stop the container, press `Ctrl+C` in the terminal where the container is running.

## Usage

- On the main page, enter a location (city, address, or landmark) to fetch weather data for that area.
- The forecast visualization dashboard displays interactive charts of various weather parameters:
  - Temperature and Humidity
  - Wind Speed and Direction
  - Precipitation
- The current weather section shows detailed current conditions.
- The Maps page provides integrated weather maps from OpenStreetMap and Windy.
- To manually fetch new forecast data, click the "Refresh Data" button.
- The Status page (`/status`) provides information about the application's health and data availability.
- Join our Discord community or visit the GitHub repository using the links in the footer.

## File Structure

- `app.py`: The main Flask application file
- `templates/`:
  - `header.html`: Base template with common head content
  - `index.html`: Template for the main page
  - `visualize.html`: Template for the forecast visualization dashboard
  - `maps.html`: Template for weather maps
  - `current_weather.html`: Template for the current weather page
  - `status.html`: Template for the application status page
  - `error.html`: Template for error messages
  - `footer.html`: Template for the footer, including Discord and GitHub links
- `weather_data_*.json`: JSON files containing fetched weather forecast data
- `Dockerfile`: Instructions for building the Docker image
- `.dockerignore`: Specifies files and directories to be excluded from the Docker build context

## Customization

To modify the default location or other parameters, edit the `params` dictionary in `app.py`.

## Troubleshooting

If you encounter any issues:
1. Ensure all required packages are installed correctly.
2. Check that the Open-Meteo API is accessible and responding.
3. Verify that you have write permissions in the directory for storing JSON data files.
4. If geocoding fails, try a different location or check your internet connection.
5. For Docker-related issues, ensure Docker is installed and running correctly on your system.

## Community and Support

- Join our Discord community for discussions, support, and updates: [Discord Invite Link](https://discord.gg/sCfj8c9CcK)
- For bug reports and feature requests, please use the [GitHub issue tracker](https://github.com/01000001-01001110/flask_weather/issues).

## Contributing

Contributions to improve the Weather Dashboard Flask App are welcome. Please feel free to submit pull requests or open issues to discuss potential changes or enhancements. Make sure that you have tested your changes and provide quality notes on the modifications you are suggesting.

Remember to deactivate the virtual environment when you're done:
```
deactivate
```

## License

This project is open-source and available under the MIT License. See the LICENSE file for more details.
