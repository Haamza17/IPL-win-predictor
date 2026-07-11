
from flask import Flask, render_template, request, jsonify
import random
import joblib
import pandas as pd

app = Flask(__name__)

# ============================================================
# Load the real trained model + supporting data
# ============================================================
model = joblib.load('models/ipl_model.pkl')
scaler = joblib.load('models/ipl_scaler.pkl')
df_pred = joblib.load('models/df_pred.pkl')
df_mt_combined = joblib.load('models/df_mt_combined.pkl')
df_players = joblib.load('models/df_players.pkl')
# The exact 3 features the model was trained on, in the exact order the
# scaler expects them — this MUST match feature_columns_trimmed from your notebook.
FEATURE_COLUMNS = ['team1_rating', 'team1_bowling_strength', 'team2_bowling_strength']

TEAM_NAMES = df_pred['Team Name'].tolist()

# ============================================================
# Badge short-codes + colors for each team — real IPL logos are
# trademarked, so we render original circular monogram badges instead.
# (Ratings/strengths themselves come from df_pred, not from here.)
# ============================================================
TEAM_BADGES = {
    "Chennai Super Kings":          {"short": "CSK",  "color": "#F2C14E"},
    "Mumbai Indians":               {"short": "MI",   "color": "#2F8FFF"},
    "Royal Challengers Bengaluru":  {"short": "RCB",  "color": "#D6303F"},
    "Kolkata Knight Riders":        {"short": "KKR",  "color": "#7C5CFC"},
    "Sunrisers Hyderabad":          {"short": "SRH",  "color": "#F2994A"},
    "Delhi Capitals":               {"short": "DC",   "color": "#1656C9"},
    "Punjab Kings":                 {"short": "PBKS", "color": "#B71C3C"},
    "Rajasthan Royals":             {"short": "RR",   "color": "#EC4899"},
    "Gujarat Titans":               {"short": "GT",   "color": "#1B4965"},
    "Lucknow Super Giants":         {"short": "LSG",  "color": "#06B6D4"},
}

DEFAULT_BADGE = {"short": "??", "color": "#4B5A73"}


def get_team_row(team_name):
    """Look up a team's row in df_pred, or None if it's not found."""
    match = df_pred[df_pred['Team Name'] == team_name]
    return match.iloc[0] if len(match) else None


def get_recent_form_sequence(team_name, history_df, n=5):
    """Last n results for a team, oldest to most recent, as a list of 'W'/'L'."""
    team_matches = history_df[
        (history_df['team1'] == team_name) | (history_df['team2'] == team_name)
    ].sort_values('date').tail(n)
    return ['W' if winner == team_name else 'L' for winner in team_matches['match_winner']]


# ============================================================
# PAGE ROUTES
# ============================================================
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stats')
def stats_page():
    return render_template('stats.html')


@app.route('/teams')
def teams_page():
    return render_template('teams.html')


# ============================================================
# API ROUTES
# ============================================================
@app.route('/api/teams')
def get_teams():
    return jsonify(TEAM_NAMES)


@app.route('/api/teams-meta')
def get_teams_meta():
    result = []
    for team_name in TEAM_NAMES:
        row = get_team_row(team_name)
        badge = TEAM_BADGES.get(team_name, DEFAULT_BADGE)
        result.append({
            "name": team_name,
            "short": badge["short"],
            "color": badge["color"],
            "rating": float(row['Team Rating']),
        })
    return jsonify(result)



@app.route('/api/team-stats')
def get_team_stats():
    team_name = request.args.get('team')
    if team_name not in TEAM_NAMES:
        return jsonify({'error': 'Unknown team'}), 400

    team_players = df_players[df_players['team_name'] == team_name]
    rows = []
    for _, p in team_players.iterrows():
        rows.append({
            'name': p['player'],
            'batting_average': None if pd.isna(p['eff_batting_avg']) else float(p['eff_batting_avg']),
            'strike_rate': None if pd.isna(p['eff_batting_sr']) else float(p['eff_batting_sr']),
            'bowling_average': None if pd.isna(p['eff_bowling_avg']) else float(p['eff_bowling_avg']),
            'economy': None if pd.isna(p['eff_bowling_econ']) else float(p['eff_bowling_econ']),
        })
    return jsonify(rows)


@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    team1 = data.get('team1')
    team2 = data.get('team2')

    if not team1 or not team2:
        return jsonify({'error': 'Both teams are required'}), 400

    team1_row = get_team_row(team1)
    team2_row = get_team_row(team2)

    if team1_row is None or team2_row is None:
        return jsonify({'error': 'Unknown team name'}), 400

    # ---- Build the exact 3 features the model was trained on ----
    feature_values = {
        'team1_rating': float(team1_row['Team Rating']),
        'team1_bowling_strength': float(team1_row['Bowling Strength']),
        'team2_bowling_strength': float(team2_row['Bowling Strength']),
    }
    X_new = pd.DataFrame([feature_values])[FEATURE_COLUMNS]  # enforce correct column order
    X_scaled = scaler.transform(X_new)

    proba = model.predict_proba(X_scaled)[0]
    # model.classes_ == [0, 1] -> index 1 is "team1_won", index 0 is "team2_won"
    team1_win_probability = float(proba[1])
    team2_win_probability = float(proba[0])

    # ---- Extra values for the comparison cards (not fed to the model itself) ----
    features = {
        'team1_rating': feature_values['team1_rating'],
        'team2_rating': float(team2_row['Team Rating']),
        'team1_batting_strength': float(team1_row['Batting Strength']),
        'team2_batting_strength': float(team2_row['Batting Strength']),
        'team1_bowling_strength': feature_values['team1_bowling_strength'],
        'team2_bowling_strength': feature_values['team2_bowling_strength'],
        'team1_star_players': [f"{int(team1_row['Star Presence'])} recognized players in squad"],
        'team2_star_players': [f"{int(team2_row['Star Presence'])} recognized players in squad"],
        'team1_form_sequence': get_recent_form_sequence(team1, df_mt_combined),
        'team2_form_sequence': get_recent_form_sequence(team2, df_mt_combined),
    }

    return jsonify({
        'team1_win_probability': team1_win_probability,
        'team2_win_probability': team2_win_probability,
        'features': features,
    })


if __name__ == '__main__':
    app.run(debug=True)
