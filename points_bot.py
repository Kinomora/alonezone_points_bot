# ============================================================
# =DISCORD BOT WRITTEN BY KINOMORA============================
# =FOR USE IN ALONESCAPE'S DISCORD SERVER=====================
# =LICENSED UNDER THE MIT LICENSE=============================
# ============================================================
import discord
import argparse
import sqlite3 as sql

from discord import app_commands
from typing import Optional
from datetime import datetime
from prettytable import *

# lets me use arguments in the commandline to set developer mode in the IDE without having to toggle it every time
parser = argparse.ArgumentParser(description='sets developer mode')
parser.add_argument('--mode', action="store", dest='mode', default="False")
parser.add_argument('--ver', action="store", dest='ver', default="")
parser.add_argument('--token', action="store", dest='token', default="")
args = parser.parse_args()

# ============================================================
# =DISCORD.PY SETUP===========================================
# ============================================================
intents = discord.Intents.all()
client = discord.Client(intents=intents)
silent_response = True
public_response = False
bot = app_commands.CommandTree(client)
allowed = discord.AllowedMentions.all()

# ============================================================
# =GLOBAL AND META VARIABLES==================================
# ============================================================
guild = 991568104687681577
admin_channel = 1164655165094244352
sql_admin = 849674454228271105  # Whoever this user ID is can send raw SQL commands to the server as long as they are also an admin. Set to "0" to disable.
clientVersion = "Version 1.0" + args.ver
database = 'alonezone_points.db'
if args.mode == "True":
    devMode = True
else:
    devMode = False


# ============================================================
# =DATA PROCESSING METHODS====================================
# ============================================================
#
# 1 Convert arbitrary table sizes into pretty outputs
def pretty_outputs(headers, string):
    table = PrettyTable(headers)
    table.add_rows(string)
    table.align = "l"
    table.set_style(DOUBLE_BORDER)
    return table


# 2 Custom print method conditional on dev mode
def printd(var):
    if devMode:
        print(str(var))


# 3 CALCULATE POINTS
def validate_point_from_donation(donation_amount, points_delta):
    # Dont trust anyone to do basic math
    # Divide by 100, result x 15 (each 100m gets 15 bonus points)
    # Modulus of previous calculation divide by 25, result x 7 (each 25m gets 7 bonus points)
    # Modulus of previous calculation added to result
    # Return total points
    # examples:
    # 7m = 7 points (1 * 7)
    # 30m = 37 points (1 * 30 /+/ 1 * 7(25m))
    # 155m = 184 points (1 * 155 /+/ 2 * 7(25m) /+/ 1 * 15(100m))
    hundred_points = int(donation_amount / 100000000)
    twenty_five_points = int((donation_amount % 100000000) / 25000000)
    ones_points = int(donation_amount / 1000000)
    total_points = (hundred_points * 15) + (twenty_five_points * 7) + ones_points
    if int(total_points) == int(points_delta):
        return True
    else:
        return False


# 4 Calculate a points value given the donation amount
def calculate_points_from_donation(donation_amount):
    hundred_points = int(donation_amount / 100000000)
    # printd("How many bonus points for 100 million: " + str(hundred_points))
    twenty_five_points = int((donation_amount % 100000000) / 25000000)
    # printd("How many bonus points for 25 million: " + str(twenty_five_points))
    ones_points = int(donation_amount / 1000000)
    # printd("How many additional points for per million: " + str(ones_points))
    total_points = (hundred_points * 15) + (twenty_five_points * 7) + ones_points
    printd("Total points: " + str(total_points))
    return total_points


# 5 VALIDATE COMMAND USER
def admin_abuse(discord_id_receiver, discord_admin_id):
    if int(discord_id_receiver) == int(discord_admin_id):
        return True
    else:
        return False


# 6 DATE MANAGER
def valid_date(date_string):
    # Date must be provided in 'YYYY-MM-DD' format
    printd(str(date_string))
    try:
        datetime.fromisoformat(str(date_string))
    except Exception as ex:
        printd(ex)
        return False
    return True


