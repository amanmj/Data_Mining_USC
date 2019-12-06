import os
import sys
import time
from pyspark import SparkContext
from pyspark.sql import SQLContext
from graphframes import GraphFrame


"""
To run code:
spark-submit --packages graphframes:graphframes:0.6.0-spark2.3-s_2.11 minh_tran_task1.py power_input.txt minh_tran_task1_community_python.txt
"""

# function to return vertice list [(1,),(2,)...] and edge list [(1, 2),(1, 3)]
def readTxt(input_file_path):
    verticeList = []
    edgeList = []
    with open(input_file_path, 'r') as fobj:
        for line in fobj:
            points = [int(num) for num in line.split()]
            # print("points", points)
            # do something with this line of numbers before moving on to the next.

            # update the set
            if tuple(points) not in edgeList:
                edgeList.append(tuple(points))

            if tuple([points[0]]) not in verticeList:
                verticeList.append(tuple([points[0]]))

            if tuple([points[1]]) not in verticeList:
                verticeList.append(tuple([points[1]]))

    return verticeList, edgeList

# finalResult [(1,[[a],[c],...]),...)
# [(4, [[1, 2, 3, 11], [5, 6, 7, 444]])]
def writeTxt(community_output_file_path, finalResult):
    out = ""

    for x in sorted(finalResult):  # sort int of size of communities
        communityList = [[str(j) for j in i] for i in x[1]]  # convert all components to str
        for community in communityList:
            community.sort()  # sort each community internally lexicographically

        for community in sorted(communityList):
            # community1 = sorted([str(i) for i in community])
            for member in community:
                out += "'" + str(member) + "', "
            out = out[0:len(out) - 2]
            out += "\n"

    # remove extra things at the end
    out = out[0:len(out) - 1]

    # print("start writting to community file")
    with open(community_output_file_path, "w") as f:
        f.write(out)
        f.close()

def writeTxt2(community_output_file_path, finalResult):
    out = ""
    for x in finalResult.collect():
        communities = x[1]
        for community in communities:
            for member in community:
                out += "'" + str(member)+"', " + '\n'
    with open(community_output_file_path, "w") as f:
        f.write(out)
        f.close()

# answers_dict
def writeTxt3(community_output_file_path, answers_dict):
    # write output
    f = open(community_output_file_path, "w+")
    out = ""

    # sort key lexicographically
    for key in sorted(answers_dict.keys()):
        answers = answers_dict[key]
        for i in range(len(answers)):
            # sort each community internally
            answers[i] = sorted(answers[i])
        # sort all communities based on first member
        answers.sort()

        for row in answers:
            for user in row:
                out += "'" + str(user) + "', "
            out = out[0:len(out) - 2]
            out += "\n"
        out = out[0:len(out) - 1]
        out += "\n"
    f.write(out)
    f.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "This function needs 3 input arguments <filter> <input_file_name> <input_file_path> <community_output_file_path>")
        sys.exit(1)

    start = time.time()

    input_file_path = sys.argv[1]
    community_output_file_path = sys.argv[2]


    # read text file input
    verticeList, edgeList = readTxt(input_file_path)
    # print("edgeList", sorted(edgeList))
    # print("verticeList", sorted(verticeList))
    # print("number of edges", len(edgeList))
    # print("number of vertices", len(verticeList))

    # graphframe environment
    os.environ["PYSPARK_SUBMIT_ARGS"] = ("--packages graphframes:graphframes:0.6.0-spark2.3-s_2.11")
    # os.environ["PYSPARK_SUBMIT_ARGS"] = ("--packages graphframes:graphframes:0.6.0-spark2.3-s_2.11 pyspark-shell")

    sc = SparkContext("local[*]")
    sqlContext = SQLContext(sc)

    # create vertices
    # vertices = sqlContext.createDataFrame([(1,), (2,), (3,)], ["id"])
    # print("create vertice")
    vertices = sqlContext.createDataFrame(verticeList, ["id"])
    # vertices.show()

    # edges
    # edges = sqlContext.createDataFrame([(1,2),(1,4)], ["src","dst"])
    # print("create edges")
    edges =sqlContext.createDataFrame(edgeList, ["src","dst"])
    # edges.show()

    # Let's create a graph from these vertices and these edges:
    # print("create graph")
    g = GraphFrame(vertices, edges)
    # g.edges.show()

    """
    Label Propagation
    Run static Label Propagation Algorithm for detecting communities in networks.

    Each node in the network is initially assigned to its own community. At every superstep, nodes send their community affiliation to all neighbors and update their state to the most frequent community affiliation of incoming messages.

    LPA is a standard community detection algorithm for graphs. It is very inexpensive computationally, although (1) convergence is not guaranteed and (2) one can end up with trivial solutions (all nodes are identified into a single community).
    """
    # print("Label Propagation Algorithm for detecting communities")
    result = g.labelPropagation(maxIter=5)


    """
    1st approach
    """
    # 1st map to (label1, id1)...
    # 1st reduceByKey to {label1:[id1,id2...],...}
    # 2nd map is mapping to (len(community1), [sorted(ids)])
    # 2nd reduceByKey is to group all communities of the same length: (len1: [sorted(ids1), sorted(ids2),...]
    # print("start rdd")

    # start = time.time()

    finalResult = result.rdd.map(lambda x: (x['label'], [x['id']])) \
        .reduceByKey(lambda old, new: old + new) \
        .map(lambda x: (len(x[1]), [x[1]])) \
        .reduceByKey(lambda old, new: old + new) \
        .collect()


    # print(finalResult)

    """
    2nd approach: no rdd
    """
    # # group by community label and add a column with number of vertices in each community
    # # print("unsorted dataframe")
    # communityList = result.groupBy("label").count().orderBy("count").collect()
    # # communityList = result.groupBy("label").agg((collect_list("id")).alias('listVertices')).select('*', size('listVertices').alias('numVertices'))
    # # print("ocmmunity List", communityList)
    #
    # # then sort by number of vertices in community
    # # communityList = communityList.orderBy("numVertices", ascending=False)
    # answers = []
    #
    # for row in communityList:
    #     community = result.select("id").where(result.label == row[0]).collect()
    #     temp = []
    #     for row_ in community:
    #         temp.append(str(row_[0]))
    #     answers.append(temp)
    #
    # answers_dict = {}
    #
    # for i in range(len(answers)):
    #     try:
    #         answers_dict[len(answers[i])].append(sorted(answers[i]))
    #     except:
    #         answers_dict[len(answers[i])] = [sorted(answers[i])]
    #
    # # print("sorted dataframe")
    # # communityList.show()
    # # print("answer_dict", answers_dict)
    """
    end of 2nd approach
    """

    # writeTxt3(community_output_file_path, answers_dict)
    writeTxt(community_output_file_path, finalResult)
    end = time.time()

    print("time: ", str(end - start))
