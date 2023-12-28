# ============================================================
# =DISCORD BOT WRITTEN BY KINOMORA============================
# =FOR USE IN ALONESCAPE'S DISCORD SERVER=====================
# =LICENSED UNDER THE MIT LICENSE=============================
# ============================================================
import math

import discord
import argparse
import sqlite3 as sql

from discord import app_commands
from typing import Optional
from datetime import datetime
from prettytable import *
from pagination import Pagination

# lets me use arguments in the commandline to set developer mode in the IDE without having to toggle it every time
parser = argparse.ArgumentParser(description='Various required arguments in order to launch the software')
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
hundred_mil_bonus = 7  # Default 15 - bonus points per 100mil
twenty_five_mil_bonus = 4  # Default 5 - bonus points per 25 mil
ten_mil_bonus = 3  # Default 3 - bonus points per 10 mil
mil_points = 1  # Default 1 - points per mil
entries_per_page = 10  # Set the number of records per discord message (pagination for long point and donation histories)
clientVersion = "Version 1.0" + args.ver
database = 'clan_points.db'
if args.mode == "True":
    devMode = True
else:
    devMode = False


# ============================================================
# =DATA PROCESSING METHODS====================================
# ============================================================
#
# a1 Convert arbitrary table sizes into pretty outputs
def pretty_outputs(headers, table_input):
    table = PrettyTable(headers)
    table.add_rows(table_input)
    table.align = "l"
    table.set_style(DOUBLE_BORDER)
    return table


# a2 Custom print method conditional on dev mode
def printd(var):
    if devMode:
        print(str(var))


# a3 CALCULATE POINTS
def validate_point_from_donation(donation_amount, points_delta):
    # Dont trust anyone to do basic math
    # Bonus points are awared for passing thresholds plus the standard point-per-mil (default 1 ppm)
    # Points cannot count for more than 1 threshold, ie, 100m points doesn't give 7*1(100m) + 4*4(25m) + 3*10(10m), it only gives 107 points)
    # Divide by 100, result x 15 (each 100m gets 15 bonus points)
    # Modulus of previous calculation divide by 25, result x 7 (each 25m gets 7 bonus points)
    # Modulus of previous calculation added to result
    # Return total points
    mils = int(donation_amount / 1000000)  # converting mils donated into single digits for easier math
    hundred_points = int(mils / 100)
    printd("Member gets " + str(hundred_points) + " bonus 100 mil points.")
    twenty_five_points = int((mils % 100) / 25)
    printd("Member gets " + str(twenty_five_points) + " bonus 25 mil points.")
    ten_points = int(((mils % 100) % 25) / 10)
    printd("Member gets " + str(ten_points) + " bonus 10 mil points.")
    ones_points = int(mils * mil_points)
    total_points = (hundred_points * hundred_mil_bonus) + (twenty_five_points * twenty_five_mil_bonus) + (ten_points * ten_mil_bonus) + ones_points
    printd("Member gets " + str(total_points) + " points.")
    if int(total_points) == int(points_delta):
        return True
    else:
        return False


# a4 Calculate a points value given the donation amount
def calculate_points_from_donation(donation_amount):
    hundred_points = int(donation_amount / 100000000)
    # printd("How many bonus points for 100 million: " + str(hundred_points))

    twenty_five_points = int((donation_amount % 100000000) / 25000000)
    # printd("How many bonus points for 25 million: " + str(twenty_five_points))

    ones_points = int(donation_amount / 1000000)
    # printd("How many additional points for per million: " + str(ones_points))

    total_points = (hundred_points * hundred_mil_bonus) + (twenty_five_points * twenty_five_mil_bonus) + ones_points
    printd("Total points: " + str(total_points))
    return total_points


# a5 VALIDATE COMMAND USER
def admin_abuse(discord_id_receiver, discord_admin_id):
    if int(discord_id_receiver) == int(discord_admin_id):
        return True
    else:
        return False


# a6 DATE MANAGER
def valid_date(date_string):
    # Date must be provided in 'YYYY-MM-DD' format
    printd(str(date_string))
    try:
        datetime.fromisoformat(str(date_string))
    except Exception as ex:
        printd(ex)
        return False
    return True


