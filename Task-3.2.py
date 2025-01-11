import pandas as pd
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os


load_dotenv()

API_KEY = os.getenv("API_KEY")

# Fixed Reference Point (latitude, longitude)
REFERENCE_POINT = (37.7749, -122.4194)  # San Francisco, CA


# Load data from CSV
def load_data(file_path):
    return pd.read_csv(file_path)


# Get coordinates using Geocoding API
def get_coordinates(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": API_KEY}
    response = requests.get(url, params=params).json()
    if response["status"] == "OK":
        location = response["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        print(f"Error fetching coordinates for address: {address}")
        return None, None


# Calculate distance using Distance Matrix API
def calculate_distance(origin, destination):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin[0]},{origin[1]}",
        "destinations": f"{destination[0]},{destination[1]}",
        "key": API_KEY,
    }
    response = requests.get(url, params=params).json()

    print(f"Response: {response}")

    # Check overall status
    if response.get("status") == "OK":
        element = response["rows"][0]["elements"][0]
        # Check element status
        if element.get("status") == "OK":
            return element["distance"]["text"]
        elif element.get("status") == "ZERO_RESULTS":
            print("No results for the given origin-destination pair.")
            return "No route found"
        else:
            print(f"Element status error: {element.get('status')}")
            return "Error calculating distance"
    else:
        print(f"API response error: {response.get('status')}")
        return "API Error"


# Write data to Google Sheets
def write_to_google_sheets(data, spreadsheet_id, range_name, credentials_file):
    creds = Credentials.from_service_account_file(credentials_file)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    # Update sheet values
    body = {"values": data}
    sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body=body,
    ).execute()


# Main workflow
def main():
    file_path = (
        r"d:\My Paid Projects\Buildberg\addresses.csv" 
    )
    data = load_data(file_path)
    results = [["Address", "Latitude", "Longitude", "Distance to Reference Point"]]

    for _, row in data.iterrows():
        address = row["Address"]
        lat, lng = row.get("Latitude"), row.get("Longitude")

        # Fetch coordinates if missing
        if pd.isna(lat) or pd.isna(lng):
            lat, lng = get_coordinates(address)

        if lat is not None and lng is not None:
            # Calculate distance
            distance = calculate_distance(REFERENCE_POINT, (lat, lng))
            results.append([address, lat, lng, distance])
        else:
            results.append(
                [
                    address,
                    "Error fetching coordinates",
                    "Error fetching coordinates",
                    "N/A",
                ]
            )

    # Write to Google Sheets
    SPREADSHEET_ID = "1rpjV48KUjOgh5YFGr-m4Fy9jJ0XB6N8w16k70ZyKKZI"
    RANGE_NAME = "Sheet1!A1"
    CREDENTIALS_FILE = "credentials.json"
   
    write_to_google_sheets(results, SPREADSHEET_ID, RANGE_NAME, CREDENTIALS_FILE)


main()
