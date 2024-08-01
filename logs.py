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

    log_aspects = ["kick", "ban", "join", "leave", "message_delete"]

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
    async def on_message_delete(message):
        if message.author.bot:
            return

        embed = discord.Embed(title="Message Deleted", description=f"A message by {message.author.mention} was deleted in {message.channel.mention}", color=discord.Color.red())
        embed.add_field(name="Content", value=message.content if message.content else "No text content")
        await log_event(message.guild, "message_delete", embed)