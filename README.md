# 🤖 KINGPARTHH Bot

A comprehensive, production-ready Telegram bot with AI capabilities, RAG system, and multiple useful features.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20+-green)

## 📋 Features

| Feature | Description |
|---------|-------------|
| **AI Chat** | Intelligent conversation with memory and context |
| **News Search** | Search and browse current news via GNews API |
| **Fact Check** | Verify claims using Google Fact Check API |
| **OCR** | Extract text from images using Google Cloud Vision |
| **PDF Summary** | Summarize and extract text from PDF documents |
| **Web Research** | Deep research on any topic using Tavily API |
| **Website Summarizer** | Extract and summarize website content |
| **YouTube Summary** | Get summaries of YouTube videos |
| **Coding Assistant** | Explain, review, and generate code |
| **RAG System** | Personal knowledge base with semantic search |
| **Memory System** | Persistent conversation history per user |
| **Premium System** | Daily limits with premium user support |

## 🏗️ Architecture

```
telegram-super-bot/
├── bot.py                 # Main entry point
├── handlers/              # Command handlers
│   ├── ai.py             # AI chat handler
│   ├── news.py           # News search handler
│   ├── factcheck.py     # Fact check handler
│   ├── ocr.py            # OCR handler
│   ├── pdf.py            # PDF handler
│   ├── research.py       # Web research handler
│   ├── website.py        # Website handler
│   ├── youtube.py        # YouTube handler
│   ├── code.py           # Coding assistant
│   └── ask.py            # RAG/knowledge base
├── services/             # Business logic
│   ├── llm_service.py    # OpenAI/LLM integration
│   ├── vector_db.py     # FAISS vector database
│   ├── memory.py        # Conversation memory
│   └── utils.py         # Utility functions
├── database/             # Database layer
│   └── db.py            # SQLite operations
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## 🚀 Quick Setup

### 1. Prerequisites

- Python 3.11 or higher
- Telegram Bot Token
- API keys for desired features

### 2. Clone and Install

```bash
# Clone or navigate to the project
cd telegram-super-bot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
BOT_TOKEN=your_telegram_bot_token

# LLM Configuration (supports OpenAI, Anthropic, Ollama, etc.)
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-3.5-turbo

# Optional APIs (enable features you want)
GNEWS_API_KEY=your_gnews_api_key
GOOGLE_FACT_CHECK_API_KEY=your_google_fact_check_api_key
TAVILY_API_KEY=your_tavily_api_key
GOOGLE_CLOUD_VISION_API_KEY=your_google_cloud_vision_api_key

# Premium Configuration
PREMIUM_DAILY_LIMIT=10
PREMIUM_USER_IDS=123456789,987654321
```

### 4. Get API Keys

| Service | How to Get | Required For |
|---------|------------|--------------|
| **Telegram Bot** | @BotFather on Telegram | ✅ Required |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | ✅ Required |
| **GNews** | [gnews.io](https://gnews.io) | News feature |
| **Tavily** | [tavily.com](https://tavily.com) | Research feature |
| **Google Cloud Vision** | [console.cloud.google.com](https://console.cloud.google.com) | OCR feature |
| **Google Fact Check** | [developers.google.com](https://developers.google.com/fact-check) | Fact check |

### 5. Run the Bot

```bash
# Run locally
python bot.py
```

The bot should now be live on Telegram!

## 📖 Command Reference

### AI & Chat
| Command | Description |
|---------|-------------|
| `/ai <message>` | Chat with AI |
| `<message>` | Just send a message to chat |
| `/clear` | Clear conversation memory |
| `/usage` | Check daily usage |

### News
| Command | Description |
|---------|-------------|
| `/news <topic>` | Search for news |
| `/topnews` | Get top headlines |
| `/topic <name>` | News by topic |

### Research & Fact Check
| Command | Description |
|---------|-------------|
| `/research <topic>` | Web research |
| `/deepsearch <topic>` | In-depth research |
| `/factcheck <claim>` | Verify a claim |

### Document Processing
| Command | Description |
|---------|-------------|
| Send PDF | Summarize PDF |
| `/pdfurl <url>` | Summarize PDF from URL |
| `/extract <url>` | Extract text from website |
| `/website <url>` | Summarize website |

### YouTube
| Command | Description |
|---------|-------------|
| `/youtube <url>` | Summarize video |
| `/transcript <url>` | Get video transcript |

### Coding
| Command | Description |
|---------|-------------|
| `/explain <code>` | Explain code |
| `/review <code>` | Code review |
| `/code <description>` | Generate code |
| `/helpcode <topic>` | Coding help |

### Knowledge Base (RAG)
| Command | Description |
|---------|-------------|
| `/addkb <content>` | Add to knowledge base |
| `/ask <question>` | Ask using knowledge |
| `/mykb` | View knowledge base |
| `/searchkb <query>` | Search knowledge |
| `/clearkb` | Clear knowledge base |

## 🏢 Deployment

### Deploying to a Server

1. **Using Systemd (Linux)**

```bash
# Create systemd service
sudo nano /etc/systemd/system/telegram-bot.service
```

```ini
[Unit]
Description=KINGPARTHH Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-super-bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/path/to/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start the service
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot
```

2. **Using Docker**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t telegram-bot .
docker run -d --name telegram-bot \
  -e BOT_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  telegram-bot
```

3. **Using PM2 (Node.js process manager for Python)**

```bash
pip install pm2
pm2 start bot.py --name telegram-bot
pm2 save
pm2 startup
```

### Cloud Platforms

- **Railway**: Easy deployment with environment variables
- **Render**: Free tier available
- **Fly.io**: Good for long-running bots
- **Heroku**: Classic deployment option

## 💎 Premium System

The bot includes a premium system with daily limits:

- **Free Users**: 10 AI queries per day
- **Premium Users**: Unlimited queries

To set premium users, add user IDs to `PREMIUM_USER_IDS` in `.env`:

```env
PREMIUM_USER_IDS=123456789,987654321
```

Or manage programmatically using database functions.

## 🔧 Configuration

### Changing Daily Limits

```env
PREMIUM_DAILY_LIMIT=20  # Change from 10 to 20
```

### Using Different LLM Providers

**Anthropic (Claude):**
```env
OPENAI_BASE_URL=https://api.anthropic.com
LLM_MODEL_NAME=claude-3-sonnet-20240229
```

**Ollama (Local):**
```env
OPENAI_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama2
```

**Azure OpenAI:**
```env
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions
OPENAI_API_KEY=your_azure_key
```

## 🐛 Troubleshooting

### Bot not responding?
1. Check `BOT_TOKEN` is correct
2. Run `python bot.py` and check for errors
3. Make sure bot has privacy mode disabled (@BotFather → /BotSettings)

### OCR not working?
1. Verify `GOOGLE_CLOUD_VISION_API_KEY` is set
2. Check the image has clear text

### News not working?
1. Verify `GNEWS_API_KEY` is set
2. Check API quota limits

### LLM errors?
1. Verify `OPENAI_API_KEY` is correct
2. Check `OPENAI_BASE_URL` matches your provider
3. Ensure `LLM_MODEL_NAME` is valid

## 📝 Logging

Logs are printed to stdout. To save to file:

```bash
python bot.py > bot.log 2>&1
```

## 🔐 Security Notes

- Never commit `.env` file to version control
- Keep API keys secure
- The bot only stores user messages locally
- No data is sent to third parties except for API calls

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - Feel free to use and modify!

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [OpenAI](https://openai.com)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://sbert.net)

---

Made with ❤️ for Telegram bots!
