import logging
import sys

level_colors = {
	logging.CRITICAL: ("1;35", "CRIT"),
	logging.ERROR:    ("1;31", "ERROR"),
	logging.WARNING:  ("1;33", "WARN"),
	logging.INFO:     ("1;39", "INFO"),
	logging.DEBUG:    ("0;39", "DEBUG"),
	logging.NOTSET:   ("1;30", "")
}

class ColorFormatter(logging.Formatter):
	def __init__(self, fmt=None, datefmt=None):
		super().__init__(fmt, datefmt)

	def format(self, record):
		level = max(filter(lambda lvl: record.levelno >= lvl, level_colors))
		color_pre = "\033[" + level_colors[level][0] + "m"
		color_post = "\033[0m"
		level_label = level_colors[level][1]
		super().format(record)
		return "%s%s [%-5s] [%s] %s%s" % (
			color_pre,
			super(ColorFormatter, self).formatTime(record),
			level_label,
			record.name,
			record.message,
			color_post
		)

console = logging.StreamHandler(sys.stdout)
console.setFormatter(ColorFormatter())
root_logger = logging.getLogger()
root_logger.addHandler(console)
root_logger.setLevel(logging.WARN)
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)

import discord
import discord.ext.commands

BOT_TOKEN = 
GUILD_ID = 
TEAM_NAME_PREFIX = 'Team '
TEAM_ROLE_COLOR = discord.Colour.dark_blue()

class TeamBot:
	def __init__(self):
		self.logger = logging.getLogger('bot')
		self.guild = None
		self.users = {}
		self.teams = {}

	def client_ready(self, client):
		self.logger.info("Logged in as %s (%s)", client.user.name, client.user.id)
		for guild in client.guilds:
			if str(guild.id) == GUILD_ID:
				self.guild = guild
				self.process_guild(guild)

	def process_guild(self, guild):
		self.logger.debug("Processing guild %s (%s)", guild.name, guild.id)
		for role in guild.roles:
			self.process_role(role)
		for member in guild.members:
			self.process_user(member)

	def process_role(self, role):
		self.logger.debug("Processing role %s (%s)", role.name, role.id)
		if role.name.startswith(TEAM_NAME_PREFIX):
			self.process_team(role)

	def unprocess_role(self, role):
		self.logger.debug("Unprocessing role %s (%s)", role.name, role.id)
		if role.name.startswith(TEAM_NAME_PREFIX):
			self.unprocess_team(role)

	def process_team(self, role):
		team = {
			'id': str(role.id),
			'name': role.name,
			'members': [str(m.id) for m in role.members],
			'role': role
		}
		self.teams[team['id']] = team
		self.logger.debug("Processed team \"%s\" with %d member(s)", team['name'], len(team['members']))

	def unprocess_team(self, role):
		team = self.teams[str(role.id)]
		del self.teams[str(role.id)]
		self.logger.debug("Deleted team \"%s\" with %d member(s)", team['name'], len(team['members']))

	def process_user(self, user):
		new_user = {
			'id': str(user.id),
			'name': user.name
		}
		self.users[new_user['id']] = new_user

		for role in user.roles:
			self.process_role(role)

		self.logger.debug("Processed user %s (%s)", new_user['name'], new_user['id'])

	def unprocess_user(self, user):
		for role in user.roles:
			self.process_role(role)

		old_user = self.users[str(user.id)]
		del self.users[str(user.id)]
		self.logger.debug("Unprocessed used %s (%s)", old_user['name'], old_user['id'])

	def get_team_by_id(self, id):
		return self.teams.get(id)

	def get_user_by_id(self, id):
		return self.users.get(id)

	def get_user_by_name(self, name):
		for user in self.users.values():
			if user['name'] == name:
				return user
		return None

	def get_team_of(self, user):
		for team in self.teams.values():
			if user['id'] in team['members']:
				return team
		return None

	async def create_team(self, owner, name):
		name = TEAM_NAME_PREFIX + name
		self.logger.info("Creating team \"%s\" for %s", name, owner['name'])

		role = await self.guild.create_role(
			name=name,
			permissions=discord.Permissions(),
			colour=TEAM_ROLE_COLOR,
			hoist=True,
			mentionable=True,
			reason="Create team command by %s (%s)" % (owner['name'], owner['id'])
		)
		await self.add_user_to_team(owner, self.get_team_by_id(str(role.id)))

	async def add_user_to_team(self, user, team):
		self.logger.info("Adding %s to %s", user, team)
		member = await self.guild.fetch_member(user['id'])
		await member.add_roles(team['role'])

client = discord.ext.commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot = TeamBot()

async def respond(channel, user, message):
	await channel.send(message)

@client.event
async def on_ready():
	bot.client_ready(client)

@client.command('status')
async def status(context):
	msg = context.message.clean_content
	users = [bot.get_user_by_name(uname) for uname in msg.split()[1:]]

	if len(users) == 0:
		uid = str(context.message.author.id)
		user = bot.get_user_by_id(uid)
		if user is None:
			logger.error("Unable to find user with id %s", uid)
		users = [user]

	for user in users:
		if user is None:
			continue

		team = bot.get_team_of(user)
		status = "Name: %s Team: %s" % (user['name'], ("(none)" if team is None else team['name']))
		await respond(context.channel, context.message.author, status)

@client.command('create')
async def create_team(context):
	msg = context.message.clean_content
	msg_split = msg.split(maxsplit=1)

	if len(msg_split) == 1:
		await respond(context.channel, context.message.author, "Syntax: !create <team_name>")
		return
	else:
		team_name = msg_split[1]

	owner = bot.get_user_by_id(str(context.message.author.id))
	await bot.create_team(owner, team_name)

@client.command('add')
async def add_to_team(context):
	msg = context.message.clean_content
	msg_split = msg.split(maxsplit=1)

	if len(msg_split) == 1:
		await respond(context.channel, context.message.author, "Syntax: !add <user_name>")
		return
	else:
		user_name = msg_split[1]

	source_user = bot.get_user_by_id(str(context.message.author.id))
	target_team = bot.get_team_of(source_user)
	if target_team is None:
		await respond(context.channel, context.message.author, "You are not in a team")
		return

	user = bot.get_user_by_name(user_name)
	if user is None:
		await respond(context.channel, context.message.author, "Could not find user \"%s\"" % (user_name,))
		return

	existing_team = bot.get_team_of(user)
	if existing_team is not None:
		await respond(context.channel, context.message.author, "%s is already in %s\n" % (user_name, existing_team['name']))
		return

	await bot.add_user_to_team(user, target_team)

@client.event
async def on_guild_role_create(role):
	bot.process_role(role)

@client.event
async def on_guild_role_delete(role):
	bot.unprocess_role(role)

@client.event
async def on_guild_role_update(before, after):
	bot.process_role(after)

@client.event
async def on_member_join(member):
	bot.process_user(member)

@client.event
async def on_member_remove(member):
	bot.unprocess_user(member)

@client.event
async def on_member_update(before, after):
	bot.process_user(after)

def main():
	client.run(BOT_TOKEN)

if __name__ == '__main__':
	main()

