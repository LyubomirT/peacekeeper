import discord
from discord.commands import Option
from discord.ext import commands
import sqlite3
from datetime import datetime

def setup_warnings(bot):
    conn = sqlite3.connect('peacekeeper.db')
    c = conn.cursor()
    
    # Modify the table to include message_id
    c.execute('''CREATE TABLE IF NOT EXISTS warnings
                 (guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, reason TEXT, timestamp TEXT, message_id INTEGER)''')
    conn.commit()

    class WarningPaginator(discord.ui.View):
        def __init__(self, warnings, user):
            super().__init__(timeout=60)
            self.warnings = warnings
            self.user = user
            self.page = 0

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
        async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.page -= 1
            await self.update_message(interaction)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
        async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.page += 1
            await self.update_message(interaction)

        async def update_message(self, interaction: discord.Interaction):
            embed = create_warnings_embed(self.warnings, self.user, self.page)
            self.previous_button.disabled = (self.page == 0)
            self.next_button.disabled = (self.page >= (len(self.warnings) - 1) // 3)
            await interaction.response.edit_message(embed=embed, view=self)

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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send the warning message to the user
        try:
            warn_msg = await member.send(f"You have been warned in {ctx.guild.name} for the following reason:\n{reason}")
            message_id = warn_msg.id
        except discord.Forbidden:
            message_id = None
        
        # Insert the warning into the database, including the message_id
        c.execute("INSERT INTO warnings VALUES (?, ?, ?, ?, ?, ?)", (ctx.guild.id, member.id, ctx.author.id, reason, timestamp, message_id))
        conn.commit()

        embed = discord.Embed(title="User Warned", description=f"{member.mention} has been warned.", color=discord.Color.orange())
        embed.add_field(name="Reason", value=reason)
        await ctx.respond(embed=embed)

    @bot.slash_command(name="warnings", description="View warnings for a user")
    @commands.has_permissions(kick_members=True)
    async def warnings(ctx, member: Option(discord.Member, "The member to check warnings for")):
        c.execute("SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        warnings = c.fetchall()

        if not warnings:
            await ctx.respond(f"{member.mention} has no warnings.")
            return

        embed = create_warnings_embed(warnings, member, 0)
        view = WarningPaginator(warnings, member)
        await ctx.respond(embed=embed, view=view)

    @bot.slash_command(name="remove_warning", description="Remove a specific warning from a user")
    @commands.has_permissions(kick_members=True)
    async def remove_warning(ctx, member: Option(discord.Member, "The member to remove a warning from"), warning_index: Option(int, "The index of the warning to remove")):
        c.execute("SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        warnings = c.fetchall()

        if not warnings:
            await ctx.respond(f"{member.mention} has no warnings.")
            return

        if warning_index < 1 or warning_index > len(warnings):
            await ctx.respond("Invalid warning index.")
            return

        warning = warnings[warning_index - 1]
        c.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ? AND moderator_id = ? AND reason = ? AND timestamp = ? AND message_id = ?", warning)
        conn.commit()

        embed = discord.Embed(title="Warning Removed", description=f"Warning {warning_index} has been removed from {member.mention}.", color=discord.Color.green())
        
        # Try to delete the warning message using the stored message_id
        if warning[5]:  # Check if message_id is not None
            try:
                warning_message = await member.fetch_message(warning[5])
                await warning_message.delete()
            except discord.NotFound:
                embed.description += "\n\nWarning message could not be found."
            except discord.Forbidden:
                embed.description += "\n\nBot doesn't have permission to delete the warning message."
        
        await ctx.respond(embed=embed)

    @bot.slash_command(name="clear_warnings", description="Clear all warnings for a user")
    @commands.has_permissions(administrator=True)
    async def clear_warnings(ctx, member: Option(discord.Member, "The member to clear warnings for")):
        c.execute("SELECT message_id FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        message_ids = [row[0] for row in c.fetchall() if row[0] is not None]

        c.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        conn.commit()

        embed = discord.Embed(title="Warnings Cleared", description=f"All warnings have been cleared for {member.mention}.", color=discord.Color.green())

        # Try to delete all warning messages
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

        if deleted_count > 0:
            embed.description += f"\n\n{deleted_count} warning message(s) were deleted."
        
        await ctx.respond(embed=embed)