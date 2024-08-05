import discord
from discord.commands import Option
from discord.ext import commands
from db_utils import execute_db_query

def setup_notes(bot):
    execute_db_query('''CREATE TABLE IF NOT EXISTS user_notes
                 (guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, note TEXT, timestamp TEXT)''')

    class NotePaginator(discord.ui.View):
        def __init__(self, notes, user):
            super().__init__(timeout=60)
            self.notes = notes
            self.user = user
            self.page = 0
            self.create_next_button()

        @discord.ui.button(label="◀", style=discord.ButtonStyle.gray, disabled=True)
        async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.page -= 1
            await self.update_message(interaction)

        def create_next_button(self):
            if len(self.notes) > 5:
                @discord.ui.button(label="▶", style=discord.ButtonStyle.gray, disabled=(len(self.notes) <= 5))
                async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                    self.page += 1
                    await self.update_message(interaction)
            else:
                @discord.ui.button(label="▶", style=discord.ButtonStyle.gray, disabled=True)
                async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                    pass

        async def update_message(self, interaction: discord.Interaction):
            embed = create_notes_embed(self.notes, self.user, self.page)
            self.previous_button.disabled = (self.page == 0)
            self.next_button.disabled = (self.page >= (len(self.notes) - 1) // 5)
            await interaction.response.edit_message(embed=embed, view=self)

    def create_notes_embed(notes, user, page):
        start = page * 5
        end = start + 5
        current_notes = notes[start:end]

        embed = discord.Embed(title=f"Notes for {user.name}", color=discord.Color.blue())
        for i, (moderator_id, note, timestamp) in enumerate(current_notes, start=start+1):
            moderator = user.guild.get_member(moderator_id)
            moderator_name = moderator.name if moderator else "Unknown Moderator"
            embed.add_field(name=f"Note {i} | By {moderator_name} on {timestamp}", value=note, inline=False)

        embed.set_footer(text=f"Page {page + 1}/{(len(notes) - 1) // 5 + 1}")
        return embed

    @bot.slash_command(name="add_note", description="Add a note to a user")
    @commands.has_permissions(manage_messages=True)
    async def add_note(ctx, user: Option(discord.Member, "The user to add a note to"), note: Option(str, "The note to add")):
        await ctx.defer()
        timestamp = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        execute_db_query("INSERT INTO user_notes VALUES (?, ?, ?, ?, ?)", 
                         (ctx.guild.id, user.id, ctx.author.id, note, timestamp))
        
        embed = discord.Embed(title="Note Added", description=f"A note has been added to {user.mention}'s profile.", color=discord.Color.green())
        embed.add_field(name="Note", value=note)
        embed.set_footer(text=f"Added by {ctx.author.name} | {timestamp}")
        await ctx.respond(embed=embed)

    @bot.slash_command(name="view_notes", description="View notes for a user")
    @commands.has_permissions(manage_messages=True)
    async def view_notes(ctx, user: Option(discord.Member, "The user to view notes for")):
        await ctx.defer()
        notes = execute_db_query("SELECT moderator_id, note, timestamp FROM user_notes WHERE guild_id = ? AND user_id = ?", 
                                 (ctx.guild.id, user.id))
        
        if not notes:
            await ctx.respond(f"No notes found for {user.mention}.")
            return

        embed = create_notes_embed(notes, user, 0)
        view = NotePaginator(notes, user)
        await ctx.respond(embed=embed, view=view)

    @bot.slash_command(name="edit_note", description="Edit a note for a user")
    @commands.has_permissions(manage_messages=True)
    async def edit_note(ctx, user: Option(discord.Member, "The user whose note to edit"), 
                        note_index: Option(int, "The index of the note to edit"), 
                        new_note: Option(str, "The new content of the note")):
        await ctx.defer()
        notes = execute_db_query("SELECT rowid, moderator_id, note, timestamp FROM user_notes WHERE guild_id = ? AND user_id = ?", 
                                 (ctx.guild.id, user.id))
        
        if not notes or note_index < 1 or note_index > len(notes):
            await ctx.respond("Invalid note index.")
            return

        note_id, moderator_id, old_note, timestamp = notes[note_index - 1]
        
        if ctx.author.id != moderator_id and not ctx.author.guild_permissions.administrator:
            await ctx.respond("You can only edit notes that you've added, unless you're an administrator.")
            return

        execute_db_query("UPDATE user_notes SET note = ? WHERE rowid = ?", (new_note, note_id))
        
        embed = discord.Embed(title="Note Edited", description=f"A note for {user.mention} has been edited.", color=discord.Color.yellow())
        embed.add_field(name="Old Note", value=old_note, inline=False)
        embed.add_field(name="New Note", value=new_note, inline=False)
        embed.set_footer(text=f"Edited by {ctx.author.name} | Original timestamp: {timestamp}")
        await ctx.respond(embed=embed)

    @bot.slash_command(name="delete_note", description="Delete a note for a user")
    @commands.has_permissions(manage_messages=True)
    async def delete_note(ctx, user: Option(discord.Member, "The user whose note to delete"), 
                          note_index: Option(int, "The index of the note to delete")):
        await ctx.defer()
        notes = execute_db_query("SELECT rowid, moderator_id, note FROM user_notes WHERE guild_id = ? AND user_id = ?", 
                                 (ctx.guild.id, user.id))
        
        if not notes or note_index < 1 or note_index > len(notes):
            await ctx.respond("Invalid note index.")
            return

        note_id, moderator_id, note = notes[note_index - 1]
        
        if ctx.author.id != moderator_id and not ctx.author.guild_permissions.administrator:
            await ctx.respond("You can only delete notes that you've added, unless you're an administrator.")
            return

        execute_db_query("DELETE FROM user_notes WHERE rowid = ?", (note_id,))
        
        embed = discord.Embed(title="Note Deleted", description=f"A note for {user.mention} has been deleted.", color=discord.Color.red())
        embed.add_field(name="Deleted Note", value=note)
        embed.set_footer(text=f"Deleted by {ctx.author.name}")
        await ctx.respond(embed=embed)