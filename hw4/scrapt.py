finalResult = [(4, [[1, 2, 3, 11], [5, 6, 7, 444]]), (2, [[55,111], [424, 444]]),(1, [[55],[111], [424], [444]])]
out = ""

for x in sorted(finalResult): # sort int of size of communities
    communityList = [[str(j) for j in i] for i in x[1]] # convert all components to str
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

print(out)