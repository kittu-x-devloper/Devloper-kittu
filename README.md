# Kittu OSINT X — VIP Edition

## Data storage
- **Bot DB (Turso):** users, VIP, credits, contacts, TG↔num, settings, logs
- **External OSINT DBs (VPS/RDP):** max 20 files × 3 GB each

## Run
```bash
pip install -r requirements.txt
# set env or edit bot.py defaults
python3 bot.py
```

## Env
See `.env.example` — especially `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN`.

# Deploy notes (Render)

1. Copy values from the secrets list the assistant gave you into Render **Environment**.
2. Do **not** commit `.env` or real tokens to GitHub.
3. Set at least: `BOT_TOKEN`, `OWNER_ID`, `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `BOT_USERNAME`.

## Role menus
- **Free** — basic OSINT + profile / refer / history / help / VIP upsell
- **Premium** — same + Spin button + VIP card styling
- **Admin** — + Admin Panel
- **Owner** — + Owner Panel (full)

## Menu keyboard
`is_persistent=False` — phone **Back** hides the reply keyboard; open the bot again or send `/start` / any command to show it again.

## Commands only for this bot
Commands like `/x@OtherBot` are ignored. Unknown commands are not answered in groups.

## /cmd
Shows the full command list for your role (owner sees all).
