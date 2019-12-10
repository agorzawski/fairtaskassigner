import itertools

def combineEvents(allJobs, badgesTimeline):
    toReturn = []
    for oneJob in allJobs:
        toReturn.append(oneJob)
    for oneBadge in badgesTimeline.values():
        toReturn.append((oneBadge['date'],
                         oneBadge['grantByUserName'],
                         oneBadge['username'],
                         "<img src=\'%s\'/ width=\"25\", height=\"25\"> %s " % (oneBadge['img'], oneBadge['badgeName']),0))
    sortedToReturn = sorted(toReturn, key=lambda x: x[0], reverse=True)

    dictToReturn = {}
    localIndex = 0
    lastDateYYMMDD = None
    sum = 0
    for index, one in enumerate(sortedToReturn):

        dateYYMMDD = one[0].split(' ')[0]
        dateArray = dateYYMMDD.split('-')

        if lastDateYYMMDD != dateYYMMDD:
            dictToReturn[dateYYMMDD] = {}
            localIndex = 0
            if index > 0:
                dictToReturn[lastDateYYMMDD]['total'] = sum
                dictToReturn[lastDateYYMMDD]['all'] = one[0]
                pass
            sum = one[4]
        if dateYYMMDD == lastDateYYMMDD or lastDateYYMMDD is None:
            localIndex += 1
            sum += one[4]
        dictToReturn[dateYYMMDD][localIndex] = {'date': {'all': one[0],
                                                         'year': dateArray[0],
                                                         'month': dateArray[1],
                                                         'day': dateArray[2], },
                                                'who': one[1],
                                                'towhom': one[2],
                                                'what': one[3],
        }
        lastDateYYMMDD = dateYYMMDD

    return dictToReturn


def compute_who_with_whom(storage):
    uniqePairs = list(itertools.combinations([u['id'] for u in storage.get_users().values()], 2))
    toReturn = {}
    for one in uniqePairs:
        toReturn[one]=0
    #print(toReturn)
    #print(len(uniqePairs))
    data = storage.execute_get_sql('select date, buyer, to_whom from contract where buyer != to_whom')
    lastDate=data[0][0]
    tmpJob = []
    for one in data:
        #print(one[0])
        if lastDate == one[0]:
            tmpJob.append(one[1])
            tmpJob.append(one[2])
            continue

        fromJob = extract(uniqePairs, set(tmpJob))
        #print(fromJob)
        for oneResult in fromJob.keys():
            toReturn[oneResult] += fromJob[oneResult]

        tmpJob = []
        tmpJob.append(one[1])
        tmpJob.append(one[2])
        lastDate = one[0]

    toReturnNonZeros = {}
    for one in toReturn.keys():
        if toReturn[one] > 0:
            toReturnNonZeros[one] = toReturn[one]
    #print(toReturnNonZeros)
    return toReturnNonZeros

def extract(uniqePairs, tmpJobSingle):
    tmpJob = list(itertools.combinations(tmpJobSingle, 2))
    tmpToReturn = {}
    for one in tmpJob:
        if one in uniqePairs:
            tmpToReturn[one] = 1
        else:
            tmpToReturn[(one[1], one[0])] = 1
    return tmpToReturn