# 7 REWARD COSTS
def get_reward_cost(reward):
    switcher = {
        1: 75,   # 3-month temporary in-game icon
        2: 200,  # Permanent icon and discord role
        3: 50,   # Discord role change or icon unlock
        4: 275,  # Custom SOTW
        5: 400,  # Custom event (non-SOTW)
    }
    return switcher.get(reward, 0)


# 8 REWARD NAMES
def get_reward_name(reward_id):
    switcher = {
        1: "3-month temporary in-game icon",
        2: "Permanent icon and discord role",
        3: "Discord role change or icon unlock",
        4: "Custom SOTW",
        5: "Custom event (non-SOTW)",
    }
    return switcher.get(reward_id, 0)


# 9 REWARD LIMITS
def get_reward_limits(reward_id):
    switcher = {
        1: 0,  # Members can get a temporary icon unlimited times
        2: 1,  # Members can only unlock a permanent icon once
        3: 0,  # Members can pay to unlock a discord icon or change their role color unlimited times
        4: 0,  # Members can create unlimited SOTW events
        5: 0,  # Members can create unlimited non-SOTW events
    }
    return switcher.get(reward_id, 0)


# 10 REWARD PRE-REQUSITES
def get_reward_pre_reqs(reward_id):
    switcher = {
        1: 0,  # Temp icon has no pre-reqs
        2: 0,  # Discord name has no pre-reqs
        3: 2,  # Change color/icon requires reward id 2
        4: 0,  # SOTW event has no pre-reqs
        5: 0,  # non-SOTW event has no pre-reqs
    }
    return switcher.get(reward_id, 0)


# ============================================================
# =DATABASE MANAGEMENT========================================
# ============================================================
#
# 1 CREATE THE DATABASES
db_main = sql.connect('alonezone_points.db')
cursor_main = db_main.cursor()
result_main = [0]
try:
    cursor_main.execute("CREATE TABLE members(discord_id_receiver PRIMARY KEY, current_points)")
    printd("Table 'members' created successfully.")
except Exception as e:
    printd(e)
try:
    cursor_main.execute("CREATE TABLE donations(txid type PRIMARY KEY, discord_id_receiver, discord_name_admin, date_of_action, donation_amount, points_delta, reward_id, note)")
    printd("Table 'donations' created successfully.")
except Exception as e:
    printd(e)

# 2 FILLING THE DATABASES
printd("===MEMBERS===")

# 3 TESTS AND CLEANUP
printd("===TESTS===")
result_main = cursor_main.execute("SELECT * FROM members")
printd(result_main.fetchall())
result_main = cursor_main.execute("SELECT * FROM donations")
printd(result_main.fetchall())
cursor_main.close()
db_main.close()
printd("===END STARTUP===")


# ============================================================
# =USER COMMANDS==============================================
# ============================================================
#
# 1 Lets the user check how many points they have
@bot.command(name="points", description="Allows a member to check their current points.", guild=discord.Object(id=guild))
async def points_cmd(interaction):
    points = get_user_points(str(interaction.user.id))

    if abs(points) == 1:
        await interaction.response.send_message("You have " + str(points) + " point!", allowed_mentions=allowed, ephemeral=public_response)
    else:
        await interaction.response.send_message("You have " + str(points) + " points!", allowed_mentions=allowed, ephemeral=public_response)


