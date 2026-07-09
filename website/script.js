// ============================================================
// NIRUPAMA — site scripts, v2 "signal"
// ============================================================

// ===== CONFIGURATION =====
const GIST_ID = 'cdb82a1247ae6095f5d43098eb074dba';
const GIST_RAW_URL = `https://gist.githubusercontent.com/Mistromy/${GIST_ID}/raw/stats.json`;
const GIST_API_URL = `https://api.github.com/gists/${GIST_ID}`;
const COMMITS_URL = 'https://img.shields.io/github/commit-activity/t/Mistromy/NIrupama.json';
const LAST_UPDATE_URL = 'https://img.shields.io/github/last-commit/Mistromy/Nirupama.json'

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
    lastUpdate: 'last_update'
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

async function fetchLastUpdate() {
    const response = await fetch(LAST_UPDATE_URL);
    if (!response.ok) throw new Error('Failed to fetch last update info from Shields.io');
    const data = await response.json();
    if (data.value !== undefined) {
        statsData.lastUpdate = data.value;
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

    try {
        await fetchLastUpdate();
        console.log(`✅ Last update timestamp loaded: ${statsData.lastUpdate}`);
    } catch (error) {
        console.error('⚠️ Could not load last update info.', error);
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
    if (value === null || value === undefined) {
        element.textContent = MASK; //
        return;
    }
    const cell = element.closest('.stat-soon'); //
    if (cell) cell.classList.add('is-live'); //

    if (typeof value === 'string') {
        element.textContent = value + (element.dataset.suffix || ''); //
    } else {
        element.textContent = formatStat(Number(value), element.dataset.suffix || ''); //
    }
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
            if (!entry.isIntersecting) return; //
            statsObserver.disconnect(); //
            statsRevealed = true; //

            document.querySelectorAll('[data-stat]').forEach(element => {
                const value = statsData[element.dataset.stat]; //

                if (value === null || value === undefined) {
                    element.textContent = MASK; //
                    return;
                }

                const cell = element.closest('.stat-soon'); //
                if (cell) cell.classList.add('is-live'); //

                // Choose the right animation sequence depending on the data type
                if (typeof value === 'string') {
                    animateText(element, value + (element.dataset.suffix || ''), 900);
                } else {
                    animateCounter(element, Number(value), 900, element.dataset.suffix || ''); //
                }
            });
        });
    }, { threshold: 0.3 });

    statsObserver.observe(statsSection);
}

function animateText(element, target, duration = 900) {
    // The pool of characters to scramble through
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789░▒▓█$#@%';
    const startTime = performance.now();
    const targetLength = target.length;

    function frame(now) {
        const progress = Math.min((now - startTime) / duration, 1);

        // Determine how many characters are "locked into place" based on time
        const lockCount = Math.floor(progress * targetLength);

        let currentText = target.substring(0, lockCount);

        // Fill the rest of the string with randomized glyphs
        for (let i = lockCount; i < targetLength; i++) {
            if (target[i] === ' ') {
                currentText += ' '; // Preserve spaces if your strings have them
            } else {
                currentText += chars[Math.floor(Math.random() * chars.length)];
            }
        }

        element.textContent = currentText;

        if (progress < 1) {
            requestAnimationFrame(frame);
        } else {
            element.textContent = target; // Ensure absolute accuracy at the end
        }
    }
    requestAnimationFrame(frame);
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

// ============================================================
// TERMS GATE
// Every invite link runs through the SYS_PROMPT modal until the
// visitor accepts. Acceptance is remembered per browser; bump
// TERMS_VERSION when the documents change to re-prompt everyone.
// ============================================================
const TERMS_VERSION = '2026-07-06'; // <- change this date when ToS/EULA/privacy change
const TERMS_STORAGE_KEY = 'nirupama_terms_accepted';

const termsModal = document.getElementById('termsModal');
const termsCheckbox = document.getElementById('termsCheckbox');
const termsAgree = document.getElementById('termsAgree');
const termsCancel = document.getElementById('termsCancel');
const termsClose = document.getElementById('termsClose');

let pendingInviteUrl = null;
let lastFocusedElement = null;

function hasAcceptedTerms() {
    return false;
}

function rememberAcceptance() {
}

// function hasAcceptedTerms() {
//     try {
//         return localStorage.getItem(TERMS_STORAGE_KEY) === TERMS_VERSION;
//     } catch (e) {
//         return false; // private browsing etc. — just show the modal
//     }
// }

// function rememberAcceptance() {
//     try {
//         localStorage.setItem(TERMS_STORAGE_KEY, TERMS_VERSION);
//     } catch (e) {
//         // storage unavailable — they'll see the modal again next time, fine
//     }
// }

function openTermsModal(inviteUrl) {
    pendingInviteUrl = inviteUrl;
    lastFocusedElement = document.activeElement;
    termsCheckbox.checked = false;
    termsAgree.disabled = true;
    termsModal.hidden = false;
    document.body.classList.add('modal-open');
    termsCheckbox.focus();
}

function closeTermsModal() {
    termsModal.hidden = true;
    document.body.classList.remove('modal-open');
    pendingInviteUrl = null;
    if (lastFocusedElement) lastFocusedElement.focus();
}

if (termsModal) {
    // intercept every invite link on the page
    document.querySelectorAll('a[href*="discord.com/oauth2/authorize"]').forEach(link => {
        link.addEventListener('click', (e) => {
            if (hasAcceptedTerms()) return; // already agreed — sail through
            e.preventDefault();
            openTermsModal(link.href);
        });
    });

    termsCheckbox.addEventListener('change', () => {
        termsAgree.disabled = !termsCheckbox.checked;
    });

    termsAgree.addEventListener('click', () => {
        if (!termsCheckbox.checked) return;
        rememberAcceptance();
        const url = pendingInviteUrl;
        closeTermsModal();
        if (url) window.location.href = url;
    });

    termsCancel.addEventListener('click', closeTermsModal);
    termsClose.addEventListener('click', closeTermsModal);

    // click the backdrop (not the panel) to dismiss
    termsModal.addEventListener('click', (e) => {
        if (e.target === termsModal) closeTermsModal();
    });

    // Esc to dismiss, Tab stays inside the dialog
    document.addEventListener('keydown', (e) => {
        if (termsModal.hidden) return;

        if (e.key === 'Escape') {
            closeTermsModal();
            return;
        }

        if (e.key === 'Tab') {
            const focusables = termsModal.querySelectorAll(
                'button:not(:disabled), input, a[href]'
            );
            if (!focusables.length) return;
            const first = focusables[0];
            const last = focusables[focusables.length - 1];

            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    });
}

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