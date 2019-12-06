"""
Task 3: Exploration on Multiple Datasets (2 points)
In task3, you are asked to explore two datasets together containing review information (review.json) and business information (business.json) and write a program to answer the following questions:
"""

from pyspark.context import SparkContext
import time
import json
import sys

"""
To run code: spark-submit hw1/minh_tran_task3.py yelp_dataset/testReview.json yelp_dataset/testBusiness.json outputTask3.txt outputTask3.txt
"""

## Function to process review.json
def reviewProcessor(taskInput):
    # import data
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x['business_id'], x['stars']))
    return data

## Function to process business.json
def businessProcessor(taskInput):
    # import data
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x['business_id'], x['state']))
    return data

## Function to return average rating of each state
def task3Processor(reviewData, businessData):
    # join data on 'business_id': (stars, state)
    joinData = reviewData.join(businessData)
    # print(data_review.join(data_business).take(1)) # check output

    # map state as key and (stars,1) as value, then collapse by similar state and sum up total stars as well as count, then sort by state
    stateStar = joinData.map(lambda x: (x[1][1], (x[1][0], 1))).reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])).sortByKey()
    # print(stateStar.take(1))

    # calculate average rating for each state
    answer = stateStar.map(lambda x: (x[0], format(float(x[1][0]) / x[1][1]))).sortBy(lambda x: x[1], ascending=False)

    return answer


if __name__ == "__main__":
    # ensure number of inputs is 4: py file, input files, output files
    if len(sys.argv)!= 5:
        print("This script requires 4 input arguments to run: 2 inputFile and 2 outputFile")

        # break it
        sys.exit(1)

    # create an interface between pyspark and spark server
    sc = SparkContext('local[*]')

    # read input files
    inputFileReview = sc.textFile(sys.argv[1])
    inputFileBusiness = sc.textFile(sys.argv[2])

    reviewData = reviewProcessor(inputFileReview)
    businessData = businessProcessor(inputFileBusiness)

    answer = task3Processor(reviewData, businessData)

    """
    Method 1: collect all the data then print the first 5 states
    """
    # start timer
    startTimer1 = time.time()

    method1 = answer.collect()
    for i in range(5):
        print(method1[i])

    # stop timer
    endTimer1 = time.time()

    """
    Method 2: Take the first 5 states, and then print them
    """
    startTimer2 = time.time()
    method2 = answer.take(5)
    print(method2)
    endTimer2 = time.time()

    ## Output results
    # Part 1
    outputTask3Part1 = open(sys.argv[3], 'w')
    outputTask3Part1.write("state,stars")
    for i in range(answer.count()):
        outputTask3Part1.write("\n" + method1[i][0] + "," + method1[i][1])
    outputTask3Part1.close()

    # Part 2
    outputTask3Part2 = open(sys.argv[4], 'w')
    answerDict = {"m1": endTimer1-startTimer1,
                 "m2": endTimer2-startTimer2,
                 "explanation": "The second method needs less time compared to the first one because it accesses less amount of data. In the \"take\" method, which is a transformation, only a portion of the data is accessed and acted on while in the \"collect\" method the whole output is accessed"}

    answerJson = json.dumps(answerDict)
    outputTask3Part2.write(answerJson)
    outputTask3Part2.close()
