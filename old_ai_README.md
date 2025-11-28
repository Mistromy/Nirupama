# Nirupama Discord Bot

![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![Issues](https://img.shields.io/github/issues/Mistromy/Nirupama)
![Last Commit](https://img.shields.io/github/last-commit/Mistromy/Nirupama)


<p align="center"><img src="https://socialify.git.ci/Mistromy/Nirupama/image?custom_description=Fun+Util+Discord+bot+with+AI&amp;description=1&amp;font=Raleway&amp;forks=1&amp;language=1&amp;name=1&amp;owner=1&amp;pattern=Circuit+Board&amp;stargazers=1&amp;theme=Dark" alt="project-image"></p>

## Planned Features / Ideas
- Add Server Moderation Features, such as report button on messages that send report to mod channel and allows to easily perform moderation tasks, or automate them based on report amount or frequencey

- Toggle AI Personality To be more funny or useful.
- Give the ai memory.
- Let it see the message that is being responded to.

# Enhanced Discord Bot with AI Tool System


## 🆕 New Features

### Core Tool System
- **Code Detection & Upload**: AI can wrap code in `{code:filename.py}...{endcode}` tags
- **Multiple File Support**: Support for multiple files in one message
- **Configurable Code Retention**: Global setting + per-message overrides with `{code:filename.py:keep}` or `{code:filename.py:remove}` 
- **Automatic File Upload**: Code is automatically uploaded to Discord as files

### Enhanced Logging System
- **Complete Rewrite**: New logging system that works as "print with extra parameters"
- **Color Support**: Easy color specification in `bot_log()` function calls
- **Discord Integration**: All console messages are sent to Discord channel
- **Message Splitting**: Proper handling of messages over 2000 characters
- **Error Handling**: Graceful error handling throughout the system

### Scalable Tool Infrastructure
- **Tool Processor Class**: Modular system for easy tool addition
- **Multiple Tool Support**:
  - `{code:filename.py}...{endcode}` - Upload code as file
  - `{react:😀}` - Add reactions
  - `{tenor:search_term}` - Send GIFs (placeholder)
  - `{aiimage:description}` - Generate AI images (placeholder)
  - `{localimage:filename}` - Send local images
  - `{newmessage}` - Split into multiple messages
- **Parameter Support**: All tools support parameters in `{tool:parameter}` format

### Conversation History System
- **Three Modes**: Separate users, unified, or off
- **Persistent Storage**: SQLite database for conversation history
- **Context Integration**: History context is added to AI prompts
- **Token Optimization**: Built-in structure for message summarization
- **Management Commands**: `/history_mode_cmd` and `/clear_history`

### Enhanced Message Splitting
- **Smart Splitting**: Preserves code blocks and formatting
- **File Attachment**: Files are attached to the "last chunk with text"
- **{newmessage} Tool**: Manual message breaks supported
- **Empty Chunk Handling**: Skips empty message chunks automatically

## 🔧 New Commands

- `/keep_code [true/false]` - Control global code retention setting
- `/history_mode_cmd [mode]` - Set history mode (separate/unified/off)
- `/clear_history` - Clear conversation history

## 🛠️ Technical Improvements

### Logging Enhancements
```python
# Enhanced logging with colors and better formatting
bot_log("Message", level=logging.INFO, command="test", color="green")

# Multiple color options available
bot_log("Error occurred", level=logging.ERROR, color="red")
bot_log("Debug info", level=logging.DEBUG, color="cyan")
```

### Tool System Example
```python
# AI can now use tools like this:
# {code:example.py}
# def hello_world():
#     print("Hello, World!")
# {endcode}

# {react:👍}  # Adds reaction
# {newmessage}  # Splits into new message
```

### History Integration
The bot now maintains conversation context across messages, with three different modes:
- **Separate**: Per-user conversation history
- **Unified**: All users in one shared context
- **Off**: No history tracking

## 📁 File Structure

- `logging_setup_enhanced.py` - Complete rewrite of logging system
- `bot_enhanced.py` - Enhanced bot with all new features
- `conversation_history.db` - SQLite database for history (auto-created)
- `README.md` - This documentation

## 🚀 Usage

1. Replace your current `logging_setup.py` with `logging_setup_enhanced.py`
2. Replace your current `bot.py` with `bot_enhanced.py`
3. The bot will automatically create the history database on first run

## 🔧 Configuration

### Global Settings
- `keep_code_in_message` - Whether to keep code in messages after file upload
- `history_mode` - Conversation history mode
- All existing AI settings (temperature, model, personality, etc.)

### Tool System
The tool processor is modular and easily extensible. To add new tools:
1. Add regex pattern in `process_tools()` method
2. Add tool description to `Tools` dictionary
3. Implement tool functionality

## 🐛 Error Handling

- Enhanced error handling throughout the system
- Graceful fallbacks for missing files, failed reactions, etc.
- Proper Discord permission handling
- Console and Discord logging of all errors

## 📋 Requirements

All existing requirements plus:
- `sqlite3` (built-in with Python)

## 🔄 Backward Compatibility

All existing functionality is preserved:
- Ship command
- 8Ball command
- AI personalities and settings
- Git commands
- All existing slash commands

The enhanced system is fully backward compatible while adding powerful new features for AI tool integration and better logging.

### Ship command Modifiers
- Current activity
- server join date
- account creation date
- current status
- roles on server
- nickname similarities (how many characters in strings are similar)
- message count
