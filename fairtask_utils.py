
def combineEvents(allJobs, badgesTimeline):
    toReturn = []
    for oneJob in allJobs:
        toReturn.append(oneJob)
    for oneBadge in badgesTimeline:
        toReturn.append((oneBadge[4],
                         oneBadge[5],
                         oneBadge[1],
                         "<img src=\'%s\'/ width=\"25\", height=\"25\"> %s " % (oneBadge[3], oneBadge[2]),0))
    sortedToReturn = sorted(toReturn, key=lambda x: x[0], reverse=True)

    dictToReturn = {}  # valid for time-line
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
