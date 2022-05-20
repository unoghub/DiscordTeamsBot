import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

import discord
import discord.ext.commands

BOT_TOKEN = 
TEAM_NAME_PREFIX = 'Team '
TEAM_ROLE_COLOR = discord.Colour.dark_blue()

client = discord.ext.commands.Bot(command_prefix='!', intents=discord.Intents.all())

def get_team_of(member):
	for role in member.roles:
		if role.name.startswith(TEAM_NAME_PREFIX):
			if member in role.members:
				return role
	return None

def team_exists(guild, name):
	return any([role.name == name for role in guild.roles])

def ignore_context(context):
	return context.guild is None

async def respond(channel, user, message):
	await channel.send(f"<@!{user.id}>: {message}")

@client.event
async def on_ready():
	logger.info("Logged in as %s (%s)", client.user.name, client.user.id)

@client.command('status')
async def status(context):
	if ignore_context(context):
		return

	members = context.message.mentions

	if len(members) == 0:
		members = [context.message.author]

	for member in members:
		team = get_team_of(member)
		status = f"{member.name} :: {'(none)' if team is None else team.name}"
		await respond(context.channel, context.message.author, status)

@client.command('create')
async def create_team(context):
	async def _respond(msg):
		await respond(context.channel, context.message.author, msg)

	if ignore_context(context):
		return

	msg = context.message.clean_content
	msg_split = msg.split(maxsplit=1)

	if len(msg_split) == 1:
		await _respond("Syntax: !create <team_name>")
		return
	else:
		name = msg_split[1]

	team_name = TEAM_NAME_PREFIX + name
	owner = context.message.author

	if get_team_of(owner) is not None:
		await _respond("You are already in a team")
		return

	if team_exists(context.guild, team_name):
		await _respond(f"Team {name} already exists!")
		return

	logger.info("Creating team \"%s\" for %s", name, owner)

	role = await context.guild.create_role(
		name=team_name,
		permissions=discord.Permissions(),
		colour=TEAM_ROLE_COLOR,
		hoist=True,
		mentionable=True,
		reason=f"Create team command by {owner}"
	)
	await owner.add_roles(role, reason="Create team command")
	await _respond(f"Team {name} created!")

@client.command('add')
async def add_to_team(context):
	async def _respond(msg):
		await respond(context.channel, context.message.author, msg)

	if ignore_context(context):
		return

	members = context.message.mentions

	if len(members) == 0:
		await _respond("Syntax: !add <user>")
		return

	target_team = get_team_of(context.message.author)

	if target_team is None:
		await _respond("You are not in a team")
		return

	for member in members:
		existing_team = get_team_of(member)

		if existing_team is None:
			await member.add_roles(team, reason=f"Added by {context.message.author}")
			await _respond(f"{member.name} was added to {target_team.name}")
		else:
			await _respond(f"{member.name} is already in {existing_team.name}")

@client.command('leave')
async def leave_team(context):
	async def _respond(msg):
		await respond(context.channel, context.message.author, msg)

	user = context.message.author
	team = get_team_of(user)

	if team is None:
		await _respond("You are not in a team")
		return

	await user.remove_roles(team, reason=f"Leave command")
	await _respond(f"You have left {team.name}")

	if len(team.members) == 0:
		await context.channel.send(f"Removing empty team {team.name}")
		await team.delete(reason=f"Empty team")

client.run(BOT_TOKEN)
