import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

import discord
import discord.ext.commands

BOT_TOKEN = 
COMMAND_CHANNEL_ID = 
TEAM_NAME_PREFIX = 'Team '

client = discord.ext.commands.Bot(command_prefix='!', intents=discord.Intents.all())

def build_category_name(team_name):
	return f"🧩 {team_name}"

async def create_team(guild, team_name, owner):
	role = await guild.create_role(
		name=team_name,
		permissions=discord.Permissions(),
		colour=discord.Colour.dark_blue(),
		hoist=True,
		mentionable=True,
		reason=f"Create team command by {owner}"
	)
	category_permissions = {
		guild.default_role: discord.PermissionOverwrite.from_pair(
			discord.Permissions( # allow
			),
			discord.Permissions( # deny
			)
		),
		role: discord.PermissionOverwrite.from_pair(
			discord.Permissions( # allow
				manage_permissions=True,
				connect=True,
				read_messages=True,
				send_messages=True,
				speak=True,
			),
			discord.Permissions( # deny
				manage_channels=True,
			)
		)
	}
	category = await guild.create_category(
		name=build_category_name(team_name),
		overwrites=category_permissions,
		reason="Team creation"
	)
	await guild.create_text_channel(
		name=team_name,
		category=category,
		overwrites=category_permissions,
		reason="Team creation"
	)
	await guild.create_voice_channel(
		name=team_name,
		category=category,
		reason="Team creation"
	)
	await owner.add_roles(role, reason="Create team command")

async def delete_team(team):
	team_category = None
	for category in team.guild.categories:
		if category.name == build_category_name(team.name):
			team_category = category
			break

	if team_category is not None:
		for channel in team_category.channels:
			await channel.delete()
		await team_category.delete()

	await team.delete(reason=f"Empty team")

def get_team_of(member):
	for role in member.roles:
		if role.name.startswith(TEAM_NAME_PREFIX):
			if member in role.members:
				return role
	return None

def team_exists(guild, name):
	return any([role.name == name for role in guild.roles])

async def check_command_context(context):
	if str(context.channel.id) != COMMAND_CHANNEL_ID:
		await respond(context.channel, context.author, "I do not respond to messages on this channel")
		return False
	return True

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
async def create_team_cmd(context):
	async def _respond(msg):
		await respond(context.channel, context.message.author, msg)

	if not await check_command_context(context):
		return

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

	await create_team(context.guild, team_name, owner)
	await _respond(f"Team {name} created!")

@client.command('add')
async def add_to_team_cmd(context):
	async def _respond(msg):
		await respond(context.channel, context.message.author, msg)

	if not await check_command_context(context):
		return

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
async def leave_team_cmd(context):
	async def _respond(msg):
		await respond(context.channel, context.message.author, msg)

	if not await check_command_context(context):
		return

	user = context.message.author
	team = get_team_of(user)

	if team is None:
		await _respond("You are not in a team")
		return

	await user.remove_roles(team, reason=f"Leave command")
	await _respond(f"You have left {team.name}")

	if len(team.members) == 0:
		await context.channel.send(f"Removing empty team {team.name}")
		await delete_team(team)

client.run(BOT_TOKEN)
