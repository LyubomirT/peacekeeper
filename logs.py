import discord
from discord.commands import Option
from discord.ext import commands
import sqlite3

def setup_logs(bot):
    conn = sqlite3.connect('peacekeeper.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS log_channels
                 (guild_id INTEGER, channel_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS log_settings
                 (guild_id INTEGER, aspect TEXT, enabled INTEGER)''')
    conn.commit()

    log_aspects = [
        "kick", "ban", "unban", "join", "leave", "message_delete", "message_edit",
        "channel_create", "channel_delete", "channel_update", "role_create",
        "role_delete", "role_update", "nickname_change", "user_update",
        "voice_state_update", "invite_create", "invite_delete", "member_timeout"
    ]

    @bot.slash_command(name="set_log_channel", description="Set the log channel for the server")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(ctx, channel: Option(discord.TextChannel, "The channel to set as log channel")):
        c.execute("INSERT OR REPLACE INTO log_channels VALUES (?, ?)", (ctx.guild.id, channel.id))
        conn.commit()
        embed = discord.Embed(title="Log Channel Set", description=f"Log channel has been set to {channel.mention}", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="enable_log", description="Enable a log aspect")
    @commands.has_permissions(administrator=True)
    async def enable_log(ctx, aspect: Option(str, "The log aspect to enable", autocomplete=discord.utils.basic_autocomplete(log_aspects))):
        if aspect not in log_aspects:
            embed = discord.Embed(title="Invalid Aspect", description="Please choose a valid log aspect.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        c.execute("INSERT OR REPLACE INTO log_settings VALUES (?, ?, ?)", (ctx.guild.id, aspect, 1))
        conn.commit()
        embed = discord.Embed(title="Log Aspect Enabled", description=f"The {aspect} log aspect has been enabled.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="disable_log", description="Disable a log aspect")
    @commands.has_permissions(administrator=True)
    async def disable_log(ctx, aspect: Option(str, "The log aspect to disable", autocomplete=discord.utils.basic_autocomplete(log_aspects))):
        if aspect not in log_aspects:
            embed = discord.Embed(title="Invalid Aspect", description="Please choose a valid log aspect.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        c.execute("INSERT OR REPLACE INTO log_settings VALUES (?, ?, ?)", (ctx.guild.id, aspect, 0))
        conn.commit()
        embed = discord.Embed(title="Log Aspect Disabled", description=f"The {aspect} log aspect has been disabled.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    async def log_event(guild, aspect, embed):
        c.execute("SELECT channel_id FROM log_channels WHERE guild_id = ?", (guild.id,))
        result = c.fetchone()
        if result:
            channel_id = result[0]
            c.execute("SELECT enabled FROM log_settings WHERE guild_id = ? AND aspect = ?", (guild.id, aspect))
            enabled = c.fetchone()
            if enabled and enabled[0]:
                channel = guild.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

    @bot.event
    async def on_member_join(member):
        embed = discord.Embed(title="Member Joined", description=f"{member.mention} has joined the server.", color=discord.Color.green())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await log_event(member.guild, "join", embed)

    @bot.event
    async def on_member_remove(member):
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                embed = discord.Embed(title="Member Kicked", description=f"{member.mention} was kicked from the server.", color=discord.Color.orange())
                embed.add_field(name="Reason", value=entry.reason if entry.reason else "No reason provided")
                await log_event(member.guild, "kick", embed)
                return

        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == member.id:
                embed = discord.Embed(title="Member Banned", description=f"{member.mention} was banned from the server.", color=discord.Color.red())
                embed.add_field(name="Reason", value=entry.reason if entry.reason else "No reason provided")
                await log_event(member.guild, "ban", embed)
                return

        embed = discord.Embed(title="Member Left", description=f"{member.mention} has left the server.", color=discord.Color.orange())
        await log_event(member.guild, "leave", embed)

    @bot.event
    async def on_member_unban(guild, user):
        embed = discord.Embed(title="Member Unbanned", description=f"{user.mention} was unbanned from the server.", color=discord.Color.green())
        await log_event(guild, "unban", embed)

    @bot.event
    async def on_message_delete(message):
        if message.author.bot:
            return

        embed = discord.Embed(title="Message Deleted", description=f"A message by {message.author.mention} was deleted in {message.channel.mention}", color=discord.Color.red())
        embed.add_field(name="Content", value=message.content if message.content else "No text content")
        await log_event(message.guild, "message_delete", embed)

    @bot.event
    async def on_message_edit(before, after):
        if before.author.bot:
            return

        if before.content != after.content:
            embed = discord.Embed(title="Message Edited", description=f"A message by {before.author.mention} was edited in {before.channel.mention}", color=discord.Color.blue())
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            await log_event(before.guild, "message_edit", embed)

    @bot.event
    async def on_guild_channel_create(channel):
        embed = discord.Embed(title="Channel Created", description=f"A new channel {channel.mention} was created.", color=discord.Color.green())
        await log_event(channel.guild, "channel_create", embed)

    @bot.event
    async def on_guild_channel_delete(channel):
        embed = discord.Embed(title="Channel Deleted", description=f"The channel '{channel.name}' was deleted.", color=discord.Color.red())
        await log_event(channel.guild, "channel_delete", embed)

    @bot.event
    async def on_guild_channel_update(before, after):
        if before.name != after.name:
            embed = discord.Embed(title="Channel Updated", description=f"The channel {after.mention} was renamed from '{before.name}' to '{after.name}'.", color=discord.Color.blue())
            await log_event(after.guild, "channel_update", embed)

    @bot.event
    async def on_guild_role_create(role):
        embed = discord.Embed(title="Role Created", description=f"A new role '{role.name}' was created.", color=discord.Color.green())
        await log_event(role.guild, "role_create", embed)

    @bot.event
    async def on_guild_role_delete(role):
        embed = discord.Embed(title="Role Deleted", description=f"The role '{role.name}' was deleted.", color=discord.Color.red())
        await log_event(role.guild, "role_delete", embed)

    @bot.event
    async def on_guild_role_update(before, after):
        if before.name != after.name:
            embed = discord.Embed(title="Role Updated", description=f"The role '{before.name}' was renamed to '{after.name}'.", color=discord.Color.blue())
            await log_event(after.guild, "role_update", embed)

    @bot.event
    async def on_member_update(before, after):
        if before.nick != after.nick:
            embed = discord.Embed(title="Nickname Changed", description=f"{before.mention}'s nickname was changed.", color=discord.Color.blue())
            embed.add_field(name="Before", value=before.nick if before.nick else "No nickname", inline=False)
            embed.add_field(name="After", value=after.nick if after.nick else "No nickname", inline=False)
            await log_event(after.guild, "nickname_change", embed)

    @bot.event
    async def on_user_update(before, after):
        if before.name != after.name or before.discriminator != after.discriminator:
            embed = discord.Embed(title="User Updated", description=f"User {before.mention} updated their profile.", color=discord.Color.blue())
            embed.add_field(name="Before", value=f"{before.name}#{before.discriminator}", inline=False)
            embed.add_field(name="After", value=f"{after.name}#{after.discriminator}", inline=False)
            for guild in bot.guilds:
                if guild.get_member(after.id):
                    await log_event(guild, "user_update", embed)

        if before.is_timed_out() != after.is_timed_out():
            if after.is_timed_out():
                embed = discord.Embed(title="Member Timed Out", description=f"{after.mention} was timed out", color=discord.Color.orange())
                embed.add_field(name="Until", value=after.timed_out_until.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                embed = discord.Embed(title="Member Timeout Removed", description=f"{after.mention}'s timeout was removed", color=discord.Color.green())
            await log_event(after.guild, "member_timeout", embed)

    @bot.event
    async def on_voice_state_update(member, before, after):
        if before.channel != after.channel:
            if after.channel:
                embed = discord.Embed(title="Member Joined Voice Channel", description=f"{member.mention} joined {after.channel.name}", color=discord.Color.green())
            else:
                embed = discord.Embed(title="Member Left Voice Channel", description=f"{member.mention} left {before.channel.name}", color=discord.Color.orange())
            await log_event(member.guild, "voice_state_update", embed)

    @bot.event
    async def on_invite_create(invite):
        embed = discord.Embed(title="Invite Created", description=f"A new invite was created by {invite.inviter.mention}", color=discord.Color.green())
        embed.add_field(name="Code", value=invite.code)
        embed.add_field(name="Max Uses", value=invite.max_uses if invite.max_uses else "Unlimited")
        embed.add_field(name="Expires", value=invite.expires_at.strftime("%Y-%m-%d %H:%M:%S") if invite.expires_at else "Never")
        await log_event(invite.guild, "invite_create", embed)

    @bot.event
    async def on_invite_delete(invite):
        embed = discord.Embed(title="Invite Deleted", description=f"An invite was deleted", color=discord.Color.red())
        embed.add_field(name="Code", value=invite.code)
        await log_event(invite.guild, "invite_delete", embed)