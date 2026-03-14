"""
Insights ACH Funding Agent
--------------------------
CLI-based conversational agent that guides customers through ACH account funding.
Uses the Anthropic Claude API with a stateful conversation loop.

Usage:
    python agent.py                  # fresh session
    python agent.py --session <id>   # resume saved session (bonus memory feature)
"""

import json
import os
import sys
import uuid
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

# ---------------------------------------------------------------------------
# Routing-number lookup table (simulated; sources: bank official sites / ABA)
# ---------------------------------------------------------------------------
ROUTING_TABLE: dict = {
    "bank of america": {
        "default":   "026009593",
        "ca":        "121000358",
        "tx":        "026009593",
        "fl":        "063100277",
        "ny":        "021000322",
        "il":        "081904808",
        "ga":        "061000052",
        "nc":        "053000196",
        "az":        "122101706",
        "wa":        "125000024",
        "nj":        "021200339",
    },
    "wells fargo": {
        "default":   "121042882",
        "ca":        "121042882",
        "tx":        "111900659",
        "fl":        "063107513",
        "ny":        "026012881",
        "il":        "071101307",
        "az":        "122105155",
        "wa":        "125008547",
        "co":        "102000076",
        "nv":        "321270742",
    },
    "chase": {
        "default":   "021000021",
        "ca":        "322271627",
        "tx":        "111000614",
        "fl":        "267084131",
        "ny":        "021000021",
        "il":        "071000013",
        "az":        "122100024",
        "wa":        "325070760",
        "co":        "102001017",
        "ga":        "061092387",
    },
    "citibank": {
        "default":   "021000089",
        "ca":        "322271724",
        "tx":        "113193532",
        "fl":        "266086554",
        "ny":        "021000089",
        "il":        "271070801",
        "nv":        "322271724",
    },
    "td bank": {
        "default":   "031101266",
        "ny":        "026013673",
        "fl":        "067014822",
        "nj":        "031201360",
        "pa":        "036001808",
        "ma":        "211370545",
        "ct":        "011600033",
    },
    "regions bank": {
        "default":   "062000019",
        "al":        "062000019",
        "fl":        "063104668",
        "tx":        "113000023",
        "tn":        "064000017",
        "ms":        "065400137",
        "ga":        "061101375",
    },
    "banco popular": {
        "default":   "021502011",
        "ny":        "021502011",
        "fl":        "067010898",
        "nj":        "021202337",
        "pr":        "021502011",
    },
    "bbva usa": {
        "default":   "062001186",
        "tx":        "113010547",
        "al":        "062001186",
        "ca":        "122238420",
        "az":        "122105045",
        "nm":        "107002192",
        "fl":        "063013897",
        "co":        "107002453",
    },
    "suntrust": {
        "default":   "061000104",
        "ga":        "061000104",
        "fl":        "063102152",
        "va":        "055002707",
        "tn":        "064000030",
        "nc":        "053100737",
        "md":        "044000024",
    },
    "truist": {
        "default":   "053101121",
        "ga":        "061000104",
        "fl":        "063102152",
        "va":        "055002707",
        "nc":        "053101121",
        "md":        "044000024",
    },
    "us bank": {
        "default":   "091000022",
        "mn":        "091000022",
        "ca":        "122235821",
        "il":        "071904779",
        "oh":        "042100175",
        "mo":        "081000210",
        "wa":        "125000105",
        "co":        "102101645",
    },
    "pnc bank": {
        "default":   "043000096",
        "pa":        "043000096",
        "oh":        "041000124",
        "nj":        "031207607",
        "md":        "054000030",
        "va":        "054000030",
        "il":        "071921891",
        "fl":        "267084199",
    },
}

