"""
Task 2: Partition (2 points)
Since processing large volumes of data requires performance decisions, properly partitioning the data for processing is imperative. In this task, you will show the number of partitions for the RDD used for Task 1 Question F and the number of items per partition. Then, you need to use a customized partition function to improve the performance of map and reduce tasks. A time duration (for executing Task 1 Question F) comparison between the default partition and the customized partition (RDD built using the partition function) should also be shown in your results.
"""

from pyspark.context import SparkContext
import time
import json
import sys

"""
To run code: spark-submit hw1/minh_tran_task2.py yelp_dataset/testUser.json outputTask2.txt 8
"""

## (F) Find Top 10 user ids who have written the most number of reviews (0.5 point)
def taskF(taskInput):
    # map only "user_id" as key and 1 as value
    data = taskInput.map(lambda x: json.loads(x)).map(lambda x: (x["user_id"],(x["review_count"], x["name"])))

    # collapse by "name" while adding values to find the counts,
    # sort by negative value of count and name in ascending order)
    answer = data.sortBy(lambda x: (-x[1][0], x[1][1]), ascending=True).map(lambda x: (x[0], x[1][0])).take(10)

    return answer

def task2Processor(task2Input):
    # map only "user_id" as key and 1 as value
    data = task2Input.map(lambda x: json.loads(x)).map(lambda x: (x["user_id"], (x["review_count"], x["name"])))

    # collapse by "name" while adding values to find the counts,
    # sort by negative value of count and name in ascending order)
    builder = data.sortBy(lambda x: (-x[1][0], x[1][1]), ascending=True).map(lambda x: (x[0], x[1][0]))
    answer = builder.take(10)
    return answer, builder

def dohash(value):
    return abs(hash(value))

if __name__ == "__main__":
    # ensure number of inputs is 4: py file, input files, output files
    if len(sys.argv) != 4:
        print("This script requires 3 input arguments to run: 1 inputFile and 1 outputFile")

        # break it
        sys.exit(1)

    # create an interface between pyspark and spark server
    sc = SparkContext('local[*]')

    # to simplify output
    # sc.setLogLevel("ERROR")



    """
    DEFAULT APPROACH
    """

    # start timer
    startTimer1 = time.time()

    # get input file and import into the SparkContext object
    task2Input1 = sc.textFile(sys.argv[1])

    answer1, builder1 = task2Processor(task2Input1)

    endTimer1 = time.time()

    # get number of partitions
    answer1_1 = builder1.getNumPartitions()
    answer1_2 = builder1.mapPartitions(lambda it: [sum(1 for _ in it)])

    """
    CUSTOMIZED APPROACH
    """

    # start timer
    startTimer2 = time.time()

    # get input file and import into the SparkContext object, repartition to optimize map-reduce
    task2Input2 = sc.textFile(sys.argv[1]).repartition(int(sys.argv[3]))

    answer2, builder2 = task2Processor(task2Input2)

    # stop timer
    endTimer2 = time.time()

    # get number of partitions
    answer2_1 = builder2.getNumPartitions()
    answer2_2 = builder2.mapPartitions(lambda it: [sum(1 for _ in it)])


    # initiate output
    task2Output = {}
    task2Output["default"]={}
    task2Output["default"]["n_partition"] = answer1_1
    task2Output["default"]["n_items"] = answer1_2.collect()
    task2Output["default"]["exe_time"] = endTimer1-startTimer1

    task2Output["customized"] = {}
    task2Output["customized"]["n_partition"] = answer2_1
    task2Output["customized"]["n_items"] = answer2_2.collect()
    task2Output["customized"]["exe_time"] = endTimer2 - startTimer2

    task2Output["explanation"] = {}
    task2Output["explanation"] = "The customized partition is faster because it proportionately distribute workload to workers more evenly compared to the default partition"

    # write out json files
    jsonOutputFile = json.dumps(task2Output)
    with open(sys.argv[2],"w") as fileOut:
        fileOut.write(jsonOutputFile)

