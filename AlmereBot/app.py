import streamlit as st
import json
import time
import requests
import pandas as pd
from profile_logic import determine_commuter_profile, COMMUTER_PROFILES
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo # Note: Adding ZoneInfo for time zone awareness in the main canvas display

# --- Configuration ---
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual Gemini API key.
# You can get one from Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY = "AIzaSyDIIEigopopIPB4kZP55IFyeoaT7tRK2xc"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"

# --- Helper to determine status from percentage ---
def get_crowding_status(percentage):
    if percentage == 0:
        return "not operating"
    elif percentage <= 20:
        return "not crowded"
    elif percentage <= 50:
        return "slightly crowded"
    elif percentage <= 80:
        return "moderately crowded"
    elif percentage <= 99:
        return "very crowded"
    else: # 100%
        return "overcrowded"

# --- Simulated Crowding Data (Based on bus line.pdf heatmaps) ---
# This data provides hourly occupancy percentages and statuses.
SIMULATED_CROWDING_DATA = {
    'M1': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M2': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M3': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M4': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M5': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M6': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M7': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'M8': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    '22': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    '24': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'N22': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    'N23': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    '322': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    '326': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    '327': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
    '330': {
        f'Hour {h}': {'percentage': 0, 'status': 'not operating'} for h in range(24)
    },
}

# Populate data based on heatmaps and operational times
# M1-M7: ~04:30 AM - ~02:00 AM (7 days)
for line in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7']:
    for h in range(4, 23): # Roughly 4 AM to 1 AM (next day)
        if 6 <= h <= 9: # Morning peak
            perc = 70 if line in ['M2'] else 85 if line in ['M7'] else 90 # Example variations
        elif 12 <= h <= 14: # Midday
            perc = 30 if line in ['M1', 'M2'] else 50 if line in ['M7'] else 40
        elif 16 <= h <= 19: # Evening peak
            perc = 75 if line in ['M1'] else 80 if line in ['M2'] else 95 if line in ['M7'] else 90
        elif h >= 22 or h <= 3: # Late night/early morning (still operating)
            perc = 10
        else:
            perc = 20 # Off-peak
        SIMULATED_CROWDING_DATA[line][f'Hour {h}'] = {'percentage': perc, 'status': get_crowding_status(perc)}

# M8: ~04:47 AM - ~01:30-02:00 AM (7 days)
for h in range(5, 23): # Roughly 5 AM to 1 AM (next day)
    if 7 <= h <= 9: # Morning peak
        perc = 80
    elif 12 <= h <= 14: # Midday
        perc = 45
    elif 16 <= h <= 19: # Evening peak
        perc = 85
    elif h >= 22 or h <= 4: # Late night/early morning (still operating)
        perc = 15
    else:
        perc = 25
    SIMULATED_CROWDING_DATA['M8'][f'Hour {h}'] = {'percentage': perc, 'status': get_crowding_status(perc)}

# Lines 22, 24: Weekday peaks only (6:00-20:00)
for line in ['22', '24']:
    for h in range(6, 20): # 6 AM to 8 PM
        if 7 <= h <= 9 or 16 <= h <= 18: # Peaks
            perc = 60 if line == '22' else 70
        else:
            perc = 30 if line == '22' else 40
        SIMULATED_CROWDING_DATA[line][f'Hour {h}'] = {'percentage': perc, 'status': get_crowding_status(perc)}

# Night lines N22, N23: Overnight only (22:00-04:00), Mon-Sat nights only
# For simplicity, we'll show data for all days, but note it's primarily Mon-Sat nights.
for line in ['N22', 'N23']:
    for h in [22, 23, 0, 1, 2, 3]: # 10 PM to 3 AM (next day)
        perc = 40 if line == 'N22' else 50
        SIMULATED_CROWDING_DATA[line][f'Hour {h}'] = {'percentage': perc, 'status': get_crowding_status(perc)}


# R-net regional lines (322, 326, 327, 330): Weekday daytime (6:00-20:00)
# Line 326: Monday & Friday only
for line in ['322', '327', '330']:
    for h in range(6, 20): # 6 AM to 8 PM
        if 7 <= h <= 9 or 16 <= h <= 18: # Peaks
            perc = 70 if line == '322' else 60
        else:
            perc = 30 if line == '322' else 25
        SIMULATED_CROWDING_DATA[line][f'Hour {h}'] = {'percentage': perc, 'status': get_crowding_status(perc)}

