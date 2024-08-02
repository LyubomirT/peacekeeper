import discord
from discord.commands import Option
from discord.ext import commands
import sqlite3
import re

def setup_filter(bot):
    conn = sqlite3.connect('peacekeeper.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS filter
                 (guild_id INTEGER, word TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS block_filter
                 (guild_id INTEGER, block_type TEXT, is_blocked INTEGER)''')
    conn.commit()

    block_list = ["discord_url", "telegram_url", "twitch_url", "youtube_url", "facebook_url", "twitter_url", "reddit_url", "instagram_url", "github_url",
                  "file", "image", "video", "audio", "attachment", "invite", "emoji", "custom_emoji", "role_mention", "everyone_mention", "here_mention",
                  "user_mention", "channel_mention", "url", "spoiler", "code", "inline_code", "quote", "block_quote", "bold", "italic", "underline"]

    block_patterns = {
        "discord_url": r"(?:https?://)?(?:www\.)?discord(?:app)?\.(?:com|gg)/(?:invite/)?[a-zA-Z0-9]+",
        "telegram_url": r"(?:https?://)?(?:t\.me|telegram\.me)/[a-zA-Z0-9_]+",
        "twitch_url": r"(?:https?://)?(?:www\.)?twitch\.tv/[a-zA-Z0-9_]+",
        "youtube_url": r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+",
        "facebook_url": r"(?:https?://)?(?:www\.)?facebook\.com/[a-zA-Z0-9.]+",
        "twitter_url": r"(?:https?://)?(?:www\.)?twitter\.com/[a-zA-Z0-9_]+",
        "reddit_url": r"(?:https?://)?(?:www\.)?reddit\.com/r/[a-zA-Z0-9_]+",
        "instagram_url": r"(?:https?://)?(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+",
        "github_url": r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+",
        "file": r"\S+\.[a-zA-Z0-9]+",
        "image": r"\S+\.(?:jpg|jpeg|png|gif|bmp)",
        "video": r"\S+\.(?:mp4|avi|mov|flv|wmv)",
        "audio": r"\S+\.(?:mp3|wav|ogg|flac)",
        "attachment": r"https://cdn\.discordapp\.com/attachments/\S+",
        "invite": r"(?:https?://)?(?:www\.)?discord(?:app)?\.(?:com|gg)/(?:invite/)?[a-zA-Z0-9]+",
        "emoji": r"<:[a-zA-Z0-9_]+:\d+>",
        "custom_emoji": r"<:[a-zA-Z0-9_]+:\d+>",
        "role_mention": r"<@&\d+>",
        "everyone_mention": r"@everyone",
        "here_mention": r"@here",
        "user_mention": r"<@!?\d+>",
        "channel_mention": r"<#\d+>",
        "url": r"https?://\S+",
        "spoiler": r"\|\|.+?\|\|",
        "code": r"```[\s\S]+?```",
        "inline_code": r"`[^`\n]+`",
        "quote": r"^>\s.+",
        "block_quote": r"^>>>\s[\s\S]+",
        "bold": r"\*\*[^*]+\*\*",
        "italic": r"\*[^*]+\*",
        "underline": r"__[^_]+__"
    }

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
        c.execute("DELETE FROM block_filter WHERE guild_id = ?", (ctx.guild.id,))
        conn.commit()
        embed = discord.Embed(title="Filter Reset", description="The filter has been reset for this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="block", description="Block a specific type of content")
    @commands.has_permissions(manage_messages=True)
    async def block(ctx, block_type: Option(str, "Type of content to block", autocomplete=discord.utils.basic_autocomplete(block_list))):
        if block_type not in block_list:
            await ctx.respond("Invalid block type. Please choose from the autocomplete list.")
            return
        
        c.execute("INSERT OR REPLACE INTO block_filter VALUES (?, ?, ?)", (ctx.guild.id, block_type, 1))
        conn.commit()
        embed = discord.Embed(title="Content Blocked", description=f"'{block_type}' has been blocked in this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="unblock", description="Unblock a specific type of content")
    @commands.has_permissions(manage_messages=True)
    async def unblock(ctx, block_type: Option(str, "Type of content to unblock", autocomplete=discord.utils.basic_autocomplete(block_list))):
        if block_type not in block_list:
            await ctx.respond("Invalid block type. Please choose from the autocomplete list.")
            return
        
        c.execute("DELETE FROM block_filter WHERE guild_id = ? AND block_type = ?", (ctx.guild.id, block_type))
        conn.commit()
        embed = discord.Embed(title="Content Unblocked", description=f"'{block_type}' has been unblocked in this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="view_blocks", description="View the current block list")
    @commands.has_permissions(manage_messages=True)
    async def view_blocks(ctx):
        c.execute("SELECT block_type FROM block_filter WHERE guild_id = ? AND is_blocked = 1", (ctx.guild.id,))
        blocked_types = [row[0] for row in c.fetchall()]
        
        if not blocked_types:
            embed = discord.Embed(title="Block List", description="No content types are currently blocked.", color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Block List", description=", ".join(blocked_types), color=discord.Color.blue())
        
        await ctx.respond(embed=embed)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        
        # Block filter
        c.execute("SELECT block_type FROM block_filter WHERE guild_id = ? AND is_blocked = 1", (message.guild.id,))
        blocked_types = [row[0] for row in c.fetchall()]

        for block_type in blocked_types:
            if block_type in block_patterns:
                pattern = block_patterns[block_type]
                if re.search(pattern, message.content):
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, your message was removed because it contained blocked content: {block_type}")
                    return

        # Word filter
        c.execute("SELECT word FROM filter WHERE guild_id = ?", (message.guild.id,))
        filtered_words = [row[0] for row in c.fetchall()]

        content = message.content.lower()
        for word in filtered_words:
            if word in content:
                censored_content = content.replace(word, f"||{word}||")
                await message.delete()
                censored_content_chunks = [censored_content[i:i+2000] for i in range(0, len(censored_content), 2000)]
                for chunk in censored_content_chunks:
                    await message.channel.send(f"{message.author.mention} said: {chunk}")
                return

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