import streamlit as st
import pandas as pd
from pymongo import MongoClient


# Initialize MongoDB connection (runs only once)
@st.cache_resource
def init_connection():
    return MongoClient("mongodb+srv://st.secrets.db_username:st.secrets.db_pswd@st.secrets.cluster_name.iy27erl.mongodb.net/")

client = init_connection()
db = client["chess_tournament"]

# Access collections
results_col = db["match_results"]
scores_col = db["player_scores"]

# Players
players = ["Ankush", "Aman", "Yogesh", "Jaspreet"]

# Page Config
st.set_page_config(page_title="Hybrid Chess Tournament", layout="wide")

ADMIN_PASSWORD = "chess123"

# --- Load or Initialize Mongo Data ---
def load_match_results():
    match_structure = {
        1: {"players": ["Ankush", "Aman"], "winner": ""},
        2: {"players": ["Yogesh", "Jaspreet"], "winner": ""},
        3: {"players": ["Ankush", "Yogesh"], "winner": ""},
        4: {"players": ["Aman", "Jaspreet"], "winner": ""},
        5: {"players": ["Ankush", "Jaspreet"], "winner": ""},
        6: {"players": ["Aman", "Yogesh"], "winner": ""},
        7: {"players": [], "winner": ""},  # Semi Final 1
        8: {"players": [], "winner": ""},  # Semi Final 2
        9: {"players": [], "winner": ""},  # Final
        10: {"players": [], "winner": ""}, # Third Place
    }
    results = {i: {"match_id": i, **match_structure[i]} for i in match_structure}
    for doc in results_col.find():
        results[doc["match_id"]] = doc
    return results

def load_scores():
    scores = {name: 0 for name in players}
    for doc in scores_col.find():
        scores.update(doc.get("scores", {}))
    return scores

def save_result(match_id, match_data):
    match_data = match_data.copy()
    match_data["match_id"] = match_id
    results_col.update_one(
        {"match_id": match_id},
        {"$set": match_data},
        upsert=True
    )

def save_scores(score_dict):
    scores_col.update_one(
        {"type": "score_data"},
        {"$set": {"scores": score_dict}},
        upsert=True
    )

def determine_finalists(scores):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_four = sorted_scores[:4]
    return [p[0] for p in top_four]

# Load match_results from Mongo
if "match_results" not in st.session_state:
    match_docs = list(results_col.find())
    if match_docs:
        st.session_state.match_results = {
            doc["match_id"]: {k: v for k, v in doc.items() if k not in ["_id", "match_id"]}
            for doc in match_docs
        }
    else:
        st.session_state.match_results = load_match_results()
        for mid, match in st.session_state.match_results.items():
            results_col.insert_one({"match_id": mid, **match})

# Load scores from Mongo
if "scores" not in st.session_state:
    scores_doc = scores_col.find_one({"type": "score_data"})
    if scores_doc:
        st.session_state.scores = scores_doc["scores"]
    else:
        default_scores = {name: 0 for name in players}
        st.session_state.scores = default_scores
        scores_col.insert_one({"type": "score_data", "scores": default_scores})

# --- Title ---
st.markdown("<div style='text-align: center;'><h1>♟️ Chess Tournament: Ankush, Aman, Yogesh, Jaspreet</h1></div>", unsafe_allow_html=True)

# --- Sidebar Admin Control ---
with st.sidebar:
    st.header("🔐 Admin Control")
    password_input = st.text_input("Enter admin password to update results", type="password")
    is_admin = password_input == ADMIN_PASSWORD
    if is_admin:
        st.success("Access granted: You can edit match results.")
    else:
        st.warning("Results are view-only unless you're admin.")

# --- Load State ---
m = st.session_state.match_results

# --- Progression Logic for Semis and Final ---
score_df = pd.DataFrame.from_dict(st.session_state.scores, orient="index", columns=["wins"]).reset_index()
score_df.columns = ["name", "wins"]
score_df = score_df.sort_values("wins", ascending=False)

