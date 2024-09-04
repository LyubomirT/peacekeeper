import discord
from discord.ext import commands
from discord import Option

def setup_help(bot):
    class HelpView(discord.ui.View):
        def __init__(self, embeds):
            super().__init__(timeout=60)
            self.embeds = embeds
            self.index = 0

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
        async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.index -= 1
            await self.update_message(interaction)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
        async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.index += 1
            await self.update_message(interaction)

        @discord.ui.select(
            placeholder="Jump to section",
            options=[
                discord.SelectOption(label="Overview", value="0"),
                discord.SelectOption(label="Moderation", value="1"),
                discord.SelectOption(label="Filters", value="2"),
                discord.SelectOption(label="Logs", value="3"),
                discord.SelectOption(label="User Management", value="4"),
                discord.SelectOption(label="Utilities", value="5"),
                discord.SelectOption(label="Automod", value="6")
            ]
        )
        async def select_section(self, select: discord.ui.Select, interaction: discord.Interaction):
            self.index = int(select.values[0])
            await self.update_message(interaction)

        async def update_message(self, interaction: discord.Interaction):
            embed = self.embeds[self.index]
            self.previous.disabled = (self.index == 0)
            self.next.disabled = (self.index == len(self.embeds) - 1)
            await interaction.response.edit_message(embed=embed, view=self)

    def create_help_embeds():
        embeds = []

        # Main help embed
        embed = discord.Embed(title="PeaceKeeper Help", description="Welcome to PeaceKeeper! Here's an overview of available commands:", color=discord.Color.blue())
        embed.add_field(name="Moderation", value="`/ban`, `/kick`, `/timeout`, `/warn`, `/clear`", inline=False)
        embed.add_field(name="Filters", value="`/add_filter`, `/remove_filter`, `/view_filter`, `/block`, `/unblock`", inline=False)
        embed.add_field(name="Logs", value="`/set_log_channel`, `/enable_log`, `/disable_log`, `/view_log_settings`", inline=False)
        embed.add_field(name="User Management", value="`/add_role`, `/remove_role`, `/temprole`, `/notes`", inline=False)
        embed.add_field(name="Utilities", value="`/server_info`, `/user_info`, `/role_info`, `/channel_info`", inline=False)
        embed.add_field(name="Automod", value="`/automod set`, `/automod view`", inline=False)
        embeds.append(embed)

        # Moderation commands
        embed = discord.Embed(title="Moderation Commands", color=discord.Color.red())
        embed.add_field(name="/ban <member> [reason]", value="Ban a member from the server", inline=False)
        embed.add_field(name="/kick <member> [reason]", value="Kick a member from the server", inline=False)
        embed.add_field(name="/timeout <member> <duration> [reason]", value="Timeout a member for a specified duration", inline=False)
        embed.add_field(name="/warn <member> <reason>", value="Warn a member", inline=False)
        embed.add_field(name="/clear <amount>", value="Clear a specified number of messages", inline=False)
        embeds.append(embed)

        # Filter commands
        embed = discord.Embed(title="Filter Commands", color=discord.Color.green())
        embed.add_field(name="/add_filter <word>", value="Add a word to the filter", inline=False)
        embed.add_field(name="/remove_filter <word>", value="Remove a word from the filter", inline=False)
        embed.add_field(name="/view_filter", value="View the current filter list", inline=False)
        embed.add_field(name="/block <block_type>", value="Block a specific type of content", inline=False)
        embed.add_field(name="/unblock <block_type>", value="Unblock a specific type of content", inline=False)
        embeds.append(embed)

        # Log commands
        embed = discord.Embed(title="Log Commands", color=discord.Color.blue())
        embed.add_field(name="/set_log_channel <channel>", value="Set the log channel for the server", inline=False)
        embed.add_field(name="/enable_log <aspect>", value="Enable a log aspect", inline=False)
        embed.add_field(name="/disable_log <aspect>", value="Disable a log aspect", inline=False)
        embed.add_field(name="/view_log_settings", value="View the current log settings", inline=False)
        embeds.append(embed)

        # User management commands
        embed = discord.Embed(title="User Management Commands", color=discord.Color.gold())
        embed.add_field(name="/add_role <member> <role>", value="Add a role to a member", inline=False)
        embed.add_field(name="/remove_role <member> <role>", value="Remove a role from a member", inline=False)
        embed.add_field(name="/temprole <member> <role> <duration> [reason]", value="Assign a temporary role to a member", inline=False)
        embed.add_field(name="/add_note <user> <note>", value="Add a note to a user", inline=False)
        embed.add_field(name="/view_notes <user>", value="View notes for a user", inline=False)
        embed.add_field(name="/edit_note <user> <note_index> <new_note>", value="Edit a note for a user", inline=False)
        embed.add_field(name="/delete_note <user> <note_index>", value="Delete a note for a user", inline=False)
        embeds.append(embed)

        # Utility commands
        embed = discord.Embed(title="Utility Commands", color=discord.Color.purple())
        embed.add_field(name="/server_info", value="Get information about the server", inline=False)
        embed.add_field(name="/user_info <user>", value="Get information about a user", inline=False)
        embed.add_field(name="/role_info <role>", value="Get information about a role", inline=False)
        embed.add_field(name="/channel_info <channel>", value="Get information about a channel", inline=False)
        embed.add_field(name="/roles", value="List all roles in the server", inline=False)
        embed.add_field(name="/user_roles <user>", value="List all roles of a user", inline=False)
        embeds.append(embed)

        # Automod commands
        embed = discord.Embed(title="Automod Commands", color=discord.Color.orange())
        embed.add_field(name="/automod set <setting> <value>", value="Configure an automod setting", inline=False)
        embed.add_field(name="/automod view", value="View current automod settings", inline=False)
        embed.add_field(name="Available Settings", value="caps_percent, repeated_chars, spam_messages, mention_limit, emoji_limit, max_lines, max_words, zalgo_text", inline=False)
        embed.add_field(name="Setting Values", value="Use 'off', 'low', 'medium', 'high', or a specific number", inline=False)
        embeds.append(embed)

        return embeds

    @bot.slash_command(name="help", description="Get help with PeaceKeeper commands")
    async def help(ctx):
        await ctx.defer()
        # Provide general help with pagination
        embeds = create_help_embeds()
        view = HelpView(embeds)
        await ctx.respond(embed=embeds[0], view=view)

    @bot.slash_command(name="setup_guide", description="Get a guide on how to set up PeaceKeeper")
    async def setup_guide(ctx):
        await ctx.defer()
        embed = discord.Embed(title="PeaceKeeper Setup Guide", color=discord.Color.blue())
        embed.add_field(name="Step 1: Set up logging", value="Use `/set_log_channel` to set up a logging channel", inline=False)
        embed.add_field(name="Step 2: Configure logs", value="Use `/enable_log` to enable specific log aspects", inline=False)
        embed.add_field(name="Step 3: Set up filters", value="Use `/add_filter` to add words to the filter", inline=False)
        embed.add_field(name="Step 4: Configure auto-mod", value="Use `/block` to block specific types of content", inline=False)
        embed.add_field(name="Step 5: Set up roles", value="Use `/add_role` and `/remove_role` to manage roles", inline=False)
        embed.add_field(name="Step 6: Configure automod", value="Use `/automod set` to configure automod settings", inline=False)
        embed.add_field(name="Step 7: Familiarize with commands", value="Use `/help` to see all available commands", inline=False)
        embed.set_footer(text="For more detailed help, use /help <command> for specific commands.")
        await ctx.respond(embed=embed)

    @bot.slash_command(name="normal_user_guide", description="Get a guide for normal server members")
    async def normal_user_guide(ctx):
        await ctx.defer()
        embed = discord.Embed(title="PeaceKeeper User Guide", color=discord.Color.green())
        embed.add_field(name="Server Rules", value="Make sure to read and follow the server rules to avoid warnings or bans.", inline=False)
        embed.add_field(name="Reporting Issues", value="If you see any rule violations, report them to the moderators.", inline=False)
        embed.add_field(name="Useful Commands", value="You can use `/server_info` to get information about the server.", inline=False)
        embed.add_field(name="Roles", value="You can view your roles using `/user_roles`.", inline=False)
        embed.add_field(name="Be Respectful", value="Always be respectful to other members and follow moderator instructions.", inline=False)
        embed.add_field(name="Automod", value="Be aware of automod settings to avoid accidental violations.", inline=False)
        embed.set_footer(text="If you have any questions, don't hesitate to ask a moderator!")
        await ctx.respond(embed=embed)