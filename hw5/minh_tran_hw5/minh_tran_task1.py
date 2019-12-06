"""
Task1: generate a simulated data stream with the Yelp dataset and implement Bloom Filtering with Spark Steaming.
"""

"""
You will implement the Bloom Filtering algorithm to estimate whether the US state of a coming business
in the data stream has shown before. The details of the Bloom Filtering Algorithm can be found at the
streaming lecture slide. You need to find proper hash functions and the number of hash functions in the
Bloom Filtering algorithm.
"""

'''
DATA: yelp.json
{"business_id":"Apn5Q_b6Nz61Tq4XzPdf9A",
"name":"Minhas Micro Brewery",
"neighborhood":"",
"address":"1314 44 Avenue NE",
"city":"Calgary",
"state":"AB",
"postal_code":"T2E 6L6",
"latitude":51.0918130155,
"longitude":-114.031674872,
"stars":4.0,"review_count":24,"is_open":1,
"attributes":{"BikeParking":"False","BusinessAcceptsCreditCards":"True","BusinessParking":"{'garage': False, 'street': True, 'validated': False, 'lot': False, 'valet': False}","GoodForKids":"True","HasTV":"True","NoiseLevel":"average","OutdoorSeating":"False","RestaurantsAttire":"casual","RestaurantsDelivery":"False","RestaurantsGoodForGroups":"True","RestaurantsPriceRange2":"2","RestaurantsReservations":"True","RestaurantsTakeOut":"True"},"categories":"Tours, Breweries, Pizza, Restaurants, Food, Hotels & Travel","hours":{"Monday":"8:30-17:0","Tuesday":"11:0-21:0","Wednesday":"11:0-21:0","Thursday":"11:0-21:0","Friday":"11:0-21:0","Saturday":"11:0-21:0"}}
'''

'''
To run code:
spark-submit minh_tran_task1.py 9999 output_task1.csv
java -cp stream.jar StreamSimulation yelp.json 9999 100
'''

# import libraries
from pyspark import SparkContext, StorageLevel
from pyspark.streaming import StreamingContext
import sys
import json
import csv
import itertools
from time import time
import math
import random
import binascii
from datetime import datetime

FILTERBITARRAY = 200
NUMHASHES = 10  # number of hash functions


'''
Function to check if a number is prime or not (from geeksforgeeks)
'''
def isPrime(n):
    # Corner cases
    if (n <= 1):
        return False
    if (n <= 3):
        return True

    # This is checked so that we can skip
    # middle five numbers in below loop
    if (n % 2 == 0 or n % 3 == 0):
        return False

    i = 5
    while (i * i <= n):
        if (n % i == 0 or n % (i + 2) == 0):
            return False
        i = i + 6
    return True

SEED = 7
random.seed(SEED)
# a = random.choices([x for x in range(1, 10) if isPrime(x)], k=1)
A=7
# b = random.choices([x for x in range(1, 10) if isPrime(x)], k=1)
B=11

'''
Function to generate hash code
input is the state int
'''
def hashGenerator(state):
    global NUMHASHES
    hashes = []

    # avoid i = 0
    for i in range(1, NUMHASHES+1):
        currentHash = ((A * i * B)+(i * state)) % FILTERBITARRAY
        hashes.append(currentHash)
    return hashes

'''
Function to generate hash code
input is a batch of streaming elements
'''
def bloomFilter(streamElements):
    # keep these varible global to keep updating them
    global visitedStates
    global fp
    global numStates
    global outputFile

    statesInStream = streamElements.collect()
    # print("state: ", statesInStream)
    
    # initiate time stamp in the correct format
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for state in statesInStream:
        # update number of states
        numStates += 1

        # As the state of a business is a string, you need to find its associated state, convert the state into an integer
        stateHash = int(binascii.hexlify(state.encode('utf8')), 16)
        # print("stateHash: ", stateHash)

        #  apply hash functions
        hashes = hashGenerator(stateHash)
        # print("hashes: ", hashes)

        isNewState = False
        # check each hash
        for hash in hashes:
            # if any of the hash is 0, set it to 1 (update array) and confirm it is new entry
            if bloomBitArray[hash] == 0:
                bloomBitArray[hash] = 1
                isNewState = True
        
        # update false positive by checking if state is actually visited or not
        if state not in visitedStates and not isNewState:
            fp += 1
        
        # update the set
        visitedStates.add(state)
        # print("visited States: ", visitedStates)

    # calculate false positive rate after batch
    # print("numStates: ", numStates)
    # print("fp: ", fp)
    fpRate = float(fp)/numStates

    out = str(current_timestamp) + "," + str(fpRate) + "\n"
    outputFile.write(out)
    outputFile.flush()  # clean up buffering output
    return

'''
MAIN
'''
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark-submit minh_tran_task1.py <port_number> <outputFilePath>")
        exit(-1)

    # import:
    port_number = int(sys.argv[1])
    outputFilePath = sys.argv[2]

    # Create a local StreamingContext with two working thread and batch interval of 1 second
    # SparkContext.setSystemProperty('spark.executor.memory', '4g')
    # SparkContext.setSystemProperty('spark.driver.memory', '4g')
    sc = SparkContext("local[*]", "distinctState")
    sc.setLogLevel(logLevel="OFF")

    # batch interval of 10 second
    ssc = StreamingContext(sc, 10)

    # In this task, you should keep a global filter bit array and the length is 200.
    bloomBitArray = [0] * FILTERBITARRAY
    numStates = 0  # number of cities
    fp = 0  # false positive
    visitedStates = set()  # set of cities that have been visisted

    # open file to write
    outputFile = open(outputFilePath, "w")
    out = "Time,FPR" + "\n"
    outputFile.write(out)

    # Create a Data Stream that connects to localhost:9999
    dataRDD = ssc.socketTextStream("localhost", port_number)

    # modify to obtain state of incoming business, then apply bloom filter
    resultRDD = dataRDD.map(json.loads).map(lambda x: x['state']).foreachRDD(bloomFilter)

    # start batches
    ssc.start()
    ssc.awaitTermination()