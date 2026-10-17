import streamlit as st
import json
import pandas as pd
from google import genai

# ---------------------------------
# 1. Page configuration
# ---------------------------------
st.set_page_config(
    page_title="Hackathon Coordinator Copilot",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Hackathon & Competition Coordinator")
st.write("Generate tracks, match mentors to teams, and summarize submissions effortlessly!")

# ---------------------------------
# 2. Sidebar configuration & settings
# ---------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

    model_name = st.selectbox(
        "Choose model",
        ["gemini-3.8-flash",       
        "gemini-3.5-flash-lite",
        "gemini-3.1-pro"]
    )

    st.markdown("---")
    st.header("🎯 Hackathon Parameters")
    
    event_name = st.text_input("Event Name", "TechSprint 2026")
    theme = st.text_input("Theme / Focus Area", "AI for Sustainability & Green Tech")
    duration = st.selectbox("Event Duration", ["24 Hours", "36 Hours", "48 Hours", "1 Week"])

# ---------------------------------
# 3. Initialize chat & state variables
# ---------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "hackathon_data" not in st.session_state:
    st.session_state.hackathon_data = None

if "match_data" not in st.session_state:
    st.session_state.match_data = None

if "summary_data" not in st.session_state:
    st.session_state.summary_data = None

# ---------------------------------
# 4. Main App Tabs
# ---------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "💡 Tracks & Problem Statements", 
    "🤝 Judge & Mentor Allocator", 
    "📝 Submission Summarizer", 
    "💬 Coordinator Chat"
])

# =========================================================================
# TAB 1: Problem Statement & Track Generator
# =========================================================================
with tab1:
    st.subheader("💡 Generate Tracks, Problems & Judging Rubric")
    
    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        num_tracks = st.slider("Number of Tracks", 1, 5, 3)
    with col_t2:
        target_audience = st.selectbox("Target Participant Level", ["Beginner", "Intermediate / College", "Professional / Advanced"])
    
    generate_tracks_btn = st.button("🚀 Generate Hackathon Package")

    if generate_tracks_btn:
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with st.spinner("Brainstorming tracks, rubrics, and problem statements..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    You are a lead technical hackathon organizer. Generate a structured JSON package for an event.
                    Event Name: {event_name}
                    Theme: {theme}
                    Duration: {duration}
                    Number of Tracks: {num_tracks}
                    Target Audience Level: {target_audience}

                    Output MUST strictly be valid JSON matching this structure (no extra keys):
                    {{
                        "event_overview": "Short high-level description",
                        "tracks": [
                            {{
                                "track_name": "Track Name",
                                "problem_statement": "Detailed problem statement",
                                "expected_deliverable": "What participants should build",
                                "tech_stack_suggestions": ["Python", "Streamlit", "TensorFlow"]
                            }}
                        ],
                        "judging_rubric": [
                            {{"criterion": "Innovation & Originality", "weight_percentage": 30, "description": "How unique is the solution?"}},
                            {{"criterion": "Technical Complexity", "weight_percentage": 30, "description": "Quality and depth of code/architecture"}},
                            {{"criterion": "Feasibility & Impact", "weight_percentage": 20, "description": "Real-world applicability"}},
                            {{"criterion": "UI/UX & Presentation", "weight_percentage": 20, "description": "Design quality and demo clarity"}}
                        ]
                    }}
                    """

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    
                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]

                    st.session_state.hackathon_data = json.loads(raw_text.strip())
                    st.success("Hackathon track package created!")
                except Exception as e:
                    st.error(f"Error generating tracks: {e}")

    # Display generated tracks
    if st.session_state.hackathon_data:
        hdata = st.session_state.hackathon_data
        st.write(f"**Overview:** {hdata.get('event_overview', '')}")
        
        st.markdown("### 🎯 Event Tracks")
        for idx, trk in enumerate(hdata.get("tracks", []), 1):
            with st.expander(f"Track {idx}: {trk['track_name']}", expanded=True):
                st.write(f"**Problem Statement:** {trk['problem_statement']}")
                st.write(f"**Expected Deliverable:** {trk['expected_deliverable']}")
                st.write(f"**Recommended Stack:** {', '.join(trk.get('tech_stack_suggestions', []))}")

        st.markdown("### 📊 Judging Rubric")
        rubric_df = pd.DataFrame(hdata.get("judging_rubric", []))
        st.table(rubric_df)

# =========================================================================
# TAB 2: Judge & Mentor Allocator
# =========================================================================
with tab2:
    st.subheader("🤝 Match Mentors/Judges to Teams")
    st.write("Enter mentor profiles and team technical stacks to find optimal pairings.")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        mentors_input = st.text_area(
            "Mentors & Experts List (one per line)",
            "Dr. Sharma - Domain: Climate Tech, Python, Data Science\n"
            "Ananya R. - Domain: Web Dev, UI/UX, React, Streamlit\n"
            "Rahul V. - Domain: Cybersecurity, Cloud, AWS, DevOps"
        )
    with col_m2:
        teams_input = st.text_area(
            "Competing Teams List (one per line)",
            "Team EcoBytes - Project: AI Carbon Tracker (Stack: Python, Gemini API)\n"
            "Team SecureNet - Project: Cloud Firewall Dashboard (Stack: AWS, Docker)\n"
            "Team GreenUI - Project: Waste Management Portal (Stack: React, Node.js)"
        )

    match_btn = st.button("⚡ Run Mentor Allocation Engine")

    if match_btn:
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with st.spinner("Matching mentors based on skills and team stacks..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    You are a hackathon logistics manager. Match mentors to teams based on expertise overlap.
                    Mentors:
                    {mentors_input}

                    Teams:
                    {teams_input}

                    Return strictly a JSON list of objects:
                    [
                        {{
                            "team": "Team Name",
                            "assigned_mentor": "Mentor Name",
                            "match_reason": "Brief technical justification for match",
                            "confidence_score": "95%"
                        }}
                    ]
                    """

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]

                    st.session_state.match_data = json.loads(raw_text.strip())
                except Exception as e:
                    st.error(f"Error matching mentors: {e}")

    if st.session_state.match_data:
        st.markdown("### 📋 Mentor Allocation Matrix")
        match_df = pd.DataFrame(st.session_state.match_data)
        st.dataframe(match_df, use_container_width=True)

