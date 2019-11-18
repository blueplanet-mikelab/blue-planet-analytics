import json, sys, os, pprint
path_to_current = "D:/AOM_Document/blue-planet-pantip-analytics/python/"
sys.path.append(path_to_current)
os.chdir(path_to_current)

from utils.measurementsUtil import accuracy, confusionMatrix, recallScore, precisionScore
from utils.fileWritingUtil import removeAndWriteFile

with open('./6-values-test.json') as json_data_file:
    values = json.load(json_data_file)

csvData = [["Theme", "Accuracy(%)", "Recall", "Precision"]]

for theme, valDict in values.items():
        # print(theme,"--------------------")
        actualVal = valDict["actual"]
        predictVal = valDict["predict"]
        # print("actualVal:", actualVal)
        # print("predictVal:", predictVal)
        acc = accuracy(actualVal, predictVal)
        recall = recallScore(actualVal, predictVal)
        precision = precisionScore(actualVal, predictVal)
        values[theme]["accuracy"] = acc
        values[theme]["confusion_matrix"] = confusionMatrix(actualVal, predictVal)
        values[theme]["recall_score"] = recall
        values[theme]["precision_score"] = precision

        csvData.append([theme, acc, recall, precision])

# pprint.pprint(values)
removeAndWriteFile('7-measurements-test.json', values)
print(csvData)
removeAndWriteFile('7-measurements.csv', csvData, 'csv')