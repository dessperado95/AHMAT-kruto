import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import argparse
import json

# Load environment variables
load_dotenv()

class WeatherDashboard:
    """A Python application that fetches weather data and creates visualizations."""
    
    def __init__(self, api_key=None):
        """Initialize the WeatherDashboard with API key."""
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set OPENWEATHER_API_KEY environment variable or pass it as an argument.")
        
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cities = []
        self.weather_data = {}
        
        # Set up styling for visualizations
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
    
    def add_city(self, city_name):
        """Add a city to track weather for."""
        self.cities.append(city_name)
        return self
    
    def fetch_current_weather(self):
        """Fetch current weather data for all added cities."""
        for city in self.cities:
            url = f"{self.base_url}/weather?q={city}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                self.weather_data[city] = response.json()
            else:
                print(f"Error fetching data for {city}: {response.status_code}")
        
        return self
    
    def fetch_forecast(self, days=5):
        """Fetch forecast data for all added cities."""
        self.forecast_data = {}
        
        for city in self.cities:
            url = f"{self.base_url}/forecast?q={city}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            
            if response.status_code == 200:
                self.forecast_data[city] = response.json()
            else:
                print(f"Error fetching forecast for {city}: {response.status_code}")
        
        return self
    
    def prepare_data(self):
        """Transform raw API data into pandas DataFrames for analysis."""
        # Prepare current weather data
        current_weather_records = []
        
        for city, data in self.weather_data.items():
            record = {
                'city': city,
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'description': data['weather'][0]['description'],
                'timestamp': datetime.fromtimestamp(data['dt'])
            }
            current_weather_records.append(record)
        
        self.current_df = pd.DataFrame(current_weather_records)
        
        # Prepare forecast data
        forecast_records = []
        
        for city, data in self.forecast_data.items():
            for item in data['list']:
                record = {
                    'city': city,
                    'temperature': item['main']['temp'],
                    'feels_like': item['main']['feels_like'],
                    'humidity': item['main']['humidity'],
                    'pressure': item['main']['pressure'],
                    'wind_speed': item['wind']['speed'],
                    'description': item['weather'][0]['description'],
                    'timestamp': datetime.fromtimestamp(item['dt']),
                    'forecast_time': item['dt_txt']
                }
                forecast_records.append(record)
        
        self.forecast_df = pd.DataFrame(forecast_records)
        return self
    
    def visualize_temperature_comparison(self):
        """Create a bar chart comparing temperatures across cities."""
        plt.figure(figsize=(12, 6))
        chart = sns.barplot(x='city', y='temperature', data=self.current_df, palette='viridis')
        
        # Add value labels on top of bars
        for p in chart.patches:
            chart.annotate(f"{p.get_height():.1f}°C", 
                         (p.get_x() + p.get_width() / 2., p.get_height()), 
                         ha = 'center', va = 'bottom', 
                         xytext = (0, 5), textcoords = 'offset points')
        
        plt.title('Current Temperature Comparison Across Cities')
        plt.ylabel('Temperature (°C)')
        plt.xlabel('City')
        plt.tight_layout()
        plt.savefig('output/temperature_comparison.png')
        return self
    
    def visualize_forecast_trends(self):
        """Create line charts showing temperature forecast trends."""
        plt.figure(figsize=(14, 8))
        
        # Get data for the next few days only
        end_date = datetime.now() + timedelta(days=5)
        filtered_df = self.forecast_df[self.forecast_df['timestamp'] <= end_date]
        
        for city in self.cities:
            city_data = filtered_df[filtered_df['city'] == city]
            sns.lineplot(x='timestamp', y='temperature', data=city_data, label=city, linewidth=2.5)
        
        plt.title('5-Day Temperature Forecast')
        plt.ylabel('Temperature (°C)')
        plt.xlabel('Date')
        plt.xticks(rotation=45)
        plt.legend(title='City')
        plt.tight_layout()
        plt.savefig('output/forecast_trends.png')
        return self
    
    def visualize_weather_parameters(self):
        """Create a multi-faceted view of different weather parameters."""
        # Select parameters to visualize
        params = ['temperature', 'humidity', 'wind_speed', 'pressure']
        
        # Create a figure with subplots
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        axs = axs.flatten()
        
        for i, param in enumerate(params):
            sns.barplot(x='city', y=param, data=self.current_df, ax=axs[i], palette='cool')
            axs[i].set_title(f'Current {param.replace("_", " ").title()}')
            axs[i].set_xlabel('')
            
            # Add value labels
            for p in axs[i].patches:
                axs[i].annotate(f"{p.get_height():.1f}", 
                             (p.get_x() + p.get_width() / 2., p.get_height()), 
                             ha = 'center', va = 'bottom', 
                             xytext = (0, 5), textcoords = 'offset points')
        
        plt.tight_layout()
        plt.savefig('output/weather_parameters.png')
        return self
    
    def create_weather_report(self):
        """Generate a text report of current weather conditions."""
        report = "# Current Weather Report\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for idx, row in self.current_df.iterrows():
            report += f"## {row['city']}\n\n"
            report += f"- **Temperature**: {row['temperature']:.1f}°C (Feels like: {row['feels_like']:.1f}°C)\n"
            report += f"- **Description**: {row['description'].capitalize()}\n"
            report += f"- **Humidity**: {row['humidity']}%\n"
            report += f"- **Wind Speed**: {row['wind_speed']} m/s\n"
            report += f"- **Pressure**: {row['pressure']} hPa\n\n"
        
        # Write report to file
        with open("output/weather_report.md", "w") as f:
            f.write(report)
        
        print(f"Report generated: output/weather_report.md")
        return self
    
    def export_data(self):
        """Export the processed data to CSV files."""
        self.current_df.to_csv("output/current_weather.csv", index=False)
        self.forecast_df.to_csv("output/forecast_weather.csv", index=False)
        
        # Also export as JSON for API-like access
        with open("output/current_weather.json", "w") as f:
            f.write(self.current_df.to_json(orient="records", date_format="iso"))
        
        return self
    
    def run_dashboard(self):
        """Run the complete dashboard workflow."""
        self.fetch_current_weather()
        self.fetch_forecast()
        self.prepare_data()
        self.visualize_temperature_comparison()
        self.visualize_forecast_trends()
        self.visualize_weather_parameters()
        self.create_weather_report()
        self.export_data()
        
        print("Dashboard generated successfully!")
        print("Check the 'output' directory for all visualizations and reports.")


def main():
    parser = argparse.ArgumentParser(description="Weather Dashboard - A Python weather visualization tool")
    parser.add_argument("--cities", nargs="+", default=["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan"],
                        help="List of cities to fetch weather data for")
    parser.add_argument("--api-key", help="OpenWeatherMap API key (optional if set as environment variable)")
    
    args = parser.parse_args()
    
    try:
        dashboard = WeatherDashboard(api_key=args.api_key)
        
        for city in args.cities:
            dashboard.add_city(city)
        
        dashboard.run_dashboard()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTo use this dashboard:")
        print("1. Get a free API key from https://openweathermap.org/")
        print("2. Set it as an environment variable OPENWEATHER_API_KEY or pass it with --api-key")
        print("3. Run the script again")

if __name__ == "__main__":
    main()
