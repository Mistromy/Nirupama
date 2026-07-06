// ============================================================
// NIRUPAMA — site scripts, v2 "signal"
// ============================================================

// ===== CONFIGURATION =====
const GIST_ID = 'cdb82a1247ae6095f5d43098eb074dba';
const GIST_RAW_URL = `https://gist.githubusercontent.com/Mistromy/${GIST_ID}/raw/stats.json`;
const GIST_API_URL = `https://api.github.com/gists/${GIST_ID}`;
const COMMITS_URL = 'https://img.shields.io/github/commit-activity/t/Mistromy/NIrupama.json';

// The bot pushes to the gist every 5 minutes. Allow a little grace for
// clock drift + task delay before declaring it dead.
const ONLINE_WINDOW_MS = 7 * 60 * 1000;
const REFRESH_INTERVAL_MS = 5 * 60 * 1000;   // refetch the gist
const STATUS_TICK_MS = 60 * 1000;            // re-evaluate staleness

const MASK = '░░░'; // "no data" placeholder

// Maps stat element ids (data-stat="...") -> keys in the gist's stats.json.
// To surface a NEW stat: add a card in index.html with data-stat="myStat",
// add an entry here, and have website.py write that key to the gist. Done.
const STAT_KEYS = {
    serverCount: 'guild_count',
    userCount: 'user_count',
    uptime: 'uptime',
    // --- future stats: stay masked until website.py starts sending them ---
    messagesTracked: 'messages_tracked',
    shipsCalculated: 'ships_calculated',
    aiReplies: 'ai_replies',
    diceRolled: 'dice_rolled'
};

// Resolved values live here; null = not loaded / not available
const statsData = {};
Object.keys(STAT_KEYS).forEach(k => statsData[k] = null);
statsData.updates = null; // commit count from Shields.io

let lastHeartbeatMs = null; // when the bot last updated the gist
let statsRevealed = false;  // counters already animated once?

// ============================================================
// STATUS — online / offline / unknown, driven by the heartbeat
// ============================================================
function relativeTime(ms) {
    const diff = Math.max(0, Date.now() - ms);
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins === 1) return '1 min ago';
    if (mins < 60) return `${mins} min ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} h ago`;
    return `${Math.floor(hours / 24)} d ago`;
}

function evaluateStatus() {
    let state = 'unknown';
    if (lastHeartbeatMs !== null) {
        state = (Date.now() - lastHeartbeatMs) < ONLINE_WINDOW_MS ? 'online' : 'offline';
    }
    applyStatus(state);
}

function applyStatus(state) {
    document.body.dataset.botStatus = state;

    // dots + short labels (nav pill, hero eyebrow, avatar caption)
    const labels = { online: 'online', offline: 'offline', unknown: 'no signal' };
    document.querySelectorAll('[data-status-text]').forEach(el => {
        el.textContent = labels[state];
    });

    // telemetry board headline — poster wording included, as tradition demands
    const board = document.querySelector('[data-board-status]');
    if (board) {
        const boardText = {
            online: 'signal: live // refreshes every 5 min',
            offline: 'system offline… running diagnostic',
            unknown: 'no signal // showing last known numbers'
        };
        board.textContent = boardText[state];
    }

    // heartbeat readout in the board footer
    const hb = document.querySelector('[data-heartbeat]');
    if (hb) hb.textContent = lastHeartbeatMs ? relativeTime(lastHeartbeatMs) : '———';

    const ep = document.querySelector('[data-epoch]');
    if (ep) ep.textContent = lastHeartbeatMs ? Math.floor(lastHeartbeatMs / 1000) : '——————';
}

