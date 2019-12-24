import itertools


def combineEvents(allJobs, badgesTimeline):
    toReturn = []
    for oneJob in allJobs:
        toReturn.append(oneJob)
    for oneBadge in badgesTimeline.values():
        toReturn.append((oneBadge['date'],
                         oneBadge['grantByUserName'],
                         oneBadge['username'],
                         "<img src=\'%s\'/ width=\"25\", height=\"25\"> %s " %
                         (oneBadge['img'], oneBadge['badgeName']), 0))
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
    uniqePairs = getUniqeParisOfUsers([u['id'] for u in storage.get_users().
                                       values()])
    data = storage.execute_get_sql('select date, buyer, to_whom from contract\
                                    where buyer != to_whom')
    return compute_who_with_whom_alghoritm(uniqePairs, data)


def getUniqeParisOfUsers(usersList, subsets=2):
    return list(itertools.combinations(usersList, subsets))


def compute_who_with_whom_alghoritm(uniqePairs, whenWhoToWhom, verbose=False):
    '''
    Unique pairs of users ids combinations
    whenWhoToWhom - list of all transcactions
    '''
    toReturn = {}
    for one in uniqePairs:
        toReturn[one] = 0
    lastDate = whenWhoToWhom[0][0]
    tmpJobPresent = []
    for i, one in enumerate(whenWhoToWhom):
        if lastDate == one[0]:
            if verbose:
                print('when: ', one[0])
            tmpJobPresent.append(one[1])
            tmpJobPresent.append(one[2])
            if i < len(whenWhoToWhom) - 1:
                continue
        fromJob = extractAndCountForOneJob(uniqePairs, set(tmpJobPresent))
        if verbose:
            print('From one job: ', fromJob)
        for oneResult in fromJob.keys():
            toReturn[oneResult] += fromJob[oneResult]

        tmpJobPresent = []
        tmpJobPresent.append(one[1])
        tmpJobPresent.append(one[2])
        lastDate = one[0]
    toReturnNonZeros = {}
    for one in toReturn.keys():
        if toReturn[one] > 0:
            toReturnNonZeros[one] = toReturn[one]
    if verbose:
        print('Nonzero meet: ', toReturnNonZeros)
    return toReturnNonZeros


def extractAndCountForOneJob(uniqePairs, tmpJobSingle):
    tmpJob = getUniqeParisOfUsers(tmpJobSingle)
    tmpToReturn = {}
    for one in tmpJob:
        if one in uniqePairs:
            tmpToReturn[one] = 1
        else:
            tmpToReturn[(one[1], one[0])] = 1
    return tmpToReturn
