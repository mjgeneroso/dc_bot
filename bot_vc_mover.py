import os
import csv
import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from dotenv import load_dotenv

load_dotenv()

################################################

# Replace with your bot's token
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)


# Store the task loop to manage scheduling
notify_task = None


def get_random_quote():
    quotes = [
        "Life is what happens when you're busy making other plans.",
        "The only limit to our realization of tomorrow is our doubts of today.",
        "Do what you can, with what you have, where you are.",
    ]
    return random.choice(quotes)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()


@bot.tree.command(name="sync", description="Manually sync commands")
async def sync(interaction: discord.Interaction):
    print("Executing /sync command...")
    await interaction.response.defer()
    await bot.tree.sync()
    print("/sync command executed successfully.")
    await interaction.followup.send("Commands synced successfully!", ephemeral=True)


@bot.tree.command(
    name="move_all", description="Move all members from one VC to another"
)
async def move_all(
    interaction: discord.Interaction,
    from_channel: discord.VoiceChannel,
    to_channel: discord.VoiceChannel,
):
    print(f"Executing /move_all from {from_channel.name} to {to_channel.name}...")
    await interaction.response.defer()
    for member in from_channel.members:
        await member.move_to(to_channel)
    print("/move_all command executed successfully.")
    await interaction.followup.send(
        f"Moved all members from {from_channel.name} to {to_channel.name}",
        ephemeral=True,
    )


@bot.tree.command(
    name="move_all_servers",
    description="Move all members in all voice channels to a target channel",
)
async def move_all_servers(
    interaction: discord.Interaction, to_channel: discord.VoiceChannel
):
    print("Executing /move_all_servers...")
    await interaction.response.defer()
    for vc in interaction.guild.voice_channels:
        for member in vc.members:
            await member.move_to(to_channel)
    print("/move_all_servers command executed successfully.")
    await interaction.followup.send(
        f"Moved all members to {to_channel.name}", ephemeral=True
    )


@bot.tree.command(
    name="remove_all", description="Disconnect all members from a specific VC"
)
async def remove_all(
    interaction: discord.Interaction, from_channel: discord.VoiceChannel
):
    print(f"Executing /remove_all for {from_channel.name}...")
    await interaction.response.defer()
    for member in from_channel.members:
        await member.move_to(None)
    print("/remove_all command executed successfully.")
    await interaction.followup.send(
        f"Disconnected all members from {from_channel.name}", ephemeral=True
    )


@bot.tree.command(
    name="remove_all_servers",
    description="Disconnect all members from all voice channels",
)
async def remove_all_servers(interaction: discord.Interaction):
    print("Executing /remove_all_servers...")
    await interaction.response.defer()
    for vc in interaction.guild.voice_channels:
        for member in vc.members:
            await member.move_to(None)
    print("/remove_all_servers command executed successfully.")
    await interaction.followup.send(
        "Disconnected all members from all voice channels", ephemeral=True
    )


@bot.tree.command(
    name="mute_member", description="Mute a member in a text channel for a given time"
)
async def mute_member(
    interaction: discord.Interaction, member: discord.Member, hours: int
):
    print(f"Executing /mute_member for {member.name} for {hours} hours...")
    await interaction.response.defer()
    overwrite = interaction.channel.overwrites_for(member)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(member, overwrite=overwrite)
    await interaction.followup.send(
        f"Muted {member.mention} for {hours} hours.", ephemeral=True
    )
    await asyncio.sleep(hours * 3600)
    overwrite.send_messages = None
    await interaction.channel.set_permissions(member, overwrite=overwrite)
    print(
        f"/mute_member command executed successfully. {member.name} has been unmuted."
    )
    await interaction.followup.send(f"{member.mention} has been unmuted.")