// ============================================================
// DATA FETCHING
// ============================================================
async function fetchGistStats() {
    // cache-buster so the CDN never serves stale numbers
    const response = await fetch(`${GIST_RAW_URL}?_=${Date.now()}`);
    if (!response.ok) throw new Error('Failed to fetch from Gist');
    const data = await response.json();

    Object.entries(STAT_KEYS).forEach(([statId, gistKey]) => {
        if (data[gistKey] !== undefined && data[gistKey] !== null) {
            statsData[statId] = data[gistKey];
        }
    });

    // Heartbeat, plan A: website.py writes "last_updated" (epoch seconds)
    if (data.last_updated) {
        lastHeartbeatMs = data.last_updated * 1000;
    } else {
        // Plan B: ask the GitHub API when the gist was last touched.
        // Works with the current website.py, costs one (rate-limited) call.
        try {
            const meta = await fetch(GIST_API_URL);
            if (meta.ok) {
                const metaData = await meta.json();
                if (metaData.updated_at) {
                    lastHeartbeatMs = new Date(metaData.updated_at).getTime();
                }
            }
        } catch (e) {
            console.warn('⚠️ Gist metadata fallback failed.', e);
        }
    }
}

async function fetchCommitCount() {
    const response = await fetch(COMMITS_URL);
    if (!response.ok) throw new Error('Failed to fetch from Shields.io');
    const data = await response.json();
    if (data.value !== undefined) {
        statsData.updates = parseInt(data.value, 10);
    }
}

async function initialLoad() {
    try {
        await fetchGistStats();
        console.log('✅ Nirupama live stats loaded from Gist.');
    } catch (error) {
        console.error('⚠️ Could not load live stats, keeping placeholders.', error);
    }

    try {
        await fetchCommitCount();
        console.log(`✅ Total commits loaded: ${statsData.updates}`);
    } catch (error) {
        console.error('⚠️ Could not load commit stats.', error);
    }

    evaluateStatus();
    startObservingStats();

    // Update the CTA joke number ("Join over N servers") — stays honest as it grows
    if (statsData.serverCount !== null) {
        document.querySelectorAll('[data-cta-servers]').forEach(el => {
            el.textContent = statsData.serverCount.toLocaleString();
        });
    }
}

// Periodic refresh: catch the bot going down (or coming back) while
// someone has the page open. No animation on refresh, just new numbers.
async function backgroundRefresh() {
    try {
        await fetchGistStats();
        if (statsRevealed) {
            document.querySelectorAll('[data-stat]').forEach(el => {
                setStatText(el, statsData[el.dataset.stat]);
            });
        }
    } catch (e) {
        // network hiccup — staleness timer will flip the status if it persists
    }
    evaluateStatus();
}

// ============================================================
// COUNTERS
// ============================================================
function formatStat(value, suffix) {
    const isFloat = value % 1 !== 0;
    return (isFloat ? value.toFixed(1) : Math.floor(value).toLocaleString()) + suffix;
}

function setStatText(element, value) {
    if (value === null || value === undefined || isNaN(value)) {
        element.textContent = MASK;
        return;
    }
    const cell = element.closest('.stat-soon');
    if (cell) cell.classList.add('is-live');
    element.textContent = formatStat(Number(value), element.dataset.suffix || '');
}

function animateCounter(element, target, duration = 900, suffix = '') {
    const startTime = performance.now();

    function frame(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        // ease-out so big numbers don't slam to a stop
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = formatStat(target * eased, suffix);
        // note: formatStat floors integers, so intermediate frames read clean
        if (progress < 1) {
            requestAnimationFrame(frame);
        } else {
            element.textContent = formatStat(target, suffix);
        }
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
            statsRevealed = true;

            document.querySelectorAll('[data-stat]').forEach(element => {
                const value = statsData[element.dataset.stat];

                if (value === null || value === undefined || isNaN(value)) {
                    element.textContent = MASK; // no data -> honest placeholder
                    return;
                }

                const cell = element.closest('.stat-soon');
                if (cell) cell.classList.add('is-live');

                animateCounter(element, Number(value), 900, element.dataset.suffix || '');
            });
        });
    }, { threshold: 0.3 });

    statsObserver.observe(statsSection);
}

// ===== KICK EVERYTHING OFF =====
initialLoad();
setInterval(backgroundRefresh, REFRESH_INTERVAL_MS);
setInterval(evaluateStatus, STATUS_TICK_MS);

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