from data.ai_data import PERSONALITIES, TOOLS, THINKING_MODES, MODELS, PRESETS, PROVIDERS

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
        self.current_provider = "Groq"  # Default to Groq (free and uncensored)
        self.current_model = PROVIDERS["Groq"]["models"]["Llama 3.3 70B"]
        self.current_model_name = "Llama 3.3 70B"

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
            
            # Get provider and model
            provider = p.get('provider', 'Groq')
            self.current_provider = provider
            
            model_name = p.get('model')
            if model_name and model_name in PROVIDERS[provider]["models"]:
                self.current_model = PROVIDERS[provider]["models"][model_name]
                self.current_model_name = model_name
            
            self.temperature = p['temp']
            return True
        return False

    def get_provider_config(self):
        """Get the current provider's configuration"""
        return PROVIDERS[self.current_provider]

# Global instance
ai_state = AIStateManager()