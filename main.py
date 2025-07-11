import streamlit as st
import plotly.graph_objects as go
from streamlit_sortables import sort_items

# --------------------------------------------
# Scoring function
# --------------------------------------------
def calculate_match_score(
    provider_priorities,
    provider_comp_range,
    provider_states,
    provider_values,
    job_hours,
    job_weekend,
    job_on_call,
    job_salary_min,
    job_salary_max,
    sign_on_bonus,
    job_state,
    job_region,
    job_values
):
    # Priority weights
    weights = {}
    weight_map = {0: 0.4, 1: 0.3, 2: 0.2, 3: 0.1}
    for i, p in enumerate(provider_priorities):
        weights[p] = weight_map[i]

    # Work-Life Score
    work_score = max(0, min(100, (80 - job_hours) * 2.5))
    if job_weekend:
        work_score -= 10
    if job_on_call:
        work_score -= 10
    work_score = max(0, work_score)

    # Compensation Score
    job_salary = (job_salary_min + job_salary_max) / 2 + sign_on_bonus
    preferred_min, preferred_max = provider_comp_range
    if job_salary < preferred_min:
        comp_score = 0
    elif job_salary > preferred_max:
        comp_score = 100
    else:
        comp_score = ((job_salary - preferred_min) / (preferred_max - preferred_min)) * 100

    # Location Score
    region_map = {
        "WEST": ["California", "Oregon"],
        "MIDWEST": ["Illinois", "Ohio"]
    }
    provider_regions = set()
    for region, states in region_map.items():
        if any(state in provider_states for state in states):
            provider_regions.add(region)

    if job_state in provider_states:
        loc_score = 100
    elif job_region in provider_regions:
        loc_score = 50
    else:
        loc_score = 0

    # Values Score
    matches = len(set(provider_values) & set(job_values))
    value_score = {3: 100, 2: 66, 1: 33, 0: 0}[matches]

    # Final Score
    total_score = (
        work_score * weights.get("Work-Life Balance", 0) +
        comp_score * weights.get("Compensation", 0) +
        loc_score * weights.get("Location", 0) +
        value_score * weights.get("Values", 0)
    )

    breakdown = {
        "Work-life balance": round(work_score),
        "Compensation": round(comp_score),
        "Location": round(loc_score),
        "Values": round(value_score),
        "Total": round(total_score)
    }

    return breakdown

# --------------------------------------------
# Streamlit Layout
# --------------------------------------------