if all(m[i]["winner"] for i in range(1, 7)) and not m[7]["players"]:
    top4 = determine_finalists(dict(zip(score_df["name"], score_df["wins"])))
    m[7]["players"] = [top4[0], top4[3]]  # Semi 1: 1st vs 4th
    m[8]["players"] = [top4[1], top4[2]]  # Semi 2: 2nd vs 3rd
    save_result(7, m[7])
    save_result(8, m[8])

if m[7]["winner"] and m[8]["winner"] and not m[9]["players"]:
    finalists = [m[7]["winner"], m[8]["winner"]]
    losers = [p for p in m[7]["players"] + m[8]["players"] if p not in finalists]
    m[9]["players"] = finalists       # Final
    m[10]["players"] = losers         # Third Place Match
    save_result(9, m[9])
    save_result(10, m[10])

# --- Layout Columns ---
col1, col2, col3 = st.columns([1.5, 2, 2])

# --- Column 1: Tournament Process ---
with col1:
    st.markdown("""
    ### Process of Tournament
    - **Group Stage**: Everyone plays each other once
    - **Matches**:
        - Match 1: Ankush vs Aman
        - Match 2: Yogesh vs Jaspreet
        - Match 3: Ankush vs Yogesh
        - Match 4: Aman vs Jaspreet
        - Match 5: Ankush vs Jaspreet
        - Match 6: Aman vs Yogesh
    - **Semi Final 1**: 1st vs 4th
    - **Semi Final 2**: 2nd vs 3rd
    - **Match 9**: Final (Winners of Semis)
    - **Match 10**: 3rd Place Match (Losers of Semis)
    """)

# --- Winner Dropdowns ---
for match_id in range(1, 11):
    match = m[match_id]
    if match["players"]:
        if match["winner"]:
            st.success(f"✅ Match {match_id} ({match['players'][0]} vs {match['players'][1]}) → Winner: {match['winner']}")
        elif is_admin:
            winner = st.selectbox(
                f"Pick Winner of Match {match_id} ({match['players'][0]} vs {match['players'][1]})",
                options=["Select"] + match["players"],
                key=f"match_{match_id}"
            )
            if winner != "Select":
                st.session_state.match_results[match_id]["winner"] = winner
                st.session_state.scores[winner] += 1
                save_result(match_id , st.session_state.match_results[match_id])
                save_scores(st.session_state.scores)
                st.rerun()

# --- Column 2: Upcoming Matches ---
with col2:
    st.markdown("### 📅 Upcoming Matches")
    upcoming = [
        {"Match": f"Match {mid}", "Fixture": f"{match['players'][0]} vs {match['players'][1]}"}
        for mid, match in m.items() if match["players"] and not match["winner"]
    ]
    if upcoming:
        st.table(pd.DataFrame(upcoming).reset_index(drop=True))
    else:
        winner_name = m[9].get("winner")
        if winner_name:
            st.markdown(f"All matches completed. **Winner: {winner_name}** 🏆")
        else:
            st.markdown("All matches completed.")

# --- Column 3: Scores ---
with col3:
    st.markdown("### 📊 Current Scores")

    final_scores = {p: 0 for p in players}
    for match in m.values():
        winner = match.get("winner")
        if winner:
            final_scores[winner] += 1

    def head_to_head(player1, player2):
        for match in m.values():
            if sorted(match.get("players", [])) == sorted([player1, player2]):
                return match.get("winner")
        return None

    sorted_players = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    i = 0
    while i < len(sorted_players) - 1:
        p1, w1 = sorted_players[i]
        p2, w2 = sorted_players[i+1]
        if w1 == w2:
            winner = head_to_head(p1, p2)
            if winner == p2:
                sorted_players[i], sorted_players[i+1] = sorted_players[i+1], sorted_players[i]
        i += 1

    rank_data = [{"Rank": i+1, "Player": p, "Wins": final_scores[p]} for i, (p, _) in enumerate(sorted_players)]
    st.table(pd.DataFrame(rank_data))

# --- Full Match Flow ---
st.markdown("---")
st.markdown("## 🧾 Full Match Flow")
flow = []
for mid, match in m.items():
    flow.append({
        "Match": f"Match {mid}",
        "Players": " vs ".join(match.get("players", [])),
        "Winner": match.get("winner", "")
    })
st.dataframe(pd.DataFrame(flow), use_container_width=True)