# =========================================================================
# TAB 3: Submission Review Summarizer
# =========================================================================
with tab3:
    st.subheader("📝 Project Submission Reviewer")
    st.write("Paste a team's project writeup or GitHub Readme to get a quick evaluation summary.")

    sub_team = st.text_input("Team Name", "Team EcoBytes")
    sub_text = st.text_area(
        "Paste Project Summary / README",
        "Project: EcoTracker\n"
        "We built an AI tool using Streamlit and Gemini API that calculates household carbon footprints. "
        "Users enter monthly energy usage, and the app plots charts using Pandas. "
        "We implemented local state caching, but ran out of time for mobile responsive UI."
    )

    summarize_btn = st.button("🔍 Evaluate Submission")

    if summarize_btn:
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with st.spinner("Analyzing project submission..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    You are an expert hackathon judge. Review this project submission for team '{sub_team}'.
                    Submission Content:
                    {sub_text}

                    Provide a concise JSON evaluation:
                    {{
                        "team_name": "{sub_team}",
                        "key_strengths": ["Strength 1", "Strength 2"],
                        "potential_weaknesses": ["Weakness 1"],
                        "suggested_questions_for_demo": ["Question 1", "Question 2"],
                        "preliminary_score_estimate": "8/10"
                    }}
                    """

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]

                    st.session_state.summary_data = json.loads(raw_text.strip())
                except Exception as e:
                    st.error(f"Evaluation error: {e}")

    if st.session_state.summary_data:
        sdata = st.session_state.summary_data
        st.success(f"Preliminary Score: {sdata.get('preliminary_score_estimate', 'N/A')}")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.write("**Key Strengths:**")
            for strg in sdata.get("key_strengths", []):
                st.write(f"✅ {strg}")
        with col_s2:
            st.write("**Potential Weaknesses / Gaps:**")
            for wk in sdata.get("potential_weaknesses", []):
                st.write(f"⚠️ {wk}")

        st.write("**Suggested Questions for Live Demo:**")
        for q in sdata.get("suggested_questions_for_demo", []):
            st.write(f"❓ {q}")

# =========================================================================
# TAB 4: Coordinator Chat
# =========================================================================
with tab4:
    st.subheader("💬 Hackathon Coordinator Assistant")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input("Ask about logistics, rule creation, tie-breaker policies...")

    if user_question:
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        if not api_key:
            answer = "Please enter your Gemini API Key in the sidebar to use the assistant."
        else:
            try:
                client = genai.Client(api_key=api_key)

                instructions = f"""
                You are an experienced Hackathon Coordinator assisting in managing {event_name}.
                Theme: {theme}
                Duration: {duration}

                Help organizers write announcement emails, resolve team disputes, generate sample FAQs, 
                and refine hackathon rules. Keep answers concise, actionable, and structured.
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
# 5. Clear Session
# ---------------------------------
if st.sidebar.button("Clear Session"):
    st.session_state.messages = []
    st.session_state.hackathon_data = None
    st.session_state.match_data = None
    st.session_state.summary_data = None
    st.rerun()
