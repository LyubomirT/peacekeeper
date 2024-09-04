import discord
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands, tasks
import re
import datetime
from db_utils import execute_db_query

def setup_filter(bot):

    execute_db_query('''CREATE TABLE IF NOT EXISTS filter
                    (guild_id INTEGER, word TEXT)''')
    
    execute_db_query('''CREATE TABLE IF NOT EXISTS block_filter
                    (guild_id INTEGER, block_type TEXT, is_blocked INTEGER)''')

    execute_db_query('''CREATE TABLE IF NOT EXISTS automod_settings
                    (guild_id INTEGER, setting TEXT, value INTEGER)''')

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

    automod_settings = {
        "caps_percent": {"name": "Excessive Caps", "description": "Percentage of uppercase characters allowed"},
        "repeated_chars": {"name": "Repeated Characters", "description": "Maximum number of repeated characters allowed"},
        "spam_messages": {"name": "Spam Messages", "description": "Maximum number of messages allowed per minute"},
        "mention_limit": {"name": "Mention Limit", "description": "Maximum number of mentions allowed per message"},
        "emoji_limit": {"name": "Emoji Limit", "description": "Maximum number of emojis allowed per message"},
        "max_lines": {"name": "Maximum Lines", "description": "Maximum number of lines allowed per message"},
        "max_words": {"name": "Maximum Words", "description": "Maximum number of words allowed per message"},
        "zalgo_text": {"name": "Zalgo Text", "description": "Whether to filter out Zalgo text (0 for off, 1 for on)"}
    }

    def get_automod_value(value_str):
        if value_str.lower() == "off":
            return 0
        elif value_str.lower() == "low":
            return 25
        elif value_str.lower() == "medium":
            return 50
        elif value_str.lower() == "high":
            return 75
        elif value_str.isdigit():
            return int(value_str)
        else:
            return None

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

    automod = SlashCommandGroup("automod", "Automod configuration commands")

    @automod.command(name="set", description="Configure an automod setting")
    @commands.has_permissions(administrator=True)
    async def set_automod(ctx, 
                          setting: Option(str, "Automod setting to configure", autocomplete=discord.utils.basic_autocomplete(automod_settings.keys())),
                          value: Option(str, "Value for the setting (off/low/medium/high or a number)")):
        await ctx.defer()
        if setting not in automod_settings:
            await ctx.respond("Invalid automod setting. Please choose from the autocomplete list.")
            return
        
        numeric_value = get_automod_value(value)
        if numeric_value is None:
            await ctx.respond("Invalid value. Please use 'off', 'low', 'medium', 'high', or a number.")
            return
        
        execute_db_query("INSERT OR REPLACE INTO automod_settings VALUES (?, ?, ?)", (ctx.guild.id, setting, numeric_value))
        embed = discord.Embed(title="Automod Setting Updated", description=f"'{automod_settings[setting]['name']}' has been set to {value}.", color=discord.Color.green())
        await ctx.respond(embed=embed)

    @automod.command(name="view", description="View current automod settings")
    @commands.has_permissions(administrator=True)
    async def view_automod(ctx):
        await ctx.defer()
        settings = execute_db_query("SELECT setting, value FROM automod_settings WHERE guild_id = ?", (ctx.guild.id,))
        
        embed = discord.Embed(title="Automod Settings", color=discord.Color.blue())
        for setting, value in settings:
            if setting in automod_settings:
                embed.add_field(name=automod_settings[setting]['name'], value=f"{'On' if value > 0 else 'Off'} (Value: {value})", inline=False)
        
        if not settings:
            embed.description = "No automod settings configured."
        
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

        automod_settings = execute_db_query("SELECT setting, value FROM automod_settings WHERE guild_id = ?", (message.guild.id,))
        automod_settings = dict(automod_settings)

        violations = []

        # Check caps percentage
        if "caps_percent" in automod_settings and automod_settings["caps_percent"] > 0:
            caps_count = sum(1 for c in message.content if c.isupper())
            if len(message.content) > 0 and (caps_count / len(message.content)) * 100 > automod_settings["caps_percent"]:
                violations.append("excessive caps")

        # Check repeated characters
        if "repeated_chars" in automod_settings and automod_settings["repeated_chars"] > 0:
            if any(char * automod_settings["repeated_chars"] in message.content for char in set(message.content)):
                violations.append("repeated characters")

        # Check mention limit
        if "mention_limit" in automod_settings and automod_settings["mention_limit"] > 0:
            mention_count = len(message.mentions) + len(message.role_mentions)
            if mention_count > automod_settings["mention_limit"]:
                violations.append("excessive mentions")

        # Check emoji limit
        if "emoji_limit" in automod_settings and automod_settings["emoji_limit"] > 0:
            emoji_count = len(re.findall(r'<:[a-zA-Z0-9_]+:\d+>', message.content))
            if emoji_count > automod_settings["emoji_limit"]:
                violations.append("excessive emojis")

        # Check max lines
        if "max_lines" in automod_settings and automod_settings["max_lines"] > 0:
            if len(message.content.split('\n')) > automod_settings["max_lines"]:
                violations.append("too many lines")

        # Check max words
        if "max_words" in automod_settings and automod_settings["max_words"] > 0:
            if len(message.content.split()) > automod_settings["max_words"]:
                violations.append("too many words")

        # Check Zalgo text
        if "zalgo_text" in automod_settings and automod_settings["zalgo_text"] > 0:
            if re.search(r'[\u0300-\u036f\u0489]', message.content):
                violations.append("Zalgo text")

        # Take action if there are violations
        if violations:
            await message.delete()
            violation_text = ", ".join(violations)
            warn_embed = discord.Embed(title="Automod Warning", description=f"{message.author.mention}, your message was removed for the following reason(s): {violation_text}", color=discord.Color.orange())
            await message.channel.send(embed=warn_embed)

            # Timeout the user
            try:
                await message.author.timeout_for(duration=datetime.timedelta(minutes=5), reason=f"Automod violation: {violation_text}")
                timeout_embed = discord.Embed(title="User Timed Out", description=f"{message.author.mention} has been timed out for 5 minutes due to automod violations.", color=discord.Color.red())
                await message.channel.send(embed=timeout_embed)
            except discord.errors.Forbidden:
                print(f"Unable to timeout {message.author} (ID: {message.author.id}) due to lack of permissions.")

            # Log the violation
            log_channel_id = execute_db_query("SELECT channel_id FROM log_channels WHERE guild_id = ?", (message.guild.id,))
            if log_channel_id:
                log_channel = message.guild.get_channel(log_channel_id[0][0])
                if log_channel:
                    log_embed = discord.Embed(title="Automod Violation", color=discord.Color.orange())
                    log_embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
                    log_embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                    log_embed.add_field(name="Violations", value=violation_text, inline=False)
                    log_embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
                    await log_channel.send(embed=log_embed)

    @tasks.loop(minutes=1)
    async def reset_spam_tracker():
        message_counts_min.clear()

    reset_spam_tracker.start()

    bot.add_application_command(automod)