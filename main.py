import pandas
import os
from scipy import stats
from datetime import datetime
from itertools import combinations
import variables

event_points = variables.event_points
points_curve = variables.points_curve
DIRECTORY = variables.DIRECTORY
RANKING_FILE_NAME = variables.RANKING_FILE_NAME
RANKING_AS_OF = variables.RANKING_AS_OF
DEPRECIATION_PERIOD = variables.DEPRECIATION_PERIOD
SHOWING_SCORE_BOOST = variables.SHOWING_SCORE_BOOST

def update_rankings(race_result_file):

    for (index, row) in race_result_file.iterrows():
        race_date = datetime.strptime(row.date, "%m/%d/%Y")
        rank_date = datetime.strptime(RANKING_AS_OF, "%m/%d/%Y")
        if (rank_date.date() - race_date.date()).days > DEPRECIATION_PERIOD or rank_date.date() < race_date.date():
            pass
        else:
            days_old = (rank_date.date() - race_date.date()).days
            row.race_weight = 1 - (days_old / DEPRECIATION_PERIOD)
            row.athlete_name = row.athlete_name.title()
            row.max_points = int(event_points.max_points[event_points.event == row.event])
            row.place = index + 1
            row.points_pct_max = float(points_curve.percent_of_max[points_curve.place == row.place])
            row.points = row.max_points * row.points_pct_max * row.race_weight
            if row.points > 0:
                results_dict["name"].append(row.athlete_name)
                results_dict["place"].append(row.place)
                results_dict["points"].append(row.points)
                results_dict["weight"].append(row.race_weight)
                # results_dict["event"].append(row.location)

    all_results = pandas.DataFrame(results_dict)
    grouped_results = all_results.groupby("name")["points"].sum().reset_index()
    grouped_results = grouped_results.sort_values(by="points", ascending=False).reset_index(drop=True)

    # ----- GET FINISH SCORE -----
    # For every athlete, get their average place. Then rank it (0 - 1, with 1 being the best) compared to the rest of the
    # field and add as a new column in the grouped_results dataframe:

    avg_places = [all_results.place[all_results.name == name].mean() for name in grouped_results.name]
    avg_place_ranks = [1 - (stats.percentileofscore(avg_places, avg_place) / 100) for avg_place in avg_places]
    grouped_results["finish_score"] = avg_place_ranks

    # ----- GET VOLUME SCORE -----
    # For every athlete, sum their race_weights from all results. Rank these weights (0 - 1, with 1 being the best)
    # compared to the rest of the field and add as a new column in the grouped_results dataframe:

    cum_race_weights = [all_results.weight[all_results.name == name].sum() for name in grouped_results.name]
    # gives a "race volume" score based on the percentile of the rank of an athlete's cumulative_weight:
    volume_scores = [stats.percentileofscore(cum_race_weights, weight) / 100 for weight in cum_race_weights]
    # alternatively, gives a "race volume" score based on the athlete's cumulative_weight as a % of the max
    # cumulative_weight:
    # max_weight = max(cum_race_weights)
    # race_weight_percentiles = [weight / max_weight for weight in cum_race_weights]
    grouped_results["volume_score"] = volume_scores

    # ----- CREATE SHOWING SCORE -----
    # Create a "showing score" which is a weighted average of the athlete's finish_score (based on average finish place)
    # and volume_score (based on the number of races within the eligible time frame and how recent they are) and add that
    # to the dataframe:
    FINISH_SCORE_WEIGHT = variables.FINISH_SCORE_WEIGHT
    VOLUME_SCORE_WEIGHT = 1 - FINISH_SCORE_WEIGHT
    showing_scores = [f * FINISH_SCORE_WEIGHT + v * VOLUME_SCORE_WEIGHT for (f, v) in zip(avg_place_ranks, volume_scores)]

    # ----- ADJUST POINTS BASED ON SHOWING SCORE TO GET RANKING POINTS -----
    ranking_points = [points + points * SHOWING_SCORE_BOOST * score for (points, score) in
                      zip(grouped_results.points, showing_scores)]
    grouped_results["ranking_score"] = ranking_points
    final_ranking = grouped_results.sort_values(by="ranking_score", ascending=False).reset_index(drop=True)
    final_ranking["rank"] = [num + 1 for num in final_ranking.index]

    final_ranking.to_csv(RANKING_FILE_NAME, index=False)


correct_predictions = 0
total_matchups = 0


def test_predictability(file_to_test):
    """
    :param file_to_test: a new race result file to compare against the ranking at that point in time
    :return: percentage of the time the ranking predicted the outcome accurately
    """

    global correct_predictions
    global total_matchups

    ranking_data = pandas.read_csv(RANKING_FILE_NAME)
    race_data = pandas.read_csv(file_to_test)
    name_list = race_data.athlete_name.tolist()
    combos = list(combinations(name_list, 2))


    for matchup in combos:
        winner_name = matchup[0].title()
        loser_name = matchup[1].title()
        if winner_name in list(ranking_data.name) and loser_name in list(ranking_data.name):
            winner_rank = int(ranking_data["rank"][ranking_data.name == winner_name])
            loser_rank = int(ranking_data["rank"][ranking_data.name == loser_name])
            total_matchups += 1
            if winner_rank < loser_rank:
                correct_predictions += 1


results_dict = {
        "name": [],
        "place": [],
        "points": [],
        "weight": [],
        # "event": []
    }

if os.path.exists(RANKING_FILE_NAME):
    os.remove(RANKING_FILE_NAME)

for file in os.listdir(DIRECTORY):
    file_path = os.path.join(DIRECTORY, file)
    results_data = pandas.read_csv(file_path)
    if os.path.exists(RANKING_FILE_NAME):
        test_predictability(file_path)
    update_rankings(results_data)

predictability_score = correct_predictions / total_matchups
print(predictability_score)