# Line 326 (Monday & Friday only, 6:00-20:00) - for simplicity in this general simulation,
# we'll include it in the general hourly data, but note its limited days.
for h in range(6, 20):
    if 7 <= h <= 9 or 16 <= h <= 18:
        perc = 50
    else:
        perc = 20
    SIMULATED_CROWDING_DATA['326'][f'Hour {h}'] = {'percentage': perc, 'status': get_crowding_status(perc)}


# --- Extracted Bus Schedule Data from scheduling.pdf and schedule.pdf ---
# This dictionary contains detailed operational schedules and stops for each bus line.
BUS_SCHEDULE_DATA = {
    "M1": {"Route": "Almere Centrum → Almere Haven", "Start Time": "04:13", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~7-15 min", "Notes": "Full loop route incl.", "Stops": ["Station Centrum", "Stadhuisplein", "Passage", "Stedenwijk Midden", "Stedenwijk Zuid", "'t Oor", "De Steiger", "De Marken", "De Grienden", "De Wierden", "De Hoven", "Haven Centrum", "De Werven", "De Meenten"]},
    "M2": {"Route": "Almere Centrum → Almere Buiten", "Start Time": "04:30", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~7-15 min", "Notes": "Covers Stripheldenbuurt + Station Buiten", "Stops": ["Station Centrum", "Staatsliedenwijk", "Markerkant", "Waterwijk West", "Waterwijk Oost", "FBK Sportpark", "Bouwmeesterbuurt West", "Bouwmeesterbuurt Oost", "Molenbuurt Noord", "Molenbuurt Zuid", "Baltimoreplein", "Station Buiten", "Stripheldenbuurt Noord", "Stripheldenbuurt Oost", "Stripheldenbuurt Midden"]},
    "M3": {"Route": "Almere Muziekwijk → Almere Centrum", "Start Time": "04:30", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~7-15 min", "Notes": "Serves Kruidenwijk, Componistenpad", "Stops": ["Station Centrum", "Staatsliedenwijk", "Kruidenwijk Oost", "Kruidenwijk West", "Beatrixpark", "Fugaplantsoen", "Wim Kanplein", "Count Basiestraat", "Station Muziekwijk", "Componistenpad"]},
    "M4": {"Route": "Almere Poort → Almere Centrum", "Start Time": "04:30", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~7-15 min", "Notes": "Via Homeruskwartier, Literatuurwijk", "Stops": ["Station Poort", "Europakwartier West", "Columbuskartier", "Homeruskwartier West", "Homeruskwartier Midden", "Homeruskwartier Oost", "Middenkant", "Hogekant", "Literatuurwijk West", "Literatuurwijk Midden", "Literatuurwijk Oost", "Operetteweg", "Station Muziekwijk", "Componistenpad", "Haydnplantsoen", "Stedenwijk Midden", "Passage", "Stadhuisplein", "Station Centrum"]},
    "M5": {"Route": "Almere Parkwijk → Almere Centrum", "Start Time": "04:30", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~7-15 min", "Notes": "Passes Filmwijk, Flevoziekenhuis", "Stops": ["Station Parkwijk", "Parkwijk Midden", "Parkwijk Zuid", "Danswijk", "Walt Disneyplantsoen", "Bunuellaan", "Romy Schneiderweg", "Greta Garboplantsoen", "Flevoziekenhuis", "Stadhuisplein", "Station Centrum"]},
    "M6": {"Route": "Noorderplassen Almere Centrum", "Start Time": "04:30", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~10-15 min", "Notes": "Shortest route; via Kruidenwijk, Beatrixpark", "Stops": ["Noorderplassen Noord", "Noorderplassen Zuid", "Kruidenwijk", "Beatrixpark", "Kruidenwijk West", "Kruidenwijk Oost", "Staatsliedenwijk", "Station Centrum"]},
    "M7": {"Route": "Almere Oostvaarders → Almere Centrum", "Start Time": "04:30", "End Time": "02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~7-15 min", "Notes": "Long route via Verzetswijk, Buiten", "Stops": ["Station Oostvaarders", "Eilandenbuurt Noord", "Eilandenbuurt Zuid", "Regenboogbuurt Noord", "Regenboogbuurt Zuid", "Station Buiten", "Bloemenbuurt", "Faunabuurt", "Landgoederenbuurt", "Tussen de Vaarten Noord", "Verzetswijk", "Station Parkwijk", "Parkwijk West", "Greta Garboplantsoen", "Flevoziekenhuis", "Stadhuisplein", "Station Centrum"]},
    "M8": {"Route": "Nobelhorst → Almere Centrum", "Start Time": "04:47", "End Time": "01:30-02:00", "Days of Operation": "7 days", "Service Type": "Metro (allGo)", "Weekend Service": "Yes", "Frequency": "~15 min", "Notes": "Covers Nobelhorst, Sallandsekant", "Stops": ["Nobelhorst Midden", "Nobelhorst Noord", "Sallandsekant", "Tussen de Vaarten Zuid", "Tussen de Vaarten Midden", "Tussen de Vaarten Noord", "Verzetswijk", "Station Parkwijk", "Parkwijk West", "Greta Garboplantsoen", "Flevoziekenhuis", "Stadhuisplein", "Station Centrum"]},
    "22": {"Route": "Pontonweg → Station Buiten", "Start Time": "06:00", "End Time": "20:00", "Days of Operation": "Weekdays (Mon-Fri)", "Service Type": "Local (FlexiGo)", "Weekend Service": "No", "Frequency": "~15-30 min", "Notes": "Industrial zone De Vaart", "Stops": ["Pontonweg", "Groene Kadeweg", "Schutsluisweg", "Damsluisweg", "Hefbrugweg", "Vlotbrugweg", "Draaibrugweg", "Bolderweg", "Molenbuurt Noord", "Molenbuurt Zuid", "Baltimoreplein", "Station Buiten"]},
    "24": {"Route": "Station Poort → Duinstraat", "Start Time": "06:00", "End Time": "20:00", "Days of Operation": "Weekdays (Mon-Fri), summer", "Service Type": "Local (DuinGo)", "Weekend Service": "No", "Frequency": "~15 min", "Notes": "Seasonal, short shuttle", "Stops": ["Station Poort", "Duinplein", "Duinstraat", "Marinaweg", "Duinbeekstraat"]},
    "N22": {"Route": "Amsterdam Leidseplein → Almere Buiten", "Start Time": "22:00", "End Time": "04:00", "Days of Operation": "Nights (Mon-Sat only)", "Service Type": "NightGo", "Weekend Service": "No (daytime only)", "Frequency": "1 trip/night", "Notes": "Almere-only segment shown", "Stops": ["Station Poort", "Homeruskwartier", "Literatuurwijk", "Operetteweg", "Muziekwijk", "Componistenpad", "Beatrixpark", "Kruidenwijk", "Staatsliedenwijk", "Centrum", "Parkwijk", "Tussen de Vaarten Zuid", "Tussen de Vaarten Midden", "Tussen de Vaarten Noord", "Sallandsekant", "Faunabuurt", "Station Buiten"]},
    "N23": {"Route": "Amsterdam Centraal → Almere Centrum", "Start Time": "22:00", "End Time": "04:00", "Days of Operation": "Nights (Mon-Sat only)", "Service Type": "NightGo", "Weekend Service": "No (daytime only)", "Frequency": "1 trip/night", "Notes": "Focus on Filmwijk, Centrum", "Stops": ["'t Oor", "Hortus", "Kasteel", "Veluwsekant", "Walt Disneyplantsoen", "Bunuellaan", "Romy Schneiderweg", "Greta Garboplantsoen", "Flevoziekenhuis", "Centrum"]},
    "322": {"Route": "Parkwijk → Amsterdam Amstel", "Start Time": "08:11", "End Time": "01:30", "Days of Operation": "7 days", "Service Type": "R-net", "Weekend Service": "Yes", "Frequency": "~20-50 min", "Notes": "Almere-only stops shown", "Stops": ["Station Parkwijk", "Verzetswijk", "Tussen de Vaarten Noord", "Tussen de Vaarten Midden", "Tussen de Vaarten Zuid", "Sallandsekant", "Danswijk", "Walt Disneyplantsoen", "Veluwsekant", "Kasteel", "Hortus", "'t Oor", "Gooisekant West", "Gooisekant Midden", "Gooisekant Oost", "Station Poort"]},
    "326": {"Route": "Almere Centrum Blaricum", "Start Time": "06:00", "End Time": "20:00", "Days of Operation": "Monday & Friday only", "Service Type": "R-net", "Weekend Service": "No", "Frequency": "~30-60 min", "Notes": "Almere-only stops shown", "Stops": ["Centrum", "Stadhuisplein", "Passage", "Stedenwijk Midden", "Stedenwijk Zuid", "'t Oor", "Hortus", "Kasteel", "Veluwsekant", "Kemphaan", "De Steiger"]},
    "327": {"Route": "Almere Haven → Amsterdam Amstel", "Start Time": "06:00", "End Time": "20:00", "Days of Operation": "Weekdays (Mon-Fri)", "Service Type": "R-net", "Weekend Service": "No", "Frequency": "~20-60 min", "Notes": "Almere-only stops shown", "Stops": ["'t Oor", "Hortus", "Kasteel", "Veluwsekant", "Walt Disneyplantsoen", "Bunuellaan", "Romy Schneiderweg", "Greta Garboplantsoen", "Flevoziekenhuis", "Centrum"]},
    "330": {"Route": "Almere Buiten → Bijlmer ArenA", "Start Time": "06:00", "End Time": "20:00", "Days of Operation": "Weekdays (Mon-Fri)", "Service Type": "R-net", "Weekend Service": "No", "Frequency": "~30 min", "Notes": "Ends at Station Buiten / Bijlmer", "Stops": ["'t Oor", "Hortus", "Kasteel", "Veluwsekant", "Walt Disneyplantsoen", "Danswijk", "Sallandsekant", "Tussen de Vaarten Zuid", "Tussen de Vaarten Midden", "Tussen de Vaarten Noord", "Landgoederenbuurt", "Faunabuurt", "Bloemenbuurt", "Station Buiten"]}
}


# --- Load and Analyze Survey Data from CSV ---
try:
    df = pd.read_csv("AlmereBot/urban.csv")

    # Clean and analyze the data to create a summary for the chatbot
    # Ensure column names match your CSV exactly
    issues_frustration = df['What issues frustrate you most about Almere Bus line?'].value_counts()
    
    # Handle potential non-numeric values in 'What time do you usually leave for work/school?'
    # Convert to datetime objects for proper averaging
    df['Departure_Hour'] = df['What time do you usually leave for work/school?'].apply(lambda x: pd.to_datetime(x, format='%H:%M:%S', errors='coerce').hour if pd.notna(x) else None)
    commute_time_average_hour = df['Departure_Hour'].mean() if df['Departure_Hour'].notna().any() else None

    primary_transport = df['What is your primary mode of transportation?'].value_counts().idxmax()
    crowd_levels = df['How crowded is your usual bus during peak hours?'].value_counts()

    # Safely get the count for app openness
    app_openness_col = 'Would you be open to using an app that gives personal travel advice based on real-time crowd levels?'
    if app_openness_col in df.columns:
        open_to_app_count = df[df[app_openness_col] == 'Yes'].shape[0]
    else:
        open_to_app_count = "N/A (column not found)"

    csv_data_summary = f"""
    Summary of Urban Mobility Survey responses from Almere:
    - The most common frustrations with the bus line are: {issues_frustration.head(3).to_dict()}
    - The average commuter leaves for work/school around {commute_time_average_hour:.0f}:00.
    - The most common primary mode of transportation is: {primary_transport}.
    - Commuters perceive peak hour crowding as follows: {crowd_levels.to_dict()}.
    - A significant number of people ({open_to_app_count}) are open to using a travel advice app.
    """
except FileNotFoundError:
    st.error("Survey data file not found. The bot will use general knowledge instead.")
    csv_data_summary = "No survey data available for analysis."
except Exception as e:
    st.error(f"Error loading or processing survey data: {e}. The bot will use general knowledge instead.")
    csv_data_summary = "Error processing survey data for analysis."


# --- Conversational Questions for Profile Determination ---
# These are simplified versions of the survey questions with controlled options.
CONVERSATIONAL_QUESTIONS = [
    {
        "text": "Hello! I'm your Urbanvind Commuter Chatbot. To get started, I need to understand your travel habits. What time do you usually leave for work/school?",
        "key": "What time do you usually leave for work/school?",
        "options": [
            "04:00 AM - 07:00 AM (Early Morning)",
            "07:00 AM - 09:00 AM (Morning Peak)",
            "09:00 AM - 04:00 PM (Midday)",
            "04:00 PM - 08:00 PM (Evening Peak)",
            "08:00 PM - 04:00 AM (Late Night/Overnight)"
        ]
    },
    {
        "text": "How many days per week do you typically commute?",
        "key": "How many days per week do you commute?",
        "options": ["1-2 days", "3-4 days", "5+ days", "I work remotely"]
    },
    {
        "text": "How crowded is your usual bus or train during peak hours?",
        "key": "How crowded is your usual bus during peak hours?",
        "options": ["Not crowded", "Slightly crowded", "Very crowded", "Overcrowded"]
    },
    {
        "text": "If you knew your usual bus was full, would you change your departure time? (1='Definitely not', 5='Definitely')",
        "key": "I would change my departure time if I knew my usual bus was full.",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "text": "If your usual bus arrived 90% full, what would you most likely do?",
        "key": "If your usual bus is 90% full when it arrives, what would you most likely do?",
        "options": ["Wait for the next one", "Change my travel time", "Switch to a different line", "Board anyway", "Cancel or delay the trip"]
    }
]


def call_gemini_api(prompt_text):
    """
    Calls the Gemini API with the given prompt and handles exponential backoff.
    """
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt_text}]}
        ]
    }

    retries = 0
    max_retries = 5
    base_delay = 1  # seconds

    while retries < max_retries:
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            if result.get('candidates') and result['candidates'][0].get('content') and \
               result['candidates'][0]['content'].get('parts') and \
               result['candidates'][0]['content']['parts'][0].get('text'):
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                st.error(f"Unexpected API response structure: {result}")
                return "I'm sorry, I couldn't generate a response due to an unexpected API format."

        except requests.exceptions.RequestException as e:
            retries += 1
            if retries < max_retries:
                delay = base_delay * (2 ** (retries - 1)) # Exponential backoff
                time.sleep(delay)
                # print(f"API call failed: {e}. Retrying in {delay} seconds...") # For debugging
            else:
                st.error(f"Failed to connect to Gemini API after {max_retries} retries: {e}")
                return "I'm currently unable to connect to my knowledge base. Please try again later."
        except json.JSONDecodeError:
            st.error("Failed to decode JSON response from API.")
            return "I'm sorry, I received an unreadable response from my knowledge base."
    return "I'm currently unable to process your request. Please try again later."


def generate_bot_response_with_gemini(user_message, selected_profile, csv_summary, bus_schedule_data):
    """
    Generates a tailored bot response using the Gemini API, incorporating
    the user's profile, simulated crowding data, CSV survey summary, and bus schedule data.
    """
    profile_info = COMMUTER_PROFILES.get(selected_profile, {"description": "unknown", "logic_keywords": "unknown"})
    current_hour = datetime.now().hour
    current_time_key = f'Hour {current_hour}' # Use exact hour for lookup

    # Get current crowding data for all lines
    current_crowding_info = {}
    for line, hours_data in SIMULATED_CROWDING_DATA.items():
        data = hours_data.get(current_time_key, {'status': 'not operating', 'percentage': 0})
        current_crowding_info[line] = data

    # Construct the prompt for Gemini, including all relevant data
    prompt = f"""
    You are Urbanvind Commuter Chatbot, a decision support system for Almere residents.
    Your goal is to provide tailored travel suggestions and information based on the user's commuter profile, real-time (simulated) crowding data, insights from a survey of Almere commuters, and detailed bus schedules.

    Insights from the Almere Commuter Survey:
    {csv_summary}

    Almere Bus Schedules:
    {json.dumps(bus_schedule_data, indent=2)}

    The user's profile is: "{selected_profile}".
    This means: {profile_info['description']}
    Key characteristics of this profile include: {profile_info['logic_keywords']}

    Current simulated crowding data for Almere bus lines at {current_time_key}:
    {json.dumps(current_crowding_info, indent=2)}

    Based on the user's profile, the survey insights, the current crowding data, AND the bus schedule data, provide a tailored travel suggestion or answer their question.
    Keep your response concise, helpful, and align it with their profile's characteristics.
    If the user asks about crowding, provide specific details from the simulated data.
    If the user asks for general travel advice for Almere, use the current simulated crowding data and the survey insights to give a general recommendation, considering typical frustrations and popular transport modes.
    If the user asks about a specific bus line's schedule, route, or stops, provide details from the bus schedule data.
    If the user asks for general advice, use their profile to suggest appropriate actions (e.g., for 'Flexible Avoider', suggest proactive changes; for 'Peak Routine Commuter', acknowledge their routine but gently suggest minor adjustments if needed).

    User's message: "{user_message}"
    """

    response_text = call_gemini_api(prompt)
    return response_text

# --- Streamlit UI ---
st.set_page_config(page_title="Urbanvind Traveller Chatbot", layout="centered")

st.title("🏙️ Urbanvind Traveller Chatbot")
st.markdown("Your personalized travel assistant for Almere.")

# --- Main Canvas: Display Current Time ---
# Get current time in Almere (Europe/Amsterdam timezone)
try:
    current_time_almere = datetime.now(ZoneInfo('Europe/Amsterdam'))
except NameError:
    # Fallback if ZoneInfo isn't available (though it should be with modern Python)
    current_time_almere = datetime.now() 
    
# Format as a clear date and time string
formatted_time = current_time_almere.strftime("%A, %B %d, %H:%M:%S %Z")

st.caption("Current Local Time (Almere):")
st.markdown(f"**{formatted_time}**")
st.markdown("---")
# --- END Main Canvas Time ---


# --- Sidebar for Live Crowding Data ---
st.sidebar.title("📊 Live Crowding Data")
st.sidebar.markdown("*(Simulated data for demonstration)*")

# Get current hour for sidebar lookup
current_hour_for_display = current_time_almere.hour

# --- MODIFIED: Format the hour as HH:00 ---
# Use 02d for zero padding (e.g., 9 -> 09)
formatted_hour_display = f"{current_hour_for_display:02d}:00" 
# --- END MODIFIED ---

current_time_key_for_display = f'Hour {current_hour_for_display}'

st.sidebar.subheader("Almere Bus Lines")
for line, hours_data in SIMULATED_CROWDING_DATA.items():
    data = hours_data.get(current_time_key_for_display, {'status': 'not operating', 'percentage': 0})
    status = data['status']
    percentage = data['percentage']
    
    # Determine color for progress bar
    if percentage == 0:
        color = "#cccccc" # Grey for not operating
    elif percentage < 50:
        color = "#4CAF50" # Green
    elif percentage < 80:
        color = "#FFC107" # Orange
    else:
        color = "#F44336" # Red

    # --- MODIFIED: Use the formatted time string ---
    st.sidebar.markdown(f"**{line}** ({formatted_hour_display}):")
    st.sidebar.progress(percentage, text=f"{percentage}% ({status})")


# Initialize session state for conversation
if "chat_phase" not in st.session_state:
    st.session_state.chat_phase = "questions"
    st.session_state.questions_asked = 0
    st.session_state.user_answers = {}
    st.session_state.selected_profile = None
    st.session_state.messages = []


# --- Conversation Flow Logic ---
if st.session_state.chat_phase == "questions":
    # Check if all questions have been asked
    if st.session_state.questions_asked >= len(CONVERSATIONAL_QUESTIONS):
        st.session_state.chat_phase = "determining_profile"
        st.rerun()

    # If not all questions have been asked, display the next one
    else:
        current_question_index = st.session_state.questions_asked
        current_question = CONVERSATIONAL_QUESTIONS[current_question_index]

        # Use a single chat message container for the bot's question
        with st.chat_message("bot"):
            st.markdown(current_question['text'])

        # Use radio buttons for all questions with predefined options
        user_answer = st.radio(
            "Please select an option:",
            current_question['options'],
            key=f"q_radio_{current_question_index}"
        )
        if st.button("Next Question", key=f"next_{current_question_index}"):
            st.session_state.user_answers[current_question['key']] = user_answer
            st.session_state.questions_asked += 1
            st.rerun()

elif st.session_state.chat_phase == "determining_profile":
    with st.spinner("Analyzing your answers and determining your commuter profile..."):
        determined_profile = determine_commuter_profile(st.session_state.user_answers)
        st.session_state.selected_profile = determined_profile

        profile_message = f"Based on your answers, your profile is: **{determined_profile}**."
        st.session_state.messages.append({"role": "bot", "content": profile_message})
        
        st.session_state.chat_phase = "chatting"
        st.session_state.messages.append({"role": "bot", "content": "Now you can ask me for personalized travel advice!"})
        st.rerun()
        
elif st.session_state.chat_phase == "chatting":
    st.info(f"Your current profile: **{st.session_state.selected_profile}**")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("bot"):
            with st.spinner("Thinking..."):
                # Pass the csv_data_summary and BUS_SCHEDULE_DATA to the generate_bot_response_with_gemini function
                bot_response = generate_bot_response_with_gemini(prompt, st.session_state.selected_profile, csv_data_summary, BUS_SCHEDULE_DATA)
                st.markdown(bot_response)
            st.session_state.messages.append({"role": "bot", "content": bot_response})

    st.markdown("---")
    st.caption("Note: Crowding data is simulated for this prototype.")