# 2 Lets the user check their donation history
@bot.command(name="donation_history", description="Allows a member to check their donation history.", guild=discord.Object(id=guild))
async def donation_history_cmd(interaction):
    db = sql.connect('alonezone_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT date_of_action, donation_amount FROM donations WHERE discord_id_receiver=" + str(interaction.user.id) + " AND donation_amount >0 ORDER BY txid")
    table_data = result.fetchall()
    headers = ('DATE', 'DONATION')
    cursor.close()
    db.close()
    await interaction.response.send_message(f"```\n{pretty_outputs(headers, table_data)}\n```", allowed_mentions=allowed, ephemeral=public_response)


# 3 Lets the user check their point history
@bot.command(name="point_history", description="Allows a member to check their point history.", guild=discord.Object(id=guild))
async def point_history_cmd(interaction):
    db = sql.connect('alonezone_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT date_of_action, points_delta FROM donations WHERE discord_id_receiver=" + str(interaction.user.id) + " AND points_delta != 0 ORDER BY txid")
    table_data = result.fetchall()
    headers = ('DATE', 'POINTS')
    cursor.close()
    db.close()
    await interaction.response.send_message(f"```\n{pretty_outputs(headers, table_data)}\n```", allowed_mentions=allowed, ephemeral=public_response)


# 4 Lets the user claim a reward with their points
@bot.command(name="claim_reward", description="Allows a member to claim a reward using points.", guild=discord.Object(id=guild))
@app_commands.describe(reward_id='The reward number you want to claim. Refer to /rewards for a list', )
async def claim_reward_cmd(interaction, reward_id: int):
    txid = str(get_next_donation_TXID())
    points_delta = ((get_reward_cost(reward_id)) * -1)
    printd("Points to be removed: " + str(points_delta))
    donation = str(0)
    discord_id_receiver = str(interaction.user.id)
    date = str(datetime.today().strftime('%Y-%m-%d'))
    note = "ID: " + str(reward_id)

    # Make sure all of the input data is valid before injecting it into the database
    validated_input = valid_command_user(discord_id_receiver, points_delta, reward_id)

    if points_delta != 0:
        if validated_input == "0":
            printd("Command validated, connecting to DB.")
            db = sql.connect('alonezone_points.db')
            cursor = db.cursor()
            # Add the "donation" to the donation history table, this will be a "0" GP donation with a negative point value
            cursor.execute("INSERT INTO donations VALUES(" + txid + ", " + discord_id_receiver + ", '" + interaction.user.name + "', '" + date + "', " + str(donation) + ", " + str(points_delta) + ", " + str(reward_id) + ", '" + str(note) + "')")
            db.commit()
            printd("Inserted data into donations table.")
            # Update the member table with the new point total
            cursor.execute("UPDATE members SET current_points = " + str(get_user_points(discord_id_receiver) + points_delta) + " WHERE discord_id_receiver='" + discord_id_receiver + "'")
            db.commit()
            printd("Updated data in the members table.")
            # Be a good dev and do your own gc
            cursor.close()
            db.close()
            if abs(points_delta) == 1:
                await interaction.response.send_message("**Reward claimed!**\n" + str(points_delta)[1:] + " point has been duducted and your new balance is " + str(get_user_points(discord_id_receiver)) + ".\nAn admin has been notified and will deliver your reward shortly.\n",
                                                        allowed_mentions=allowed, ephemeral=public_response)
            else:
                await interaction.response.send_message("**Reward claimed!**\n" + str(points_delta)[1:] + " points have been duducted and your new balance is " + str(get_user_points(discord_id_receiver)) + ".\nAn admin has been notified and will deliver your reward shortly.\n",
                                                        allowed_mentions=allowed, ephemeral=public_response)
                await interaction.guild.get_channel(admin_channel).send("A member has claimed a clan point reward!\n"
                                                                        "Please refer to the following record and process the reward.\n"
                                                                        "When completed, react to this message to indicate the reward has been processed.\n"
                                                                        "> Member: <@" + str(interaction.user.id) + ">\n"
                                                                        "> Reward: " + get_reward_name(reward_id))
        else:
            await interaction.response.send_message(validated_input, allowed_mentions=allowed, ephemeral=public_response)
    else:
        await interaction.response.send_message("Invalid reward ID provided! Please check /rewards and make sure you are claiming the correct reward.", allowed_mentions=allowed, ephemeral=public_response)


# 5 Lets the user see all the rewards available
@bot.command(name="rewards", description="Shows the list of currently available rewards.", guild=discord.Object(id=guild))
async def rewards_cmd(interaction):
    rewards_list = [('1', '75', '3-month temporary in-game clan icon'),
                    ('2', '200', 'Permanent in-game clan icon and discord role w/ custom name and color'),
                    ('3', '50', 'Discord role icon unlock *OR* change role name/color/icon'),
                    ('4', '275', 'Custom SOTW event - Must be claimed during a SOTW vote period'),
                    ('5', '400', 'Custom non-SOTW event - An admin will message you to discuss details')]
    await interaction.response.send_message(f"```\n{pretty_outputs(['ID', 'COST', 'DESCRIPTION'], rewards_list)}\n```", allowed_mentions=allowed, ephemeral=public_response)


# ============================================================
# =ADMIN COMMANDS=============================================
# ============================================================
# 1 Lets an admin add points to a member
@bot.command(name="add_donation", description="Allows an admin to add a donation to a members history.", guild=discord.Object(id=guild))
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    member='The discord ID of the member donating.',
    date='The date the donation occurred. Must be formatted as YYYY-MM-DD ie 2022-05-22',
    donation='The amount of GP donated.',
    note='Optional: A note about the transaction such as if a correction is being made'
)
async def add_donation_cmd(interaction, member: discord.Member, date: str, donation: int, note: Optional[str]):
    txid = str(get_next_donation_TXID())
    points_delta = calculate_points_from_donation(donation)
    discord_id_receiver = str(member.id)
    validated_input = valid_command_admin(discord_id_receiver, interaction.user, date, points_delta, donation)

    if validated_input == "0":
        printd("Command validated, connecting to DB.")
        db = sql.connect('alonezone_points.db')
        cursor = db.cursor()
        # Add the donation to the donation history table
        cursor.execute("INSERT INTO donations VALUES(" + txid + ", " + discord_id_receiver + ", '" + interaction.user.name + "', '" + date + "', " + str(donation) + ", " + str(points_delta) + ", " + "-1" + ", '" + str(note) + "')")
        db.commit()
        printd("Inserted data into donations table.")
        # Update the member table with the donors new point total
        cursor.execute("UPDATE members SET current_points = " + str(get_user_points(discord_id_receiver) + points_delta) + " WHERE discord_id_receiver='" + discord_id_receiver + "'")
        db.commit()
        printd("Updated data in the members table.")
        # Be a good dev and do your own gc
        cursor.close()
        db.close()
        await interaction.response.send_message("Successfully added donation of " + str(donation) + "gp from " + str(member.name) + ", awarding " + str(points_delta) + " points.", allowed_mentions=allowed, ephemeral=silent_response)
    else:
        await interaction.response.send_message(validated_input, allowed_mentions=allowed, ephemeral=silent_response)


# 2 Lets an admin remove points from a member
@bot.command(name="remove_points", description="Allows an admin to remove points from a member.", guild=discord.Object(id=guild))
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    member='The discord ID of the member to remove points from.',
    points_to_remove='The amount of points to remove.',
    note='Explain why you are removing points from this member.'
)
async def remove_points_cmd(interaction, member: discord.Member, points_to_remove: int, note: str):
    txid = str(get_next_donation_TXID())
    points_delta = (abs(points_to_remove) * -1)
    printd("Points to be removed: " + str(points_delta))
    donation = str(0)
    discord_id_receiver = str(member.id)
    date = str(datetime.today().strftime('%Y-%m-%d'))

    # Make sure all of the input data is valid before injecting it into the database
    validated_input = valid_command_admin(discord_id_receiver, interaction.user, date, points_delta, donation)

    if points_to_remove != 0:
        if validated_input == "0":
            printd("Command validated, connecting to DB.")
            db = sql.connect('alonezone_points.db')
            cursor = db.cursor()
            # Add the "donation" to the donation history table, this will be a "0" GP donation with a negative point value
            cursor.execute("INSERT INTO donations VALUES(" + txid + ", " + discord_id_receiver + ", '" + interaction.user.name + "', '" + date + "', " + str(donation) + ", " + str(points_delta) + ", " + "-1" + ", '" + str(note) + "')")
            db.commit()
            printd("Inserted data into donations table.")
            # Update the member table with the new point total
            cursor.execute("UPDATE members SET current_points = " + str(get_user_points(discord_id_receiver) + points_delta) + " WHERE discord_id_receiver='" + discord_id_receiver + "'")
            db.commit()
            printd("Updated data in the members table.")
            # Be a good dev and do your own gc
            cursor.close()
            db.close()
            if abs(points_delta) == 1:
                await interaction.response.send_message("Successfully removed " + str(points_delta)[1:] + " point from " + str(member.name) + ", new balance is " + str(get_user_points(discord_id_receiver)) + ".", allowed_mentions=allowed, ephemeral=silent_response)
            else:
                await interaction.response.send_message("Successfully removed " + str(points_delta)[1:] + " points from " + str(member.name) + ", new balance is " + str(get_user_points(discord_id_receiver)) + ".", allowed_mentions=allowed, ephemeral=silent_response)
        else:
            await interaction.response.send_message(validated_input, allowed_mentions=allowed, ephemeral=silent_response)
    else:
        await interaction.response.send_message("Cannot remove 0 points!", allowed_mentions=allowed, ephemeral=silent_response)


