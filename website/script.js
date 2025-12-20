// ===== SMOOTH SCROLLING FOR NAVIGATION LINKS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        
        // Don't prevent default for placeholder links
        if (href === '#invite-link') {
            e.preventDefault();
            alert('Please replace #invite-link with your actual Discord bot invite URL!\n\nTo get your invite link:\n1. Go to Discord Developer Portal\n2. Select your bot application\n3. Go to OAuth2 > URL Generator\n4. Select "bot" and "applications.commands" scopes\n5. Select the permissions your bot needs\n6. Copy the generated URL');
            return;
        }
        
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
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        // Format numbers with commas
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

// ===== INTERSECTION OBSERVER FOR STATS ANIMATION =====
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && entry.target.textContent === '---') {
            // These are placeholder values - will be replaced with real API data
            const statsData = {
                serverCount: 150,
                userCount: 5420,
                commandCount: 12847,
                aiResponses: 8934
            };
            
            Object.keys(statsData).forEach(key => {
                const element = document.getElementById(key);
                if (element && element.textContent === '---') {
                    animateCounter(element, statsData[key]);
                }
            });
        }
    });
}, { threshold: 0.5 });

// Observe stats section
const statsSection = document.querySelector('.stats');
if (statsSection) {
    statsObserver.observe(statsSection);
}

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

// Observe all cards
document.querySelectorAll('.feature-card, .command-card, .roadmap-item').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    fadeInObserver.observe(card);
});

// ===== FETCH LIVE STATS FROM API (PLACEHOLDER) =====
// This function will be used when you implement the backend API
async function fetchLiveStats() {
    try {
        // Replace with your actual API endpoint
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }
        
        const data = await response.json();
        
        // Update stat values
        if (data.servers) {
            const serverElement = document.getElementById('serverCount');
            if (serverElement) animateCounter(serverElement, data.servers);
        }
        
        if (data.users) {
            const userElement = document.getElementById('userCount');
            if (userElement) animateCounter(userElement, data.users);
        }
        
        if (data.commands) {
            const commandElement = document.getElementById('commandCount');
            if (commandElement) animateCounter(commandElement, data.commands);
        }
        
        if (data.aiResponses) {
            const aiElement = document.getElementById('aiResponses');
            if (aiElement) animateCounter(aiElement, data.aiResponses);
        }
        
    } catch (error) {
        console.log('Stats API not yet implemented - using placeholder data');
    }
}

// ===== CONSOLE EASTER EGG =====
console.log('%c🤖 Nirupama Bot Website', 'font-size: 24px; font-weight: bold; color: #5865F2;');
console.log('%cHey there, curious developer! 👀', 'font-size: 16px; color: #57F287;');
console.log('%cLike what you see? Check out the code on GitHub:', 'font-size: 14px;');
console.log('%chttps://github.com/mistromy/Nirupama', 'font-size: 14px; color: #EB459E;');

// ===== LIVE STATS REFRESH (UNCOMMENT WHEN API IS READY) =====
// Refresh stats every 30 seconds
// setInterval(fetchLiveStats, 30000);

// ===== COMMAND TAG COLORS =====
document.querySelectorAll('.command-tag').forEach(tag => {
    const tagText = tag.textContent.toLowerCase();
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

// ===== MOBILE MENU TOGGLE (if needed) =====
// Add this if you want a hamburger menu for mobile
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

// Check on load and resize
window.addEventListener('load', createMobileMenu);
window.addEventListener('resize', createMobileMenu);
