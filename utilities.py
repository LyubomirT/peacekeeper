import discord
from discord.ext import commands
import sqlite3
import datetime

def setup_utilities(bot):
    conn = sqlite3.connect('utilities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS temporary_roles
                 (guild_id INTEGER, user_id INTEGER, role_id INTEGER, expiry_time TEXT)''')
    conn.commit()

    @bot.slash_command(name="server_info", description="Get information about the server")
    async def server_info(ctx):
        guild = ctx.guild
        embed = discord.Embed(title=guild.name, description=f"ID: {guild.id}", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Created At", value=guild.created_at.strftime("%B %d, %Y"))
        await ctx.respond(embed=embed)
    
    @bot.slash_command(name="user_info", description="Get information about a user")
    @commands.has_permissions(kick_members=True)
    async def user_info(ctx, user: discord.User):
        embed = discord.Embed(title=user.name, description=f"ID: {user.id}", color=discord.Color.blurple())
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Bot", value=user.bot)
        embed.add_field(name="Created At", value=user.created_at.strftime("%B %d, %Y"))
        embed.add_field(name="Joined At", value=user.joined_at.strftime("%B %d, %Y"))
        await ctx.respond(embed=embed)
    
    @bot.slash_command(name="role_info", description="Get information about a role")
    @commands.has_permissions(kick_members=True)
    async def role_info(ctx, role: discord.Role):
        embed = discord.Embed(title=role.name, description=f"ID: {role.id}", color=role.color)
        embed.add_field(name="Color", value=role.color)
        embed.add_field(name="Members", value=len(role.members))
        embed.add_field(name="Position", value=role.position)
        embed.add_field(name="Created At", value=role.created_at.strftime("%B %d, %Y"))
        await ctx.respond(embed=embed)
    
    @bot.slash_command(name="channel_info", description="Get information about a channel")
    @commands.has_permissions(kick_members=True)
    async def channel_info(ctx, channel: discord.TextChannel):
        embed = discord.Embed(title=channel.name, description=f"ID: {channel.id}", color=discord.Color.blurple())
        embed.add_field(name="Category", value=channel.category)
        embed.add_field(name="Position", value=channel.position)
        embed.add_field(name="Created At", value=channel.created_at.strftime("%B %d, %Y"))
        await ctx.respond(embed=embed)
    
    @bot.slash_command(name="roles", description="List all roles in the server")
    async def roles(ctx):
        roles = ctx.guild.roles
        roles.reverse()
        # split the roles into chunks of 50
        chunks = [roles[i:i + 50] for i in range(0, len(roles), 50)]
        for chunk in chunks:
            embed = discord.Embed(title="Roles", description="\n".join([role.mention for role in chunk]), color=discord.Color.blurple())
            await ctx.respond(embed=embed)
        
    @bot.slash_command(name="user_roles", description="List all roles of a user")
    async def user_roles(ctx, user: discord.Member):
        roles = user.roles
        roles.reverse()
        # split the roles into chunks of 50
        chunks = [roles[i:i + 50] for i in range(0, len(roles), 50)]
        for chunk in chunks:
            embed = discord.Embed(title=f"{user.name}'s Roles", description="\n".join([role.mention for role in chunk]), color=discord.Color.blurple())
            await ctx.respond(embed=embed)
        
    @bot.slash_command(name="create_embed", description="Create a custom embed")
    @commands.has_permissions(manage_messages=True)
    async def create_embed(ctx, title: str, description: str, color: discord.Color, thumbnail: str = None, image: str = None, footer: str = None, footer_icon: str = None, timestamp: bool = False, author: bool = True):
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            try:
                embed.set_thumbnail(url=thumbnail)
            except:
                pass
        if image:
            try:
                embed.set_image(url=image)
            except:
                pass
        if footer:
            if footer_icon:
                try:
                    embed.set_footer(text=footer, icon_url=footer_icon)
                except:
                    pass
            else:
                embed.set_footer(text=footer)
        if timestamp:
            embed.timestamp = datetime.datetime.utcnow()
        if author:
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
        
        await ctx.respond(embed=embed)

    @bot.slash_command(name="id_to_user", description="Convert a user ID to a user")
    @commands.has_permissions(manage_messages=True)
    async def id_to_user(ctx, user_id: int):
        user = ctx.guild.get_member(user_id)
        if user is None:
            user = await bot.fetch_user(user_id)
        if user is None:
            await ctx.respond("User not found")
        else:
            await ctx.respond(user.mention)
    
    @bot.slash_command(name="user_to_id", description="Convert a user to a user ID")
    @commands.has_permissions(manage_messages=True)
    async def user_to_id(ctx, user: discord.User):
        await ctx.respond(user.id)