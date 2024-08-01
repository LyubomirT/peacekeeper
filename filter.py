import discord
from discord.commands import Option
from discord.ext import commands
import sqlite3

def setup_filter(bot):
    conn = sqlite3.connect('peacekeeper.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS filter
                 (guild_id INTEGER, word TEXT)''')
    conn.commit()

    @bot.slash_command(name="add_filter", description="Add a word to the filter")
    @commands.has_permissions(manage_messages=True)
    async def add_filter(ctx, word: Option(str, "Word to add to the filter")):
        c.execute("INSERT INTO filter VALUES (?, ?)", (ctx.guild.id, word.lower()))
        conn.commit()
        embed = discord.Embed(title="Word Added", description=f"'{word}' has been added to the filter.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="remove_filter", description="Remove a word from the filter")
    @commands.has_permissions(manage_messages=True)
    async def remove_filter(ctx, word: Option(str, "Word to remove from the filter")):
        c.execute("DELETE FROM filter WHERE guild_id = ? AND word = ?", (ctx.guild.id, word.lower()))
        conn.commit()
        embed = discord.Embed(title="Word Removed", description=f"'{word}' has been removed from the filter.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="reset_filter", description="Reset the entire filter")
    @commands.has_permissions(administrator=True)
    async def reset_filter(ctx):
        c.execute("DELETE FROM filter WHERE guild_id = ?", (ctx.guild.id,))
        conn.commit()
        embed = discord.Embed(title="Filter Reset", description="The filter has been reset for this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        c.execute("SELECT word FROM filter WHERE guild_id = ?", (message.guild.id,))
        filtered_words = [row[0] for row in c.fetchall()]

        content = message.content.lower()
        for word in filtered_words:
            if word in content:
                censored_content = content.replace(word, f"||{word}||")
                await message.delete()
                await message.channel.send(f"{message.author.mention} said: {censored_content}")
                break

    @bot.slash_command(name="view_filter", description="View the current filter list")
    @commands.has_permissions(manage_messages=True)
    async def view_filter(ctx):
        c.execute("SELECT word FROM filter WHERE guild_id = ?", (ctx.guild.id,))
        filtered_words = [row[0] for row in c.fetchall()]
        
        if not filtered_words:
            embed = discord.Embed(title="Filter List", description="The filter list is currently empty.", color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Filter List", description=", ".join(filtered_words), color=discord.Color.blue())
        
        await ctx.respond(embed=embed)