
def combineEvents(allJobs, badgesTimeline):
    toReturn = []
    for oneJob in allJobs:
        toReturn.append(oneJob)
    for oneBadge in badgesTimeline:
        toReturn.append( (oneBadge[3], 'system', oneBadge[0], "<img src=\'%s\'/ width=\"25\", height=\"25\"> %s "%(oneBadge[2], oneBadge[1]) ) )
    sortedToReturn = sorted(toReturn, key=lambda x: x[0], reverse=True)
    return sortedToReturn
