import discord
from discord.ext import commands

def setup_error_handlers(bot):
    @bot.event
    async def on_application_command_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have the necessary permissions to use this command.", ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.respond("I don't have the necessary permissions to perform this action.", ephemeral=True)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.respond("The specified member was not found.", ephemeral=True)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.respond("The specified channel was not found.", ephemeral=True)
        elif isinstance(error, commands.RoleNotFound):
            await ctx.respond("The specified role was not found.", ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.", ephemeral=True)
        elif isinstance(error, commands.DisabledCommand):
            await ctx.respond("This command is currently disabled.", ephemeral=True)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("This command cannot be used in private messages.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.respond("Invalid argument provided. Please check the command usage.", ephemeral=True)
        else:
            await ctx.respond("An error occurred while executing the command. Please try again later.", ephemeral=True)
            print(f"Unhandled error: {error}")