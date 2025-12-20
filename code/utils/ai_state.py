from data.ai_data import PERSONALITIES, TOOLS, THINKING_MODES, MODELS, PRESETS

class AIStateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIStateManager, cls).__new__(cls)
            cls._instance._init_defaults()
        return cls._instance

    def _init_defaults(self):
        # Default Settings
        self.temperature = 1.0
        self.debug_mode = False
        self.history_mode = "off"
        self.enabled_tools = []
        
        self.current_personality_name = "Discord"
        self.current_thinking_mode = THINKING_MODES["Dynamic"]
        self.current_model = MODELS["DolphinV"]

    @property
    def system_prompt(self):
        base = "You're a discord bot. Your user ID is 1209887142839586876. Use Discord markdown formatting. Act like the user, adapting to their behavior. Keep your answers short, avoid punctiuation and emojis. "
        personality = PERSONALITIES.get(self.current_personality_name, "")
        
        # Only send enabled tools
        enabled_strings = [TOOLS[t] for t in self.enabled_tools if t in TOOLS]
        tools_text = str(enabled_strings)
        
        return f"{base} {personality} Tools: {tools_text}"

    def apply_preset(self, preset_name):
        if preset_name in PRESETS:
            p = PRESETS[preset_name]
            self.current_personality_name = p['personality']
            # Safely get thinking mode value
            t_mode = p['thinking']
            self.current_thinking_mode = THINKING_MODES.get(t_mode, 0)
            
            # Safely get model
            m_name = p['model']
            self.current_model = MODELS.get(m_name, "gemini-2.5-flash")
            
            self.temperature = p['temp']
            return True
        return False

# Global instance
ai_state = AIStateManager()