# OSRS CLAN DISCORD BOT
The purpose of this bot is to help clans grow and mantain a clan coffer in order to encourage growth of the community.

Clan events can help grow a clans size more rapidly than waiting for organic growth, even with the help of a community figure like a streamer or a youtuber. They can help bring clanmates together and create long-lasting friendships as well as encourage personal account growth and progress.

Clan events with rewards draw larger crowds and more participation as well as competiton, however, without incentives it can be difficult to keep a well-stocked coffer for small and medium sized clans- some large clans even have issues with this problem.

This discord bot will help alleviate the issue of keeping the coffer stocked by rewarding players who donate GP to the clan while giving something back that could be coveted such as a discord role, an in-game clan role, or directorship of the next event.

# COMMANDS
## Admin Commands
* `/add_donation <user> <date> <int> [note]` **Adds a donation to the record of a member.**
  * `<user>` Must be a valid discord user. If donator is not in discord, they cannot claim rewards.
  * `<date>` Must be formated as YYYY-MM-DD. Ie, for December 25th 2023 you'd type `2023-12-25`
  * `<int>` The amount of GP donated. More GP at once = higher point multiplier
  * `[note]` An optional note an admin can add for any reason.
* `/remove_points <user> <int> <note>` **Removes points from a member's account.**
  * `<user>` Must be a valid discord user.
  * `<int>` The number of points to remove
  * `<note>` When removing points, a "reason" note must be added.
* `/all_history <user>` **Allows an admin to view a members full donation and point history including notes.**
  * `<user>` Must be a valid discord user.
* `/version` **Allows an admin to check the current version of the bot. Can also include custom info, see `lauch args` below.**
* `/sql <text>` **Allows certain admins to execute SQL commands directly through a discord message.**
  * **INCREDIBLY DANGEROUS COMMAND**
  * Delete, Truncate, and Drop are disabled for security
  * Only the server owner and 1 admin, as specified on line 37, may use this command
  * `<text>` The SQL command as you would type into a console.

## User commands
* `/points` **Allows a member to check their current point total.**
* `/bonuses` **Allows a member to see current donation bonuses.**
* `/rewards` **Displays all current rewards w/ IDs.**
* `/claim_reward <int>` **Allows a member to claim a reward by spending points.**
  * `<int>` The ID of the reward the member wants to claim, see `/rewards`
* `/point_history` **Allows a member to view their point earning and spending history.**
* `/donation_history` **Allows a member to view their donation histroy.**

## HOW TO MODIFY TO FIT YOUR NEEDS
1.) First you will need [to get a discord bot token](https://www.writebots.com/discord-bot-token/).

2.) Download `points_bot.py` and edit the file as described below.

3.) Invite the bot to your server, go to server settings, Integrations, Bots and Apps, then click this bot in the menu.

4.) Click each command and DISABLE the admin commands for `@everyone` and ENABLE them for `@admins`.
By default every command will be visible to `@everyone` you will not need to add overrides for the rest.

5.) Variables to edit:
* Line 35: Your discord server guild ID
* Line 36: The channel where claimed reward notifications go, this should be an admin-only bot channel.
* Line 37: The "SQL admin" is a user who has the Admin role *and* has permssion to execute raw SQL commands, only give this to a user you are SURE knows how to use SQL.
* Lines 38-41: The multiplier for points per mil and milestone
* Methods 7-10/Lines 128-172: Various reward mechanisms including cost, name, limits, and pre-reqs.

6.) Next you need to launch the script using some args: `--mode False --ver _loc_a --token <discord bot token>`. The "mode: `False`" enables(True) or disables(False) debug-mode which is mainly for developers but if you're having issues it may help you identify them. "-ver `_loc_a`" can be changed to any string, it simply appeds that to the version when printed using `/version`, it's useful if you chose to run the bot on a remote server but dont remember where. Of course, `<discord bot token>` will be the token given to you by discord. in step 1

7.) Test the bot using various commands to give points and claim rewards.