# a7 REWARD COSTS
def get_reward_cost(reward):
    switcher = {
        1: 75,  # 3-month temporary in-game icon
        2: 200,  # Permanent icon and discord role
        3: 50,  # Discord role change or icon unlock
        4: 275,  # Custom SOTW
        5: 400,  # Custom event (non-SOTW)
    }
    return switcher.get(reward, 0)


# a8 REWARD NAMES
def get_reward_name(reward_id):
    switcher = {
        1: "3-month temporary in-game icon",
        2: "Permanent icon and discord role",
        3: "Discord role change or icon unlock",
        4: "Custom SOTW",
        5: "Custom event (non-SOTW)",
    }
    return switcher.get(reward_id, 0)


# a9 REWARD LIMITS
def get_reward_limits(reward_id):
    switcher = {
        1: 0,  # Members can get a temporary icon unlimited times
        2: 1,  # Members can only unlock a permanent icon once
        3: 0,  # Members can pay to unlock a discord icon or change their role color unlimited times
        4: 0,  # Members can create unlimited SOTW events
        5: 0,  # Members can create unlimited non-SOTW events
    }
    return switcher.get(reward_id, 0)


# a10 REWARD PRE-REQUSITES
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
db_main = sql.connect('clan_points.db')
cursor_main = db_main.cursor()
result_main = [0]
try:
    cursor_main.execute("CREATE TABLE members(discord_id_receiver PRIMARY KEY, current_points)")
    printd("Table 'members' created successfully.")
except Exception as e:
    printd(e)
try:
    cursor_main.execute("CREATE TABLE donations(txid type PRIMARY KEY, discord_id_receiver, discord_name_interaction, date_of_action, donation_amount, points_delta, reward_id, note)")
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
        await interaction.response.send_message("You have " + str(points) + " point!", allowed_mentions=allowed, ephemeral=silent_response)
    else:
        await interaction.response.send_message("You have " + str(points) + " points!", allowed_mentions=allowed, ephemeral=silent_response)