st.set_page_config(page_title="Job Match Calculator", layout="wide")
st.markdown("<h1 style='text-align: center;'>Job Match Scoring Tool</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 1.5, 1])

# --------------------------------------------
# PROVIDER SECTION
# --------------------------------------------
with col1:
    st.markdown("<h3 style='margin-bottom: 0.25rem;'>🔹 Provider Preferences</h3>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div >", unsafe_allow_html=True)

        # Priority Ranking
        st.markdown("<h5 style='margin-top: 0.5rem;'>🧠 Rank Your Priorities (Drag to Reorder)</h5>", unsafe_allow_html=True)
        priority_items = ["Work-Life Balance", "Compensation", "Location", "Values"]
        sorted_priorities = sort_items(priority_items, direction="vertical")
        if sorted_priorities:
            for i, item in enumerate(sorted_priorities, 1):
                st.write(f"**{i}. {item}**")

        # Compensation Range
        st.markdown("<h5 style='margin-top: 1rem;'>💰 Preferred Compensation Range</h5>", unsafe_allow_html=True)
        comp_range = st.slider(
            "Select your expected compensation range:",
            min_value=0, max_value=500000, value=(100000, 300000), step=5000, format="₹%d"
        )
        st.write(f"Selected range: ₹{comp_range[0]:,} – ₹{comp_range[1]:,}")

        # Location
        st.markdown("<h5 style='margin-top: 1rem;'>📍 Preferred Work Location(s)</h5>", unsafe_allow_html=True)
        st.markdown("**WEST**")
        west_ca = st.checkbox("California", key="west_ca")
        west_or = st.checkbox("Oregon", key="west_or")

        st.markdown("**MIDWEST**")
        midwest_il = st.checkbox("Illinois", key="midwest_il")
        midwest_oh = st.checkbox("Ohio", key="midwest_oh")

        selected_states = []
        if west_ca: selected_states.append("California")
        if west_or: selected_states.append("Oregon")
        if midwest_il: selected_states.append("Illinois")
        if midwest_oh: selected_states.append("Ohio")

        st.markdown(f"✅ Selected States: {', '.join(selected_states) if selected_states else 'None'}")

        # Values
        st.markdown("<h5 style='margin-top: 1rem;'>💡 Your Top 3 Personal Values</h5>", unsafe_allow_html=True)
        value_options = [
            "Integrity", "Collaboration", "Innovation",
            "Compassion", "Accountability", "Diversity"
        ]
        selected_values = st.multiselect(
            "Select exactly 3 values that matter most to you:",
            options=value_options,
            max_selections=3
        )
        if len(selected_values) != 3:
            st.warning("⚠️ Please select exactly 3 values.")
        else:
            st.success(f"✅ You selected: {', '.join(selected_values)}")

        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------
# RECRUITER SECTION
# --------------------------------------------
with col2:
    st.markdown("### 🔸 Recruiter / Job Input")
    with st.container():
        st.markdown("<div >", unsafe_allow_html=True)

        # Work-Life
        st.markdown("<h5 style='margin-top: 0.5rem;'>🧘 Work-Life Balance</h5>", unsafe_allow_html=True)
        job_hours = st.slider("Average hours/week", min_value=40, max_value=80, value=50, step=10)
        job_weekend = st.checkbox("Weekend shifts?", key="job_weekend")
        job_on_call = st.checkbox("On-call shifts?", key="job_on_call")

        # Compensation
        st.markdown("<h5 style='margin-top: 1rem;'>💰 Compensation</h5>", unsafe_allow_html=True)
        salary_range = st.slider(
            "Salary Range (Base)" ,
            min_value=0 , max_value=500000 , value=(120000 , 180000) , step=5000 , format="₹%d"
        )
        salary_min , salary_max = salary_range
        st.write(f"Selected range: ₹{salary_min:,} – ₹{salary_max:,}")
        sign_on_bonus = st.number_input("Sign-on Bonus (if any)", min_value=0, max_value=100000, value=10000, step=1000)

        # Location
        st.markdown("<h5 style='margin-top: 1rem;'>📍 Job Location</h5>", unsafe_allow_html=True)
        region_map = {
            "WEST": ["California", "Oregon"],
            "MIDWEST": ["Illinois", "Ohio"]
        }

        grouped_states = []
        for region, states in region_map.items():
            grouped_states.extend([f"{region} - {state}" for state in states])
        selected_state_label = st.selectbox("Job State", options=grouped_states)
        job_region, job_state = selected_state_label.split(" - ")
        st.markdown(f"**Region auto-selected:** {job_region}")

        # Values
        st.markdown("<h5 style='margin-top: 1rem;'>🧠 Top 3 Job/Company Values</h5>", unsafe_allow_html=True)
        job_values = st.multiselect(
            "Select top 3 values for this job/company:",
            options=value_options,
            max_selections=3
        )
        if len(job_values) != 3:
            st.warning("⚠️ Please select exactly 3 values.")
        else:
            st.success(f"✅ You selected: {', '.join(job_values)}")

        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------
# SCORE + SMART FIT PREVIEW
# --------------------------------------------
with col3:
    st.markdown("### 🎯 Match Score")

    if (
        sorted_priorities and
        len(selected_values) == 3 and
        len(job_values) == 3 and
        selected_states
    ):
        breakdown = calculate_match_score(
            provider_priorities=sorted_priorities,
            provider_comp_range=comp_range,
            provider_states=selected_states,
            provider_values=selected_values,
            job_hours=job_hours,
            job_weekend=job_weekend,
            job_on_call=job_on_call,
            job_salary_min=salary_min,
            job_salary_max=salary_max,
            sign_on_bonus=sign_on_bonus,
            job_state=job_state,
            job_region=job_region,
            job_values=job_values
        )
        match_score = breakdown["Total"]
    else:
        match_score = 0
        breakdown = {
            "Work-life balance": 0,
            "Compensation": 0,
            "Location": 0,
            "Values": 0,
            "Total": 0
        }

    # Gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=match_score,
        title={'text': "Total Match Score", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 75], 'color': "gray"},
                {'range': [75, 100], 'color': "lightgreen"}
            ],
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

    # Fit Breakdown
    st.markdown("### 🧠 Smart Fit Preview")
    st.success(f"✅ {match_score}% overall match")
    st.write(f"• Work-life balance: **{breakdown['Work-life balance']}**")
    st.write(f"• Compensation: **{breakdown['Compensation']}**")
    st.write(f"• Location: **{breakdown['Location']}**")
    st.write(f"• Values: **{breakdown['Values']}**")
