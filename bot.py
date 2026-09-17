import discord
from discord.ext import commands
import random
import json
import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

SERVER_ID = 1549149647476363384
COUNTING_CHANNEL_ID = 1550160615065129051
ZEITLIMIT = 30

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# FLAGGEN
# =========================

flaggen = {
    "🇩🇪": ("Deutschland", 1),
    "🇫🇷": ("Frankreich", 1),
    "🇮🇹": ("Italien", 1),
    "🇪🇸": ("Spanien", 1),
    "🇬🇧": ("England", 1),
    "🇺🇸": ("USA", 1),
    "🇯🇵": ("Japan", 1),
    "🇨🇦": ("Kanada", 1),
    "🇧🇷": ("Brasilien", 1),
    "🇦🇹": ("Österreich", 1),
    "🇵🇱": ("Polen", 2),
    "🇳🇱": ("Niederlande", 2),
    "🇧🇪": ("Belgien", 2),
    "🇨🇭": ("Schweiz", 2),
    "🇩🇰": ("Dänemark", 2),
    "🇸🇪": ("Schweden", 2),
    "🇳🇴": ("Norwegen", 2),
    "🇫🇮": ("Finnland", 2),
    "🇬🇷": ("Griechenland", 2),
    "🇵🇹": ("Portugal", 2),
    "🇧🇹": ("Bhutan", 3),
    "🇲🇳": ("Mongolei", 3),
    "🇰🇿": ("Kasachstan", 3),
    "🇱🇰": ("Sri Lanka", 3)
}

# =========================
# PUNKTE SPEICHERN
# =========================

try:
    with open("scores.json", "r") as f:
        punkte = json.load(f)
except:
    punkte = {}

def speichern():
    with open("scores.json", "w") as f:
        json.dump(punkte, f)

# =========================
# FLAGGEN-SPIEL
# =========================

spiele = {}

async def neue_frage(channel):
    flagge = random.choice(list(flaggen))
    land, wert = flaggen[flagge]

    spiele[channel.id] = {
        "flagge": flagge,
        "land": land,
        "wert": wert
    }

    await channel.send(
        f"🌍 **Flaggen-Quiz!**\n\n"
        f"# {flagge}\n\n"
        f"⏱️ **{ZEITLIMIT} Sekunden**\n"
        f"💰 **{wert} Punkt(e)**\n\n"
        f"Schreibe das Land!"
    )

    asyncio.create_task(timer(channel, flagge))

async def timer(channel, flagge):
    await asyncio.sleep(ZEITLIMIT)

    spiel = spiele.get(channel.id)

    if spiel and spiel["flagge"] == flagge:
        del spiele[channel.id]

        await channel.send(
            f"⏰ **Zeit abgelaufen!**\n"
            f"Richtig wäre **{spiel['land']}** gewesen."
        )

        await asyncio.sleep(2)

        if channel.id not in spiele:
            await neue_frage(channel)

# =========================
# COUNTING
# =========================

counting_number = 0
last_counter = None
counting_record = 0

# =========================
# BOT ONLINE
# =========================

@bot.event
async def on_ready():
    guild = discord.Object(id=SERVER_ID)

    synced = await bot.tree.sync(guild=guild)

    print(f"Bot ist online als {bot.user}")
    print(f"{len(synced)} Slash-Befehle synchronisiert.")
    print(f"Counting-Kanal: {COUNTING_CHANNEL_ID}")

# =========================
# /FLAGGEN
# =========================

@bot.tree.command(
    name="flaggen",
    description="Startet das Flaggen-Quiz",
    guild=discord.Object(id=SERVER_ID)
)
async def flaggen_quiz(interaction):

    if interaction.channel.id == COUNTING_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Hier läuft nur das Counting!"
        )
        return

    if interaction.channel.id in spiele:
        await interaction.response.send_message(
            "⚠️ Hier läuft bereits ein Quiz!"
        )
        return

    await interaction.response.send_message(
        "🏁 **Flaggen-Quiz gestartet!**"
    )

    await asyncio.sleep(1)

    await neue_frage(interaction.channel)

# =========================
# /BEENDEN
# =========================

