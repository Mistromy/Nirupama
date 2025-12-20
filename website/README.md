# Nirupama Bot Website

A modern, responsive website for the Nirupama Discord bot.

## 🚀 Features

- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Modern UI**: Dark theme with smooth animations and transitions
- **Ko-fi Integration**: Support section with embedded Ko-fi widget
- **Live Stats Ready**: Placeholder for future live statistics integration
- **SEO Optimized**: Proper meta tags and semantic HTML
- **Smooth Scrolling**: Beautiful navigation experience

## 📁 Files

- `index.html` - Main HTML structure
- `styles.css` - All styling and responsive design
- `script.js` - Interactive features and animations

## 🔧 Setup

1. **Replace the invite link**: 
   - Find all instances of `#invite-link` in `index.html`
   - Replace with your actual Discord bot invite URL
   - Get your invite URL from: Discord Developer Portal > Your Bot > OAuth2 > URL Generator

2. **Update Ko-fi username**:
   - In `index.html`, find the Ko-fi iframe
   - Replace `mistromy` with your Ko-fi username in the iframe src

3. **Deploy**:
   - Upload all files to a web hosting service (GitHub Pages, Netlify, Vercel, etc.)
   - Or serve locally with: `python -m http.server 8000`

## 🎨 Customization

### Colors
Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #5865F2;  /* Main brand color */
    --accent: #EB459E;         /* Accent color */
    --secondary-color: #57F287; /* Secondary accent */
    /* ... more colors */
}
```

### Content
- Modify text in `index.html`
- Add/remove features in the Features section
- Update commands in the Commands section
- Edit roadmap items

### Stats
The stats section currently uses placeholder data. To implement live stats:

1. Create an API endpoint in your bot that exposes stats
2. Update `fetchLiveStats()` in `script.js` with your API URL
3. Uncomment the setInterval call at the bottom of `script.js`

## 💡 Future Features to Implement

### 1. Live Statistics Dashboard
Create a backend API that exposes real-time bot statistics:

**Backend (Python/Flask example)**:
```python
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/api/stats')
def get_stats():
    # Get data from your bot
    return jsonify({
        'servers': bot.guild_count,
        'users': sum(g.member_count for g in bot.guilds),
        'commands': total_commands_run,
        'aiResponses': total_ai_responses,
        'uptime': bot.uptime,
        'latency': bot.latency
    })

if __name__ == '__main__':
    app.run(port=5000)
```

**Features to add**:
- Real-time guild count
- Total user count across all servers
- Commands executed (daily/weekly/total)
- AI responses generated
- Uptime percentage
- Average response time
- Most used commands chart
- Activity graph over time

### 2. Interactive Command Explorer
- Searchable command list
- Command usage examples
- Try commands in a simulated environment
- Command categories with filters

### 3. User Dashboard
- Login with Discord OAuth2
- View personal stats (commands used, servers shared with bot)
- Customizable bot settings per server
- Server-specific AI personality configuration

### 4. Activity Feed
- Recent AI conversations (anonymized)
- Funny ship results
- Top servers using the bot
- Community highlights

### 5. Documentation Section
- Detailed command documentation
- Setup guides
- FAQ section
- Troubleshooting guides
- API documentation

### 6. Admin Panel
For bot owners:
- Manage bot settings
- View detailed analytics
- Monitor bot health
- Manage blacklists/whitelists
- View error logs

### 7. Community Features
- User testimonials
- Featured servers
- Community showcase
- User-submitted content gallery

### 8. Status Page
- Bot online/offline status
- Recent incidents
- Scheduled maintenance
- Service health metrics

## 📊 Implementing Live Stats

### Option 1: WebSocket Connection
For real-time updates:

```javascript
// In script.js
const ws = new WebSocket('ws://your-server.com/stats');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateStats(data);
};
```

### Option 2: Polling
Current implementation (commented out in script.js):

```javascript
setInterval(fetchLiveStats, 30000); // Update every 30 seconds
```

### Option 3: Server-Sent Events (SSE)
For one-way real-time updates:

```javascript
const eventSource = new EventSource('/api/stats/stream');
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateStats(data);
};
```

## 🛠️ Tech Stack Suggestions

For full implementation:

**Frontend:**
- React/Next.js (for more complex features)
- Chart.js or D3.js (for graphs)
- Socket.io (for real-time updates)

**Backend:**
- Flask or FastAPI (Python)
- Express.js (Node.js)
- PostgreSQL/MongoDB (database)
- Redis (caching)

**Hosting:**
- Frontend: Netlify, Vercel, GitHub Pages
- Backend: Heroku, DigitalOcean, AWS
- Database: Supabase, MongoDB Atlas, Railway

## 📝 License

This website template is free to use and modify for your bot!

## 🤝 Contributing

Feel free to submit issues or pull requests to improve the website!

---

Made with 💙 by [Mistromy](https://github.com/mistromy)
