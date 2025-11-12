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
# Use st.secrets for secure key management (recommended)
GEMINI_API_KEY = "AIzaSyDIIEigopopIPB4kZP55IFyeoaT7tRK2xc"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"

if GEMINI_API_KEY == "AIzaSyDIIEigopopIPB4kZP55IFyeoaT7tRK2xc":
    st.warning("🚨 Using placeholder API key. For production, secure your key using Streamlit secrets.")


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
for line in SIMULATED_CROWDING_DATA:
    for h in range(24):
        hour_key = f'Hour {h}'
        if hour_key not in SIMULATED_CROWDING_DATA[line]:
            percentage = 20 if 6 <= h < 20 else 0
            SIMULATED_CROWDING_DATA[line][hour_key] = {'percentage': percentage, 'status': get_crowding_status(percentage)}


# --- Simulated Bus Schedule Data ---
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
# The chatbot uses this summary to provide general, data-backed advice.
try:
    df = pd.read_csv("urban.csv")

    # Clean and analyze the data to create a summary for the chatbot
    issues_frustration = df['What issues frustrate you most about Almere Bus line?'].value_counts().head(3).to_dict()
    commute_frequency = df['How many days per week do you commute?'].value_counts().idxmax()
    crowd_levels = df['How crowded is your usual bus during peak hours?'].value_counts().idxmax()

    csv_data_summary = f"""
    Summary of Survey Data (Almere Commuters):
    - Most frequent commute frequency: {commute_frequency}
    - Most common crowding experience: {crowd_levels}
    - Top frustrations: {json.dumps(issues_frustration)}
    """

    # Try to determine the profile of the first person in the CSV to suggest a default
    first_row_answers = df.iloc[0].to_dict()
    default_profile_from_csv = determine_commuter_profile(first_row_answers)

except FileNotFoundError:
    st.error("urban.csv not found. Using default data summaries.")
    csv_data_summary = "General data suggests frequent commuters experience high crowding levels."
    default_profile_from_csv = "Adaptive Off-Peak Traveller"
except Exception as e:
    st.warning(f"Error reading or analyzing urban.csv: {e}. Using fallback profile.")
    csv_data_summary = "General data suggests frequent commuters experience high crowding levels."
    default_profile_from_csv = "Adaptive Off-Peak Traveller"

# --- Gemini Interaction Function ---

# Implement exponential backoff for API calls
def call_gemini_with_retry(payload):
    max_retries = 3
    delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GEMINI_API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=15 # Set a timeout
            )
            response.raise_for_status() # Raise an exception for bad status codes
            return response.json()

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                # print(f"API request failed (Attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                st.error(f"Failed to connect to the Gemini API after {max_retries} attempts.")
                raise


