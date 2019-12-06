import csv
from csv import reader, writer
import datetime
import sys

def csvProcessor(csvInputFilePath, csvOutputFilePath):
    with open(csvOutputFilePath, 'w') as csvFileOut, open(csvInputFilePath, 'r') as csvFileIn:
        next(csvFileIn)
        writer = csv.writer(csvFileOut)
        reader = csv.reader(csvFileIn, delimiter=',')

        for row in reader:
            # print(row)
            dt = datetime.datetime.strptime(row[0], '%m/%d/%Y')
            # dtStr = '{0}/{1}/{2:02}'.format(dt.month, dt.day, dt.year % 100)
            # dateCustomerID = dtStr + '-' + row[4]
            # productID = row[5]
            # print(dateCustomerID)
            # print(productID)
            dateCustomerTD = '{0}/{1}/{2:02}'.format(dt.month, dt.day, dt.year % 100) + '-' + row[4]
            productID = row[5]
            writer.writerow([dateCustomerTD, productID])

if __name__ == "__main__":
    # check number of input
    if len(sys.argv) != 5:
        print('Error: spark-submit hw2/minh_tran_task1.py 1 4 hw2/small1.csv minh_tran_task1.txt')
        exit(-1)

    # specify case number
    filterThreshold = float(sys.argv[1])

    # specify support threshold
    support = float(sys.argv[2])

    # specify file paths
    inputFilePath = sys.argv[3]
    outputFilePath = sys.argv[4]

    csvProcessor(inputFilePath, outputFilePath)