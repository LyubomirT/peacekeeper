import discord
from discord.commands import Option
from discord.ext import commands, tasks
import datetime
from utilities import sendToModChannel, findRolesByPermission
from db_utils import execute_db_query

def setup_moderation(bot):
    execute_db_query('''CREATE TABLE IF NOT EXISTS temporary_roles
                    (guild_id INTEGER, user_id INTEGER, role_id INTEGER, expiry_time TEXT)''')
    execute_db_query('''CREATE TABLE IF NOT EXISTS max_messages
                    (guild_id INTEGER, max_messages INTEGER)''')
    @bot.slash_command(name="ban", description="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: Option(discord.Member, "The member to ban"), reason: Option(str, "Reason for the ban", required=False)):
        await ctx.defer()
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
        await ctx.defer()
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
        await ctx.defer()
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
        await ctx.defer()
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
        await ctx.defer()
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
        await ctx.defer()
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
        await ctx.defer()
        if reason is None:
            reason = "No reason provided"

        if ctx.guild.me.top_role <= role:
            await ctx.respond("I don't have permission to assign that role. My highest role must be above the role you're trying to assign.", ephemeral=True)
            return

        await member.add_roles(role, reason=reason)

        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)

        execute_db_query("INSERT INTO temporary_roles VALUES (?, ?, ?, ?)", 
                  (ctx.guild.id, member.id, role.id, expiry_time.isoformat()))

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
        expired_roles = execute_db_query("SELECT * FROM temporary_roles WHERE expiry_time <= ?", (current_time,))

        for guild_id, user_id, role_id, _ in expired_roles:
            guild = bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user_id)
                role = guild.get_role(role_id)
                if member and role:
                    await member.remove_roles(role, reason="Temporary role expired")

                    embed = discord.Embed(title="Temporary Role Expired", color=discord.Color.orange())
                    embed.add_field(name="Member", value=member.mention, inline=False)
                    embed.add_field(name="Role", value=role.mention, inline=False)

                    try:
                        log_channel_id = execute_db_query("SELECT channel_id FROM log_channels WHERE guild_id = ?", (guild_id,))
                        if log_channel_id:
                            log_channel = guild.get_channel(log_channel_id[0][0])
                            if log_channel:
                                await log_channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending log message: {e}")

        execute_db_query("DELETE FROM temporary_roles WHERE expiry_time <= ?", (current_time,))

    @check_expired_roles.before_loop
    async def before_check_expired_roles():
        await bot.wait_until_ready()
    
    @bot.slash_command(name="add_role", description="Add a role to a user")
    @commands.has_permissions(manage_roles=True)
    async def add_role(ctx, member: Option(discord.Member, "The member to add the role to"), role: Option(discord.Role, "The role to add")):
        await ctx.defer()
        await member.add_roles(role)
        embed = discord.Embed(title="Role Added", description=f"{role.mention} has been added to {member.mention}.", color=discord.Color.green())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)
    
    @bot.slash_command(name="remove_role", description="Remove a role from a user")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(ctx, member: Option(discord.Member, "The member to remove the role from"), role: Option(discord.Role, "The role to remove")):
        await ctx.defer()
        await member.remove_roles(role)
        embed = discord.Embed(title="Role Removed", description=f"{role.mention} has been removed from {member.mention}.", color=discord.Color.red())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)
    
    @bot.slash_command(name="set_mod_channel", description="Set the mod log channel")
    @commands.has_permissions(manage_guild=True)
    async def set_mod_channel(ctx, channel: Option(discord.TextChannel, "The channel to set as the mod log channel")):
        await ctx.defer()
        execute_db_query("INSERT OR REPLACE INTO mod_channels VALUES (?, ?)", (ctx.guild.id, channel.id))
        embed = discord.Embed(title="Mod Log Channel Set", description=f"{channel.mention} has been set as the mod log channel.", color=discord.Color.blue())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)
    
    @bot.slash_command(name="report", description="Report a user")
    async def report(ctx, member: discord.Member, reason: str):
        await ctx.defer()
        embed = discord.Embed(title="User Reported", description=f"{member.mention} has been reported by {ctx.author.mention}.", color=discord.Color.red())
        embed.add_field(name="Reason", value=reason)
        embed2 = discord.Embed(title="User Reported", description=f"{ctx.author.mention} has reported {member.mention}.", color=discord.Color.red())
        embed2.add_field(name="Reason", value=reason)
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        embed2.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed2, file=file)
        await sendToModChannel(ctx, embed, True)
    
    @bot.slash_command(name="set_max_messages", description="Set the maximum number of messages users can send in a minute")
    @commands.has_permissions(administrator=True)
    async def set_max_messages(ctx, max_messages: Option(int, "Maximum number of messages per minute")):
        await ctx.defer()
        if max_messages < 1:
            await ctx.respond("The maximum number of messages must be at least 1.", ephemeral=True)
            return

        # delete old max_messages value if it exists
        execute_db_query("DELETE FROM max_messages WHERE guild_id = ?", (ctx.guild.id,))
        execute_db_query("INSERT INTO max_messages VALUES (?, ?)", (ctx.guild.id, max_messages))

        embed = discord.Embed(title="Max Messages Updated", description=f"Users can now send a maximum of {max_messages} messages per minute.", color=discord.Color.blue())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)

    @bot.slash_command(name="get_max_messages", description="Get the current maximum number of messages per minute")
    @commands.has_permissions(administrator=True)
    async def get_max_messages(ctx):
        await ctx.defer()
        result = execute_db_query("SELECT max_messages FROM max_messages WHERE guild_id = ?", (ctx.guild.id,))
        max_messages = result[0][0] if result else 10  # Default to 10 if not set

        embed = discord.Embed(title="Current Max Messages", description=f"The current maximum is {max_messages} messages per minute.", color=discord.Color.blue())
        file = discord.File("PeaceKeeper.png", filename="PeaceKeeper.png")
        embed.set_thumbnail(url="attachment://PeaceKeeper.png")
        await ctx.respond(embed=embed, file=file)

    check_expired_roles.start()