@bot.tree.command(
    name="unreacted_members",
    description="List members with a specific role who have not reacted to a message",
)
async def unreacted_members(
    interaction: discord.Interaction,
    role: discord.Role,
    channel: discord.TextChannel,
    message_id: str,
):
    await interaction.response.defer()

    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        await interaction.followup.send("Message not found.", ephemeral=True)
        return

    reacted_users = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            reacted_users.add(user.id)

    role_members = {member.id: member.mention for member in role.members}
    non_reacted_members = [
        mention
        for member_id, mention in role_members.items()
        if member_id not in reacted_users
    ]

    if non_reacted_members:
        response = "Members with the role who **did not** react:\n" + "\n".join(
            non_reacted_members
        )
    else:
        response = "Everyone with the role has reacted!"

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(
    name="notify_unreacted",
    description="Notify members with a role who have not reacted to the last 24-hour message.",
)
async def notify_unreacted(
    interaction: discord.Interaction, role: discord.Role, channel: discord.TextChannel
):
    await interaction.response.defer()

    # Get messages within the last 24 hours
    now = discord.utils.utcnow()
    recent_messages = []
    async for message in channel.history(limit=20):
        if (now - message.created_at).total_seconds() <= 172800:
            recent_messages.append(message)

    if not recent_messages:
        await interaction.followup.send(
            "No messages found within the last 48 hours.", ephemeral=True
        )
        return

    role_members = {member.id: member for member in role.members}
    unreacted_messages = {}

    for message in recent_messages:
        reacted_users = set()
        for reaction in message.reactions:
            async for user in reaction.users():
                reacted_users.add(user.id)

        for member_id in role_members.keys():
            if member_id not in reacted_users:
                if member_id not in unreacted_messages:
                    unreacted_messages[member_id] = []
                unreacted_messages[member_id].append(message.jump_url)

    notified = []
    not_notified = []
    for member_id, messages in unreacted_messages.items():
        member = role_members[member_id]
        try:
            await member.send(
                f"You haven't reacted to {len(messages)} messages in {channel.mention}. Please check them: \n"
                + "\n".join(messages)
            )
            notified.append(member.mention)
        except discord.Forbidden:
            not_notified.append(member.mention)

    response = f"**Notification Summary**\n\n"
    response += f"**Total Messages Checked:** {len(recent_messages)}\n"
    response += f"**Members Notified:** {', '.join(notified) if notified else 'None'}\n"
    response += (
        f"**Could Not Notify:** {', '.join(not_notified) if not_notified else 'None'}"
    )

    await interaction.followup.send(response, ephemeral=True)


# Function to notify unreacted members
async def notify_unreacted_task(role, channel):
    await bot.wait_until_ready()

    now = discord.utils.utcnow()
    recent_messages = []
    async for message in channel.history(limit=100):
        if (now - message.created_at).total_seconds() <= 172800:
            recent_messages.append(message)

    if not recent_messages:
        print("No messages found within the last 24 hours.")
        return

    role_members = {member.id: member for member in role.members}
    unreacted_messages = {}

    for message in recent_messages:
        reacted_users = set()
        for reaction in message.reactions:
            async for user in reaction.users():
                reacted_users.add(user.id)

        for member_id in role_members.keys():
            if member_id not in reacted_users:
                if member_id not in unreacted_messages:
                    unreacted_messages[member_id] = []
                unreacted_messages[member_id].append(message.jump_url)

    notified = []
    not_notified = []
    for member_id, messages in unreacted_messages.items():
        member = role_members[member_id]
        try:
            await member.send(
                f"You haven't reacted to {len(messages)} messages in {channel.mention}. Please check them: \n"
                + "\n".join(messages)
            )
            notified.append(member.mention)
        except discord.Forbidden:
            not_notified.append(member.mention)

    response = f"**Notification Summary**\n\n"
    response += f"**Total Messages Checked:** {len(recent_messages)}\n"
    response += f"**Members Notified:** {', '.join(notified) if notified else 'None'}\n"
    response += (
        f"**Could Not Notify:** {', '.join(not_notified) if not_notified else 'None'}"
    )

    print(response)


@bot.tree.command(
    name="start_auto_notify",
    description="Start notifying unreacted members at a specific interval",
)
async def start_notify_unreacted(
    interaction: discord.Interaction,
    role: discord.Role,
    channel: discord.TextChannel,
    hours: int,
    minutes: int,
):
    global notify_task

    # Stop any existing task
    if notify_task and notify_task.is_running():
        notify_task.cancel()

    # Create a new task with the specified interval
    interval = hours * 3600 + minutes * 60

    @tasks.loop(seconds=interval)
    async def scheduled_notify():
        await notify_unreacted_task(role, channel)

    notify_task = scheduled_notify
    notify_task.start()

    await interaction.response.send_message(
        f"Started notifying unreacted members every {hours} hour(s) and {minutes} minute(s).",
        ephemeral=True,
    )


@bot.tree.command(
    name="stop_auto_notify",
    description="Stop the scheduled task for notifying unreacted members",
)
async def stop_notify_unreacted(interaction: discord.Interaction):
    global notify_task

    if notify_task and notify_task.is_running():
        notify_task.cancel()
        await interaction.response.send_message(
            "The scheduled task for notifying unreacted members has been stopped.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "No scheduled task is currently running.", ephemeral=True
        )


@bot.tree.command(name="test_quote", description="Get a random inspirational quote")
async def test_quote(interaction: discord.Interaction):
    print("Executing /test_quote...")
    await interaction.response.defer()
    quote = get_random_quote()
    print("/test_quote command executed successfully.")
    await interaction.followup.send(f'"{quote}"', ephemeral=True)


bot.run(TOKEN)
