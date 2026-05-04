# 🎙️ Discord Voice XP Bot

A gamified voice experience bot for Discord that rewards users for spending time in voice channels.

## ✨ Features

- 📊 Track voice activity and earn XP
- 🔥 Daily streaks and multipliers
- ⏰ Time-based bonuses (morning, night, weekend)
- 📢 Channel type multipliers
- 🏆 Leaderboards (all-time, weekly, monthly)
- 📋 Daily/Weekly quests
- 🎖️ Achievements and titles
- 👑 Level roles and rewards

## 🚀 Commands

| Command | Description |
|---------|-------------|
| `/voice` | View your XP stats |
| `/leaderboard` | View all-time leaderboard |
| `/top-weekly` | View weekly leaderboard |
| `/top-monthly` | View monthly leaderboard |
| `/multipliers` | Show active XP bonuses |
| `!test` | Test if bot is responding |

### Admin Commands

| Command | Description |
|---------|-------------|
| `!give-xp @user 100` | Give XP to a user |
| `!reset-xp @user` | Reset a user's XP |
| `!xp-config` | View/change settings |

## 🛠️ Setup

### Local Development

1. Clone the repository
2. Create `.env` file with `DISCORD_TOKEN=your_token`
3. Run `pip install -r requirements.txt`
4. Run `python main.py`

### Deploy to Render

1. Push to GitHub
2. Connect repository to Render
3. Add `DISCORD_TOKEN` environment variable
4. Deploy!

## 📋 Requirements

- Python 3.11+
- Discord Bot Token
- Discord Bot with Intents:
  - Server Members Intent
  - Message Content Intent
  - Voice States Intent

## 📄 License

MIT License