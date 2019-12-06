import sys
from pyspark import SparkContext
import time

"""
spark-submit minh_tran_task2.py ub_sample_data.csv minh_tran_task2_edge_betweenness_python.txt minh_tran_task2_community_python.txt
To run code: spark-submit minh_tran_task2.py power_input.txt minh_tran_task2_edge_betweenness_python.txt minh_tran_task2_community_python.txt
"""


'''
Function to calculate betweenness given a graph (dict with node as key) and root
Girvan Newman algorithm 
'''
def calcBetweenness(root, graph):
    # initialize
    tempQueue = [] # first in first out
    tempQueue.append(root)

    visitedNodeList = [root]

    levelDict = {root: 0} # {node: level}

    # see step 2 in Girvan Newman
    numShortestPathDict = {root: 1} # {node: (# shortest paths from root)}

    parentDict = {root: None} # {node: ??}

    # loop until queue is empty
    while (len(tempQueue) != 0):
        # get the node by popping the first item in queue
        currentNode = tempQueue.pop(0)

        # looping all neighbors of the current node
        for neighbor in graph[currentNode]:
            # if that neighbor was visitedNodeList
            if neighbor in visitedNodeList: # only consider nodes of lower level
                # and if that neighbor lower level (child of current node)
                if levelDict[neighbor] == levelDict[currentNode] + 1:
                    # update number of shortest path from root
                    numShortestPathDict[neighbor] += 1

                    # update parent node of the neighbor
                    parentDict[neighbor].append(currentNode)

                # for nodes that are higher level (parents) or same level (non-DAG), do nothing
                continue

            else: # if that neighbor was not visitedNodeList, add them to visitedNodeList queue
                visitedNodeList.append(neighbor)
    
                # add neighbor to queue
                tempQueue.append(neighbor)
    
                # because we travel downward from root, level can only increase
                levelDict[neighbor] = levelDict[currentNode] + 1
    
                # update number of shortest path
                numShortestPathDict[neighbor] = 1
    
                # update parent of neighbor
                parentDict[neighbor] = [currentNode]


    # print("visitedNodeList: ",visitedNodeList)
    # print("levelDict:", levelDict)
    # print("numShortestPathDict: ", numShortestPathDict)
    # print("parentChute: ", parentDict)

    # step 3 of girvan newman algo
    nodeCredit = {x: 1 for x in visitedNodeList}  # giving all nodes an initial credit of 1
    nodeCredit[root] = 0
    ans = []

    # traverse from leaf node
    for node in visitedNodeList[::-1]:
        # break at root node
        if parentDict[node] == None:
            break

        # for each node, scan through all their parents
        for parent in parentDict[node]:
            # child'module credit transferred upwards to parents based on weight, which is number of shortest paths to that child node
            edgeCredit = nodeCredit[node] / numShortestPathDict[node]

            # parent got assigned credit from children'module credits divided by number of shortest path to children node
            nodeCredit[parent] += edgeCredit

            # save this way to ensure overwrite repeating edge to later take the sum over that edge correctly
            edgeID = (min((parent, node)), max((parent, node)))

            # ans: [(('B', 'C'), 1.0), (('A', 'B'), 1.0), (('D', 'G'), 0.5), (('F', 'G'), 0.5), (('B', 'D'), 3.0), (('E', 'F'), 1.5), (('D', 'E'), 4.5)]
            ans.append((edgeID, edgeCredit))

    return ans

'''
Utility functions
'''
def readTxt(x):
    return x.split(' ')

# function to combine two list of nodes into 1 list
def mergeLists(nodeLists):
    old = nodeLists[0]
    new = nodeLists[1]
    # if both are not empty, combine them
    if old != None and new != None:
        return old + new

    # if new is empty
    elif old != None:
        return old

    elif new != None:
        return new

    else:
        print("stopping script")
        print(old, new)
        exit(1)

'''
Function to calculate modularity
G - Graph
allModules - Modules: collection of nodes
m - total number of edges
degrees - degree of each node
'''
def calcModularity(graph, allModules, numEdges, degreeDict):
    ans = 0

    # loop for all allModules
    for module in allModules:
        # loop for each node in that module
        for node1 in module:
            # loop for the other node in that module
            for node2 in module:
                # initiate Aij to be all zeros at first
                # taking care of case when 2 nodes are different but not connected
                if node1 != node2:
                    Aij = 0

                    # exception if 2 nodes are connected
                    if node2 in graph[node1]:
                        Aij = 1

                    # calculate modularity slide 37 social network part 2
                    ans += (Aij - ((degreeDict[node1] * degreeDict[node2]) / (2 * numEdges)))

    # normalize final answer by 2m
    return (1 / (2 * numEdges)) * ans


