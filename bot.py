import os
import json
import random
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import discord
from discord.ext import commands


# =========================
# EINSTELLUNGEN
# =========================

SERVER_ID = 1549149647476363384
COUNTING_CHANNEL_ID = 1550160615065129051

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN wurde nicht gefunden. "
        "Setze ihn mit: export BOT_TOKEN='DEIN_TOKEN'"
    )


# =========================
# JSON-HILFSFUNKTIONEN
# =========================

def lade_json(dateiname, standard):
    try:
        with open(dateiname, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return standard


def speichere_json(dateiname, daten):
    with open(dateiname, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)


# =========================
# DATEN
# =========================

punkte = lade_json("scores.json", {})
geld = lade_json("geld.json", {})
daily = lade_json("daily.json", {})
slot_punkte = lade_json("slot_punkte.json", {})


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
# FLAGGEN
# =========================

flaggen = {
    "🇩🇪": "Deutschland",
    "🇫🇷": "Frankreich",
    "🇮🇹": "Italien",
    "🇪🇸": "Spanien",
    "🇬🇧": "Vereinigtes Königreich",
    "🇺🇸": "USA",
    "🇨🇦": "Kanada",
    "🇯🇵": "Japan",
    "🇨🇳": "China",
    "🇧🇷": "Brasilien",
    "🇦🇺": "Australien",
    "🇳🇱": "Niederlande",
    "🇧🇪": "Belgien",
    "🇦🇹": "Österreich",
    "🇨🇭": "Schweiz",
    "🇵🇱": "Polen",
    "🇹🇷": "Türkei",
    "🇬🇷": "Griechenland",
    "🇵🇹": "Portugal",
    "🇳🇴": "Norwegen",
}

quiz_aktiv = {}
quiz_antwort = {}


# =========================
# FLAGGEN-QUIZ
# =========================

@bot.tree.command(
    name="flaggen",
    description="Startet das Flaggen-Quiz"
)
async def flaggen_quiz(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    if user_id in quiz_aktiv:
        await interaction.response.send_message(
            "❌ Du hast bereits ein Flaggen-Quiz laufen."
        )
        return

    flagge, land = random.choice(list(flaggen.items()))

    quiz_aktiv[user_id] = True
    quiz_antwort[user_id] = land.lower()

    await interaction.response.send_message(
        f"🇺🇳 **Flaggen-Quiz**\n\n"
        f"Welche Flagge ist das?\n\n"
        f"# {flagge}\n\n"
        f"Schreibe deine Antwort in den Chat."
    )


@bot.tree.command(
    name="beenden",
    description="Beendet dein Flaggen-Quiz"
)
async def beenden(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    if user_id not in quiz_aktiv:
        await interaction.response.send_message(
            "❌ Du hast kein aktives Quiz."
        )
        return

    quiz_aktiv.pop(user_id, None)
    quiz_antwort.pop(user_id, None)

    await interaction.response.send_message(
        "🛑 Dein Flaggen-Quiz wurde beendet."
    )


# =========================
# PUNKTE-RANGLISTE
# =========================

@bot.tree.command(
    name="leaderboard",
    description="Zeigt die Punkte-Rangliste"
)
async def leaderboard(interaction: discord.Interaction):

    if not punkte:
        await interaction.response.send_message(
            "🏆 Noch hat niemand Punkte."
        )
        return

    sortiert = sorted(
        punkte.items(),
        key=lambda x: x[1],
        reverse=True
    )

    text = "🏆 **Punkte-Rangliste**\n\n"

    for platz, (user_id, wert) in enumerate(sortiert[:10], 1):

        user = bot.get_user(int(user_id))
        name = user.display_name if user else f"User {user_id}"

        text += (
            f"**{platz}. {name}** — "
            f"⭐ {wert} Punkte\n"
        )

    await interaction.response.send_message(text)


# =========================
# PUNKTE
# =========================

@bot.tree.command(
    name="punkte",
    description="Zeigt deine Punkte"
)
async def punkte_befehl(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    wert = punkte.get(user_id, 0)

    await interaction.response.send_message(
        f"⭐ **{interaction.user.display_name}**\n"
        f"Du hast **{wert} Punkte**."
    )


# =========================
# COINS
# =========================

@bot.tree.command(
    name="geld",
    description="Zeigt dein virtuelles Guthaben"
)
async def geld_befehl(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    # Jeder startet automatisch mit 100 Coins.
    if user_id not in geld:
        geld[user_id] = 100
        speichere_json("geld.json", geld)

    betrag = geld[user_id]

    await interaction.response.send_message(
        f"💰 Du hast **{betrag} Coins**."
    )


# =========================
# DAILY
# =========================

@bot.tree.command(
    name="daily",
    description="Holt deine täglichen virtuellen Coins"
)
async def daily_befehl(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    heute = str(date.today())

    if user_id not in geld:
        geld[user_id] = 100

    if daily.get(user_id) == heute:
        await interaction.response.send_message(
            "⏰ Du hast deine Daily-Coins heute "
            "bereits abgeholt."
        )
        return

    belohnung = 100

    geld[user_id] += belohnung
    daily[user_id] = heute

    speichere_json("geld.json", geld)
    speichere_json("daily.json", daily)

    await interaction.response.send_message(
        f"🎁 Du bekommst **{belohnung} Coins**!\n"
        f"💰 Dein Guthaben: **{geld[user_id]} Coins**"
    )


# =========================
# COIN-RANGLISTE
# =========================

@bot.tree.command(
    name="geldrangliste",
    description="Zeigt die Coin-Rangliste"
)
async def geldrangliste(interaction: discord.Interaction):

    if not geld:
        await interaction.response.send_message(
            "💰 Noch hat niemand Coins."
        )
        return

    sortiert = sorted(
        geld.items(),
        key=lambda x: x[1],
        reverse=True
    )

    text = "💰 **Coin-Rangliste**\n\n"

    for platz, (user_id, betrag) in enumerate(
        sortiert[:10],
        1
    ):

        user = bot.get_user(int(user_id))
        name = user.display_name if user else f"User {user_id}"

        text += (
            f"**{platz}. {name}** — "
            f"💰 {betrag} Coins\n"
        )

    await interaction.response.send_message(text)


# =========================
# AUTOMAT MIT GELD-EINSATZ
# =========================

@bot.tree.command(
    name="slots",
    description="Spiele den Punkte-Automaten mit Coins"
)
async def slots(
    interaction: discord.Interaction,
    einsatz: int
):
    user_id = str(interaction.user.id)

    if einsatz <= 0:
        await interaction.response.send_message(
            "❌ Der Einsatz muss mindestens 1 Coin betragen."
        )
        return

    if user_id not in geld:
        geld[user_id] = 100

    if geld[user_id] < einsatz:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug Coins. "
            f"Du hast **{geld[user_id]} Coins**."
        )
        return

    symbole = [
        "🍒",
        "🍋",
        "⭐",
        "🔔",
        "💎"
    ]

    # Einsatz wird zuerst abgezogen.
    geld[user_id] -= einsatz

    ergebnis = [
        random.choice(symbole),
        random.choice(symbole),
        random.choice(symbole)
    ]

    if (
        ergebnis[0]
        == ergebnis[1]
        == ergebnis[2]
    ):
        multiplikator = 5
        gewinn = einsatz * multiplikator
        ergebnis_text = (
            f"🎉 JACKPOT! Du gewinnst **{gewinn} Coins**!"
        )

    elif (
        ergebnis[0] == ergebnis[1]
        or ergebnis[1] == ergebnis[2]
        or ergebnis[0] == ergebnis[2]
    ):
        multiplikator = 2
        gewinn = einsatz * multiplikator
        ergebnis_text = (
            f"🎉 Zwei gleiche Symbole! "
            f"Du gewinnst **{gewinn} Coins**!"
        )

    else:
        gewinn = 0
        ergebnis_text = (
            f"❌ Kein Gewinn – du verlierst "
            f"**{einsatz} Coins**."
        )

    geld[user_id] += gewinn
    speichere_json("geld.json", geld)

    await interaction.response.send_message(
        f"🎰 **Automat**\n\n"
        f"{' | '.join(ergebnis)}\n\n"
        f"💰 Einsatz: **{einsatz} Coins**\n"
        f"{ergebnis_text}\n"
        f"💰 Guthaben: **{geld[user_id]} Coins**"
    )


# =========================
# BLACKJACK MIT GELD-EINSATZ
# =========================

kartenspiele = {}


def neue_karte():
    karten = [
        ("A", 11),
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
    ]

    return random.choice(karten)


def kartenwert(hand):
    wert = sum(
        karte[1]
        for karte in hand
    )

    asse = sum(
        1
        for karte in hand
        if karte[0] == "A"
    )

    while wert > 21 and asse > 0:
        wert -= 10
        asse -= 1

    return wert


def hand_text(hand):
    return " ".join(
        f"`{karte[0]}`"
        for karte in hand
    )


@bot.tree.command(
    name="blackjack",
    description="Starte Blackjack mit einem Coin-Einsatz"
)
async def blackjack(
    interaction: discord.Interaction,
    einsatz: int
):
    user_id = str(interaction.user.id)

    if einsatz <= 0:
        await interaction.response.send_message(
            "❌ Der Einsatz muss mindestens 1 Coin betragen."
        )
        return

    if user_id in kartenspiele:
        await interaction.response.send_message(
            "❌ Du hast bereits eine laufende Runde."
        )
        return

    if user_id not in geld:
        geld[user_id] = 100

    if geld[user_id] < einsatz:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug Coins. "
            f"Du hast **{geld[user_id]} Coins**."
        )
        return

    # Einsatz wird beim Start der Runde abgezogen.
    geld[user_id] -= einsatz
    speichere_json("geld.json", geld)

    spieler = [
        neue_karte(),
        neue_karte()
    ]

    dealer = [
        neue_karte(),
        neue_karte()
    ]

    kartenspiele[user_id] = {
        "spieler": spieler,
        "dealer": dealer,
        "einsatz": einsatz
    }

    # Sofortiger Blackjack: 3:2 Auszahlung.
    if kartenwert(spieler) == 21:
        kartenspiele.pop(user_id, None)
        gewinn = einsatz + (einsatz * 3 // 2)
        geld[user_id] += gewinn
        speichere_json("geld.json", geld)

        await interaction.response.send_message(
            f"🃏 **Blackjack!**\n\n"
            f"Deine Karten: {hand_text(spieler)}\n"
            f"Wert: **21**\n\n"
            f"🎉 Auszahlung: **{gewinn} Coins**\n"
            f"💰 Guthaben: **{geld[user_id]} Coins**"
        )
        return

    await interaction.response.send_message(
        f"🃏 **Blackjack**\n\n"
        f"💰 Einsatz: **{einsatz} Coins**\n\n"
        f"Deine Karten: {hand_text(spieler)}\n"
        f"Wert: **{kartenwert(spieler)}**\n\n"
        f"Dealer: `{dealer[0][0]}` + ❓\n\n"
        f"Nutze `/hit` oder `/stand`."
    )


@bot.tree.command(
    name="hit",
    description="Ziehe eine weitere Karte"
)
async def hit(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    if user_id not in kartenspiele:
        await interaction.response.send_message(
            "❌ Du hast keine laufende Runde."
        )
        return

    spiel = kartenspiele[user_id]

    karte = neue_karte()
    spiel["spieler"].append(karte)

    wert = kartenwert(spiel["spieler"])

    if wert > 21:

        einsatz = spiel["einsatz"]
        kartenspiele.pop(user_id, None)

        await interaction.response.send_message(
            f"💥 Deine Karten: "
            f"{hand_text(spiel['spieler'])}\n"
            f"Wert: **{wert}**\n\n"
            f"❌ Du bist über 21 und verlierst "
            f"**{einsatz} Coins**.\n"
            f"💰 Guthaben: **{geld.get(user_id, 0)} Coins**"
        )

        return

    await interaction.response.send_message(
        f"🃏 Du ziehst eine Karte.\n\n"
        f"Deine Karten: "
        f"{hand_text(spiel['spieler'])}\n"
        f"Wert: **{wert}**\n\n"
        f"💰 Einsatz: **{spiel['einsatz']} Coins**"
    )


@bot.tree.command(
    name="stand",
    description="Beende deine Blackjack-Runde"
)
async def stand(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    if user_id not in kartenspiele:
        await interaction.response.send_message(
            "❌ Du hast keine laufende Runde."
        )
        return

    spiel = kartenspiele.pop(user_id)

    spieler = spiel["spieler"]
    dealer = spiel["dealer"]
    einsatz = spiel["einsatz"]

    spieler_wert = kartenwert(spieler)

    while kartenwert(dealer) < 17:
        dealer.append(neue_karte())

    dealer_wert = kartenwert(dealer)

    auszahlung = 0

    if spieler_wert > 21:
        ergebnis = (
            f"❌ Du bist über 21 und verlierst "
            f"**{einsatz} Coins**."
        )

    elif dealer_wert > 21:
        auszahlung = einsatz * 2
        ergebnis = (
            f"🎉 Der Dealer ist über 21 – "
            f"du bekommst **{auszahlung} Coins**!"
        )

    elif spieler_wert > dealer_wert:
        auszahlung = einsatz * 2
        ergebnis = (
            f"🎉 Du gewinnst – "
            f"du bekommst **{auszahlung} Coins**!"
        )

    elif spieler_wert == dealer_wert:
        auszahlung = einsatz
        ergebnis = (
            f"🤝 Unentschieden – dein Einsatz von "
            f"**{einsatz} Coins** wird zurückgegeben."
        )

    else:
        ergebnis = (
            f"❌ Der Dealer gewinnt. Du verlierst "
            f"**{einsatz} Coins**."
        )

    geld[user_id] = geld.get(user_id, 0) + auszahlung
    speichere_json("geld.json", geld)

    await interaction.response.send_message(
        f"🃏 **Runde beendet**\n\n"
        f"💰 Einsatz: **{einsatz} Coins**\n\n"
        f"Deine Karten: {hand_text(spieler)}\n"
        f"Dein Wert: **{spieler_wert}**\n\n"
        f"Dealer: {hand_text(dealer)}\n"
        f"Dealer-Wert: **{dealer_wert}**\n\n"
        f"{ergebnis}\n"
        f"💰 Guthaben: **{geld[user_id]} Coins**"
    )


# =========================
# HILFE
# =========================

@bot.tree.command(
    name="hilfe",
    description="Zeigt alle Bot-Befehle"
)
async def hilfe(interaction: discord.Interaction):

    text = (
        "🤖 **Bot-Befehle**\n\n"
        "🇩🇪 `/flaggen` – Flaggen-Quiz\n"
        "🛑 `/beenden` – Quiz beenden\n"
        "🏆 `/leaderboard` – Punkte-Rangliste\n"
        "⭐ `/punkte` – Punkte anzeigen\n"
        "💰 `/geld` – Coins anzeigen\n"
        "🎁 `/daily` – Daily-Coins\n"
        "💰 `/geldrangliste` – Coin-Rangliste\n"
        "🎰 `/slots <einsatz>` – Slots mit Coins spielen\n"
        "🃏 `/blackjack <einsatz>` – Blackjack mit Coins spielen\n"
        "➕ `/hit` – Karte ziehen\n"
        "🛑 `/stand` – Runde beenden\n"
    )

    await interaction.response.send_message(text)


# =========================
# COUNTING
# =========================

counting_aktuell = 1
counting_letzter_user = None


@bot.event
async def on_message(message):

    global counting_aktuell
    global counting_letzter_user

    if message.author.bot:
        return

    user_id = str(message.author.id)

    # -------------------------
    # FLAGGEN-QUIZ
    # -------------------------

    if user_id in quiz_aktiv:

        antwort = message.content.strip().lower()

        if antwort == quiz_antwort.get(user_id):

            punkte[user_id] = (
                punkte.get(user_id, 0) + 1
            )

            speichere_json(
                "scores.json",
                punkte
            )

            quiz_aktiv.pop(user_id, None)
            quiz_antwort.pop(user_id, None)

            await message.channel.send(
                f"✅ **Richtig, "
                f"{message.author.display_name}!**\n"
                f"⭐ +1 Punkt\n"
                f"⭐ Du hast jetzt "
                f"**{punkte[user_id]} Punkte**."
            )

        return

    # -------------------------
    # COUNTING
    # -------------------------

    if message.channel.id == COUNTING_CHANNEL_ID:

        try:
            zahl = int(message.content.strip())
        except ValueError:
            return

        if (
            zahl == counting_aktuell
            and counting_letzter_user
            != message.author.id
        ):

            counting_aktuell += 1
            counting_letzter_user = message.author.id

            punkte[user_id] = (
                punkte.get(user_id, 0) + 1
            )

            speichere_json(
                "scores.json",
                punkte
            )

            await message.add_reaction("✅")

        elif zahl == counting_aktuell:

            await message.add_reaction("❌")

            await message.channel.send(
                "❌ Du kannst nicht zweimal "
                "hintereinander zählen."
            )

        return

    await bot.process_commands(message)


# =========================
# WEB SERVER FÜR RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)
        self.end_headers()

        self.wfile.write(
            b"Discord Bot is running!"
        )

    def log_message(self, format, *args):
        return


def starte_webserver():

    port = int(
        os.getenv("PORT", "10000")
    )

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"Webserver laeuft auf Port {port}"
    )

    server.serve_forever()


threading.Thread(
    target=starte_webserver,
    daemon=True
).start()


# =========================
# BOT START
# =========================

@bot.event
async def on_ready():

    guild = discord.Object(
        id=SERVER_ID
    )

    try:

        bot.tree.copy_global_to(
            guild=guild
        )

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
            f"Counting-Kanal: "
            f"{COUNTING_CHANNEL_ID}"
        )

    except Exception as e:

        print(
            f"Fehler beim Synchronisieren: {e}"
        )


bot.run(TOKEN)
