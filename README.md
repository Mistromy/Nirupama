# Nirupama Discord Bot

![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![GitHub go.mod Go version (branch)](https://img.shields.io/github/go-mod/go-version/mistromy/Nirupama/go?filename=go%2Fmain%2Fgo.mod&style=flat&logo=go)
![Issues](https://img.shields.io/github/issues/Mistromy/Nirupama)
![Last Commit](https://img.shields.io/github/last-commit/Mistromy/Nirupama)

<p align="center"><img src="https://socialify.git.ci/Mistromy/Nirupama/image?custom_description=Fun+Util+Discord+bot+with+AI&amp;description=1&amp;font=Raleway&amp;forks=1&amp;language=1&amp;name=1&amp;owner=1&amp;pattern=Circuit+Board&amp;stargazers=1&amp;theme=Dark" alt="project-image" width="66%"></p>

A versatile Discord bot with AI capabilities, fun utilities, and server management features. Nirupama combines personality-driven AI interactions with practical Discord tools to enhance your server experience.

---

## ✨ Features

### 🤖 AI Integration
- **Multiple AI Models**: Support for Gemini 2.5 Pro, Flash, and Flash Lite
- **Customizable Personalities**: Choose from Discord-friendly, helpful assistant, coder, Shakespeare, pirate, Yoda, and more
- **Thinking Modes**: Dynamic, Fast, Balanced, and Deep thinking for varied response quality
- **Conversation History**: Separate per-user or unified server-wide conversation tracking
- **Advanced Tool System**: AI can use multiple tools including:
  - Code file generation and sharing
  - Emoji reactions
  - GIF search via Tenor
  - AI image generation
  - Local image sharing
  - Multi-message responses

### 🎮 Fun Commands
- **Ship Command**: Calculate compatibility between users with visual results
- **8Ball**: Ask the magic 8ball for wisdom
- **Tone Analysis**: Analyze the tone of messages (with a humorous twist)

### 🔧 Utility Features
- **Enhanced Logging**: Comprehensive logging system with Discord channel integration
- **Cog-based Architecture**: Modular design for easy feature management
- **Git Integration**: Pull updates directly from GitHub
- **Dynamic Settings**: Adjust AI behavior on the fly
- **Debug Mode**: Detailed information about AI responses and settings

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Discord Bot Token
- Google AI API Key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mistromy/Nirupama.git
   cd Nirupama
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   CRASH_WEBHOOK_URL = ""
   BOT_TOKEN = ""
   OPENROUTER_API_KEY = ""
   SUPABASE_URL = ""
   SUPABASE_KEY = ""
   PERPLEXITY_API_KEY = ""
   GROQ_API_KEY = ""
   CRONITOR_API_KEY = ""
   ```

4. **Run the bot**
   Linux:
   ```bash
   ./Nirupama
   ```
   
   Windows:
   ```bash
   Nirupama.exe
   ```

---

## 📖 Usage

### Basic Commands

#### Fun & Utility
- `/ship @user1 @user2` - Check compatibility between two users
- `/eightball [question]` - Ask the Magic 8Ball a question
- `/tone [message]` - Analyze the tone of a message
- `/help` - Display all available commands

#### AI Configuration (Admin Only)
- `/personality [type]` - Set AI personality (Discord, Coder, Shakespeare, etc.)
- `/thinkmode [mode]` - Set thinking mode (Off, Dynamic, Fast, Balanced, Deep)
- `/model [type]` - Choose AI model (Pro, Flash, Flash Lite)
- `/temperaturevalue [0-2]` - Adjust response randomness
- `/preset [name]` - Apply predefined AI configuration presets
- `/tools` - Enable/disable AI tools via interactive menu
- `/settings` - View current AI configuration

#### History Management (Admin Only)
- `/history_mode_cmd [mode]` - Set history mode (separate, unified, off)
- `/clear_history` - Clear conversation history

#### Bot Management (Admin Only)
- `/reboot` - Restart the bot
- `/gitpull` - Update bot from GitHub
- `/kill` - Stop the bot process

### AI Interaction

Mention the bot to interact with AI:
```
@Nirupama what's the weather like today?
```

The AI can process images and text files when attached to your message!

---

## 🗺️ Roadmap

### 🔨 High Priority Fixes

#### System Improvements
- [ ] **Fix Discord logging file limit** - Optimize log rotation and storage
- [ ] **Consolidate settings into `/settings` command** - Centralize all configuration
- [ ] **Fix online status** - Ensure status changes back to yellow/idle correctly
- [ ] **Fix all tools** - Debug and repair react, tenor, and other tool integrations

#### AI Tool Enhancements
- [ ] **Improve Tenor tool** - Implement two-stage process:
  1. Cheap model searches and analyzes GIFs
  2. Selects best match based on context
  3. Example: "i want a funny gif of someone falling"

### 🎯 Planned Features

#### AI Pipeline Enhancement
Create a sophisticated AI processing pipeline:
1. **Initial Processing** - Cheap model or selected model reads message and decides tool usage
2. **Tool Execution** - Code filters response and runs necessary tools
3. **Feedback Loop** - Results fed back to AI (using cheapest model when possible)
4. **Response Delivery** - AI response sent to user with real-time status updates

#### Ship Command Improvements
- [ ] **AI-powered ship analysis** - Let AI see profile pictures and customize results
- [ ] **Enhanced compatibility factors**:
  - Current activity status
  - Server join date comparison
  - Account creation date
  - Current online status
  - Role similarities
  - Nickname similarity analysis
  - Message count correlation
- [ ] **Display name support** - Use display names instead of usernames

#### Server Moderation
- [ ] **Report System** - Message report button that sends to mod channel
- [ ] **Moderation Tools** - Easy-to-use moderation task interface
- [ ] **Auto-moderation** - Automated actions based on report frequency/count
- [ ] **Mod Dashboard** - Comprehensive moderation overview

#### AI Enhancements
- [ ] **Persistent Memory** - Give AI long-term memory across sessions
- [ ] **Context Awareness** - Allow AI to see messages being replied to
- [ ] **Personality Toggle** - Quick switch between funny and utility-focused modes
- [ ] **Embed Support** - Create rich embedded messages for better formatting

### 🔄 Developer Features
- [ ] **Auto-update Button** - Automatically pull from Git and restart necessary cogs
- [ ] **Hot-reload Cogs** - Reload individual cogs without full restart
- [ ] **Configuration UI** - Web-based configuration interface

---

## 🏗️ Architecture

### Project Structure
```
Nirupama/
├── code/
│   ├── main.py              # Bot entry point
│   ├── launch.py            # Bot launcher with auto-restart
│   ├── cogs/                # Modular command groups
│   ├── utils/               # Utility functions and helpers
│   └── data/                # Data storage
├── archive/                 # Legacy bot versions
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Technology Stack
- **Discord.py (py-cord)** - Discord API wrapper
- **Google Gemini AI** - AI model integration
- **PIL/Pillow** - Image processing for ship command
- **aiohttp** - Asynchronous HTTP requests
- **SQLite** - Conversation history storage

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow existing code style and conventions
- Test your changes thoroughly
- Update documentation as needed
- Keep commits focused and descriptive

---

## 📝 License

This project is open source and available for personal and educational use.

---

## 🙏 Credits

- **Developer**: [Mistromy](https://github.com/Mistromy)
- **AI Models**: Google Gemini API
- **Discord Library**: Pycord

---

## 📞 Support

For issues, questions, or suggestions:
- Open an [issue](https://github.com/Mistromy/Nirupama/issues)
- Check existing issues before creating new ones
- Provide detailed information for bug reports

---

<p align="center">Made with ❤️ for Discord communities</p>
