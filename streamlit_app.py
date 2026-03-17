import streamlit as st

# Define the pages
Home_Page = st.Page("Home_Page.py", title="Home_Page", icon="🎈")
Scenario_1 = st.Page("Scenario_1.py", title="Scenerio_1", icon="❄️")
Scenario_2 = st.Page("Scenario_2.py", title="Scenerio_2", icon="❄️")
Scenario_3 = st.Page("Scenario_3.py", title="Scenerio_3", icon="❄️")
Scenario_4 = st.Page("Scenario_4.py", title="Scenerio_4", icon="❄️")
Scenario_5 = st.Page("Scenario_5.py", title="Scenerio_5", icon="❄️")

# Set up navigation
pg = st.navigation([Home_Page, Scenario_1, Scenario_2, Scenario_3, Scenario_4, Scenario_5])

# Run the selected page
pg.run()