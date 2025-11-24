from data.ai_data import PERSONALITIES, TOOLS_DEF, THINKING_MODES, MODEL_OPTIONS, PRESETS

class AIStateManager:
    """
    Singleton class to hold the current configuration of the AI in RAM.
    """
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
        
        self.current_personality_name = "Discord 2"
        self.current_thinking_mode = THINKING_MODES["Dynamic"]
        self.current_model = MODEL_OPTIONS["Flash Lite"]

    @property
    def system_prompt(self):
        base = "You're a discord bot. Act like the users. "
        p_text = PERSONALITIES.get(self.current_personality_name, "")
        
        # Only send enabled tools
        enabled_strings = [TOOLS_DEF[t] for t in self.enabled_tools if t in TOOLS_DEF]
        tools_text = str(enabled_strings)
        
        return f"{base} {p_text} Tools: {tools_text}"

    def apply_preset(self, preset_name):
        if preset_name in PRESETS:
            p = PRESETS[preset_name]
            self.current_personality_name = p['personality']
            # Safely get thinking mode value
            t_mode = p['thinking']
            self.current_thinking_mode = THINKING_MODES.get(t_mode, 0)
            
            # Safely get model
            m_name = p['model']
            self.current_model = MODEL_OPTIONS.get(m_name, "gemini-2.5-flash")
            
            self.temperature = p['temp']
            return True
        return False

# Global instance
ai_state = AIStateManager()