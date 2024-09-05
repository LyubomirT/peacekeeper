import discord
from discord.ext import commands
from discord.commands import Option
from db_utils import execute_db_query

class VerificationView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(style=discord.ButtonStyle.green, label="Verify", custom_id="verify")
    async def verify_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"You have been verified and given the {role.name} role!", ephemeral=True)
        else:
            await interaction.response.send_message("The verification role could not be found. Please contact a server administrator.", ephemeral=True)

def setup_verification(bot):
    execute_db_query('''CREATE TABLE IF NOT EXISTS verification_messages
                        (guild_id INTEGER, channel_id INTEGER, message_id INTEGER, role_id INTEGER)''')

    @bot.slash_command(name="set_verification", description="Set up a verification message with a button")
    @commands.has_permissions(manage_roles=True)
    async def set_verification(
        ctx, 
        message_link: Option(str, "The link to the message you want to duplicate"),
        role: Option(discord.Role, "The role to assign when verified"),
        delete_original: Option(bool, "Whether to delete the original message", default=False)
    ):
        await ctx.defer()

        # Parse the message link
        try:
            # sample link: https://discord.com/channels/1155207826822668339/1167084718949412965/1281322495856742493
            print(message_link.split("/"))
            guild_id, channel_id, message_id = message_link.split("/")[-3:]
            guild_id = int(guild_id)
            channel_id = int(channel_id)
            message_id = int(message_id)
            role_id = role.id
        except ValueError:
            await ctx.respond("Invalid message link. Please provide a valid Discord message link.", ephemeral=True)
            return

        # Get the channel and message
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.respond("Couldn't find the channel. Make sure the bot has access to it.", ephemeral=True)
            return

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.respond("Couldn't find the message. Make sure it exists and the bot can see it.", ephemeral=True)
            return

        # Create a new message with the same content and embeds
        new_content = message.content
        new_embeds = message.embeds
        new_files = [await attachment.to_file() for attachment in message.attachments]

        # Create the verification view
        view = VerificationView(role.id)

        # Send the new message
        new_message = await channel.send(content=new_content, embeds=new_embeds, files=new_files, view=view)

        # Delete the original message if specified
        if delete_original:
            await message.delete()

        # Delete old verification message if it exists
        old_verification = execute_db_query("SELECT channel_id, message_id FROM verification_messages WHERE guild_id = ?", (ctx.guild.id,))
        if old_verification:
            old_channel_id, old_message_id = old_verification[0]
            old_channel = bot.get_channel(old_channel_id)
            if old_channel:
                try:
                    old_message = await old_channel.fetch_message(old_message_id)
                    await old_message.delete()
                except discord.NotFound:
                    pass

        # Update the database
        execute_db_query("INSERT OR REPLACE INTO verification_messages VALUES (?, ?, ?, ?)", 
                         (ctx.guild.id, channel.id, new_message.id, role.id))

        await ctx.respond(f"Verification message set up successfully. Users can now verify by clicking the button to receive the {role.name} role.", ephemeral=True)

    @bot.slash_command(name="delete_verification", description="Delete the current verification message")
    @commands.has_permissions(manage_roles=True)
    async def delete_verification(ctx):
        await ctx.defer()

        verification = execute_db_query("SELECT channel_id, message_id FROM verification_messages WHERE guild_id = ?", (ctx.guild.id,))
        if not verification:
            await ctx.respond("There is no verification message set for this server.", ephemeral=True)
            return

        channel_id, message_id = verification[0]
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
            except discord.NotFound:
                pass

        execute_db_query("DELETE FROM verification_messages WHERE guild_id = ?", (ctx.guild.id,))
        await ctx.respond("The verification message has been deleted.", ephemeral=True)