# 3 Lets an admin check the full history of points and donations of a member
@bot.command(name="all_history", description="Allows an admin to check a members full record.", guild=discord.Object(id=guild))
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    member='The discord tag of the member donating.'
)
async def all_history_cmd(interaction, member: discord.Member):
    db = sql.connect('alonezone_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT txid, discord_name_admin, date_of_action, donation_amount, points_delta, note FROM donations WHERE discord_id_receiver=" + str(member.id) + " ORDER BY txid")
    table_data = result.fetchall()
    headers = ('TXID', 'ADMIN', 'DATE', 'DONATION', 'POINTS', 'NOTE')
    cursor.close()
    db.close()
    await interaction.response.send_message(f"```\n{pretty_outputs(headers, table_data)}\n```", allowed_mentions=allowed, ephemeral=silent_response)


# 4 Lets an admin check the bot version
@bot.command(name="version", description="Displays the bots version.", guild=discord.Object(id=guild))
@app_commands.checks.has_permissions(administrator=True)
async def version(interaction):
    await interaction.response.send_message("Currenly running: " + clientVersion, allowed_mentions=allowed, ephemeral=silent_response)


# 5 Lets a specific user send SQL commands directly through discord
# THIS IS AN EXTREMELY DANGEROUS COMMAND, DO NOT LET ANYONE USE THIS
@bot.command(name="sql", description="Sends SQL commands", guild=discord.Object(id=guild))
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    command='The SQL command to send.',
)
async def SQL(interaction, command: str):
    if (str(interaction.user.id) == str(sql_admin)) | (str(interaction.user.id) == str(interaction.guild.owner.id)):  # ID's are 1 admin and the server owner
        db = sql.connect('alonezone_points.db')
        cursor = db.cursor()
        result = cursor.execute(command)
        if "DROP TABLE" not in result:
            if "TRUNCATE TABLE" not in result:
                if "DELETE" not in result:
                    await interaction.response.send_message(result.fetchall(), allowed_mentions=allowed, ephemeral=silent_response)
        else:
            await interaction.response.send_message("Sorry, the \"DROP TABLE\", \"TRUNCATE TABLE\", and \"DELETE\" commands are not available via discord command.", allowed_mentions=allowed, ephemeral=silent_response)
        cursor.close()
        db.close()
    else:
        await interaction.response.send_message("Sorry, only Trusted Users:tm: can execute SQL commands!", allowed_mentions=allowed, ephemeral=public_response)