@bot.tree.command(
    name="beenden",
    description="Beendet das Flaggen-Quiz",
    guild=discord.Object(id=SERVER_ID)
)
async def beenden(interaction):

    if interaction.channel.id not in spiele:
        await interaction.response.send_message(
            "❌ Hier läuft kein Quiz."
        )
        return

    del spiele[interaction.channel.id]

    await interaction.response.send_message(
        "🛑 **Das Flaggen-Quiz wurde beendet!**"
    )

# =========================
# /LEADERBOARD
# =========================

@bot.tree.command(
    name="leaderboard",
    description="Zeigt die Rangliste",
    guild=discord.Object(id=SERVER_ID)
)
async def leaderboard(interaction):

    if not punkte:
        await interaction.response.send_message(
            "🏆 Noch hat niemand Punkte!"
        )
        return

    rangliste = sorted(
        punkte.items(),
        key=lambda x: x[1],
        reverse=True
    )

    text = "🏆 **FLAGGEN-RANGLISTE** 🏆\n\n"

    for platz, (user_id, score) in enumerate(rangliste[:10], 1):

        user = bot.get_user(int(user_id))

        if user:
            name = user.display_name
        else:
            name = "Unbekannt"

        if platz == 1:
            symbol = "🥇"
        elif platz == 2:
            symbol = "🥈"
        elif platz == 3:
            symbol = "🥉"
        else:
            symbol = f"{platz}."

        text += f"{symbol} **{name}** — {score} Punkte\n"

    await interaction.response.send_message(text)

# =========================
# NACHRICHTEN
# =========================

@bot.event
async def on_message(message):

    global counting_number
    global last_counter
    global counting_record

    if message.author.bot:
        return

    # =========================
    # COUNTING-KANAL
    # =========================

    if message.channel.id == COUNTING_CHANNEL_ID:

        try:
            zahl = int(message.content.strip())
        except ValueError:
            return

        erwartete_zahl = counting_number + 1

        # Gleiche Person zweimal
        if message.author.id == last_counter:

            await message.add_reaction("❌")

            await message.channel.send(
                f"❌ {message.author.mention}, "
                f"du kannst nicht zweimal hintereinander zählen!\n"
                f"🔄 Counting startet wieder bei **0**."
            )

            counting_number = 0
            last_counter = None

            return

        # Falsche Zahl
        if zahl != erwartete_zahl:

            await message.add_reaction("❌")

            await message.channel.send(
                f"❌ Falsch! Es wäre **{erwartete_zahl}** gewesen.\n"
                f"🔄 Counting startet wieder bei **0**."
            )

            counting_number = 0
            last_counter = None

            return

        # Richtige Zahl
        counting_number = zahl
        last_counter = message.author.id

        # Rekord
        if counting_number > counting_record:
            counting_record = counting_number

        await message.add_reaction("✅")

        # Alle 10 Zahlen
        if counting_number % 10 == 0:

            await message.channel.send(
                f"🔥 **{counting_number}** erreicht!\n"
                f"🏆 Rekord: **{counting_record}**"
            )

        return

    # =========================
    # FLAGGEN-QUIZ
    # =========================

    spiel = spiele.get(message.channel.id)

    if spiel:

        antwort = message.content.lower().strip()

        if antwort == spiel["land"].lower():

            user_id = str(message.author.id)

            gewinn = spiel["wert"]

            punkte[user_id] = punkte.get(user_id, 0) + gewinn

            speichern()

            del spiele[message.channel.id]

            await message.channel.send(
                f"✅ **Richtig, {message.author.mention}!** 🎉\n"
                f"💰 **+{gewinn} Punkt(e)**\n"
                f"🏆 Du hast jetzt **{punkte[user_id]} Punkte**!"
            )

            await asyncio.sleep(2)

            await neue_frage(message.channel)

    await bot.process_commands(message)

# =========================
# BOT STARTEN
# =========================

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online!")

    def log_message(self, format, *args):
        return

def webserver():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=webserver, daemon=True).start()

token = os.getenv("BOT_TOKEN")

if token:
    bot.run(token)
else:
    print("❌ BOT_TOKEN wurde nicht gesetzt!")
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online!")

    def log_message(self, format, *args):
        return


def webserver():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

if token:
    bot.run(token)
else:
    print("❌ BOT_TOKEN wurde nicht gesetzt!")
