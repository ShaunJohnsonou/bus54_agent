import csv
import random
from datetime import datetime, timedelta
import os

def generate_bus_schedule(num_entries=100):
    """Generate mock bus schedule data"""
    
    # Bus companies/names
    bus_companies = [
        "Metro Express", "City Link", "Coastal Transit", "Mountain View Bus", 
        "Urban Commuter", "Regional Transit", "Express Line", "Valley Shuttle",
        "Capital Transport", "Northern Express", "Southern Comfort", "Eastern Route",
        "Western Flyer", "Downtown Direct", "Suburban Connect", "Intercity Express"
    ]
    
    # Cities for origins and destinations
    cities = [
        "Lagos", "Kano", "Ibadan", "Kaduna", "Port Harcourt", "Benin City",
        "Maiduguri", "Zaria", "Aba", "Jos", "Ilorin", "Oyo",
        "Enugu", "Abeokuta", "Abuja", "Sokoto", "Onitsha", "Warri",
        "Okene", "Calabar", "Uyo", "Katsina", "Bauchi", "Akure", "Makurdi"
    ]
    
    # Generate schedule data
    schedule_data = []
    
    for _ in range(num_entries):
        # Select random origin and destination (ensuring they're different)
        origin = random.choice(cities)
        destination = random.choice([city for city in cities if city != origin])
        
        # Generate random departure time
        departure_hour = random.randint(5, 22)  # Between 5 AM and 10 PM
        departure_minute = random.choice([0, 15, 30, 45])
        departure_time = f"{departure_hour:02d}:{departure_minute:02d}"
        
        # Calculate trip duration (between 30 minutes and 8 hours)
        duration_minutes = random.randint(30, 480)
        
        # Calculate arrival time
        departure_dt = datetime.strptime(departure_time, "%H:%M")
        arrival_dt = departure_dt + timedelta(minutes=duration_minutes)
        arrival_time = arrival_dt.strftime("%H:%M")
        
        # Select random bus company/name
        bus_name = random.choice(bus_companies)

        # Add entry to schedule data
        schedule_data.append({
            "departure_time": departure_time,
            "departure_location": origin,
            "destination": destination,
            "arrival_time": arrival_time,
            "bus_name": bus_name,
            "available_seats": random.randint(1, 60)
        })
    
    return schedule_data

def save_to_csv(data, filename="simple_bus_schedule.csv", delimiter=","):
    """Save the generated data to a CSV file
    
    Args:
        data: List of dictionaries containing bus schedule data
        filename: Name of the output file
        delimiter: Delimiter to use in the CSV file (default: comma)
    """
    
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["departure_time", "departure_location", "destination", "arrival_time", "bus_name", "available_seats"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter)
        
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)
    
    print(f"Bus schedule data saved to {filepath}")
    return filepath

if __name__ == "__main__":
    # Generate 100 bus schedule entries
    bus_schedule = generate_bus_schedule(10)
    
    # Save to CSV with comma delimiter (standard CSV)
    save_to_csv(bus_schedule, "simple_bus_schedule.csv", ",")
