Urbanvind Commuter Chatbot: A Prototype for Simulating Commuter Behaviour
This document provides a comprehensive overview of the Urbanvind Commuter Chatbot, a prototype designed to explore how personalized, real-time data and behavioral insights can influence commuter choices. The chatbot is a Streamlit application that combines a simple user profiling system with a large language model (LLM) to provide tailored advice.
1. System Overview
The chatbot operates in two main phases:
1.	User Profiling: The user answers a series of multiple-choice questions to determine their "commuter profile" (e.g., "Peak Routine Commuter," "Flexible Avoider," etc.).
2.	Interactive Chat: The user can then engage in a free-form conversation with a Gemini-powered chatbot, which provides personalized advice based on their profile, simulated real-time data, and insights from a pre-loaded survey.
This architecture demonstrates a closed-loop system where data from different sources (user input, simulated real-time data, and historical survey data) is synthesized by an LLM to generate a relevant, personalized response.
2. Core Components and Technologies
The bot is built using a stack of open-source libraries and APIs.
A. User Interface (UI)
●	Technology: Streamlit
●	Description: Streamlit is a Python library used to create and deploy data-driven web applications. It provides the conversational interface, including the chat messages, input boxes, and sidebar for displaying simulated data. The UI flow is managed through Python's st.session_state.
B. Commuter Profiling Logic
●	Technology: profile_logic.py (assumed external script) and Python dictionaries.
●	Description: This component is responsible for categorizing the user. After the user answers a series of five questions, the responses are stored. A function, determine_commuter_profile, analyzes these answers against a set of predefined rules to assign one of several commuter profiles. This profile is then used to contextualize the LLM's responses, ensuring the advice is relevant to the user's personality and habits.
C. Data Integration
The bot is unique in that it integrates three distinct types of data to provide a comprehensive response.
1.	Simulated Real-time Crowding Data (SIMULATED_CROWDING_DATA)
○	Data Source: A hard-coded Python dictionary.
○	Description: This dictionary holds mock data for various bus and train lines in Almere at different times of the day. This data is based on the provided heatmap image and simulates realistic peak and off-peak crowding levels. It's displayed in the sidebar and fed directly into the LLM's prompt. This component allows the bot to give "real-time" advice without a live data API.
2.	Historical Survey Data (urban.csv)
○	Data Source: A local CSV file named Urban Mobility Survey – Understanding Commuter Choices in Almere (Responses) - Form responses 1.csv.
○	Description: When the application starts, it reads this CSV file using the pandas library. It performs a basic analysis to summarize key findings, such as common frustrations, average commute times, and crowding perceptions. This summary is then included in the LLM's prompt, allowing the bot to provide responses that are not just personal, but also grounded in the collective experience of Almere commuters.
D. LLM Integration
●	Technology: Gemini API
●	Description: The bot communicates with a large language model (LLM) via the Gemini API. The generate_bot_response_with_gemini function is the heart of this component. It constructs a detailed prompt that includes:
○	A system persona ("Urbanvind Commuter Chatbot").
○	The user's determined commuter profile.
○	The summary of the survey data.
○	The simulated real-time crowding data.
○	The user's specific query.
This comprehensive prompt allows the LLM to generate highly contextual and nuanced responses that are more effective than simple pre-scripted answers.
3. Application Flow
The bot's user experience is managed by a state machine implemented with st.session_state.
●	chat_phase = "questions": The application starts in this phase. The bot presents a series of multiple-choice questions one at a time. The user's answers are stored in st.session_state.user_answers.
●	chat_phase = "determining_profile": Once all questions are answered, the bot transitions to this phase. It runs the user's answers through the determine_commuter_profile function to assign a profile. A loading spinner is shown to the user during this process.
●	chat_phase = "chatting": After the profile is determined, the bot transitions to the main chat interface. The user's profile is displayed for reference, and the user can now type in their queries. Each query triggers a new call to the Gemini API with the combined contextual data.
4. Limitations and Future Work
●	Simulated Data: The current version uses simulated crowding data. A more advanced version would connect to a real-time public transit API (e.g., from an operator like NS or a regional transport authority) to provide genuinely live information.
●	API Key Management: The API key is currently hard-coded. For a production-ready application, it should be managed securely, for instance, using environment variables.
●	Dynamic Profile Updates: The current profile is static for the duration of the session. A more sophisticated system could allow the profile to be refined or updated based on subsequent user conversations.
●	User Authentication: The current system does not have user authentication. Future versions could integrate with Firebase Authentication to persist user profiles and chat history across sessions.
