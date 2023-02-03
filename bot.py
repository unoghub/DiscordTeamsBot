import discord.ext.commands
import discord
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')


BOT_TOKEN = ''
COMMAND_CHANNEL_ID = ''
JAMMER_ROLE_ID = ''
ADMIN_ROLE_ID = 
TEAM_NAME_PREFIX = 'Ekip '

client = discord.ext.commands.Bot(
    command_prefix='!', intents=discord.Intents.all())


def build_category_name(team_name):
    return f"🧩 {team_name}"


async def create_team(guild, team_name, owner):
    organizer_role = guild.get_role(int(JAMMER_ROLE_ID))
    role = await guild.create_role(
        name=team_name,
        permissions=discord.Permissions(),
        colour=discord.Colour.dark_blue(),
        hoist=True,
        mentionable=True,
        reason=f"Create team command by {owner}"
    )

    category_permissions = {
        role: discord.PermissionOverwrite.from_pair(
            discord.Permissions.all_channel(),  # allow
            discord.Permissions()  # deny
        ),
        organizer_role: discord.PermissionOverwrite.from_pair(
            discord.Permissions.all_channel(),  # allow
            discord.Permissions()  # deny
        ),
        guild.default_role: discord.PermissionOverwrite.from_pair(
            discord.Permissions(),  # allow
            discord.Permissions(view_channel=True)  # deny
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
        reason="Team creation"
    )
    await guild.create_voice_channel(
        name=team_name,
        category=category,
        reason="Team creation"
    )
    await owner.add_roles(role, reason="Create team command")


async def delete_team(team, channel):
    team_category = None
    for category in team.guild.categories:
        if category.name == build_category_name(team.name):
            team_category = category
            break

    if team_category is not None:
        for _channel in team_category.channels:
            await _channel.delete()
        await team_category.delete()

    await team.delete(reason=f"Empty team")
    await channel.send(f"{team.name} başarıyla silindi.")


def get_teams_of(member):
    roles = []
    for role in member.roles:
        if role.name.startswith(TEAM_NAME_PREFIX):
            if member in role.members:
                roles.append(role)
    return roles


def get_all_teams(guild):
    teams = []
    for role in guild.roles:
        if role.name.startswith(TEAM_NAME_PREFIX):
            teams.append(role)
    return teams


def team_exists(guild, name):
    return any([role.name == name for role in guild.roles])


async def check_command_context(context):
    if str(context.channel.id) != COMMAND_CHANNEL_ID:
        await respond(context.channel, context.author, f"Lütfen <#{COMMAND_CHANNEL_ID}> kanalı üzerinden komut veriniz.")
        return False
    return True


async def is_admin(context):
    admin_role = context.guild.get_role(ADMIN_ROLE_ID)
    return True if admin_role in context.author.roles else False


def ignore_context(context):
    return context.guild is None


async def respond(channel, user, message):
    await channel.send(f"<@!{user.id}> {message}")


@client.event
async def on_ready():
    logger.info("Logged in as %s (%s)", client.user.name, client.user.id)


@client.command('durum')
async def status(context):
    if ignore_context(context):
        return

    members = context.message.mentions

    if len(members) == 0:
        members = [context.message.author]

    for member in members:
        teams = get_teams_of(member)

        status = f"Bulunduğunuz ekipler: {'(yok)' if teams is [] else ', '.join([team.name for team in teams])}"
        await respond(context.channel, context.message.author, status)


@client.command('oluştur')
async def create_team_cmd(context):
    async def _respond(msg):
        await respond(context.channel, context.message.author, msg)

    if not await check_command_context(context):
        return

    if ignore_context(context):
        return

    owner = context.message.author

    if len(get_teams_of(owner)) >= 5:
        await _respond("Azami ekip sayısına ulaştınız!")
        return

    msg = context.message.clean_content
    msg_split = msg.split(maxsplit=1)

    if len(msg_split) == 1:
        await _respond("Sözdizimi: `!oluştur <ekip_adı>`")
        return
    else:
        name = msg_split[1]

    team_name = TEAM_NAME_PREFIX + name

    if team_exists(context.guild, team_name):
        await _respond(f"Halihazırda {name} adında bir ekip bulunmakta!")
        return

    await create_team(context.guild, team_name, owner)
    await _respond(f"Ekip {name} oluşturuldu!")


@client.command('ekle')
async def add_to_team_cmd(context):
    async def _respond(msg):
        await respond(context.channel, context.message.author, msg)

    if not await check_command_context(context):
        return

    if ignore_context(context):
        return

    teams = get_teams_of(context.message.author)

    if teams is []:
        await _respond("Herhangi bir ekipte değilsin!")
        return

    members = context.message.mentions

    if len(members) == 0:
        await _respond("Kimseyi etiketlemedin! Sözdizimi: `!ekle @<kullanıcı>`")
        return

    msg = context.message.clean_content
    msg_split = msg.split(maxsplit=2)

    specified_index = 0

    if len(teams) > 1:

        index = 0
        team_list = ''

        for team in teams:
            team_list += team.name + 'ekibinin indeksi: `' + str(index) + '`\n'
            index += 1

        if len(msg_split) == 2:
            await _respond(f"Birden fazla ekibe dahil olduğunuz için eklemek istediğiniz ekibi belirtiniz.\n\n{team_list}\nSözdizimi: `!ekle @<kullanıcı> <ekip_indeksi>`")
            return
        else:
            if msg_split[2].isnumeric() and int(msg_split[2]) < index:
                specified_index = int(msg_split[2])
            else:
                await _respond(f"Geçersiz indeks, lütfen uygun bir ekip indeksi belirtiniz.\n\n{team_list}\Sözdizimi: `!ekle @<kullanıcı> <ekip_indeksi>`")
                return

    specified_team = teams[specified_index]

    for member in members:
        existing_teams = get_teams_of(member)

        if existing_teams == []:
            await member.add_roles(specified_team, reason=f"Added by {context.message.author}")
            await _respond(f"{member.name}, {specified_team.name} ekibine eklendi!")
            return
        elif specified_team in existing_teams:
            await _respond(f"{member.name} zaten {specified_team.name} ekibinde mevcut.")
            return
        else:
            await member.add_roles(specified_team, reason=f"Added by {context.message.author}")
            await _respond(f"{member.name}, {specified_team.name} ekibine eklendi!")


@client.command('ayrıl')
async def leave_team_cmd(context):
    async def _respond(msg):
        await respond(context.channel, context.message.author, msg)

    if not await check_command_context(context):
        return

    user = context.message.author
    teams = get_teams_of(user)

    if teams is []:
        await _respond("Herhangi bir ekipte değilsin!")
        return

    specified_index = 0

    msg = context.message.clean_content
    msg_split = msg.split(maxsplit=1)

    if len(teams) > 1:

        index = 0
        team_list = ''

        for team in teams:
            team_list += team.name + 'ekibinin indeksi: `' + str(index) + '`\n'
            index += 1

        if len(msg_split) == 1:
            await _respond(f"Birden fazla ekibe dahil olduğunuz için ayrılmak istediğiniz ekibi belirtiniz.\n\n{team_list}\nSözdizimi: `!ayrıl <ekip_indeksi>`")
            return
        else:
            if msg_split[1].isnumeric() and int(msg_split[1]) < index:
                specified_index = int(msg_split[1])
            else:
                await _respond(f"Geçersiz indeks, lütfen uygun bir ekip indeksi belirtiniz.\n\n{team_list}\nSözdizimi: `!ayrıl <ekip_indeksi>`")
                return

    specified_team = teams[specified_index]

    await user.remove_roles(specified_team, reason=f"Leave command")
    await _respond(f"{specified_team.name} ekibinden ayrıldınız.")

    if len(specified_team.members) == 0:
        await context.channel.send(f"{specified_team.name} ekibinde kimse kalmadığını için siliniyor...")
        await delete_team(specified_team, context.channel)


@client.command('sil')
async def delete_team_cmd(context):
    async def _respond(msg):
        await respond(context.channel, context.message.author, msg)

    if not await is_admin(context):
        await _respond('Bu komutu çağırma yetkiniz yok!')
        return

    teams = context.message.role_mentions

    if len(teams) == 0:
        await _respond('Herhangi bir ekip etiketlenmedi! Sözdizimi: `!sil @<ekip_rolü>`')
        return

    team = teams[0]

    if not team.name.startswith(TEAM_NAME_PREFIX):
        await _respond('Etiketlenen rol bir ekip rolü değil!')
        return

    await context.channel.send(f"{team.name} ekibi siliniyor...")
    await delete_team(team, context.channel)


@client.command('benim_mensubu_olduklarım_da_dahil_bütün_ekipleri_imha_et')
async def delete_team_all_cmd(context):
    async def _respond(msg):
        await respond(context.channel, context.message.author, msg)

    if not await is_admin(context):
        await _respond('Bu komutu çağırma yetkiniz yok!')
        return

    teams = get_all_teams(context.guild)

    if len(teams) == 0:
        await context.channel.send("Herhangi bir ekip bulunamadı!")
        return

    await context.channel.send(f"{len(teams)} ekip bulundu.")

    for team in teams:
        _msg = await context.channel.send(f"{team.name} ekibi siliniyor")
        await delete_team(team, context.channel)
        await _msg.delete()

    await context.channel.send("Bütün ekipler imha edildi.")


client.run(BOT_TOKEN)
