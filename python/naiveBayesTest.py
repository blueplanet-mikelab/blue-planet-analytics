# https://machinelearningmastery.com/naive-bayes-classifier-scratch-python/
# Make Predictions with Naive Bayes On The Iris Dataset
from csv import reader
from math import sqrt
from math import exp
from math import pi
import statistics 

# Load a CSV file
def load_csv(filename):
	dataset = list()
	with open(filename, 'r') as file:
		csv_reader = reader(file)
		for row in csv_reader:
			if not row:
				continue
			dataset.append(row)
	return dataset

# Convert string column to float
def str_column_to_float(dataset, column):
	for row in dataset:
		row[column] = float(row[column].strip())

# Convert string column to integer
def str_column_to_int(dataset, column):
	class_values = [row[column] for row in dataset]
	unique = set(class_values)
	lookup = dict()
	for i, value in enumerate(unique):
		lookup[value] = i
		print('[%s] => %d' % (value, i))
	for row in dataset:
		row[column] = lookup[row[column]]
	return lookup

# Split the dataset by class values, returns a dictionary
def separate_by_class(dataset):
	print("-----separate_by_class-----")
	separated = dict()
	for i in range(len(dataset)):
		vector = dataset[i]
		class_value = vector[-1] #! class of iris flower
		if (class_value not in separated):
			separated[class_value] = list()
		separated[class_value].append(vector)
	# print(separated)
	return separated

# Calculate the mean, stdev and count for each column in a dataset
def summarize_dataset(dataset):
	print("-----summarize_dataset-----")
	summaries = [(statistics.mean(column), statistics.stdev(column), len(column)) for column in zip(*dataset)] #! each rows have 3 statistics
	del(summaries[-1]) #! remove summarize data of class
	print(summaries)
	return summaries

# Split dataset by class then calculate statistics for each row
def summarize_by_class(dataset):
	print("-----summarize_by_class-----")
	separated = separate_by_class(dataset)
	summaries = dict()
	for class_value, rows in separated.items():
		summaries[class_value] = summarize_dataset(rows)
	return summaries

# Calculate the Gaussian probability distribution function for x
def calculate_probability(x, mean, stdev):
	exponent = exp(-((x-mean)**2 / (2 * stdev**2 )))
	return (1 / (sqrt(2 * pi) * stdev)) * exponent

# Calculate the probabilities of predicting each class for a given row
def calculate_class_probabilities(summaries, row):
	total_rows = sum([summaries[label][0][2] for label in summaries])
	probabilities = dict()
	for class_value, class_summaries in summaries.items():
		probabilities[class_value] = summaries[class_value][0][2]/float(total_rows)
		print("--->",summaries[class_value][0][2],"/",float(total_rows),"=",probabilities[class_value])
		for i in range(len(class_summaries)):
			mean, stdev, _ = class_summaries[i]
			probabilities[class_value] *= calculate_probability(row[i], mean, stdev)
	return probabilities

# Predict the class for a given row
def predict(summaries, row):
	probabilities = calculate_class_probabilities(summaries, row)
	best_label, best_prob = None, -1
	for class_value, probability in probabilities.items():
		if best_label is None or probability > best_prob:
			best_prob = probability
			best_label = class_value
	return best_label

# Make a prediction with Naive Bayes on Iris Dataset
filename = 'IRIS.csv'
dataset = load_csv(filename)
for i in range(len(dataset[0])-1):
	str_column_to_float(dataset, i)
# convert class column to integers
str_column_to_int(dataset, len(dataset[0])-1)
# fit model
model = summarize_by_class(dataset)
print("model", model)
# define a new record
row = [5.7,2.9,4.2,1.3]
# predict the label
print("------try predict------")
label = predict(model, row)
print('Data=%s, Predicted: %s' % (row, label))