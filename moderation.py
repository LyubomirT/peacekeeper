import discord
from discord.commands import Option
from discord.ext import commands, tasks
import sqlite3
import datetime

def setup_moderation(bot):
    conn = sqlite3.connect('peacekeeper.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS temporary_roles
                 (guild_id INTEGER, user_id INTEGER, role_id INTEGER, expiry_time TEXT)''')
    conn.commit()


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
    
    @bot.slash_command(name="unban", description="Unban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, member: Option(discord.User, "The user to unban"), reason: Option(str, "Reason for the unban", required=False)):
        if reason is None:
            reason = "No reason provided"
        
        await ctx.guild.unban(member, reason=reason)
        embed = discord.Embed(title="User Unbanned", description=f"{member.mention} has been unbanned from the server.", color=discord.Color.green())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        embed.add_field(name="Reason", value=reason)
        await ctx.respond(embed=embed, file=file)

    @bot.slash_command(name="untimeout", description="Remove a timeout from a user")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(ctx, member: Option(discord.Member, "The member to untimeout"), reason: Option(str, "Reason for the untimeout", required=False)):
        if reason is None:
            reason = "No reason provided"
        
        await member.remove_timeout(reason=reason)
        embed = discord.Embed(title="User Untimed Out", description=f"{member.mention} has been untimed out.", color=discord.Color.green())
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

    @bot.slash_command(name="temprole", description="Assign a temporary role to a user")
    @commands.has_permissions(manage_roles=True)
    async def temprole(ctx, 
                       member: Option(discord.Member, "The member to assign the role to"),
                       role: Option(discord.Role, "The role to assign"),
                       duration: Option(int, "Duration in minutes"),
                       reason: Option(str, "Reason for assigning the temporary role", required=False)):
        if reason is None:
            reason = "No reason provided"

        # Check if the bot's role is higher than the role to be assigned
        if ctx.guild.me.top_role <= role:
            await ctx.respond("I don't have permission to assign that role. My highest role must be above the role you're trying to assign.", ephemeral=True)
            return

        # Assign the role
        await member.add_roles(role, reason=reason)

        # Calculate expiry time
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)

        # Store in database
        c.execute("INSERT INTO temporary_roles VALUES (?, ?, ?, ?)", 
                  (ctx.guild.id, member.id, role.id, expiry_time.isoformat()))
        conn.commit()

        embed = discord.Embed(title="Temporary Role Assigned", color=discord.Color.blue())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Role", value=role.mention, inline=False)
        embed.add_field(name="Duration", value=f"{duration} minutes", inline=False)
        embed.add_field(name="Expiry Time", value=expiry_time.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")

        await ctx.respond(embed=embed, file=file)

    @tasks.loop(minutes=1)
    async def check_expired_roles():
        current_time = datetime.datetime.now().isoformat()
        c.execute("SELECT * FROM temporary_roles WHERE expiry_time <= ?", (current_time,))
        expired_roles = c.fetchall()

        for guild_id, user_id, role_id, _ in expired_roles:
            guild = bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user_id)
                role = guild.get_role(role_id)
                if member and role:
                    await member.remove_roles(role, reason="Temporary role expired")

                    # Create and send an embed to the log channel
                    embed = discord.Embed(title="Temporary Role Expired", color=discord.Color.orange())
                    embed.add_field(name="Member", value=member.mention, inline=False)
                    embed.add_field(name="Role", value=role.mention, inline=False)

                    # Attempt to send the embed to the log channel
                    try:
                        c.execute("SELECT channel_id FROM log_channels WHERE guild_id = ?", (guild_id,))
                        log_channel_id = c.fetchone()
                        if log_channel_id:
                            log_channel = guild.get_channel(log_channel_id[0])
                            if log_channel:
                                await log_channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending log message: {e}")

        # Remove expired entries from the database
        c.execute("DELETE FROM temporary_roles WHERE expiry_time <= ?", (current_time,))
        conn.commit()

    @check_expired_roles.before_loop
    async def before_check_expired_roles():
        await bot.wait_until_ready()
    
    @bot.slash_command(name="add_role", description="Add a role to a user")
    @commands.has_permissions(manage_roles=True)
    async def add_role(ctx, member: Option(discord.Member, "The member to add the role to"), role: Option(discord.Role, "The role to add")):
        await member.add_roles(role)
        embed = discord.Embed(title="Role Added", description=f"{role.mention} has been added to {member.mention}.", color=discord.Color.green())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)
    
    @bot.slash_command(name="remove_role", description="Remove a role from a user")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(ctx, member: Option(discord.Member, "The member to remove the role from"), role: Option(discord.Role, "The role to remove")):
        await member.remove_roles(role)
        embed = discord.Embed(title="Role Removed", description=f"{role.mention} has been removed from {member.mention}.", color=discord.Color.red())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)

    check_expired_roles.start()