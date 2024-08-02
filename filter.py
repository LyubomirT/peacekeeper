import discord
from discord.commands import Option
from discord.ext import commands, tasks
import re
import datetime
from db_utils import execute_db_query

def setup_filter(bot):

    execute_db_query('''CREATE TABLE IF NOT EXISTS filter
                    (guild_id INTEGER, word TEXT)''')
    
    execute_db_query('''CREATE TABLE IF NOT EXISTS block_filter
                    (guild_id INTEGER, block_type TEXT, is_blocked INTEGER)''')
    message_counts_min = {}

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
        await ctx.defer()
        execute_db_query("INSERT INTO filter VALUES (?, ?)", (ctx.guild.id, word.lower()))
        embed = discord.Embed(title="Word Added", description=f"'{word}' has been added to the filter.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="remove_filter", description="Remove a word from the filter")
    @commands.has_permissions(manage_messages=True)
    async def remove_filter(ctx, word: Option(str, "Word to remove from the filter")):
        await ctx.defer()
        execute_db_query("DELETE FROM filter WHERE guild_id = ? AND word = ?", (ctx.guild.id, word.lower()))
        embed = discord.Embed(title="Word Removed", description=f"'{word}' has been removed from the filter.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="reset_filter", description="Reset the entire filter")
    @commands.has_permissions(administrator=True)
    async def reset_filter(ctx):
        await ctx.defer()
        execute_db_query("DELETE FROM filter WHERE guild_id = ?", (ctx.guild.id,))
        execute_db_query("DELETE FROM block_filter WHERE guild_id = ?", (ctx.guild.id,))
        embed = discord.Embed(title="Filter Reset", description="The filter has been reset for this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="block", description="Block a specific type of content")
    @commands.has_permissions(manage_messages=True)
    async def block(ctx, block_type: Option(str, "Type of content to block", autocomplete=discord.utils.basic_autocomplete(block_list))):
        await ctx.defer()
        if block_type not in block_list:
            await ctx.respond("Invalid block type. Please choose from the autocomplete list.")
            return
        
        execute_db_query("INSERT OR REPLACE INTO block_filter VALUES (?, ?, ?)", (ctx.guild.id, block_type, 1))
        embed = discord.Embed(title="Content Blocked", description=f"'{block_type}' has been blocked in this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="unblock", description="Unblock a specific type of content")
    @commands.has_permissions(manage_messages=True)
    async def unblock(ctx, block_type: Option(str, "Type of content to unblock", autocomplete=discord.utils.basic_autocomplete(block_list))):
        await ctx.defer()
        if block_type not in block_list:
            await ctx.respond("Invalid block type. Please choose from the autocomplete list.")
            return
        
        execute_db_query("DELETE FROM block_filter WHERE guild_id = ? AND block_type = ?", (ctx.guild.id, block_type))
        embed = discord.Embed(title="Content Unblocked", description=f"'{block_type}' has been unblocked in this server.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @bot.slash_command(name="view_blocks", description="View the current block list")
    @commands.has_permissions(manage_messages=True)
    async def view_blocks(ctx):
        await ctx.defer()
        blocked_types = execute_db_query("SELECT block_type FROM block_filter WHERE guild_id = ? AND is_blocked = 1", (ctx.guild.id,))
        blocked_types = [row[0] for row in blocked_types]
        
        if not blocked_types:
            embed = discord.Embed(title="Block List", description="No content types are currently blocked.", color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Block List", description=", ".join(blocked_types), color=discord.Color.blue())
        
        await ctx.respond(embed=embed)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
    
        # Check for spam
        if message.guild.id not in message_counts_min:
            message_counts_min[message.guild.id] = {}
        if message.author.id not in message_counts_min[message.guild.id]:
            message_counts_min[message.guild.id][message.author.id] = 0
        message_counts_min[message.guild.id][message.author.id] += 1

        # Fetch the latest max_messages value from the database
        result = execute_db_query("SELECT max_messages FROM max_messages WHERE guild_id = ?", (message.guild.id,))
        max_messages = result[0][0] if result else 10  # Default to 10 if not set

        if message_counts_min.get(message.guild.id, {}).get(message.author.id, 0) > max_messages:
            if message_counts_min.get(message.guild.id, {}).get(message.author.id, 0) > max_messages + 10:
                await message.author.timeout_for(duration=datetime.timedelta(minutes=1), reason="Spamming")
                embed = discord.Embed(title="Spam Warning", description=f"{message.author.mention} has been timed out for spamming.", color=discord.Color.red())
                await message.channel.send(embed=embed)
                return
            embed = discord.Embed(title="Hold your horses!", description="You're sending messages too quickly. Please slow down.", color=discord.Color.red())
            await message.channel.send(message.author.mention, embed=embed)
            await message.delete()
            return

        # Block filter
        blocked_types = execute_db_query("SELECT block_type FROM block_filter WHERE guild_id = ? AND is_blocked = 1", (message.guild.id,))
        blocked_types = [row[0] for row in blocked_types]

        for block_type in blocked_types:
            if block_type in block_patterns:
                pattern = block_patterns[block_type]
                if re.search(pattern, message.content):
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, your message was removed because it contained blocked content: {block_type}")
                    return

        # Word filter
        filtered_words = execute_db_query("SELECT word FROM filter WHERE guild_id = ?", (message.guild.id,))
        filtered_words = [row[0] for row in filtered_words]

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
        await ctx.defer()
        filtered_words = execute_db_query("SELECT word FROM filter WHERE guild_id = ?", (ctx.guild.id,))
        filtered_words = [row[0] for row in filtered_words]
        
        if not filtered_words:
            embed = discord.Embed(title="Filter List", description="The filter list is currently empty.", color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Filter List", description=", ".join(filtered_words), color=discord.Color.blue())
        
        await ctx.respond(embed=embed)
    
    @tasks.loop(minutes=1)
    async def reset_spam_tracker():
        message_counts_min.clear()

    reset_spam_tracker.start()