'''
Function to check if the cut truly split the original graph into separate modules
The approach is to add all nodes into visitedNodeList and check if 
G - Graph
edge - (node1,node2)
'''
def checkSplit(G, edge):
    n1 = edge[0]
    n2 = edge[1]

    tempQueue = []
    tempQueue.append(n1)
    visitedNode = [n1]

    # loop until the queue is empty
    # recursively check for neighbor node if they are still connected to the other node
    while (tempQueue):
        # pop the oldest element in queue
        currentNode = tempQueue.pop(0)

        # check all neighbors of current node to see if they contain the other node
        for neighbor in G[currentNode]:
            # if one of the neighbor
            if neighbor == n2:
                # print("the edge does not completely split the graph: 2 nodes in that edge is still connected somehow")
                return False

            # if that neighbor was visited: ignore it
            if neighbor in visitedNode:
                continue

            # if that neighbor is not n2 and not visited yet, add them to visited List and queue to keep checking
            visitedNode.append(neighbor)
            tempQueue.append(neighbor)

    # print("graph is completely separated by that edge")
    return True

'''
This function traverse from root through graph by a BFS
'''
def bfs(start, graph):
    visited, queue = [], [start]
    while queue:
        vertex = queue.pop(0) # queue pop oldest element
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(set(graph[vertex]) - set(visited))
    return {x: graph[x] for x in visited}

# depth first search to find connected components starting from a node
def dfs(temp, node, visited, graph):
    # Mark the current vertex as visited
    visited[node] = True

    # Store the vertex to list
    temp.append(node)

    # recursively explore graph using dfs
    # Repeat for all vertices adjacent
    for neighbor in graph[node]:
        if visited[neighbor] == False:
            # Update the list
            temp = dfs(temp, neighbor, visited, graph)
    return temp

# find all connected components of a graph
def connectedComponents(graph):
    # dict: node: visited or not
    visited = {node: False for node in graph}
    cc = []

    for node in graph:
        if visited[node] == False:
            temp = []
            cc.append(dfs(temp, node, visited, graph))
    return cc

# function to remove an edge from a graph: x here is an edge rdd feed, edge is (n1,n2,btw)
def removeEdge(x, edge):
    # check both sides of the edges
    if x[0] == edge[0]:
        x[1].remove(edge[1])
    elif x[0] == edge[1]:
        x[1].remove(edge[0])

    # if passed-in has no resemblance both sides, remove it
    else:
        pass

    return x

