// ============================================================
// NIRUPAMA — site scripts
// ============================================================

// ===== CONFIGURATION =====
const GIST_RAW_URL = 'https://gist.githubusercontent.com/Mistromy/cdb82a1247ae6095f5d43098eb074dba/raw/stats.json';
const COMMITS_URL = 'https://img.shields.io/github/commit-activity/t/Mistromy/NIrupama.json';

// Maps stat element ids (data-stat="...") -> keys in the gist's stats.json.
// To surface a NEW stat: add a card in index.html with data-stat="myStat",
// add an entry here, and have website.py write that key to the gist. Done.
const STAT_KEYS = {
    serverCount: 'guild_count',
    userCount: 'user_count',
    uptime: 'uptime',
    // --- future stats: display "---" until website.py starts sending them ---
    messagesTracked: 'messages_tracked',
    shipsCalculated: 'ships_calculated',
    aiReplies: 'ai_replies',
    diceRolled: 'dice_rolled'
};

// Resolved values live here; null = not loaded / not available
const statsData = {};
Object.keys(STAT_KEYS).forEach(k => statsData[k] = null);
statsData.updates = null; // commit count from Shields.io

// ===== FETCH LIVE STATS (gist + shields) =====
async function fetchLiveStats() {
    // 1. Gist: server/user counts, uptime, and any future keys
    try {
        // cache-buster so the CDN never serves stale numbers
        const response = await fetch(`${GIST_RAW_URL}?_=${Date.now()}`);
        if (!response.ok) throw new Error('Failed to fetch from Gist');
        const data = await response.json();

        Object.entries(STAT_KEYS).forEach(([statId, gistKey]) => {
            if (data[gistKey] !== undefined && data[gistKey] !== null) {
                statsData[statId] = data[gistKey];
            }
        });

        console.log('✅ Nirupama live stats loaded from Gist.');
    } catch (error) {
        console.error('⚠️ Could not load live stats, keeping "---" placeholders.', error);
    }

    // 2. Shields.io: total commit count
    try {
        const response = await fetch(COMMITS_URL);
        if (!response.ok) throw new Error('Failed to fetch from Shields.io');
        const data = await response.json();
        if (data.value !== undefined) {
            statsData.updates = parseInt(data.value, 10);
            console.log(`✅ Total commits loaded: ${statsData.updates}`);
        }
    } catch (error) {
        console.error('⚠️ Could not load commit stats.', error);
    }

    // 3. Whatever happened, arm the scroll-triggered counters
    startObservingStats();

    // 4. Update the CTA joke number ("Join over N servers") — stays honest as it grows
    if (statsData.serverCount !== null) {
        document.querySelectorAll('[data-cta-servers]').forEach(el => {
            el.textContent = statsData.serverCount.toLocaleString();
        });
    }
}

// ===== ANIMATED COUNTERS =====
function animateCounter(element, target, duration = 900, suffix = '') {
    const isFloat = target % 1 !== 0;
    const startTime = performance.now();

    function frame(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        // ease-out so big numbers don't slam to a stop
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;
        element.textContent = (isFloat ? current.toFixed(1) : Math.floor(current).toLocaleString()) + suffix;
        if (progress < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
}

// ===== STATS SCROLL TRIGGER (fires once) =====
function startObservingStats() {
    const statsSection = document.querySelector('.stats');
    if (!statsSection) return;

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            statsObserver.disconnect();

            document.querySelectorAll('[data-stat]').forEach(element => {
                const key = element.dataset.stat;
                const value = statsData[key];

                if (value === null || value === undefined || isNaN(value)) {
                    element.textContent = '---'; // no data -> honest placeholder
                    return;
                }

                // "soon" cells light up once real data actually arrives
                const cell = element.closest('.stat-soon');
                if (cell) cell.classList.add('is-live');

                animateCounter(element, Number(value), 900, element.dataset.suffix || '');
            });
        });
    }, { threshold: 0.3 });

    statsObserver.observe(statsSection);
}

fetchLiveStats();

// ===== COMMAND TICKER — duplicate content for a seamless loop =====
const tickerTrack = document.getElementById('tickerTrack');
if (tickerTrack) {
    tickerTrack.innerHTML += tickerTrack.innerHTML;
}

// ===== NAVBAR: border + solid background on scroll =====
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
}, { passive: true });

// ===== MOBILE MENU =====
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
        const open = navMenu.classList.toggle('open');
        navToggle.classList.toggle('open', open);
        navToggle.setAttribute('aria-expanded', open);
    });

    // close the menu after tapping a link
    navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('open');
            navToggle.classList.remove('open');
            navToggle.setAttribute('aria-expanded', 'false');
        });
    });
}

// ===== SMOOTH SCROLLING FOR ANCHOR LINKS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href.startsWith('#') && href !== '#') {
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    });
});

// ===== REVEAL-ON-SCROLL =====
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (prefersReducedMotion) {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
} else {
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
}