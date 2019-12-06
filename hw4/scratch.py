def calc_bet(root, graph):
    # initialize
    temp_queue = []  # first in first out
    temp_queue.append(root)

    visited = [root]

    level_dict = {root: 0}  # {node: level}

    # see step 2 in Girvan Newman
    no_shortest_path = {root: 1}  # {node: (# shortest paths from root)}

    parentchute = {root: None}  # {node: ??}

    # loop until queue is empty
    while (len(temp_queue) != 0):
        # get the node by popping the first item in queue
        curr_node = temp_queue.pop(0)

        # looping all neighbors of the current node
        for neighbor in graph[curr_node]:
            # if that neighbor was visited
            if neighbor in visited:  # only consider nodes of lower level
                # and if that neighbor lower level (child of current node)
                if level_dict[neighbor] == level_dict[curr_node] + 1:
                    # update number of shortest path from root
                    no_shortest_path[neighbor] += 1

                    # update parent node of the neighbor
                    parentchute[neighbor].append(curr_node)

                # for nodes that are higher level (parents) or same level (non-DAG), do nothing
                continue

            # if that neighbor was not visited, add them to visited queue
            visited.append(neighbor)

            # add neighbor to queue
            temp_queue.append(neighbor)

            # because we travel downward from root, level can only increase
            level_dict[neighbor] = level_dict[curr_node] + 1

            # update number of shortest path
            no_shortest_path[neighbor] = 1

            # update parent of neighbor
            parentchute[neighbor] = [curr_node]

    print("visited: ", visited)
    print("level_dict:", level_dict)
    print("no_shortest_path: ", no_shortest_path)
    print("parentChute: ", parentchute)

    # step 3 of girvan newman algo
    nodelabels = {x: 1 for x in visited}  # giving all nodes an initial credit of 1
    nodelabels[root] = 0
    ret = []

    # traverse from leaf node
    for node in visited[::-1]:
        # break at root node
        if parentchute[node] == None:
            break

        # for each node, scan through all their parents
        for parent in parentchute[node]:
            # parent got assigned credit from children's credits divided by number of shortest path to children node
            nodelabels[parent] += nodelabels[node] / no_shortest_path[node]
            print((parent, node))

            # save this way to ensure overwritte repeating edge
            ret.append(((min((parent, node)), max((parent, node))), nodelabels[node] / no_shortest_path[node]))
    print("ret: ", ret)
    return ret

def bfs(root, graph):
    visitedNodeList = [root]
    tempQueue = [root]
    while (tempQueue):
        currentNode = tempQueue.pop(0)
        for neighbor in graph[currentNode]:
            if neighbor in visitedNodeList:
                continue
            visitedNodeList.append(neighbor)
            tempQueue.append(neighbor)
    ret = ({x: graph[x] for x in visitedNodeList})
    return ret


# Python3 Program to print BFS traversal
# from a given source vertex. BFS(int s)
# traverses vertices reachable from s.
from collections import defaultdict

graph = {'D': ['B', 'E', 'F', 'G'], 'A': ['B', 'C'], 'B': ['A', 'C', 'D'], 'C': ['A', 'B'], 'E': ['D', 'F'], 'F': ['D', 'E', 'G'], 'G': ['D', 'F']}
root = 'E'

calc_bet(root, graph)
print("bfs", bfs(root, graph))
