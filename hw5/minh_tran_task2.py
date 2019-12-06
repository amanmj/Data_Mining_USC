"""
Task 2: generate a simulated data stream with the Yelp dataset and implement Flajolet-Martin algorithm with Spark Steaming.
"""

'''
To run code:
spark-submit minh_tran_task2.py 9999 output_task2.csv
java -cp stream.jar StreamSimulation yelp.json 9999 100
'''

from pyspark import SparkContext, StorageLevel
from pyspark.streaming import StreamingContext
import sys
import json
import math
import binascii
from datetime import datetime
from statistics import mean, median
import random


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

'''
Function to apply flajolet martin algorithm
'''
PRIME = random.choices([x for x in range(1000000000, 1000000100) if isPrime(x)],k=1)[0]

SEED = 7
def FMAlgo(streamElements):
    # keep these varible global to keep updating them
    global visitedCities
    global numCities
    global outputFile
    global numHashes
    global expectedEstimate
    global sizeGroup
    
    citiesInStream = streamElements.collect()
    # print("cities: ", citiesInStream)

    # initiate time stamp in the correct format
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # get the actual distinct number of cities
    trueNumCities = len(set(citiesInStream))
    # print("numCities", trueNumCities)
    
    # initiate estimate of unique elements 2^r
    finalEstimate = 0

    # initiate count of trailing zeros
    maxNumTrailZeros = -math.inf

    # initiate all estimates of distinct count for each hash function
    allEstimates = []
    for i in range(1, numHashes+1):
        for city in citiesInStream:
            # As the state of a business is a string, you need to find its associated state, convert the state into an integer
            cityHash = int(binascii.hexlify(city.encode('utf8')), 16)
            
            # calculate hash value
            hash = (((a[i] * cityHash) + b[i]) % PRIME) % expectedEstimate
            # hash = ((a[i] * cityHash) + b[i]) % expectedEstimate

            # convert hash code to binary
            #  why [2:]: remove prefix 0b representing the result is a binary string.
            hashBinary = bin(hash)[2:]

            # removes any Zero as trailing characters
            hashBinaryWOZeros = hashBinary.rstrip("0")
            
            # calculate number of trailing zeros
            numTrailZeros = len(hashBinary) - len(hashBinaryWOZeros)
            
            # update max number of trailing zeros
            if numTrailZeros > maxNumTrailZeros:
                maxNumTrailZeros = numTrailZeros
        
        # append estimates for this hash function
        allEstimates.append((2 ** maxNumTrailZeros))
        
        # reset max number so that another hash function can be operated
        maxNumTrailZeros = -math.inf

    # combine results
    groupAvgs = []
    startIdx = 0
    for endIdx in range(sizeGroup, numHashes, sizeGroup):
        # extract mean of each group of estimates
        groupAvgs.append(mean(allEstimates[startIdx:endIdx]))

        # update idx to move to the next group
        startIdx = endIdx
    # extract the median of average
    finalEstimate = median(groupAvgs)

    # write file
    out = str(current_timestamp) + "," + str(trueNumCities) + "," + str(finalEstimate) + "\n"
    # print("out: ", out)
    outputFile.write(out)
    outputFile.flush()

    return

'''
MAIN
'''
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark-submit minh_tran_task2.py <port_number> <outputFilePath>")
        exit(-1)

    # import:
    port_number = int(sys.argv[1])
    output_file_path = sys.argv[2]

    # parameters in seconds
    batch_size = 5 # barch duration
    window_length = 30 # window length
    sliding_interval = 10 # sliding interval duration
    numHashes = 9 # number of hash functions
    sizeGroup = 3
    
    # number of distinct elements
    expectedEstimate = 2 ** numHashes


    random.seed(SEED)
    a = random.choices([x for x in range(1000, 30000) if isPrime(x)], k=numHashes+1)
    # print("a: ", a)
    b = random.choices([x for x in range(1000, 30000) if isPrime(x)], k=numHashes+1)
    # print("b: ", b)

    # Create a local StreamingContext with two working thread and batch interval of 1 second
    # SparkContext.setSystemProperty('spark.executor.memory', '4g')
    # SparkContext.setSystemProperty('spark.driver.memory', '4g')
    sc = SparkContext("local[*]", "countDistinctCity")
    sc.setLogLevel(logLevel="OFF")

    # batch interval
    ssc = StreamingContext(sc, batch_size)

    outputFile = open(output_file_path, "w", encoding="utf-8")
    out = "Time,Ground Truth,Estimation" + "\n"
    outputFile.write(out)

    # Create a Data Stream that connects to localhost:9999
    dataRDD = ssc.socketTextStream("localhost", port_number)

    # modify to obtain state of incoming business, then apply bloom filter
    resultRDD = dataRDD.map(json.loads).map(lambda x: x['city'])\
        .window(windowDuration=window_length, slideDuration=sliding_interval)\
        .foreachRDD(FMAlgo)

    # start batches
    ssc.start()
    ssc.awaitTermination()