# 2 Lets the user check their donation history
@bot.command(name="donation_history", description="Allows a member to check their donation history.", guild=discord.Object(id=guild))
async def donation_history_cmd(interaction):
    db = sql.connect('clan_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT date_of_action, donation_amount FROM donations WHERE discord_id_receiver=" + str(interaction.user.id) + " AND donation_amount >0 ORDER BY txid")
    table_data = result.fetchall()
    # printd("Table data: " + str(table_data))
    headers = ('DATE', 'DONATION')
    cursor.close()
    db.close()

    async def get_page(page: int):
        emb = discord.Embed(title="Donation History for " + str(interaction.user.name), description="")
        offset = (page - 1) * entries_per_page
        # printd("Offset: " + str(offset))
        table_data_printing = []
        index = 0
        for record in table_data:
            # printd(record)
            # if the record is equal to or below max of the current page amount, then...
            if index < (offset + entries_per_page):
                # if the record is greater than the start of the current page amount, then...
                if index >= offset:
                    # This record is between 0 and entries_per_page offset by the page number(* e_p_p)
                    # Ex, 10 e_p_p, page 1, this adds records 0-9
                    table_data_printing.append(record)
            index += 1

        formatted_table_data = pretty_outputs(headers, table_data_printing)
        # printd("Output: \n" + str(formatted_table_data))

        emb.description = f"```{formatted_table_data}```\n"
        pages = math.ceil(len(table_data) / entries_per_page)  # Pagination.compute_total_pages(len(table_data), entries_per_page)
        # printd("Total entries: " + str(len(table_data)) + " | Total pages: " + str(pages))
        emb.set_footer(text=f"Page {page} of {pages}")
        return emb, pages

    await Pagination(interaction, get_page).navigate()


# 3 Lets the user check their point history
@bot.command(name="point_history", description="Allows a member to check their point history.", guild=discord.Object(id=guild))
async def point_history_cmd(interaction):
    db = sql.connect('clan_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT date_of_action, points_delta FROM donations WHERE discord_id_receiver=" + str(interaction.user.id) + " AND points_delta != 0 ORDER BY txid")
    table_data = result.fetchall()
    headers = ('DATE', 'POINTS')
    cursor.close()
    db.close()

    # await interaction.response.send_message(f"```\n{pretty_outputs(headers, table_data)}\n```", allowed_mentions=allowed, ephemeral=silent_response)

    async def get_page(page: int):
        emb = discord.Embed(title="Point History for " + str(interaction.user.name), description="")
        offset = (page - 1) * entries_per_page
        # printd("Offset: " + str(offset))
        table_data_printing = []
        index = 0
        for record in table_data:
            # printd(record)
            # if the record is equal to or below max of the current page amount, then...
            if index < (offset + entries_per_page):
                # if the record is greater than the start of the current page amount, then...
                if index >= offset:
                    # This record is between 0 and entries_per_page offset by the page number(* e_p_p)
                    # Ex, 10 e_p_p, page 1, this adds records 0-9
                    table_data_printing.append(record)
            index += 1

        formatted_table_data = pretty_outputs(headers, table_data_printing)
        printd("Output: \n" + str(formatted_table_data))

        emb.description = f"```{formatted_table_data}```\n"
        pages = math.ceil(len(table_data) / entries_per_page)  # Pagination.compute_total_pages(len(table_data), entries_per_page)
        printd("Total entries: " + str(len(table_data)) + " | Total pages: " + str(pages))
        emb.set_footer(text=f"Page {page} of {pages}")
        return emb, pages

    await Pagination(interaction, get_page).navigate()


# 4 Lets the user claim a reward with their points
@bot.command(name="claim_reward", description="Allows a member to claim a reward using points.", guild=discord.Object(id=guild))
@app_commands.describe(
    reward_id='The reward number you want to claim. Refer to /rewards for a list',
    user_note='A note to the admins regarding your reward. If you are claiming a role or icon, please provide the "#hexnum" and the desired "@RoleName".'
)
async def claim_reward_cmd(interaction, reward_id: int, user_note: Optional[str]):
    txid = str(get_next_donation_TXID())
    points_delta = ((get_reward_cost(reward_id)) * -1)
    printd("Points to be removed: " + str(points_delta))
    donation = str(0)
    discord_id_receiver = str(interaction.user.id)
    date = str(datetime.today().strftime('%Y-%m-%d'))
    note = "ID: " + str(reward_id)

    # Make sure all of the input data is valid before injecting it into the database
    validated_input = valid_command_user(discord_id_receiver, points_delta, reward_id)

    # Perform the function
    if points_delta != 0:
        if validated_input == "0":
            printd("Command validated, connecting to DB.")
            db = sql.connect('clan_points.db')
            cursor = db.cursor()
            # Add the "donation" to the donation history table, this will be a "0" GP donation with a negative point value
            cursor.execute("INSERT INTO donations VALUES(" + txid + ", " + discord_id_receiver + ", 'REWARD CLAIMED', '" + date + "', " + str(donation) + ", " + str(points_delta) + ", " + str(reward_id) + ", '" + str(note) + "')")
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
                                                        allowed_mentions=allowed, ephemeral=silent_response)
            else:
                await interaction.response.send_message("**Reward claimed!**\n" + str(points_delta)[1:] + " points have been duducted and your new balance is " + str(get_user_points(discord_id_receiver)) + ".\nAn admin has been notified and will deliver your reward shortly.\n",
                                                        allowed_mentions=allowed, ephemeral=silent_response)
                await interaction.guild.get_channel(admin_channel).send("## A member has claimed a clan point reward!\n"
                                                                        "*Please refer to the following information and process the reward.*\n\n"
                                                                        "When completed, react to this message to indicate the reward has been processed.\n"
                                                                        "> Member: <@" + str(interaction.user.id) + ">\n"
                                                                        "> Reward: " + get_reward_name(reward_id) + "\n"
                                                                        "> User note: " + str(user_note))
        else:
            await interaction.response.send_message(validated_input, allowed_mentions=allowed, ephemeral=silent_response)
    else:
        await interaction.response.send_message("Invalid reward ID provided! Please check /rewards and make sure you are claiming the correct reward.", allowed_mentions=allowed, ephemeral=silent_response)


# 5 Lets the user see all the rewards available
@bot.command(name="rewards", description="Shows the list of currently available rewards.", guild=discord.Object(id=guild))
async def rewards_cmd(interaction):
    rewards_list = [('1', '75', '3-month temporary in-game clan icon'),
                    ('2', '200', 'Permanent in-game clan icon and discord role w/ custom name and color'),
                    ('3', '50', 'Discord role icon unlock *OR* change role name/color/icon'),
                    ('4', '275', 'Custom SOTW event - Must be claimed during a SOTW vote period'),
                    ('5', '400', 'Custom non-SOTW event - An admin will message you to discuss details')]
    await interaction.response.send_message(f"```\n{pretty_outputs(['ID', 'COST', 'DESCRIPTION'], rewards_list)}\n```", allowed_mentions=allowed, ephemeral=silent_response)


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
        db = sql.connect('clan_points.db')
        cursor = db.cursor()
        # Add the donation to the donation history table
        cursor.execute("INSERT INTO donations VALUES(" + txid + ", " + discord_id_receiver + ", '" + interaction.user.name[:15] + "', '" + date + "', " + str(donation) + ", " + str(points_delta) + ", " + "-1" + ", '" + str(note) + "')")
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
            db = sql.connect('clan_points.db')
            cursor = db.cursor()
            # Add the "donation" to the donation history table, this will be a "0" GP donation with a negative point value
            cursor.execute("INSERT INTO donations VALUES(" + txid + ", " + discord_id_receiver + ", '" + interaction.user.name[:15] + "', '" + date + "', " + str(donation) + ", " + str(points_delta) + ", " + "-1" + ", '" + str(note) + "')")
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
    db = sql.connect('clan_points.db')
    cursor = db.cursor()
    result = cursor.execute("SELECT discord_name_interaction, date_of_action, donation_amount, points_delta, note FROM donations WHERE discord_id_receiver=" + str(member.id) + " ORDER BY txid")
    table_data = result.fetchall()
    headers = ('ADMIN or ACTION', 'DATE', 'DONATION', 'POINTS', 'NOTE')
    cursor.close()
    db.close()

    # await interaction.response.send_message(f"```\n{pretty_outputs(headers, table_data)}\n```", allowed_mentions=allowed, ephemeral=silent_response)

    async def get_page(page: int):
        emb = discord.Embed(title="Point History for " + str(member.name), description="")
        offset = (page - 1) * entries_per_page
        # printd("Offset: " + str(offset))
        table_data_printing = []
        index = 0
        for record in table_data:
            # printd(record)
            # if the record is equal to or below max of the current page amount, then...
            if index < (offset + entries_per_page):
                # if the record is greater than the start of the current page amount, then...
                if index >= offset:
                    # This record is between 0 and entries_per_page offset by the page number(* e_p_p)
                    # Ex, 10 e_p_p, page 1, this adds records 0-9
                    table_data_printing.append(record)
            index += 1

        formatted_table_data = pretty_outputs(headers, table_data_printing)
        printd("Output: \n" + str(formatted_table_data))

        emb.description = f"```{formatted_table_data}```\n"
        pages = math.ceil(len(table_data) / entries_per_page)  # Pagination.compute_total_pages(len(table_data), entries_per_page)
        printd("Total entries: " + str(len(table_data)) + " | Total pages: " + str(pages))
        emb.set_footer(text=f"Page {page} of {pages}")
        return emb, pages

    await Pagination(interaction, get_page).navigate()


# 4 Lets an admin check the bot version
@bot.command(name="version", description="Displays the bots version.", guild=discord.Object(id=guild))
@app_commands.checks.has_permissions(administrator=True)
async def version(interaction):
    await interaction.response.send_message("Currenly running: " + clientVersion, allowed_mentions=allowed, ephemeral=silent_response)


# ============================================================
# =DATABASE ACCESSING METHODS=================================
# ============================================================
#
# 1 Check the member database to see if they exist
def member_exists(discord_id_receiver):
    db = sql.connect('clan_points.db')
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
            db = sql.connect('clan_points.db')
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
    db = sql.connect('clan_points.db')
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
    db = sql.connect('clan_points.db')
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
def can_claim_reward(discord_id_receiver, reward_id):
    # Certain rewards can only be claimed once
    printd("Validating reward claim history..")

    # Database opening
    db = sql.connect('clan_points.db')

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