def generate_bot_response_with_gemini(prompt, selected_profile, csv_data_summary, bus_schedule_data):
    """
    Generates a personalized response from the Gemini model.
    """

    # Get the current hour in a specific timezone (e.g., CET/CEST for Almere, Netherlands)
    # Using a general system datetime if specific timezone handling is complex in this environment
    current_hour = datetime.now().hour

    # Convert simulation data to a prompt-friendly string
    simulation_data_str = "Current simulated bus crowding data:\n"
    current_crowding_info = []

    for line, data in SIMULATED_CROWDING_DATA.items():
        hour_key = f'Hour {current_hour}'
        if hour_key in data:
            crowding = data[hour_key]
            current_crowding_info.append(f"Line {line} (Hour {current_hour}): {crowding['percentage']}% full, Status: {crowding['status']}")

    simulation_data_str += "\n".join(current_crowding_info)

    # --- Profile-Specific Instructions ---

    # Fetch details for the selected profile to guide the bot's persona and advice
    profile_details = COMMUTER_PROFILES.get(selected_profile, COMMUTER_PROFILES["Unknown Profile"])
    profile_description = profile_details["description"]
    profile_keywords = profile_details["logic_keywords"]

    # --- System Prompt Setup ---
    # The system prompt ensures the bot acts as a helpful, personalized advisor.

    system_prompt = f"""
    You are AlmereBot, a friendly and expert commuter advice chatbot.
    Your goal is to provide **personalized, data-driven advice** to the user.

    --- USER PROFILE CONTEXT ---
    The user's determined profile is: **{selected_profile}**.
    Profile Description: "{profile_description}"
    Profile Logic Keywords: "{profile_keywords}"

    --- DATA CONTEXT ---
    1. **Real-time Crowding (Simulated):** {simulation_data_str}
    2. **General Survey Data:** {csv_data_summary}
    3. **Example Schedule/Crowding:** {json.dumps(bus_schedule_data)}

    --- INSTRUCTIONS ---
    1. **Persona:** Adopt the personality of the **{selected_profile}** in your advice.
       - If the user is a **Flexible Avoider**, encourage early or late travel options and provide alternatives.
       - If the user is a **Peak Routine Traveller**, acknowledge their fixed schedule and offer small, actionable steps they *can* take (like checking the schedule right before leaving, or route alternatives for highly congested buses) instead of suggesting they shift their entire commute time.
       - If the user is **Inflexible Tolerant**, focus advice on making their fixed commute more comfortable (e.g., which bus lines are least full, or general recommendations for on-bus comfort).
       - If the user is an **Adaptive Off-Peak Traveller**, give them context-driven ideas and highlight new tools that could help them plan better.
    2. **Advice:** Always use the **SIMULATED CROWDING DATA** and **BUS SCHEDULE DATA** to ground your specific recommendations (e.g., "Bus M4 at 8 AM is 95% full, try Bus 330 at 8:05 AM which is only 70% full.").
    3. **Tone:** Be encouraging, positive, and direct. Keep responses concise and focused on solving the user's travel problem.
    """

    # --- API Call Payload ---
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "config": {
            "systemInstruction": system_prompt
        }
    }

    # API call with retry mechanism
    try:
        response_json = call_gemini_with_retry(payload)
    except Exception:
        # Fallback response if API fails after all retries
        return f"I'm sorry, I'm having trouble connecting to my advice engine right now. I know you're a **{selected_profile}**, so in the meantime, perhaps you should check the M4 line for high crowding between 7 AM and 9 AM."

    # Extract response text
    try:
        bot_response = response_json['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError, TypeError):
        bot_response = "I encountered an error processing your request. Please try again."

    return bot_response


# --- Streamlit App Initialization ---
st.set_page_config(page_title="Almere Commuter Chatbot", layout="centered")

# Initialize session state variables
if 'chat_phase' not in st.session_state:
    st.session_state.chat_phase = "survey" # 'survey', 'profile_determined', 'chatting'
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_profile' not in st.session_state:
    # Use the determined profile from CSV as default, or fallback to the new 'Adaptive Off-Peak Traveller'
    st.session_state.selected_profile = default_profile_from_csv if default_profile_from_csv != "Unknown Profile" else "Adaptive Off-Peak Traveller"


# --- App UI ---

st.title("🚌 Almere Commuter Chatbot")
st.markdown("---")

# 1. Profile Selection/Determination Phase (First run)
if st.session_state.chat_phase == "survey":
    st.header("Step 1: Determine Your Commuter Profile")
    st.write("Please answer these five questions to help us understand your travel habits and personalize your advice.")

    # ----------------------------------------------------
    # Survey Questions (Matching Keys used for profile determination)
    # ----------------------------------------------------

    # Q7 (Time of Day)
    q7 = st.selectbox(
        'What time do you usually leave for work/school?',
        options=["04:00 AM - 07:00 AM (Early Morning)", "07:00 AM - 09:00 AM (Morning Peak)", "09:00 AM - 04:00 PM (Midday)", "04:00 PM - 08:00 PM (Evening Peak)", "08:00 PM - 04:00 AM (Late Night/Overnight)"],
        key="q7_answer"
    )
    st.session_state.user_answers['What time do you usually leave for work/school?'] = q7

    # Q9 (Commute Frequency)
    q9 = st.selectbox(
        'How many days per week do you commute?',
        options=["5+ days", "3-4 days", "1-2 days", "Less than 1 day"],
        key="q9_answer"
    )
    st.session_state.user_answers['How many days per week do you commute?'] = q9

    # Q10 (Crowding Experience)
    q10 = st.selectbox(
        'How crowded is your usual bus during peak hours?',
        options=["Not crowded", "Slightly crowded", "Crowded", "Very crowded", "Overcrowded"],
        key="q10_answer"
    )
    st.session_state.user_answers['How crowded is your usual bus during peak hours?'] = q10

    # Q16 (Flexibility Scale) - Note: The CSV question used a 1-5 scale. We map it here.
    q16 = st.slider(
        'On a scale of 1 (Not at all likely) to 5 (Very likely), how likely are you to change your departure time if you knew your usual bus was full?',
        min_value=1, max_value=5, value=3, key="q16_answer"
    )
    st.session_state.user_answers['I would change my departure time if I knew my usual bus was full.'] = q16

    # Q21 (Response to Full Bus)
    q21 = st.selectbox(
        'If your usual bus is 90% full when it arrives, what would you most likely do?',
        options=["Board anyway", "Wait for the next one", "Change my travel time", "Switch to a different line"],
        key="q21_answer"
    )
    st.session_state.user_answers['If your usual bus is 90% full when it arrives, what would you most likely do?'] = q21


    if st.button("Determine My Commuter Profile"):
        # The logic is now in profile_logic.py
        determined_profile = determine_commuter_profile(st.session_state.user_answers)
        st.session_state.selected_profile = determined_profile

        profile_message = f"Based on your answers, your profile is: **{determined_profile}**."
        st.session_state.messages.append({"role": "bot", "content": profile_message})

        st.session_state.chat_phase = "chatting"
        st.session_state.messages.append({"role": "bot", "content": "Now you can ask me for personalized travel advice! Try asking: 'Is the M4 crowded right now?' or 'What is the best time to leave for a Peak Routine Traveller?'"})
        st.rerun()

# 2. Chatting Phase
elif st.session_state.chat_phase == "chatting":
    # Display the determined profile at the top
    st.info(f"Your current profile: **{st.session_state.selected_profile}**")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input and bot response
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
