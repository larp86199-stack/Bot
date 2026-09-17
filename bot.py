import discord
from discord.ext import commands
import random
import json
import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# =========================
# EINSTELLUNGEN
# =========================

SERVER_ID = 1549149647476363384
COUNTING_CHANNEL_ID = 1550160615065129051
ZEITLIMIT = 30

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =========================
# DATEIEN
# =========================

def lade_json(dateiname, standard):
    try:
        with open(dateiname, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return standard


def speichere_json(dateiname, daten):
    with open(dateiname, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4)


# Flaggenpunkte
punkte = lade_json("scores.json", {})

# Virtuelles Geld
geld = lade_json("geld.json", {})

# Daily-System
daily = lade_json("daily.json", {})

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

spiele = {}

# =========================
# COUNTING
# =========================

counting_number = 0
last_counter = None
counting_record = 0

# =========================
# BLACKJACK
# =========================

blackjack_spiele = {}

karten = [
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("5", 5),
    ("6", 6),
    ("7", 7),
    ("8", 8),
    ("9", 9),
    ("10", 10),
    ("J", 10),
    ("Q", 10),
    ("K", 10),
    ("A", 11)
]


def neue_karte():
    return random.choice(karten)


def hand_wert(hand):
    wert = sum(karte[1] for karte in hand)

    asse = sum(1 for karte in hand if karte[0] == "A")

    while wert > 21 and asse > 0:
        wert -= 10
        asse -= 1

    return wert


def hand_text(hand):
    return " ".join(karte[0] for karte in hand)


def gib_geld(user_id, menge):
    user_id = str(user_id)

    if user_id not in geld:
        geld[user_id] = 0

    geld[user_id] += menge

    speichere_json("geld.json", geld)


def hat_geld(user_id, menge):
    return geld.get(str(user_id), 0) >= menge


def verliere_geld(user_id, menge):
    user_id = str(user_id)

    if user_id not in geld:
        geld[user_id] = 0

    geld[user_id] -= menge

    if geld[user_id] < 0:
        geld[user_id] = 0

    speichere_json("geld.json", geld)


# =========================
# FLAGGEN-FRAGE
# =========================

async def neue_frage(channel):

    flagge = random.choice(list(flaggen))

    land, wert = flaggen[flagge]

    spiele[channel.id] = {
        "flagge": flagge,
        "land": land,
        "wert": wert
    }

    await channel.send(
        f"🌍 **FLAGGEN-QUIZ**\n\n"
        f"# {flagge}\n\n"
        f"⏱️ **{ZEITLIMIT} Sekunden**\n"
        f"💰 **{wert} Punkt(e)**\n\n"
        f"Schreibe das Land!"
    )

    asyncio.create_task(
        timer(channel, flagge)
    )


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
# READY
# =========================

@bot.event
async def on_ready():

    guild = discord.Object(id=SERVER_ID)

    synced = await bot.tree.sync(
        guild=guild
    )

    print(
        f"Bot ist online als {bot.user}"
    )

    print(
        f"{len(synced)} Slash-Befehle synchronisiert."
    )

    print(
        f"Counting-Kanal: {COUNTING_CHANNEL_ID}"
    )


# =========================
# FLAGGEN START
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

    await neue_frage(
        interaction.channel
    )


# =========================
# FLAGGEN BEENDEN
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
# FLAGGEN LEADERBOARD
# =========================

@bot.tree.command(
    name="leaderboard",
    description="Zeigt die Flaggen-Rangliste",
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

    for platz, (user_id, score) in enumerate(
        rangliste[:10],
        1
    ):

        user = bot.get_user(
            int(user_id)
        )

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

        text += (
            f"{symbol} **{name}** — "
            f"{score} Punkte\n"
        )

    await interaction.response.send_message(
        text
    )


# =========================
# GELD
# =========================

@bot.tree.command(
    name="geld",
    description="Zeigt dein virtuelles Guthaben",
    guild=discord.Object(id=SERVER_ID)
)
async def geld_befehl(interaction):

    user_id = str(
        interaction.user.id
    )

    if user_id not in geld:
        geld[user_id] = 1000
        speichere_json(
            "geld.json",
            geld
        )

    await interaction.response.send_message(
        f"💰 **{interaction.user.display_name}**\n\n"
        f"💵 Guthaben: **{geld[user_id]} Coins**"
    )


# =========================
# DAILY
# =========================

@bot.tree.command(
    name="daily",
    description="Holt deine täglichen virtuellen Coins",
    guild=discord.Object(id=SERVER_ID)
)
async def daily_befehl(interaction):

    user_id = str(
        interaction.user.id
    )

    heute = discord.utils.utcnow().date().isoformat()

    if daily.get(user_id) == heute:

        await interaction.response.send_message(
            "⏰ Du hast deine Daily-Coins heute bereits abgeholt!"
        )

        return

    if user_id not in geld:
        geld[user_id] = 1000

    belohnung = 500

    geld[user_id] += belohnung

    daily[user_id] = heute

    speichere_json(
        "geld.json",
        geld
    )

    speichere_json(
        "daily.json",
        daily
    )

    await interaction.response.send_message(
        f"🎁 **Daily abgeholt!**\n\n"
        f"💰 **+{belohnung} Coins**\n"
        f"💵 Neues Guthaben: **{geld[user_id]} Coins**"
    )


# =========================
# GELD LEADERBOARD
# =========================

@bot.tree.command(
    name="geldrangliste",
    description="Zeigt die reichsten Spieler",
    guild=discord.Object(id=SERVER_ID)
)
async def geldrangliste(interaction):

    if not geld:

        await interaction.response.send_message(
            "💰 Noch hat niemand Coins!"
        )

        return

    rangliste = sorted(
        geld.items(),
        key=lambda x: x[1],
        reverse=True
    )

    text = "💰 **COIN-RANGLISTE** 💰\n\n"

    for platz, (user_id, amount) in enumerate(
        rangliste[:10],
        1
    ):

        user = bot.get_user(
            int(user_id)
        )

        name = (
            user.display_name
            if user
            else "Unbekannt"
        )

        if platz == 1:
            symbol = "🥇"
        elif platz == 2:
            symbol = "🥈"
        elif platz == 3:
            symbol = "🥉"
        else:
            symbol = f"{platz}."

        text += (
            f"{symbol} **{name}** — "
            f"{amount} Coins\n"
        )

    await interaction.response.send_message(
        text
    )


# =========================
# BLACKJACK START
# =========================

@bot.tree.command(
    name="blackjack",
    description="Spiele Blackjack mit virtuellen Coins",
    guild=discord.Object(id=SERVER_ID)
)
async def blackjack(
    interaction,
    einsatz: int
):

    user_id = str(
        interaction.user.id
    )

    if einsatz <= 0:

        await interaction.response.send_message(
            "❌ Der Einsatz muss größer als 0 sein."
        )

        return

    if einsatz > 100000:

        await interaction.response.send_message(
            "❌ Der maximale Einsatz beträgt 100000 Coins."
        )

        return

    if user_id not in geld:
        geld[user_id] = 1000
        speichere_json(
            "geld.json",
            geld
        )

    if not hat_geld(
        user_id,
        einsatz
    ):

        await interaction.response.send_message(
            f"❌ Du hast nicht genug Coins.\n"
            f"💰 Dein Guthaben: **{geld[user_id]} Coins**"
        )

        return

    if user_id in blackjack_spiele:

        await interaction.response.send_message(
            "🃏 Du hast bereits ein Blackjack-Spiel laufen!"
        )

        return

    verliere_geld(
        user_id,
        einsatz
    )

    spieler_hand = [
        neue_karte(),
        neue_karte()
    ]

    dealer_hand = [
        neue_karte(),
        neue_karte()
    ]

    blackjack_spiele[user_id] = {
        "spieler": spieler_hand,
        "dealer": dealer_hand,
        "einsatz": einsatz,
        "channel": interaction.channel.id
    }

    spieler_wert = hand_wert(
        spieler_hand
    )

    dealer_wert = hand_wert(
        dealer_hand
    )

    # Blackjack direkt
    if spieler_wert == 21:

        gewinn = einsatz * 2

        gib_geld(
            user_id,
            gewinn
        )

        del blackjack_spiele[user_id]

        await interaction.response.send_message(
            f"🃏 **BLACKJACK!** 🎉\n\n"
            f"👤 Deine Karten: **{hand_text(spieler_hand)}**\n"
            f"💰 Gewinn: **+{gewinn} Coins**\n"
            f"💵 Guthaben: **{geld[user_id]} Coins**"
        )

        return

    await interaction.response.send_message(
        f"🃏 **BLACKJACK**\n\n"
        f"👤 Deine Karten: **{hand_text(spieler_hand)}**\n"
        f"🔢 Dein Wert: **{spieler_wert}**\n\n"
        f"🤖 Dealer zeigt: **{dealer_hand[0][0]}** + ❓\n\n"
        f"💰 Einsatz: **{einsatz} Coins**\n\n"
        f"➡️ Benutze `/hit` für eine weitere Karte.\n"
        f"➡️ Benutze `/stand` zum Aufhören."
    )


# =========================
# BLACKJACK HIT
# =========================

@bot.tree.command(
    name="hit",
    description="Ziehe eine weitere Blackjack-Karte",
    guild=discord.Object(id=SERVER_ID)
)
async def hit(interaction):

    user_id = str(
        interaction.user.id
    )

    spiel = blackjack_spiele.get(
        user_id
    )

    if not spiel:

        await interaction.response.send_message(
            "❌ Du hast kein laufendes Blackjack-Spiel."
        )

        return

    spiel["spieler"].append(
        neue_karte()
    )

    wert = hand_wert(
        spiel["spieler"]
    )

    if wert > 21:

        del blackjack_spiele[user_id]

        await interaction.response.send_message(
            f"💥 **Über 21!**\n\n"
            f"👤 Deine Karten: **{hand_text(spiel['spieler'])}**\n"
            f"🔢 Wert: **{wert}**\n\n"
            f"❌ Du hast verloren.\n"
            f"💵 Guthaben: **{geld.get(user_id, 0)} Coins**"
        )

        return

    await interaction.response.send_message(
        f"🃏 **Neue Karte!**\n\n"
        f"👤 Deine Karten: **{hand_text(spiel['spieler'])}**\n"
        f"🔢 Wert: **{wert}**\n\n"
        f"➡️ `/hit` = weitere Karte\n"
        f"➡️ `/stand` = stehen"
    )


# =========================
# BLACKJACK STAND
# =========================

@bot.tree.command(
    name="stand",
    description="Beende deine Blackjack-Runde",
    guild=discord.Object(id=SERVER_ID)
)
async def stand(interaction):

    user_id = str(
        interaction.user.id
    )

    spiel = blackjack_spiele.get(
        user_id
    )

    if not spiel:

        await interaction.response.send_message(
            "❌ Du hast kein laufendes Blackjack-Spiel."
        )

        return

    spieler_hand = spiel["spieler"]
    dealer_hand = spiel["dealer"]
    einsatz = spiel["einsatz"]

    # Dealer zieht bis mindestens 17
    while hand_wert(dealer_hand) < 17:
        dealer_hand.append(
            neue_karte()
        )

    spieler_wert = hand_wert(
        spieler_hand
    )

    dealer_wert = hand_wert(
        dealer_hand
    )

    if dealer_wert > 21:

        gewinn = einsatz * 2

        gib_geld(
            user_id,
            gewinn
        )

        ergebnis = (
            f"🎉 **Dealer ist über 21! Du gewinnst!**\n"
            f"💰 **+{gewinn} Coins**"
        )

    elif spieler_wert > dealer_wert:

        gewinn = einsatz * 2

        gib_geld(
            user_id,
            gewinn
        )

        ergebnis = (
            f"🎉 **Du gewinnst!**\n"
            f"💰 **+{gewinn} Coins**"
        )

    elif spieler_wert == dealer_wert:

        gib_geld(
            user_id,
            einsatz
        )

        ergebnis = (
            f"🤝 **Unentschieden!**\n"
            f"💰 Dein Einsatz wurde zurückgegeben."
        )

    else:

        ergebnis = (
            f"❌ **Dealer gewinnt!**\n"
            f"💰 Du verlierst {einsatz} Coins."
        )

    del blackjack_spiele[user_id]

    await interaction.response.send_message(
        f"🃏 **BLACKJACK ERGEBNIS**\n\n"
        f"👤 Deine Karten: **{hand_text(spieler_hand)}**\n"
        f"🔢 Dein Wert: **{spieler_wert}**\n\n"
        f"🤖 Dealer: **{hand_text(dealer_hand)}**\n"
        f"🔢 Dealer-Wert: **{dealer_wert}**\n\n"
        f"{ergebnis}\n\n"
        f"💵 Guthaben: **{geld.get(user_id, 0)} Coins**"
    )


# =========================
# COUNTING
# =========================

@bot.event
async def on_message(message):

    global counting_number
    global last_counter
    global counting_record

    if message.author.bot:
        return

    # -------------------------
    # COUNTING
    # -------------------------

    if message.channel.id == COUNTING_CHANNEL_ID:

        try:
            zahl = int(
                message.content.strip()
            )

        except ValueError:
            return

        erwartete_zahl = (
            counting_number + 1
        )

        # Zweimal hintereinander
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

        if counting_number > counting_record:

            counting_record = counting_number

        await message.add_reaction("✅")

        if counting_number % 10 == 0:

            await message.channel.send(
                f"🔥 **{counting_number}** erreicht!\n"
                f"🏆 Rekord: **{counting_record}**"
            )

        return

    # -------------------------
    # FLAGGEN
    # -------------------------

    spiel = spiele.get(
        message.channel.id
    )

    if spiel:

        antwort = (
            message.content
            .lower()
            .strip()
        )

        if antwort == spiel["land"].lower():

            user_id = str(
                message.author.id
            )

            gewinn = spiel["wert"]

            punkte[user_id] = (
                punkte.get(user_id, 0)
                + gewinn
            )

            speichere_json(
                "scores.json",
                punkte
            )

            del spiele[
                message.channel.id
            ]

            await message.channel.send(
                f"✅ **Richtig, {message.author.mention}!** 🎉\n"
                f"💰 **+{gewinn} Punkt(e)**\n"
                f"🏆 Du hast jetzt **{punkte[user_id]} Punkte**!"
            )

            await asyncio.sleep(2)

            await neue_frage(
                message.channel
            )

            return

    await bot.process_commands(
        message
    )


# =========================
# RENDER WEB SERVER
# =========================

class Handler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"Bot is online!"
        )

    def log_message(
        self,
        format,
        *args
    ):
        return


def webserver():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        Handler
    )

    print(
        f"Webserver laeuft auf Port {port}"
    )

    server.serve_forever()


threading.Thread(
    target=webserver,
    daemon=True
).start()


# =========================
# BOT STARTEN
# =========================

token = os.getenv(
    "BOT_TOKEN"
)

if token:

    bot.run(token)

else:

    print(
        "❌ BOT_TOKEN wurde nicht gesetzt!"
    )