STATE_ALIASES: dict = {
    "california": "ca", "texas": "tx", "florida": "fl", "new york": "ny",
    "illinois": "il", "georgia": "ga", "north carolina": "nc", "arizona": "az",
    "washington": "wa", "new jersey": "nj", "colorado": "co", "nevada": "nv",
    "alabama": "al", "tennessee": "tn", "mississippi": "ms", "virginia": "va",
    "maryland": "md", "ohio": "oh", "pennsylvania": "pa", "minnesota": "mn",
    "missouri": "mo", "puerto rico": "pr", "new mexico": "nm",
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are Insights ACH Funding Assistant — a friendly, professional agent for Insights Investment Platform.
Your sole purpose is to help customers fund their Insights investment account via ACH bank transfer.

=== TONE & PERSONA ===
- Warm, clear, concise. Never robotic or overly formal.
- Address the customer by name once you know it; otherwise use "you."
- Never invent information. If unsure, say so and escalate.
- Respond in the same language the user writes in (English or Spanish supported).

=== MANDATORY FIRST STEPS (do NOT skip) ===
Before providing any routing number, ACH instructions, or funding guidance:
1. Ask for the customer's BANK NAME.
2. Ask for the STATE where that bank account is registered.
Only after you have BOTH pieces of information should you call the routing_lookup tool.

=== CONVERSATION FLOW ===

STATE 1 — GREETING & INTENT CONFIRM
  - Greet warmly, introduce yourself.
  - Confirm the customer wants to fund via ACH.

STATE 2 — DATA COLLECTION (in this order, one at a time)
  a. Full legal name (as it appears on bank account)
  b. Bank name
  c. State where bank account is held
  → Call routing_lookup tool after receiving bank + state.
  d. Bank account number
  e. Account type (checking / savings)
  f. Funding amount (USD)

STATE 3 — ROUTING LOOKUP & CONFIRMATION
  - Present routing number from tool.
  - Ask customer to verify with their bank app or checkbook if unsure.

STATE 4 — STEP-BY-STEP FUNDING INSTRUCTIONS
  Step 1: Log in at app.insightsinvest.com
  Step 2: Go to Funding > Add Bank Account
  Step 3: Enter bank name, routing number, account number, account type
  Step 4: Insights sends 2 micro-deposits (< $1 each) within 1-2 business days
  Step 5: Return to Funding > Verify Account, enter both micro-deposit amounts
  Step 6: Go to Fund Account, enter amount, confirm
  Step 7: Funds available in 3-5 business days (Standard ACH) or same day if Same-Day ACH eligible (submit before 1 PM ET)

STATE 5 — CONFIRMATION & WRAP-UP
  - Summarize: name, bank, routing, amount, expected availability.
  - Support: support@insightsinvest.com | 1-800-INSIGHTS

STATE 6 — FAILURE HANDLING
  When customer mentions a failed transfer, match to these codes:

  R01 - Insufficient Funds:
    Say: "Your bank returned code R01 — Insufficient Funds. Your account balance was lower than the transfer amount. Please check your balance and retry with a smaller amount or wait for your next deposit. No fee has been charged to your Insights account."

  R03 - No Account / Unable to Locate:
    Say: "Your bank returned code R03 — Account Not Found. This typically means the account number or routing number was entered incorrectly, or the account has been closed. Please verify both numbers with your bank and re-initiate the transfer. If the problem persists, contact support@insightsinvest.com."

  R02 - Account Closed:
    Say: "Code R02 — Account Closed. Please add a new active bank account under Funding > Add Bank Account."

  R07 - Authorization Revoked:
    Say: "Code R07 — Authorization Revoked. Please contact us at support@insightsinvest.com to re-authorize the transfer."

  Generic failure:
    Acknowledge, summarize, escalate to support@insightsinvest.com | 1-800-INSIGHTS, reference session ID [SESSION_ID].

=== ESCALATION ===
Escalate immediately if: customer frustrated 3+ times, legal/compliance questions, fraud mentioned.
→ "I'm connecting you with a senior support specialist: support@insightsinvest.com | 1-800-INSIGHTS"

=== KNOWLEDGE ===
- Standard ACH: 3-5 business days for funds to be available
- Same-Day ACH: submit before 1 PM ET, available same day, max $1,000,000
- Limits: $50 min, $250,000 max per transaction at Insights
- ACH is reversible within ~60 days for unauthorized debits
- Micro-deposit verification required on first linked account

=== DISCLAIMER ===
Routing numbers are based on published data; always verify with your bank. Insights does not provide tax or legal advice.
"""

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "routing_lookup",
        "description": "Look up the ABA routing number for a given bank and US state. Returns the routing number string or 'not_found'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bank_name": {"type": "string", "description": "Bank name (e.g. 'Bank of America')"},
                "state": {"type": "string", "description": "US state name or abbreviation (e.g. 'Texas' or 'TX')"}
            },
            "required": ["bank_name", "state"]
        }
    }
]

# ---------------------------------------------------------------------------
# Routing lookup
# ---------------------------------------------------------------------------
def routing_lookup(bank_name: str, state: str) -> str:
    bank_key = bank_name.strip().lower()
    state_key = state.strip().lower()
    if len(state_key) > 2:
        state_key = STATE_ALIASES.get(state_key, state_key[:2])

    matched_bank = None
    for k in ROUTING_TABLE:
        if k in bank_key or bank_key in k:
            matched_bank = k
            break
    if not matched_bank:
        return "not_found"

    bank_data = ROUTING_TABLE[matched_bank]
    return bank_data.get(state_key, bank_data.get("default", "not_found"))

# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

def load_session(session_id: str) -> dict:
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"id": session_id, "history": [], "created": datetime.now().isoformat()}

def save_session(session: dict) -> None:
    path = SESSIONS_DIR / f"{session['id']}.json"
    session["updated"] = datetime.now().isoformat()
    path.write_text(json.dumps(session, indent=2))

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "routing_lookup":
        return routing_lookup(tool_input["bank_name"], tool_input["state"])
    return "unknown_tool"

def run_agent(session_id: Optional[str] = None) -> None:
    client = anthropic.Anthropic()

    if session_id:
        session = load_session(session_id)
        if session["history"]:
            print(f"\n[Resuming session {session_id}]\n")
    else:
        session_id = str(uuid.uuid4())[:8]
        session = {"id": session_id, "history": [], "created": datetime.now().isoformat()}

    system = SYSTEM_PROMPT.replace("[SESSION_ID]", session_id)

    print("=" * 60)
    print("  Insights ACH Funding Assistant")
    print(f"  Session ID: {session_id}")
    print("  Type 'exit' to end  |  'history' to review  |  '--session <id>' to resume")
    print("=" * 60)

    if session["history"]:
        print("[Assistant]: Welcome back! Let's continue with your ACH funding request.\n")
    else:
        # Trigger the greeting
        session["history"].append({"role": "user", "content": "Hello, I want to fund my account."})
        messages = session["history"].copy()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=system,
            tools=TOOLS,
            messages=messages,
        )
        greeting = "".join(b.text for b in response.content if hasattr(b, "text"))
        print(f"\nAssistant: {greeting}\n")
        session["history"].append({"role": "assistant", "content": greeting})

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n[Session saved. Goodbye!]")
            save_session(session)
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye", "salir"):
            print("\nAssistant: Thank you for using Insights! Session saved. Your ID is:", session_id)
            save_session(session)
            break

        if user_input.lower() == "history":
            for msg in session["history"]:
                role = "You" if msg["role"] == "user" else "Assistant"
                content = msg["content"] if isinstance(msg["content"], str) else "[tool]"
                print(f"{role}: {content[:100]}")
            continue

        session["history"].append({"role": "user", "content": user_input})
        messages = session["history"].copy()

        while True:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = process_tool_call(block.name, block.input)
                        print(f"\n  [🔍 Lookup: {block.input.get('bank_name')} / {block.input.get('state')} → {result}]")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                assistant_text = "".join(b.text for b in response.content if hasattr(b, "text"))
                print(f"\nAssistant: {assistant_text}")
                session["history"].append({"role": "assistant", "content": assistant_text})
                save_session(session)
                break

def main():
    parser = argparse.ArgumentParser(description="Insights ACH Funding Agent")
    parser.add_argument("--session", type=str, help="Resume existing session by ID")
    args = parser.parse_args()
    run_agent(session_id=args.session)

if __name__ == "__main__":
    main()
