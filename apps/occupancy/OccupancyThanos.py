import numpy as np
import pandas as pd
from datetime import timedelta
import datetime
from scipy import spatial
import math


def read_dataset_motion(dataset_filename, resample_time):
	# read from file
	data = pd.read_csv(dataset_filename, parse_dates=[0], index_col=0)

	# consider the thermostat motion sensor
	data["occ"] = data["Thermostat Motion"].astype("bool")

	# also consider each remote motion sensor
	counter = 1;
	string_check = "Remote Sensor " + str(counter) + " Motion"
	data["occ"] = data["Thermostat Motion"].astype("bool")
	while string_check in data:
		data["occ"] = data["occ"] | data[string_check].astype("bool")
		counter += 1
		string_check = "Remote Sensor " + str(counter) + " Motion"

	# return resampled occupancy data
	return data[['occ']].resample(str(resample_time)+"min").mean().astype("bool") * 1


def cosine_similarity(a, b):
	"""Calculate the cosine similarity between
	two non-zero vectors of equal length (https://en.wikipedia.org/wiki/Cosine_similarity)
	"""
	return -1.*(1.0 - spatial.distance.cosine(a, b))


def hamming_distance(a, b):
	return np.count_nonzero(a != b)


def eucl_distance(a, b):
	return pd.np.linalg.norm(a - b)


def mins_in_day(timestamp):
	return timestamp.hour * 60 + timestamp.minute


def find_similar_days(training_data, now, observation_length, k, method=hamming_distance):
	min_time = training_data.index[0] + timedelta(minutes=observation_length)
	# Find moments in our dataset that have the same hour/minute and is_weekend() == weekend.

	selector = ((training_data.index.minute == now.minute) &
				(training_data.index.hour == now.hour) &
				(training_data.index > min_time))

	"""
	if now.weekday() < 5:
		selector = (
			(training_data.index.minute == now.minute) &
			(training_data.index.hour == now.hour) &
			(training_data.index > min_time) &
			(training_data.index.weekday < 5)
		)
	else:
		selector = (
			(training_data.index.minute == now.minute) &
			(training_data.index.hour == now.hour) &
			(training_data.index > min_time) &
			(training_data.index.weekday >= 5)
		)
	"""

	similar_moments = training_data[selector][:-1]

	obs_td = timedelta(minutes=observation_length)

	similar_moments['Similarity'] = [
		method(
			training_data[(training_data.index >= now - obs_td) &
							(training_data.index <= now)].get_values(),
			training_data[(training_data.index >= i - obs_td) &
							(training_data.index <= i)].get_values()
		) for i in similar_moments.index
		]

	indexes = (similar_moments.sort_values('Similarity', ascending=True)
				.head(k).index)
	return indexes


def predict(data, now, similar_moments, prediction_time, resample_time):

	prediction = np.zeros((math.ceil(prediction_time/resample_time) + 1, len(data.columns)))
	for i in similar_moments:
		prediction += (1 / len(similar_moments)) * data[(data.index >= i) &\
														(data.index <= i + timedelta(minutes=prediction_time))]
	prediction[0] = data[data.index == now]
	return prediction



dataset_filename = 'Thermostat_5.csv'
# add 4 hours prior to the start of date (4 * 60 mins = 240)
observation_length_addition = 240
# consider k similar moments
k = 5
# predict 8 hours in the future (480 mins)
prediction_time = 480
#time_between_each_sample:
resample_time=15

data_occ = read_dataset_motion(dataset_filename, resample_time)
now = datetime.datetime(year=2015, month=10,day=31,hour=15,minute=45,second=0)
# observation length is one day plus observation_length_addition added hours
observation_length = mins_in_day(now) + observation_length_addition

similar_moments = find_similar_days(data_occ, now, observation_length, k)
prediction = np.squeeze(predict(data_occ, now, similar_moments, prediction_time, resample_time=resample_time))

for i in range(len(prediction)):
	if prediction[i] >= 0.5:
		prediction[i] = 1
	else:
		prediction[i] = 0

print(prediction)



