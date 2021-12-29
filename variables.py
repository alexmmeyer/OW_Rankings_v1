import pandas

event_points = pandas.read_csv("event_points.csv")
points_curve = pandas.read_csv("points_curve.csv")
DIRECTORY = "results"
RANKING_FILE_NAME = "ranking.csv"

# Must be in MM/DD/YYYY format:
RANKING_AS_OF = "08/12/2018"

# Depreciation Period: time period in days over which a straight-line depreciation
# is applied to the initial point value of a result.
DEPRECIATION_PERIOD = 365 * 1.00

# Once result points are tallied, the amount of points that could be added (as a %
# of total results points to any athlete's total based on the strength on their
# average place percentile and qty of races percentile.
SHOWING_SCORE_BOOST = 0.5
# I don't think this variable has an effect on predictability

# ----- CREATE SHOWING SCORE -----
# Create a "showing score" which is a weighted average of the athlete's finish_score (based on average finish place)
# and volume_score (based on the number of races within the eligible time frame and how recent they are) and add that
# to the dataframe:
FINISH_SCORE_WEIGHT = 0.5
