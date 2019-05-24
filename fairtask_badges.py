import inspect
from fairtask_db_tools import fairtaskDB
import fairtask_badge_factory

EMPTY_RESULT = {}


def get_current_badges(date, storage=None):
    storageReadOnly = storage
    if storage is None:
        storageReadOnly = fairtaskDB(allowCommit=False)

    badgesAlredyInTheSystem = {}
    for one in storageReadOnly.get_granted_badges(date):
        try:
            badgesAlredyInTheSystem[one[2]].append((one[1], one[3]))
        except KeyError:
            badgesAlredyInTheSystem[one[2]] = [(one[1], one[3])]

    userIds = storageReadOnly.execute_get_sql('select id from user')
    allTimeBadges = {}
    for name, obj in inspect.getmembers(fairtask_badge_factory):
        if inspect.isclass(obj) and name.startswith('badge'):
            oneBadge = obj(storageReadOnly)
            print(oneBadge.getBadgeId(), name)
            allTimeBadges[oneBadge.getBadgeId()] = {}
            for userId in userIds:
                tmpBadges = badgesAlredyInTheSystem.get(oneBadge.getBadgeId(),[])
                earlierDate = None
                for one in tmpBadges:
                    if one[0] == userId[0]:
                        earlierDate = one[1]
                result = oneBadge.find(date, userId[0], earlierDate=earlierDate)
                if len(result.keys()):
                    allTimeBadges[oneBadge.getBadgeId()] = result

    toReturn = []
    for oneBadgeId in allTimeBadges.keys():
        for oneUserId in allTimeBadges[oneBadgeId].keys():
            toReturn.append((oneUserId, oneBadgeId, date))
    return toReturn
