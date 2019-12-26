# Changelog

*1.8*
- admin edits for users, badges, jobs (DEV)
- fixed colours for points
- small fixes (list orders)
- instance variable (header + version from git tag)
- graph for who with whom
- -1 admin button for all active (inflation)
- reorganiezed README and CHANGELOG plus some screenshots of the graphs in the doc
- sorting orders table
- /api/stats & /api/elements exposed for external use

*1.7*
- products stats
- debt transfer (on demand form any user at negative balance)
- dependancy wheel chart in stats tab
- internal data structure change
- few layout improvements
- few bugs fixed: debt/scoring calculation, new products add (admin)

*1.6*
- users details subpage
- plots with points evolutions
- pie charts on statistics

*1.5*
- added orders/actions time line
- sortable stats table
- navigation issues (menu/top return)

*1.4*
- enabling/disabling badges
- enabling/disabling users

*1.3*
- adapted do bootstrap 4.3
- fixed bugs with badges management

*1.2*
- job can be saved only when at least three orders are in the bucket
- remove an item in the wish list
- fix the bug for the stats view when not an admin nor the badge admin

*1.1*
- admins can grant remove badges

*1.0*
- new tab - statistics
- new badge and achievements system triggered at every ordering event
- prepared for role based modifications (admin, badge admins, users)
- prepared for a events timeline

*0.3*
- The temporary rating is calculated within the preselected bucket only among the current waiting list users.
- For a logged user a predefined order button (adding to the current wish list) is available for the most often ordered product. No button is visible when never made an order.
- Moved the order history to the 'AddTask' tab accessible only for the logged users
- Disabled 'Register Job' and 'who is buying' for an empty Wish list.

*0.2*
- Preselected bucket is validated at later step

*0.1*
- Not logged user can see actual servings, top three candidates and top three servants
- Logged user can add new users
- Logged user can add serving (as him)
- New user can login and add himself to the system
