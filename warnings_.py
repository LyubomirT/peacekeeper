import discord
from discord.commands import Option
from discord.ext import commands
from datetime import datetime
from db_utils import execute_db_query

def setup_warnings(bot):
    execute_db_query('''CREATE TABLE IF NOT EXISTS warnings
                 (guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, reason TEXT, timestamp TEXT, message_id INTEGER)''')

    class WarningPaginator(discord.ui.View):
        def __init__(self, warnings, user):
            super().__init__(timeout=60)
            self.warnings = warnings
            self.user = user
            self.page = 0
            self.add_item(self.previous_button())
            self.create_next_button()

        def previous_button(self):
            return discord.ui.Button(style=discord.ButtonStyle.gray, label="◀", custom_id="previous", disabled=True)

        def create_next_button(self):
            if len(self.warnings) > 3:
                next_button = discord.ui.Button(style=discord.ButtonStyle.gray, label="▶", custom_id="next")
                self.add_item(next_button)
            else:
                next_button = discord.ui.Button(style=discord.ButtonStyle.gray, label="▶", custom_id="next", disabled=True)
                self.add_item(next_button)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.data["custom_id"] == "previous":
                if self.page > 0:
                    self.page -= 1
                    await self.update_message(interaction)
                return True
            elif interaction.data["custom_id"] == "next":
                if self.page < (len(self.warnings) - 1) // 3:
                    self.page += 1
                    await self.update_message(interaction)
                return True
            return False

        async def update_message(self, interaction: discord.Interaction):
            embed = create_warnings_embed(self.warnings, self.user, self.page)
            self.children[0].disabled = (self.page == 0)  # Previous button
            self.children[1].disabled = (self.page >= (len(self.warnings) - 1) // 3)  # Next button
            
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except discord.errors.InteractionResponded:
                await interaction.message.edit(embed=embed, view=self)

    def create_warnings_embed(warnings, user, page):
        start = page * 3
        end = start + 3
        current_warnings = warnings[start:end]

        embed = discord.Embed(title=f"Warnings for {user.name}", color=discord.Color.orange())
        for i, warning in enumerate(current_warnings, start=start+1):
            moderator = bot.get_user(warning[2])
            moderator_name = moderator.name if moderator else "Unknown Moderator"
            embed.add_field(name=f"Warning {i}", value=f"Reason: {warning[3]}\nModerator: {moderator_name}\nDate: {warning[4]}", inline=False)

        embed.set_footer(text=f"Page {page + 1}/{(len(warnings) - 1) // 3 + 1}")
        return embed

    @bot.slash_command(name="warn", description="Warn a user")
    @commands.has_permissions(kick_members=True)
    async def warn(ctx, member: Option(discord.Member, "The member to warn"), reason: Option(str, "Reason for the warning")):
        await ctx.defer()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            warn_msg = await member.send(f"You have been warned in {ctx.guild.name} for the following reason:\n{reason}")
            message_id = warn_msg.id
        except discord.Forbidden:
            message_id = None
        
        execute_db_query("INSERT INTO warnings VALUES (?, ?, ?, ?, ?, ?)", (ctx.guild.id, member.id, ctx.author.id, reason, timestamp, message_id))

        embed = discord.Embed(title="User Warned", description=f"{member.mention} has been warned.", color=discord.Color.orange())
        embed.add_field(name="Reason", value=reason)
        await ctx.respond(embed=embed)

    @bot.slash_command(name="warnings", description="View warnings for a user")
    @commands.has_permissions(kick_members=True)
    async def warnings(ctx, member: Option(discord.Member, "The member to check warnings for")):
        await ctx.defer()
        warnings = execute_db_query("SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))

        if not warnings:
            await ctx.respond(f"{member.mention} has no warnings.")
            return

        embed = create_warnings_embed(warnings, member, 0)
        view = WarningPaginator(warnings, member)
        await ctx.respond(embed=embed, view=view)

    @bot.slash_command(name="remove_warning", description="Remove a specific warning from a user")
    @commands.has_permissions(kick_members=True)
    async def remove_warning(ctx, member: Option(discord.Member, "The member to remove a warning from"), warning_index: Option(int, "The index of the warning to remove")):
        await ctx.defer()
        warnings = execute_db_query("SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))

        if not warnings:
            await ctx.respond(f"{member.mention} has no warnings.")
            return

        if warning_index < 1 or warning_index > len(warnings):
            await ctx.respond("Invalid warning index.")
            return

        warning = warnings[warning_index - 1]
        execute_db_query("DELETE FROM warnings WHERE guild_id = ? AND user_id = ? AND moderator_id = ? AND reason = ? AND timestamp = ? AND message_id = ?", warning)

        embed = discord.Embed(title="Warning Removed", description=f"Warning {warning_index} has been removed from {member.mention}.", color=discord.Color.green())
        
        if warning[5]:  # Check if message_id is not None
            try:
                warning_message = await member.fetch_message(warning[5])
                await warning_message.delete()
            except discord.NotFound:
                embed.description += "\n\nWarning message could not be found."
            except discord.Forbidden:
                embed.description += "\n\nBot doesn't have permission to delete the warning message."
            except Exception as e:
                embed.description += f"\n\nAn error occurred: {e}"
        
        await ctx.respond(embed=embed)

    @bot.slash_command(name="clear_warnings", description="Clear all warnings for a user")
    @commands.has_permissions(administrator=True)
    async def clear_warnings(ctx, member: Option(discord.Member, "The member to clear warnings for")):
        await ctx.defer()
        warnings = execute_db_query("SELECT message_id FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        message_ids = [row[0] for row in warnings if row[0] is not None]

        execute_db_query("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))

        embed = discord.Embed(title="Warnings Cleared", description=f"All warnings have been cleared for {member.mention}.", color=discord.Color.green())

        deleted_count = 0
        for message_id in message_ids:
            try:
                warning_message = await member.fetch_message(message_id)
                await warning_message.delete()
                deleted_count += 1
            except discord.NotFound:
                pass
            except discord.Forbidden:
                embed.description += "\n\nSome warning messages could not be deleted due to missing permissions."
                break
            except Exception as e:
                embed.description += f"\n\nAn error occurred: {e}"
                break

        if deleted_count > 0:
            embed.description += f"\n\n{deleted_count} warning message(s) were deleted."
        
        await ctx.respond(embed=embed)