import streamlit as st
import json
import pandas as pd
from google import genai

# ---------------------------------
# 1. Page configuration
# ---------------------------------
st.set_page_config(
    page_title="AI Travel Planner & Budget Estimator",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ AI Travel Planner & Budget Estimator")
st.write("Plan your dream vacation, estimate real-time costs, and explore map locations!")

# ---------------------------------
# 2. Sidebar configuration & trip parameters
# ---------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

    model_name = st.selectbox(
        "Choose model",
        ["gemini-3.8-flash",       # Standard, fast, and balanced model
        "gemini-3.5-flash-lite",  # Low cost, fast response times
        "gemini-3.1-pro"]
    )

    st.markdown("---")
    st.header("🗺️ Trip Preferences")
    
    destination = st.text_input("Destination", "Goa, India")
    days = st.slider("Trip Duration (Days)", 1, 14, 3)
    pace = st.selectbox("Travel Pace", ["Relaxed", "Balanced", "Fast-Packed"])
    daily_budget = st.number_input("Daily Budget per person (INR)", min_value=1000, value=5000, step=500)
    
    generate_plan_btn = st.button("🚀 Generate Itinerary")

# ---------------------------------
# 3. Initialize chat & plan state
# ---------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

# ---------------------------------
# 4. Helper function to query Gemini with Structured JSON
# ---------------------------------
def generate_travel_plan(dest, duration, travel_pace, budget, key, model):
    client = genai.Client(api_key=key)

    prompt = f"""
    Create a detailed travel itinerary for {duration} days in {dest}.
    Travel pace: {travel_pace}.
    Daily budget limit: {budget} INR per person.

    You MUST respond with valid JSON matching strictly this structure:
    {{
      "summary": "Brief travel overview text",
      "total_estimated_budget": 15000,
      "budget_breakdown": {{
          "stay": 6000,
          "food": 4000,
          "activities": 3000,
          "transport": 2000
      }},
      "itinerary": [
          {{
              "day": 1,
              "title": "Day title",
              "activities": ["Activity 1", "Activity 2"],
              "location_name": "Popular Spot Name",
              "latitude": 15.2993,
              "longitude": 74.1240
          }}
      ]
    }}
    Do not add markdown backticks outside the JSON string.
    """

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    
    # Clean output text to parse JSON safely
    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    return json.loads(raw_text.strip())

# ---------------------------------
# 5. Handle plan generation trigger
# ---------------------------------
if generate_plan_btn:
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    else:
        with st.spinner("Crafting your personalized itinerary..."):
            try:
                plan_data = generate_travel_plan(destination, days, pace, daily_budget, api_key, model_name)
                st.session_state.current_plan = plan_data
                st.success("Itinerary successfully created!")
            except Exception as e:
                st.error(f"Failed to generate plan: {e}")

# ---------------------------------
# 6. Display Dashboard (Map + Metrics)
# ---------------------------------
if st.session_state.current_plan:
    plan = st.session_state.current_plan

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📍 Interactive Location Map")
        map_data = []
        for item in plan.get("itinerary", []):
            if "latitude" in item and "longitude" in item:
                map_data.append({
                    "lat": item["latitude"],
                    "lon": item["longitude"],
                    "location": item["location_name"]
                })
        
        if map_data:
            df_map = pd.DataFrame(map_data)
            st.map(df_map)
        else:
            st.info("No coordinates found for mapping.")

    with col2:
        st.subheader("💰 Estimated Budget")
        st.metric("Total Estimated Cost", f"₹ {plan.get('total_estimated_budget', 0):,}")
        
        breakdown = plan.get("budget_breakdown", {})
        if breakdown:
            st.write("**Breakdown:**")
            st.write(f"🏨 Stay: ₹ {breakdown.get('stay', 0):,}")
            st.write(f"🍽️ Food: ₹ {breakdown.get('food', 0):,}")
            st.write(f"🎟️ Activities: ₹ {breakdown.get('activities', 0):,}")
            st.write(f"🚕 Local Transport: ₹ {breakdown.get('transport', 0):,}")

    st.markdown("---")
    st.subheader("🗓️ Day-by-Day Itinerary")

    export_text = f"# Travel Itinerary: {destination}\n\n"
    export_text += f"Total Estimated Budget: ₹{plan.get('total_estimated_budget', 0)}\n\n"

    for day in plan.get("itinerary", []):
        with st.expander(f"Day {day['day']}: {day['title']} ({day['location_name']})"):
            for act in day.get("activities", []):
                st.write(f"• {act}")
            export_text += f"## Day {day['day']}: {day['title']}\n"
            for act in day.get("activities", []):
                export_text += f"- {act}\n"
            export_text += "\n"

    # Export Button
    st.download_button(
        label="📥 Download Itinerary (Markdown)",
        data=export_text,
        file_name=f"{destination.lower().replace(' ', '_')}_itinerary.md",
        mime="text/markdown"
    )

st.markdown("---")

# ---------------------------------
# 7. Conversational Chatbot Assistant
# ---------------------------------
st.subheader("💬 Travel Assistant Chat")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_question = st.chat_input("Ask about places to eat, hotel tips, or packing lists...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    if not api_key:
        answer = "Please enter your Gemini API key in the sidebar to chat with the travel assistant."
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            context_str = f"Destination: {destination}, Duration: {days} days, Daily Budget: ₹{daily_budget}."
            if st.session_state.current_plan:
                context_str += f"\nActive Plan Summary: {st.session_state.current_plan.get('summary', '')}"

            instructions = f"""
            You are a knowledgeable, helpful travel assistant.
            Current trip context:
            {context_str}

            Provide helpful advice on packing, food options, local customs, or trip modifications.
            Keep responses clear and concise.
            """

            history = st.session_state.messages[-10:]
            contents = [f"SYSTEM: {instructions}"]
            for msg in history:
                contents.append(f"{msg['role'].upper()}: {msg['content']}")

            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            answer = response.text or "I couldn't process your request."
            
        except Exception as e:
            answer = f"Error communicating with Gemini: {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# ---------------------------------
# 8. Clear Conversation & State
# ---------------------------------
if st.sidebar.button("Clear Session"):
    st.session_state.messages = []
    st.session_state.current_plan = None
    st.rerun()
