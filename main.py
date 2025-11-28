import os
import re
from urllib.parse import urlparse

import discord
from discord.ext import commands

# ================== CONFIG TOKEN ==================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Token belum diisi. Set DISCORD_BOT_TOKEN di environment variables.")


# ================== INTENTS ==================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== BLOCK LIST ==================
BLOCKED_DOMAINS = {
    "hyperliquid-tracer.xyz",
    "hyperliquid-crypto.web.app",
    "hyperliquid-trace.web.app",
    "hyperliquid-leaderboard.xyz",
    "hyperliquid-tracking.xyz",
    "hyperliquid-portfolio.com",
    "hyperliquid-portfolio.xyz",
    "hyperliquid-tracer.com",
    "hyperliquid-trace.com",
    "hyperliquid-trace.xyz",
}

SUSPICIOUS_TLDS = {
    "xyz",
    "com",
    "app",
    "web.app",
    "net",
    "site",
    "online",
}

URL_REGEX = re.compile(r"https?://[^\s>]+", re.IGNORECASE)
PLAIN_DOMAIN_REGEX = re.compile(r"hyperliquid-[a-z0-9\-]+\.[a-z.]+",
                                re.IGNORECASE)


def normalize_domain(domain: str) -> str:
    domain = domain.lower().strip()
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def domain_is_suspicious(domain: str) -> bool:
    domain = normalize_domain(domain)

    # 1) Cocok list hitam
    if domain in BLOCKED_DOMAINS:
        return True

    # 2) Domain resmi hyperliquid tanpa strip, jangan blok
    if domain.startswith(
            "hyperliquid.") and not domain.startswith("hyperliquid-"):
        return False

    # 3) Pola hyperliquid-[apapun].[tld mencurigakan]
    if domain.startswith("hyperliquid-"):
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith("." + tld):
                return True

    return False


def message_contains_bad_link(content: str) -> bool:
    # Cek URL dengan http/https
    for url in URL_REGEX.findall(content):
        parsed = urlparse(url)
        domain = normalize_domain(parsed.netloc)
        if domain_is_suspicious(domain):
            return True

    # Cek domain polos tanpa http
    for match in PLAIN_DOMAIN_REGEX.findall(content):
        domain = normalize_domain(match)
        if domain_is_suspicious(domain):
            return True

    return False


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot anti-hyperliquid scam sudah aktif.")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message_contains_bad_link(message.content):
        try:
            await message.delete()
            print(
                f"Deleted message from {message.author} in #{message.channel} karena link scam."
            )
        except discord.Forbidden:
            print(
                "Gagal hapus pesan: bot tidak punya permission Manage Messages."
            )
        except discord.HTTPException as e:
            print(f"Gagal hapus pesan karena error HTTP: {e}")
        return

    await bot.process_commands(message)


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    await ctx.send("Bot anti-hyperliquid scam aktif ✅")


bot.run(TOKEN)
