from datetime import datetime

##########################
# Cause Model Parameters #
##########################

# diarrhea duration in days
DIARRHEA_DURATION: Tuple = (
    'diarrheal_diseases_duration', get_norm_from_quantiles(mean=4.04485, lower=3.94472, upper=4.144975)
)

# measles duration in days
MEASLES_DURATION: int = 10

# LRI duration in days
LRI_DURATION: Tuple = (
    'lri_duration', get_norm_from_quantiles(mean=7.79, lower=6.2, upper=9.64)
)

# duration > bin_duration, so there is effectively no remission,
# and duration within the bin is bin_duration / 2
EARLY_NEONATAL_CAUSE_DURATION: float = 3.5


############################
# Disease Model Parameters #
############################

REMISSION_RATE = 0.1
MEAN_SOJOURN_TIME = 10


##############################
# Screening Model Parameters #
##############################

PROBABILITY_ATTENDING_SCREENING_KEY = 'probability_attending_screening'
PROBABILITY_ATTENDING_SCREENING_START_MEAN = 0.25
PROBABILITY_ATTENDING_SCREENING_START_STDDEV = 0.0025
PROBABILITY_ATTENDING_SCREENING_END_MEAN = 0.5
PROBABILITY_ATTENDING_SCREENING_END_STDDEV = 0.005

FIRST_SCREENING_AGE = 21
MID_SCREENING_AGE = 30
LAST_SCREENING_AGE = 65


###################################
# Scale-up Intervention Constants #
###################################
SCALE_UP_START_DT = datetime(2021, 1, 1)
SCALE_UP_END_DT = datetime(2030, 1, 1)
SCREENING_SCALE_UP_GOAL_COVERAGE = 0.50
SCREENING_SCALE_UP_DIFFERENCE = SCREENING_SCALE_UP_GOAL_COVERAGE - PROBABILITY_ATTENDING_SCREENING_START_MEAN