"""
MAIN
"""
if __name__ == "__main__":
    # LOAD INPUT
    if len(sys.argv) != 4:
        print(
            "This function needs 3 input arguments <input_file_name> <betweennessOutputFile> <communityOutputFile>")
        sys.exit(1)
    start = time.time()
    
    inputFile = sys.argv[1]
    betweennessOutputFile = sys.argv[2]
    communityOutputFile = sys.argv[3]

    sc = SparkContext("local[*]")
    
    # MAKING EDGES [(vertex1, vertex2),...]
    # print("start making edges")
    edges = sc.textFile(inputFile).map(lambda x: readTxt(x)).map(lambda x: (x[0], x[1]))
    # print("edges1: ", edges.collect())
    edges_count = edges.count()
    # print("edges_count = ", edges_count)

    # MAKING HALF_EDGES: [(vertex1, [vertex2, vertex4...]),...]
    halfEdge1 = edges.map(lambda x: (x[0], [x[1]])).reduceByKey(lambda old, new: old+new)
    halfEdge2 = edges.map(lambda x: (x[1], [x[0]])).reduceByKey(lambda old, new: old+new)
    # print("half edges: ", halfEdge1.collect())

    # MAKING GRAPH dict: {'4': ['2', '5', '6', '7'], '1': ['2', '3'],...}
    # full Outer join to get all full edges
    # 2nd map to collapse 2 list into 1
    graphRDD = halfEdge2.fullOuterJoin(halfEdge1).map(lambda x: (x[0], mergeLists(x[1])))
    graph = graphRDD.collectAsMap()
    # print("graph: ", graph)

    # Evaluate connected components [[cc1], [cc2]], in case there are existing cc in original graph
    cc = connectedComponents(graph)
    # print("connected components: ", cc)
    
    # obtain list of subgraphs (each subgraph/dict corresponds to 1 cc found above)
    # [{'4': ['2', '5', '6', '7'], '2': ['1', '3', '4']}]
    subgraphList = []
    for c in cc:
        subgraph = dict()
        for x in c:
            subgraph[x] = graph[x]
        subgraphList.append(subgraph)
    # print("subgraphList: ", subgraphList)

    # FIND DEGREES OF GRAPH:
    degrees = graphRDD.map(lambda x: (x[0], len(x[1]))).collectAsMap()
    # print("degrees: ", degrees)

    # Calculate edge betweenness
    # print("start calculating betweenness")
    # flatMap is to calculate betweenness for each node
    # reduceByKey is to sum up all betweenness (from different nodes) based on edge id key
    # map is to map to (vertex1, vertex2, sum betweenness/2)
    # sortBy to order edges in terms of decreasing edge betweenness, then first node and 2nd node lexicographically
    betweenness = graphRDD.flatMap(lambda x: calcBetweenness(x[0], graph)).reduceByKey(lambda old, new: old+new)\
        .map(lambda x: (x[0][0], x[0][1], x[1] / 2)).sortBy(lambda x: (-x[2], x[0], x[1]))

    betweennessOutput = betweenness.collect()
    # print("betweenness: ", betweennessOutput)

    # write betweenness files
    # print("start writting files")
    out = ""
    for item in betweennessOutput:
        out += "('" + item[0] + "', '" + item[1] + "'), " + str(item[2]) + "\n"
    with open(betweennessOutputFile, "w") as f:
        f.write(out)
        f.close()

    """
    optimizing modularity
    """
    # print("start calculating modularity")
    edgeOfHighestBtw = betweennessOutput[0]
    # print("edgeOfHighestBtw: ", edgeOfHighestBtw)

    # inilirze modularity and partition
    # Q = []
    result = (-10, [])
    allModules = list(subgraphList)

    newGraphRDD = graphRDD.persist()
    newGraph = graph
    # print("original modules ", allModules)
    # print("original graph", newGraph)

    # ??
    i = 0

    # # looping until no more edge the betweenness i=100
    while (i <= 100 and edgeOfHighestBtw != None):
        i += 1

        # randomize??
        # if i % 10 == 0:
        #     newGraphRDD = sc.parallelize(list(newGraph.items()))

    # while (edgeOfHighestBtw != None):
        # create a new graph by removing edge of highest betweenness
        # print("removing edge")
        newGraphRDD = newGraphRDD.map(lambda x: removeEdge(x, edgeOfHighestBtw)).persist()
        newGraph = newGraphRDD.collectAsMap()

        # extract nodes of edge of highest betweenness
        n1 = edgeOfHighestBtw[0]
        n2 = edgeOfHighestBtw[1]

        # print("newGraph", newGraph)
        # print("edge of highest betweenness", (n1,n2))

        # check if edge is truly removed from graph
        if checkSplit(newGraph, (n1,n2)):
            # perform bfs for each module after split
            m1 = bfs(n1, newGraph)
            # print("m1 ", m1)
            m2 = bfs(n2, newGraph)
            # print("m2 ", m2)

            for module in allModules:
                # check if the split cut exist within a module
                if n1 in module and n2 in module:
                    # add 2 new allModules and remove the old module
                    allModules.append(m1)
                    allModules.append(m2)
                    allModules.remove(module)
                    break
            
            # CALCULATE new modularity
            q = calcModularity(graph, allModules, edges_count, degrees)

            # store results
            if q>result[0]:
            # Q.append((q, list(allModules)))
                result = (q, list(allModules))

        # if the graph is not completely separated ??
        # else:
        #     for module in allModules:
        #         if n1 in module and n2 in module:
        #             # remove edges related to the cut
        #             if n2 in module[n1]:
        #                 module[n1].remove(n2)
        #             if n1 in module[n2]:
        #                 module[n2].remove(n1)

        # print("updated Modules ", allModules)

        # recalculate betweenness .sortBy(lambda x: (-x[2], x[0], x[1]))??
        betweenness_new = newGraphRDD.flatMap(lambda x: calcBetweenness(x[0], newGraph)).reduceByKey(
            lambda old, new: old + new).map(lambda x: (x[0], x[1] / 2))
        # print("new betweenness after cut", betweenness_new.collect())

        if betweenness_new.isEmpty():
            break

        # extract the new edge of highest betweenness
        edgeOfHighestBtw = betweenness_new.max(lambda x: x[1])
        # print("new edge of highest btw", edgeOfHighestBtw)

        if edgeOfHighestBtw != []:
            edgeOfHighestBtw = edgeOfHighestBtw[0]
        else:
            edgeOfHighestBtw = None

    # extract the max modularity (q, list(allModules))
    # result = max(Q, key=lambda x: x[0])

    # print("max modularity and corresponding modules", result[0])
    # print("number of clusters: ", len(result[1]))
    # print("iterations: ", i)
    # WRITE COMMUNITY FILE
    out = ""
    # sort communities based on number of node in 1 community and first node of each community
    for community in sorted(result[1], key=lambda x: (len(x), sorted(list(x.keys()))[0]), reverse=False):
        for node in sorted(community):
            out += "'" + node + "', "

        # remove extra things at the end
        out = out[0:len(out) - 2]
        out += "\n"
    # remove extra things at the end
    out = out[0:len(out) - 1]

    # print("start writting to community file")
    with open(communityOutputFile, "w") as f:
        f.write(out)
        f.close()
    end = time.time()
    print("time: ", str(end - start))