# ============================================================
# =DATABASE ACCESSING METHODS=================================
# ============================================================
#
# 1 Check the member database to see if they exist
def member_exists(discord_id_receiver):
    db = sql.connect('alonezone_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT discord_id_receiver FROM members WHERE discord_id_receiver='" + str(discord_id_receiver) + "'")
    output = not result.fetchone() is None
    cursor.close()
    db.close()
    return output


# 2 Create a member in the member database
def create_member(discord_id_receiver, points_delta):
    if valid_points_delta(discord_id_receiver, points_delta):
        if not member_exists(discord_id_receiver):
            db = sql.connect('alonezone_points.db')
            cursor = db.cursor()
            cursor.execute("INSERT INTO members VALUES('" + str(discord_id_receiver) + "', " + str(points_delta) + ")")
            db.commit()
            cursor.close()
            db.close()
            printd("Member created with ID " + str(discord_id_receiver) + " giving " + str(points_delta) + " points.")
        else:
            printd("Member with ID " + discord_id_receiver + " already exists.")
    else:
        printd("Cannot create member with negative points.")


# 3 Returns the next TXID for proper record keeping
def get_next_donation_TXID():
    db = sql.connect('alonezone_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT * FROM donations")
    rows = len(result.fetchall())
    cursor.close()
    db.close()
    return rows


# 4 Checks the member database for points and verifies the provided point delta would not result in a negative value
def valid_points_delta(discord_id_receiver, points_delta):
    printd("Point getter: " + str(discord_id_receiver) + "; Amount: " + str(points_delta))
    if points_delta < 0:
        printd("Point delta is < 0..")
        if member_exists(discord_id_receiver):
            printd("Member already exists..")
            # Get the current points the member has so we can check if we're subtracting too many
            current_points = get_user_points(discord_id_receiver)
            printd("Current points: " + str(current_points) + ", " + "Points delta: " + str(points_delta))
            if int(abs(current_points) - abs(points_delta)) < 0:
                printd("Delta points cannot result in a negative.")
                return False
            else:
                printd("Able to subtract " + str(points_delta)[1:] + " from " + str(current_points))
                return True
        else:
            printd("Delta cannot be negative for a new member.")
            return False
    else:
        printd("Delta is positive, this is always fine.")
        return True


# 5 GET USER POINTS
def get_user_points(discord_id_receiver):
    if not member_exists(discord_id_receiver):
        create_member(discord_id_receiver, 0)
    db = sql.connect('alonezone_points.db')
    cursor = db.cursor()
    printd("Point receiver ID: " + str(discord_id_receiver))
    result = cursor.execute("SELECT current_points FROM members WHERE discord_id_receiver='" + discord_id_receiver + "'")
    points = str(result.fetchall())
    cursor.close()
    db.close()
    printd("User points: " + str(points))
    if points == "None":
        return int(0)
    else:
        return int(points[2:-3])


# 6 VALIDATE COMMAND
def valid_command_admin(discord_id_receiver, discord_admin_object, date_of_action, points_delta, amount):
    printd("Validating donation is positive..")
    if int(amount) >= 0:
        printd("Validating command..")
        if not admin_abuse(discord_id_receiver, discord_admin_object.id):
            printd("Admin abuse..")
            if valid_points_delta(discord_id_receiver, points_delta):
                printd("Point delta validation..")
                if not member_exists(discord_id_receiver):
                    printd("New member creation..")
                    create_member(discord_id_receiver, 0)
                if valid_date(date_of_action):
                    printd("All tests passed!")
                    return "0"
                else:
                    return "Date provided is invalid!"
            else:
                return "Point delta is invalid!"
        else:
            return "Admins cannot modify their own points!"
    else:
        return "Donations cant be negative!"


# 7 VALIDATE COMMAND but for users with different requirements
def valid_command_user(discord_id_receiver, points_delta, reward_id):
    # In theory this command should only be used for claiming rewards
    # We need to verify that the member exists in the database, that they have enough points, and that they haven't already claimed that reward
    printd("Validating command..")
    if not member_exists(discord_id_receiver):
        printd("New member creation..")
        create_member(discord_id_receiver, 0)
        # A new user will never have enough points to claim anything
        return "Unable to claim reward, not enough points."
    else:
        printd("Point delta validation..")
        if valid_points_delta(discord_id_receiver, points_delta):
            result_hold = can_claim_reward(discord_id_receiver, reward_id)
            if result_hold == "0":
                printd("All tests passed!")
                return "0"
            else:
                printd(str(result_hold) + " // valid_command_user")
                return result_hold
        else:
            return "Unable to claim reward, not enough points."


# 8 Make sure users don't already have the reward they want to claim
# TODO make sure this works
def can_claim_reward(discord_id_receiver, reward_id):
    # Certain rewards can only be claimed once
    printd("Validating reward claim history..")

    # Database opening
    db = sql.connect('alonezone_points.db')

    # We need to check if the reward has a pre-requisite
    # 0 means none; >0 means it requires the returned reward ID
    pre_req = int(get_reward_pre_reqs(reward_id))
    if int(pre_req) == 0:
        printd("Reward has no pre-requsites")
    else:
        printd("Reward ID " + str(reward_id) + " requires reward id " + str(pre_req) + " to purchase..")

        # ADD HANDLES FOR EACH REWARD WITH PRE-REQS HERE
        # Reward ID 3 - Requires reward ID 2
        printd("Reward ID 3 requires reward ID 2..")
        cursor = db.cursor()
        result = cursor.execute("SELECT reward_id FROM donations WHERE discord_id_receiver=" + str(discord_id_receiver) + " AND reward_id=2")
        fetchall = result.fetchall()
        printd(str(fetchall) + " // " + str(len(fetchall)))
        # This check is kind of janky. It just checks the length of the list of results where the reward ID = 2; if the list is empty, then they dont have it
        if len(fetchall) == 0:
            printd("Member does not have the required pre-requsite")
            cursor.close()
            db.close()
            return "Unable to claim reward!\nYou must have unlocked \"Permanent Discord Role with Custom Name (ID 2)\" before you can unlock a Role Icon or change the color."

    printd("The player meets that requirements to claim the reward.")
    cursor = db.cursor()
    cursor.execute("SELECT reward_id FROM donations WHERE discord_id_receiver=" + str(discord_id_receiver))

    result = str(cursor.fetchall())
    printd("List of all claimed rewards: " + str(result))
    printd("Is reward ID in list: " + str("(" + str(reward_id) + ",)" in result))

    # ###EXTRA CODE WILL NEED TO BE WRITTEN TO SUPPORT CLAIMING A REWARD X TIMES
    # ###I DONT WANT OR NEED TO DO THAT RIGHT NOW

    # We need to check if the member has claimed the same reward ID before
    if str("(" + str(reward_id) + ",)") in result:
        printd("Found reward ID " + str(reward_id) + " in user claim history..")

        # We need to check the maximum number of times that reward ID can be claimed
        # ADD HANDLES FOR EACH REWARD WHICH CANNOT BE CLAIMED MULTIPLE TIMES
        if int(reward_id) == 2:
            printd("Cannot claim reward ID 2 multiple times.")
            cursor.close()
            db.close()
            return "Cannot claim \"Permanent Discord and Clan Role\" multiple times!"
        else:
            printd("Playes can claim reward ID " + str(reward_id) + " multiple times.")
            cursor.close()
            db.close()
            return "0"
    else:
        printd("Member has not claimed reward ID " + str(reward_id) + " before.")
        cursor.close()
        db.close()
        return "0"


# ============================================================
# =BOT INITIALIZATION=========================================
# ============================================================
#
# 1 This apparently makes slash commands work or something
@client.event
async def on_ready():
    await bot.sync(guild=discord.Object(id=guild))
    printd("Slash Commands Synced.")


# ============================================================
# =RUN BOT====================================================
# ============================================================
#
# 1 Run the bot
# Uses launch args to pass the token in, to run bot execute as: "python3 points_bot.py --token <your_token_here>"
client.run(args.token)
