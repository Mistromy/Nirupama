1. Data Collected by Nirupama
To function properly, Nirupama collects and processes limited data:

Activity Metrics: Nirupama tracks the number of messages sent per day, per user, per server. Nirupama does not log the content of these daily messages, only the metadata (timestamps and message counts).

Mention Context: When you mention or trigger Nirupama, Nirupama temporarily stores the last ten (10) messages associated with that interaction to provide conversational context.

Identifiers: Nirupama processes platform-specific IDs (such as User IDs and Server/Guild IDs) to link activity metrics and context to the correct accounts.

2. How Nirupama Uses Your Data
Nirupama uses the collected data strictly for the following purposes:

To generate statistics and activity insights for users and servers.

To provide context-aware AI responses.

3. Data Sharing and Third-Party Services
Nirupama uses Groq to power the Bot’s artificial intelligence capabilities via the LLaMA model.

When you interact with Nirupama, the relevant text context (the last 10 messages mentioning the Bot) is sent to Groq's APIs for processing.

Nirupama does not sell your data to third parties. Groq’s processing of this data is subject to Groq's own privacy and data retention policies.

4. Data Retention
Context Data: The 10-message conversational context is stored on a rolling basis; older messages are automatically overwritten and deleted by Nirupama.

Activity Metrics: Daily activity counts are stored indefinitely to generate long-term statistics for the server.