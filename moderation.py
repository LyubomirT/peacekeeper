import discord
from discord.commands import Option
from discord.ext import commands
import sqlite3
import datetime

def setup_moderation(bot):
    @bot.slash_command(name="ban", description="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: Option(discord.Member, "The member to ban"), reason: Option(str, "Reason for the ban", required=False)):
        if reason is None:
            reason = "No reason provided"
        
        await member.ban(reason=reason)
        embed = discord.Embed(title="User Banned", description=f"{member.mention} has been banned from the server.", color=discord.Color.red())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        embed.add_field(name="Reason", value=reason)
        await ctx.respond(embed=embed, file=file)

    @bot.slash_command(name="kick", description="Kick a user from the server")
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, member: Option(discord.Member, "The member to kick"), reason: Option(str, "Reason for the kick", required=False)):
        if reason is None:
            reason = "No reason provided"
        
        await member.kick(reason=reason)
        embed = discord.Embed(title="User Kicked", description=f"{member.mention} has been kicked from the server.", color=discord.Color.orange())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        embed.add_field(name="Reason", value=reason)
        await ctx.respond(embed=embed, file=file)

    @bot.slash_command(name="timeout", description="Timeout a user")
    @commands.has_permissions(moderate_members=True)
    async def timeout(ctx, member: Option(discord.Member, "The member to timeout"), duration: Option(int, "Duration in minutes"), reason: Option(str, "Reason for the timeout", required=False)):
        if reason is None:
            reason = "No reason provided"
        
        await member.timeout_for(duration=datetime.timedelta(minutes=duration), reason=reason)
        embed = discord.Embed(title="User Timed Out", description=f"{member.mention} has been timed out for {duration} minutes.", color=discord.Color.orange())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        embed.add_field(name="Reason", value=reason)
        await ctx.respond(embed=embed, file=file)

    @bot.slash_command(name="clear", description="Clear a specified number of messages")
    @commands.has_permissions(manage_messages=True)
    async def clear(ctx, amount: Option(int, "Number of messages to clear")):
        await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        embed = discord.Embed(title="Chat Cleared", description=f"{amount} messages have been cleared.", color=discord.Color.blue())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, delete_after=5, file=file)