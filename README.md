[README.md](https://github.com/user-attachments/files/29930834/README.md)
# IPL Match Predictor

A machine learning web app that predicts the winner of an IPL match between any two teams, built end-to-end: data cleaning, feature engineering, model validation, and a Flask + HTML/CSS/JS frontend.

## What it does

Pick any two IPL teams, and the model returns a win probability for each, based on:
- Current team rating (derived from points table standing and net run rate)
- Bowling strength (derived from squad-wide bowling averages and economy rates)

The app has three pages:
- **Home** — pick a matchup, get a prediction with a visual breakdown of batting strength, bowling strength, team rating, star presence, and recent form
- **Stats** — browse every player's combined batting and bowling stats, team by team
- **Teams** — a grid of all 10 franchises with their current rating

## Model & methodology

The headline result isn't a bare accuracy number — it's a validated finding about which features actually matter.

Several feature sets were compared using 5-fold cross-validation (not a single train/test split, which proved unreliable at this sample size):

| Model | Features | Mean CV Accuracy |
|---|---|---|
| Full feature set | 11 features (rating, batting/bowling strength, star presence, head-to-head, recent form) | 0.546 |
| `team1_rating` only | 1 feature | 0.650 |
| **Final model** | **`team1_rating`, `team1_bowling_strength`, `team2_bowling_strength`** | **0.711** |
| Naive baseline (always guess the majority class) | — | 0.553 |

The 3-feature model was selected using L1-regularized logistic regression, which shrank 8 of the original 11 features to exactly zero. It outperforms both the full feature set and the single-feature model, and clears the naive baseline by a meaningful margin.

**Why so few features, and why so few matches?** The dataset is 38 matches from the current IPL season. That's a small sample for a classification model — cross-validation was used specifically to get an honest, stable estimate of performance rather than trusting a single lucky (or unlucky) split. A larger, multi-season dataset with season-specific player stats would be the natural next step to build a more robust model.

## Known data limitations

- A handful of well-known players (e.g. Rohit Sharma, Rashid Khan) have incomplete stats in the source data used for Batting/Bowling Strength — this likely understates the strength of the teams they play for. See `notebook/datacleaning.ipynb` for the full list flagged during data cleaning.
- Team badges on the Teams and Home pages are original circular monogram designs (team initials on the team's jersey color), not official franchise logos, since real IPL logos are trademarked.

## Project structure

```
IPL_predictor/
├── app.py                  # Flask backend — routes, API endpoints, prediction logic
├── requirements.txt
├── static/                 # CSS and JavaScript for all 3 pages
├── templates/              # HTML templates (index, stats, teams)
├── models/                 # Trained model, scaler, and supporting dataframes (.pkl)
├── notebook/
│   └── datacleaning.ipynb  # Full data cleaning, feature engineering, and model training
└── data/                   # Raw source CSVs (matches, batting/bowling stats, squads, points table)
```

## Running it locally

```bash
git clone <your-repo-url>
cd IPL_predictor
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Tech stack

- **Data & modeling:** pandas, scikit-learn (Logistic Regression, L1 feature selection, 5-fold cross-validation)
- **Backend:** Flask
- **Frontend:** vanilla HTML, CSS, and JavaScript (no framework)

## Possible future improvements

- Multi-season, per-season player stats (rather than current-season and career totals) to properly validate historical matches instead of just the current season
- Fill in the known gaps in star player data
- Expand beyond logistic regression to compare against tree-based models (e.g. gradient boosting) now that cross-validation infrastructure is in place
