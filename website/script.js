// ===== CONFIGURATION =====
const GIST_RAW_URL = 'https://gist.githubusercontent.com/Mistromy/cdb82a1247ae6095f5d43098eb074dba/raw/stats.json';

// Global stats object - Initialized to null to represent the "loading" state
let statsData = {
    serverCount: null,
    userCount: null,
    commandCount: 12847, // Hardcoded mock value for metrics not in the Gist
    aiResponses: 8934    // Hardcoded mock value for metrics not in the Gist
};

// ===== INITIALIZE PLACEHOLDERS IMMEDIATELY =====
// This forces elements to display "---" out of the gate so old placeholder numbers don't flash
function initPlaceholders() {
    ['serverCount', 'userCount'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.textContent = '---';
    });
}
initPlaceholders();

// ===== SMOOTH SCROLLING FOR NAVIGATION LINKS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        
        if (href.startsWith('#') && href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// ===== ANIMATED COUNTERS FOR STATS =====
function animateCounter(element, target, duration = 800) {
    const start = 0;
    const increment = target / (duration / 16); // ~60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        // Format numbers with commas (e.g., 1,000)
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

// ===== INTERSECTION OBSERVER SETUP =====
// Wrapped in a function so we can cleanly fire it ONLY after data resolves
function startObservingStats() {
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Disconnect immediately so it only triggers ONCE ever
                statsObserver.disconnect();
                
                // Run counter animations using the final resolved statsData
                Object.keys(statsData).forEach(key => {
                    const element = document.getElementById(key);
                    if (element) {
                        // If data loading failed or returned null, preserve the "---" state
                        if (statsData[key] === null || statsData[key] === undefined) {
                            element.textContent = '---';
                        } else {
                            animateCounter(element, statsData[key]);
                        }
                    }
                });
            }
        });
    }, { threshold: 0.3 });

    const statsSection = document.querySelector('.stats');
    if (statsSection) {
        statsObserver.observe(statsSection);
    }
}

// ===== FETCH LIVE STATS FROM GIST (RUNS ONCE) =====
async function fetchLiveStats() {
    try {
        // Appending `?_=${Date.now()}` bypasses aggressive browser/CDN caching
        const response = await fetch(`${GIST_RAW_URL}?_=${Date.now()}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch from Gist');
        }
        
        const data = await response.json();
        
        // Map Gist keys safely
        if (data.guild_count !== undefined) statsData.serverCount = data.guild_count;
        if (data.user_count !== undefined) statsData.userCount = data.user_count;
        
        console.log('✅ Nirupama live stats loaded successfully from Gist.');
        
    } catch (error) {
        console.error('⚠️ Could not load live stats, keeping "---" placeholders.', error);
        
        // Explicitly force null values on failure so the UI knows to render "---"
        statsData.serverCount = null;
        statsData.userCount = null;
    } finally {
        // Regardless of success or failure, we now kick off the scroll observer safely
        startObservingStats();
    }
}

// Fire the network fetch on execution
fetchLiveStats();

// ===== NAVBAR BACKGROUND ON SCROLL =====
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(26, 26, 26, 0.98)';
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
    } else {
        navbar.style.background = 'rgba(26, 26, 26, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// ===== FEATURE CARDS ANIMATION ON SCROLL =====
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .command-card, .roadmap-item').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    fadeInObserver.observe(card);
});

// ===== COMMAND TAG COLORS =====
document.querySelectorAll('.command-tag').forEach(tag => {
    const tagText = tag.textContent.toLowerCase().trim();
    if (tagText === 'admin') {
        tag.style.background = '#ED4245';
    } else if (tagText === 'fun') {
        tag.style.background = '#EB459E';
    } else if (tagText === 'game') {
        tag.style.background = '#FEE75C';
        tag.style.color = '#000';
    } else if (tagText === 'utility') {
        tag.style.background = '#57F287';
        tag.style.color = '#000';
    } else if (tagText === 'feedback') {
        tag.style.background = '#5865F2';
    }
});

// ===== MOBILE MENU TOGGLE =====
const createMobileMenu = () => {
    const nav = document.querySelector('.nav-menu');
    const navbar = document.querySelector('.navbar .container');
    
    if (window.innerWidth <= 768 && !document.querySelector('.mobile-menu-toggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'mobile-menu-toggle';
        toggleBtn.innerHTML = '☰';
        toggleBtn.style.cssText = `
            display: block;
            background: none;
            border: none;
            color: white;
            font-size: 2rem;
            cursor: pointer;
        `;
        
        toggleBtn.addEventListener('click', () => {
            nav.classList.toggle('mobile-active');
        });
        
        navbar.appendChild(toggleBtn);
    }
};

window.addEventListener('load', createMobileMenu);
window.addEventListener('resize', createMobileMenu);