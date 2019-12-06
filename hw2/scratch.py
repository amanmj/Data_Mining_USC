## this function is to get singleton frequent items from baskets: [basket1, basket2...] with basket_i =
def getSingleFrequents(baskets, s):
    # adjust support threshold
    support=len(baskets)*s

    # initiate list of singleton frequent items and count table
    result=[]
    countTable={}

    for basket in baskets:
        for item in basket:
            # set dict[key]=default if key is not already in dict
            countTable.setdefault(item, 0)
            countTable[item] += 1
    # print support
    # print countTable

    # check all items to reach support threshold in counts or not
    for item, count in countTable.iteritems():
        if count >= support:
            result.append(item)
    return sorted(result)

def getFrequents(baskets, s, previousfrequents, size):
    support=len(baskets)*s
    counttable={}
    result=[]
    candidates=[]
    if size==2:
        for candidate in itertools.combinations(previousfrequents,size):
            candidates.append(candidate)
    else:
        #print 'previous frequents=',previousfrequents
        for item in itertools.combinations(previousfrequents, 2):
            if len(set(item[0]).intersection(set(item[1]))) == size-2:
                candidate=tuple(sorted(set(item[0]).union(set(item[1]))))
                #print 'candidate=',candidate
                if candidate in candidates:
                    continue
                else:
                    temp = itertools.combinations(candidate, size-1)
                    if set(temp).issubset(previousfrequents):
                        #print 'appending',candidate
                        candidates.append(candidate)

    #print candidates
    for candidate in candidates:
        for basket in baskets:
            if set(candidate).issubset(basket):
                counttable.setdefault(candidate,0)
                counttable[candidate]+=1
    #print counttable
    for candidate,count in counttable.iteritems():
        if count>=support:
            result.append(candidate)
    #print sorted(result)
    return sorted(result)

## this function is to implement a-priori algorithm
def apriori(iterator):
    # initiate baskets
    baskets = []

    # add all baskets to list
    for v in iterator:
        baskets.append(v)

    # initiate list of all frequent items
    freqItems=[]

    # start with singleton
    size=1

    # get all singleton frequent items
    singlefrequents=getSingleFrequents(baskets, s)
    for item in singlefrequents:
        freqItems.append(item)

    # increase size
    size+=1
    currentfrequents = singlefrequents
    while True:
        previousfrequents = currentfrequents
        currentfrequents = getFrequents(baskets, s, previousfrequents, size)

        # update result
        for item in currentfrequents:
            freqItems.append(item)

        # if the current frequent item list is empty, stop
        if len(currentfrequents)==0:
            break

        size += 1
    return freqItems