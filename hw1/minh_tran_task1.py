"""
HW1
Task1: Data Exploration (3 points)
You will explore the dataset, user.json, containing review information for this task, and you need to write
a program to automatically answer the following questions:
"""

## LIBRARIES
import json
from pyspark import SparkContext
import sys

## TO RUN CODE
"""" 
spark-submit hw1/minh_tran_task1.py yelp_dataset/testUser.json outputTask1.txt
"""

## (A) Find the total number of users (0.5 point)
def taskA(taskInput):
    # map to read json then map each user_id as key to a value of 1
    # userID rdd: id1:1, id1:1, id2:1...
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x:(x["user_id"], 1))

    # Grouping by userID and map all values to 1, then count
    # don't need this because user ID is unique to each user
    # answer = userIDDict.groupByKey().mapValues(lambda x: 1).count()
    answer = data.count()
    return [("total_users", answer)]

## (B) Find the average number of written reviews of all users (0.5 point)
def taskB(taskInput):
    # map to read json then map each user_id as key to a value of review count
    # reviewCount rdd: id1:count1, id2:count2, ...
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x["user_id"], x["review_count"]))

    # Calculate average number of reviews written by users
    numReview = data.map(lambda tup: tup[1]).sum()
    numUsers = data.map(lambda tup: tup[0]).count()
    answer = numReview/numUsers

    return [("avg_reviews", answer)]

## (C) Find the number of distinct user names (0.5 point)
def taskC(taskInput):
    # map to read json then map each user name as key to a value of 1
    # userID rdd: id1:1, id1:1, id2:1...
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: x["name"])

    # Grouping by userID and map all values to 1, then count
    # don't need this because user ID is unique to each user
    # answer = userIDDict.groupByKey().mapValues(lambda x: 1).count()
    answer = data.distinct().count()
    return [("distinct_usernames", answer)]

## (D) Find the number of users that joined yelp in the year 2011 (0.5 point)
def taskD(taskInput):
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x["user_id"],x["yelping_since"]))

    # Filter user that joined yelp in 2011
    data2011 = data.filter(lambda x: x[1][:4] == "2011")
    answer = data2011.count()
    return [("num_users", answer)]

## (E) Find Top 10 popular names and the number of times they appear (user names that appear the most number of times) (0.5 point)
def taskE(taskInput):
    # map only "name" as key and 1 as value
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x["name"],1))

    # collapse by "name" while adding values to find the counts,
    # sort by negative value of count and name in ascending order)
    answer = data.reduceByKey(lambda x, y: x+y).sortBy(lambda x: (-x[1], x[0]), ascending=True).take(10)

    return answer

## (F) Find Top 10 user ids who have written the most number of reviews (0.5 point)
def taskF(taskInput):
    # map only "user_id" as key and 1 as value
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x["user_id"],(x["review_count"], x["name"])))

    # collapse by "name" while adding values to find the counts,
    # sort by negative value of count and name in ascending order)
    answer = data.sortBy(lambda x: (-x[1][0], x[1][1]), ascending=True).map(lambda x: (x[0], x[1][0])).take(10)

    return answer


if __name__ == "__main__":
    # ensure number of inputs is 3: py file, input file, output file
    if len(sys.argv)!= 3:
        print("This script requires 2 input arguments to run inputFile outputFile")

        # break it
        sys.exit(1)

    # import input and output file path from shell
    inputFile = sys.argv[1]
    outputFile = sys.argv[2]

    # create a spark context object using all available cores
    #conf = SparkConf().setAppName("INF553_HW1_MT").setMaster("local*]")
    sc = SparkContext("local[*]")

    # to simplify output
    sc.setLogLevel("ERROR")

    # get input file and import into the SparkContext object
    task1Input = sc.textFile(inputFile).persist()

    # answering task 1
    tA = taskA(task1Input)
    tB = taskB(task1Input)
    tC = taskC(task1Input)
    tD = taskD(task1Input)
    tE = taskE(task1Input)
    tF = taskF(task1Input)

    # output results based on given ordering
    # initiate output
    task1Output = {}

    task1Output[tA[0][0]] = tA[0][1] # rhs indexing because answer is [('total_users', 4)]
    task1Output[tB[0][0]] = tB[0][1]
    task1Output[tC[0][0]] = tC[0][1]
    task1Output[tD[0][0]] = tD[0][1]
    task1Output["top10_popular_names"] = tE
    task1Output["top10_most_reviews"] = tF

    # write out json files
    jsonOutputFile = json.dumps(task1Output)
    with open(outputFile,"w") as fileOut:
        fileOut.write(jsonOutputFile)