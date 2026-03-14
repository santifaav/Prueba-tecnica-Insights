"""
Insights ACH Funding Bot — Telegram Interface
----------------------------------------------
Corre con: python3 telegram_bot.py
Requiere:  ANTHROPIC_API_KEY y TELEGRAM_BOT_TOKEN en variables de entorno
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import anthropic

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ── Clientes ─────────────────────────────────────────────────────────────────
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# ── Routing table ─────────────────────────────────────────────────────────────
ROUTING_TABLE = {
    "bank of america": {
        "default": "026009593", "ca": "121000358", "tx": "026009593",
        "fl": "063100277", "ny": "021000322", "il": "081904808",
        "ga": "061000052", "nc": "053000196", "az": "122101706",
        "wa": "125000024", "nj": "021200339",
    },
    "wells fargo": {
        "default": "121042882", "ca": "121042882", "tx": "111900659",
        "fl": "063107513", "ny": "026012881", "il": "071101307",
        "az": "122105155", "wa": "125008547", "co": "102000076", "nv": "321270742",
    },
    "chase": {
        "default": "021000021", "ca": "322271627", "tx": "111000614",
        "fl": "267084131", "ny": "021000021", "il": "071000013",
        "az": "122100024", "wa": "325070760", "co": "102001017", "ga": "061092387",
    },
    "citibank": {
        "default": "021000089", "ca": "322271724", "tx": "113193532",
        "fl": "266086554", "ny": "021000089", "il": "271070801",
    },
    "td bank": {
        "default": "031101266", "ny": "026013673", "fl": "067014822",
        "nj": "031201360", "pa": "036001808", "ma": "211370545",
    },
    "regions bank": {
        "default": "062000019", "al": "062000019", "fl": "063104668",
        "tx": "113000023", "tn": "064000017", "ga": "061101375",
    },
    "banco popular": {
        "default": "021502011", "ny": "021502011",
        "fl": "067010898", "nj": "021202337",
    },
    "bbva usa": {
        "default": "062001186", "tx": "113010547", "ca": "122238420",
        "az": "122105045", "fl": "063013897",
    },
    "truist": {
        "default": "053101121", "ga": "061000104", "fl": "063102152",
        "va": "055002707", "nc": "053101121",
    },
    "us bank": {
        "default": "091000022", "ca": "122235821", "il": "071904779",
        "oh": "042100175", "wa": "125000105",
    },
    "pnc bank": {
        "default": "043000096", "pa": "043000096", "oh": "041000124",
        "nj": "031207607", "fl": "267084199",
    },
}

STATE_ALIASES = {
    "california": "ca", "texas": "tx", "florida": "fl", "new york": "ny",
    "illinois": "il", "georgia": "ga", "north carolina": "nc", "arizona": "az",
    "washington": "wa", "new jersey": "nj", "colorado": "co", "nevada": "nv",
    "alabama": "al", "tennessee": "tn", "virginia": "va", "maryland": "md",
    "ohio": "oh", "pennsylvania": "pa", "minnesota": "mn", "missouri": "mo",
}

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are Insights ACH Funding Assistant — a friendly, professional agent for Insights Investment Platform operating via Telegram.
Your sole purpose is to help customers fund their Insights investment account via ACH bank transfer.

=== TONE & PERSONA ===
- Warm, clear, concise. Use emojis sparingly to feel friendly (✅, 🏦, 📋).
- Address the customer by name once you know it.
- Respond in the same language the user writes in (English or Spanish supported).
- Keep responses short and scannable — this is a chat interface.

=== MANDATORY FIRST STEPS (do NOT skip) ===
Before providing any routing number or ACH instructions:
1. Ask for the customer's BANK NAME.
2. Ask for the STATE where that bank account is registered.
Only after you have BOTH should you call the routing_lookup tool.

=== CONVERSATION FLOW ===
STATE 1 — Greet and confirm ACH intent
STATE 2 — Collect in order:
  a. Full legal name
  b. Bank name ← MANDATORY BEFORE ROUTING
  c. State      ← MANDATORY BEFORE ROUTING
  → Call routing_lookup tool
  d. Account number
  e. Account type (checking/savings)
  f. Amount (USD)
STATE 3 — Show routing number, ask to verify
STATE 4 — Step-by-step instructions:
  1. Login at app.insightsinvest.com
  2. Funding → Add Bank Account
  3. Enter routing, account number, type
  4. Wait for 2 micro-deposits (1-2 business days)
  5. Verify micro-deposit amounts
  6. Fund Account → enter amount → confirm
  7. Funds available in 3-5 business days (Standard) or same day (Same-Day ACH before 1PM ET)
STATE 5 — Summary and support info
STATE 6 — Handle failures:
  R01: "Your bank returned R01 — Insufficient Funds. Please check your balance and retry with a smaller amount. No fee charged."
  R03: "Your bank returned R03 — Account Not Found. Please verify your routing and account numbers with your bank and re-initiate the transfer."
  R02: "R02 — Account Closed. Please add a new active bank account."
  Generic: Escalate to support@insightsinvest.com | 1-800-INSIGHTS with session reference.

=== ESCALATION ===
If frustrated 3+ times or legal/fraud questions → escalate immediately to support@insightsinvest.com

=== LIMITS ===
Min: $50 | Max: $250,000 per transaction

=== DISCLAIMER ===
Routing numbers based on published data — always verify with your bank. Insights does not provide tax or legal advice.
"""

TOOLS = [
    {
        "name": "routing_lookup",
        "description": "Look up ABA routing number for a bank and US state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bank_name": {"type": "string"},
                "state": {"type": "string"},
            },
            "required": ["bank_name", "state"],
        },
    }
]

# ── Routing lookup ────────────────────────────────────────────────────────────
def routing_lookup(bank_name: str, state: str) -> str:
    bank_key = bank_name.strip().lower()
    state_key = state.strip().lower()
    if len(state_key) > 2:
        state_key = STATE_ALIASES.get(state_key, state_key[:2])
    for k, v in ROUTING_TABLE.items():
        if k in bank_key or bank_key in k:
            return v.get(state_key, v.get("default", "not_found"))
    return "not_found"

# ── Session storage (in-memory per user) ─────────────────────────────────────
# user_id → list of messages
SESSIONS: dict[int, list[dict]] = {}

def get_history(user_id: int) -> list[dict]:
    return SESSIONS.setdefault(user_id, [])

def save_message(user_id: int, role: str, content):
    SESSIONS.setdefault(user_id, []).append({"role": role, "content": content})

# ── Claude call with tool loop ────────────────────────────────────────────────
async def ask_claude(user_id: int, user_text: str) -> str:
    save_message(user_id, "user", user_text)
    messages = get_history(user_id).copy()

    while True:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = routing_lookup(
                        block.input.get("bank_name", ""),
                        block.input.get("state", ""),
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            assistant_text = "".join(
                b.text for b in response.content if hasattr(b, "text")
            )
            save_message(user_id, "assistant", assistant_text)
            return assistant_text

# ── Telegram handlers ─────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    SESSIONS[user_id] = []  # reset session
    greeting = await ask_claude(user_id, "Hello, I want to fund my account via ACH.")
    await update.message.reply_text(greeting)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    SESSIONS[user_id] = []
    await update.message.reply_text("✅ Session reset. Send /start to begin again.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    reply = await ask_claude(user_id, user_text)
    await update.message.reply_text(reply, parse_mode="Markdown")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("🤖 Insights ACH Bot iniciando...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot corriendo. Abre Telegram y escribe /start")
    app.run_polling()

if __name__ == "__main__":
    main()
    