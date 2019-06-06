
def combineEvents(allJobs, badgesTimeline):
    toReturn = []
    for oneJob in allJobs:
        toReturn.append(oneJob)
    for oneBadge in badgesTimeline:
        toReturn.append( (oneBadge[4], oneBadge[5], oneBadge[1], "<img src=\'%s\'/ width=\"25\", height=\"25\"> %s "%(oneBadge[3], oneBadge[2]) ) )
    sortedToReturn = sorted(toReturn, key=lambda x: x[0], reverse=True)
    return sortedToReturn
