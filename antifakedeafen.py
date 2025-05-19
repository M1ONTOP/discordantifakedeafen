import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.anti_fakedeafen_loops = {}

bot = MyBot()

def create_embed(title, description, color):
    return discord.Embed(title=title, description=description, color=color)

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Anti fake deafen
@bot.tree.command(name="anti_fakedeafen", description="Monitor VC for fake-deafened users")
@app_commands.describe(channel="Voice channel to monitor")
@is_admin()
async def anti_fakedeafen(interaction: discord.Interaction, channel: discord.VoiceChannel):
    guild_id = interaction.guild.id

    if guild_id in bot.anti_fakedeafen_loops:
        embed = create_embed("Already Monitoring", f"I'm already monitoring `{channel.name}` for fake deafens.", discord.Color.dark_theme())
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    async def monitor_deafens():
        try:
            while True:
                await bot.wait_until_ready()
                channel_ref = interaction.guild.get_channel(channel.id)
                if not channel_ref:
                    break

                for member in channel_ref.members:
                    if member.bot:
                        continue
                    try:
                        if member.voice.self_deaf and not member.voice.deaf:
                            await member.edit(deafen=True)
                            print(f"[INFO] Server deafened {member.display_name}")
                        elif not member.voice.self_deaf and member.voice.deaf:
                            await member.edit(deafen=False)
                            print(f"[INFO] Server undeafened {member.display_name}")
                    except discord.Forbidden:
                        print(f"[WARN] No permission to edit {member.display_name}")
                    except Exception as e:
                        print(f"[ERROR] Error on {member.display_name}: {e}")
                await discord.utils.sleep_until(discord.utils.utcnow().replace(second=(discord.utils.utcnow().second + 2) % 60))
        except Exception as e:
            print(f"[ERROR] Anti-fake-deafen crash: {e}")
        finally:
            bot.anti_fakedeafen_loops.pop(guild_id, None)

    bot.anti_fakedeafen_loops[guild_id] = bot.loop.create_task(monitor_deafens())
    embed = create_embed(
        "Anti-Fake-Deafen Enabled",
        f"🔍 Now monitoring `{channel.name}` for fake-deafened users.",
        discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run("BOT_TOKEN_HERE")  # Replace with your bot token