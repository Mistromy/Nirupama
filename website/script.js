// ============================================================
// NIRUPAMA — site scripts, v3 "live wire"
// ============================================================

// ===== CONFIGURATION =====

const API_URL = 'https://api.mista.tech/nirupama';
const WS_URL = 'wss://api.mista.tech/nirupama/live';

const GIST_ID = 'cdb82a1247ae6095f5d43098eb074dba';
const GIST_RAW_URL = `https://gist.githubusercontent.com/Mistromy/${GIST_ID}/raw/stats.json`;
const GIST_API_URL = `https://api.github.com/gists/${GIST_ID}`;
const COMMITS_URL = 'https://img.shields.io/github/commit-activity/t/Mistromy/NIrupama.json';
const LAST_UPDATE_URL = 'https://img.shields.io/github/last-commit/Mistromy/Nirupama.json';

// Grace window before we call the bot "offline".
//
// This has to clear the bot's own cadence, not ours. website.py stamps
// heartbeat_epoch_ms once every five minutes, and it stamps it AFTER awaiting
// Supabase and Cronitor, neither of which has a timeout — so a slow third
// party pushes the stamp late and the gap between two heartbeats can exceed
// five minutes without anything being wrong. Seven minutes left barely two
// minutes for that, which is where the "it randomly says offline" came from.
//
// The other half of that bug — our COPY of the heartbeat being stale, rather
// than the heartbeat itself — is not fixed by widening this. It's fixed by
// refusing to judge on a stale snapshot at all; see evaluateStatus().
const ONLINE_WINDOW_MS = 9 * 60 * 1000;
// A snapshot older than this can't be used to call the bot dead. It says our
// copy is old, which is a different fact.
const SNAPSHOT_FRESH_MS = 90 * 1000;
// Safety-net poll: the websocket should make this redundant most of the
// time, but it catches the rare silently-dead connection and doubles as
// the gist-fallback refresh interval when the API is unreachable.
const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const STATUS_TICK_MS = 60 * 1000; // re-evaluate staleness even with no new data
const WS_RECONNECT_MS = 5 * 1000;
const WS_RECONNECT_MAX_MS = 30 * 1000;

// how long the count-up on the stats board runs for
const COUNTER_MS = 900;
// Shields.io is flaky and nothing else depends on it, so its two values
// retry rather than resolving to nothing on the first miss.
const SIDE_RETRIES = 3;
const SIDE_RETRY_MS = 2500;
// Shields.io is the slowest thing on the page; don't let it hold the load.
const SIDE_FETCH_TIMEOUT_MS = 3000;

const MASK = '░░░';    // nothing is coming for this one yet
const MISSING = '———'; // something was coming and it never arrived

const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Everything except uptime is a genuine whole number — this is what fixes
// the animation showing fake decimals / losing commas mid-count-up.
const FLOAT_STATS = new Set(['uptime']);

// Maps stat element ids (data-stat="...") -> the field name shared by the
// API, the websocket payload, AND the gist (all three use the same keys
// now, so one table covers every source).
const STAT_KEYS = {
    serverCount: 'guild_count',
    userCount: 'user_count',
    uptime: 'uptime',
    messagesTracked: 'messages_tracked',
    // --- future stats: stay masked until the bot starts sending these ---
    shipsCalculated: 'ships_calculated',
    aiReplies: 'ai_replies',
    lastUpdate: 'last_update'
};

// The API serves a zero-valued snapshot until the bot has phoned home, and
// per-message pushes only carry the message fields — the rest arrive as 0.
// None of these are ever legitimately 0 in practice, so a 0 means "not known
// yet", not "the real answer is zero". Without this the counters blink to 0
// every time a message lands.
const ZERO_IS_UNKNOWN = new Set(['guild_count', 'user_count', 'uptime', 'messages_tracked']);

// Resolved values live here; null = not loaded / not available
const statsData = {};
Object.keys(STAT_KEYS).forEach(k => statsData[k] = null);
statsData.updates = null; // commit count from Shields.io

let lastHeartbeatMs = null; // periodic "phone home" — the bot's own five-minute stamp
let lastMessageMs = null;   // per-message epoch — Discord's timestamp on a message the bot handled
let lastFetchAt = 0;        // when our snapshot last came from somewhere, however it got here
// The API telling us straight out whether ITS websocket to the bot is open.
// Nothing sends this yet; if and when the API starts to, it outranks every
// timestamp below, because "is the bot connected to me right now" is the
// actual question and only the API can answer it. Until then it stays null
// and we infer.
let botConnected = null;
let usingFallback = false;  // true while we're reading from the gist, not the API
let hasLoadedOnce = false;  // becomes true the instant we've attempted a first load, success or not
let wsConnected = false;    // is the live websocket actually open right now
let wsConnection = null;
let wsRetryMs = WS_RECONNECT_MS;
// Has this connection handed us its current state yet? Reset on every open,
// because the first push is always a catch-up rather than something we
// watched happen — see the flash rule in onmessage.
let wsSynced = false;

// reveal state
const failedStats = new Set(); // stat ids whose source gave up — dashes, not mask
let statsRevealed = false;     // counters already animated once?
let statsInView = false;       // the board has been scrolled to

// ============================================================
// STATUS — online / offline / unknown, driven by the heartbeat.
// The bot being up and this page having a live link are two different
// questions, so they get two different readouts. Only a dead bot is red.
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

// live | delayed | stale | down | opening
// The API poll and the gist look identical from out here: no per-message
// push, so the numbers move on the bot's five-minute cadence instead. Not
// worth two states, and definitely not worth a warning colour.
function linkState(botState) {
    if (botState === 'offline') return 'down';
    if (botState === 'connecting') return 'opening';
    // no heartbeat anywhere in the data — we can't vouch for the numbers, and
    // we mustn't imply a healthy five-minute refresh either
    if (botState === 'unknown') return 'stale';
    return wsConnected ? 'live' : 'delayed';
}

// Same idea as relativeTime, but it never rounds the seconds away while the
// number is still small enough for them to mean something. This is the one
// readout on the page that moves on its own, once a second, whether or not
// anything else does — which is most of how you can tell the feed is alive
// during a quiet stretch. "3 min ago" sitting still for sixty seconds throws
// exactly the evidence that makes the point.
function preciseTime(ms) {
    const secs = Math.max(0, Math.round((Date.now() - ms) / 1000));
    if (secs < 60) return `${secs}s ago`;
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ${secs % 60}s ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ${mins % 60}m ago`;
    return `${Math.floor(hours / 24)} d ago`;
}

function updateLastMessageReadout() {
    const el = document.querySelector('[data-last-message-inline]');
    if (!el) return;
    el.textContent = lastMessageMs ? preciseTime(lastMessageMs) : 'waiting…';
}

// The freshest thing we know the bot itself produced.
//
// The periodic heartbeat is not the only evidence it's alive: epoch_ms on a
// live push is Discord's timestamp on a message the bot actually received and
// counted, so a message thirty seconds ago proves the bot was up thirty
// seconds ago just as well as a phone-home would. Only the ABSENCE of
// messages means nothing — a dead-silent hour is not a dead bot — which is
// why this takes whichever is newer rather than swapping one for the other.
function livenessMs() {
    const newest = Math.max(
        lastHeartbeatMs === null ? -Infinity : lastHeartbeatMs,
        lastMessageMs === null ? -Infinity : lastMessageMs
    );
    return Number.isFinite(newest) ? newest : null;
}

// Going and asking again before the board is allowed to say "offline".
// Rate-limited because evaluateStatus() runs again as soon as this lands, and
// a probe that keeps failing would otherwise re-enter here forever.
const PROBE_INTERVAL_MS = 30 * 1000;
let probing = false;
let lastProbeAt = 0;
let probeFailures = 0;

function probeLiveness() {
    if (probing || Date.now() - lastProbeAt < PROBE_INTERVAL_MS) return;
    probing = true;
    lastProbeAt = Date.now();

    const before = lastFetchAt;
    loadStats().finally(() => {
        // loadStats handles its own errors and resolves either way, so
        // "did a snapshot actually land" is the only honest test
        const landed = lastFetchAt > before;
        probeFailures = landed ? 0 : probeFailures + 1;
        probing = false;
        if (landed) refreshVisibleStats();
        evaluateStatus();
    });
}

function evaluateStatus() {
    if (!hasLoadedOnce) {
        applyStatus('connecting');
        return;
    }

    // if the API ever starts telling us directly, believe it and stop guessing
    if (botConnected !== null && Date.now() - lastFetchAt < SNAPSHOT_FRESH_MS) {
        applyStatus(botConnected ? 'online' : 'offline');
        return;
    }

    const seen = livenessMs();
    if (seen === null) {
        applyStatus('unknown');
        return;
    }
    if (Date.now() - seen < ONLINE_WINDOW_MS) {
        applyStatus('online');
        return;
    }

    // The heartbeat we're holding looks stale — but staleness of the DATA and
    // staleness of OUR COPY of it are not the same thing, and only the first
    // one is about the bot. A snapshot fetched ten minutes ago, carrying a
    // heartbeat from ten minutes before that, says nothing at all about
    // whether the bot is up; it says we haven't looked recently. Going red on
    // that was the bug. So: go and look, and leave the board saying whatever
    // it already says until the answer lands.
    if (Date.now() - lastFetchAt > SNAPSHOT_FRESH_MS) {
        probeLiveness();
        // …unless we can't get an answer at all, in which case the honest
        // readout is "no signal" — not "offline", which blames the bot for
        // what is probably our own connection.
        if (probeFailures >= 2) applyStatus('unknown');
        return;
    }

    // fresh snapshot, stale heartbeat. That one is the bot.
    applyStatus('offline');
}

function applyStatus(state) {
    const link = linkState(state);
    document.body.dataset.botStatus = state;
    document.body.dataset.linkState = link;

    const labels = { connecting: 'connecting…', online: 'online', offline: 'offline', unknown: 'no signal' };
    document.querySelectorAll('[data-status-text]').forEach(el => {
        el.textContent = labels[state];
    });

    const board = document.querySelector('[data-board-status]');
    if (board) {
        const boardText = {
            connecting: 'opening the link…',
            online: link === 'live'
                ? 'online // every message, the moment it lands'
                : 'online // no live push, numbers within five minutes',
            offline: 'no heartbeat // the bot is not answering',
            unknown: 'no timestamp // these are the last numbers we saw'
        };
        board.textContent = boardText[state];
    }

    const readout = document.querySelector('[data-link-readout]');
    if (readout) {
        readout.textContent = {
            opening: 'link // opening…',
            live: 'link // live',
            delayed: 'link // five-minute refresh',
            stale: 'link // no heartbeat',
            down: 'bot // offline'
        }[link];
    }

    const hb = document.querySelector('[data-heartbeat]');
    if (hb) hb.textContent = lastHeartbeatMs ? relativeTime(lastHeartbeatMs) : '———';

    updateLastMessageReadout();
}

// ============================================================
// DATA — shared parser for API / websocket / gist, since all
// three now speak the same field names
// ============================================================
function applyStatsPayload(data) {
    Object.entries(STAT_KEYS).forEach(([statId, key]) => {
        const value = data[key];
        if (value === undefined || value === null) return;
        if (value === 0 && ZERO_IS_UNKNOWN.has(key)) return; // placeholder, not a reading
        statsData[statId] = value;
    });

    // heartbeat_epoch_ms is the bot's periodic "phone home" (or the gist's
    // last_updated, its rough equivalent) — this alone decides online vs.
    // offline. A quiet channel with no messages doesn't touch it, so the bot
    // correctly stays "online" through a dead-silent hour.
    const heartbeatMs = data.heartbeat_epoch_ms || (data.last_updated ? data.last_updated * 1000 : null);
    if (heartbeatMs) lastHeartbeatMs = heartbeatMs;

    // epoch_ms is the per-MESSAGE timestamp — fresh the instant a message
    // lands, drives the "last message" readout, and doubles as proof of life
    // (see livenessMs).
    if (data.epoch_ms) lastMessageMs = data.epoch_ms;

    // Not sent by anything today. If the API starts reporting whether its own
    // websocket to the bot is open, that answer beats every inference we make
    // from timestamps — see evaluateStatus.
    if (typeof data.bot_connected === 'boolean') botConnected = data.bot_connected;
}

function flashStat(element) {
    element.classList.remove('stat-flash');
    void element.offsetWidth; // force reflow so the animation can restart if it's already running
    element.classList.add('stat-flash');
}

// A value going from one line to two makes the cell jump, which is the one
// bit of movement on this board nobody asked for. Height can't be transitioned
// from auto, so measure across the write and interpolate the difference: the
// text is already in place, the box just takes a moment to admit it.
const HEIGHT_EASE_MS = 260;

// eases the box between two heights, clipping while it moves so a second line
// is wiped into view rather than spilling over the label underneath
function easeHeight(element, from, to) {
    if (Math.abs(to - from) < 1) return; // same number of lines — nothing to ease

    element.classList.add('is-resizing');
    element.style.height = `${from}px`;
    void element.offsetHeight; // commit the start height before transitioning off it
    element.style.transition = `height ${HEIGHT_EASE_MS}ms cubic-bezier(0.2, 0.7, 0.3, 1)`;
    element.style.height = `${to}px`;
    setTimeout(() => {
        element.classList.remove('is-resizing');
        element.style.height = '';
        element.style.transition = '';
    }, HEIGHT_EASE_MS + 40);
}

function writeValue(element, write) {
    if (REDUCED_MOTION) {
        write();
        return;
    }
    const from = element.getBoundingClientRect().height;
    element.style.height = '';
    write();
    easeHeight(element, from, element.getBoundingClientRect().height);
}

// The count-up and the scramble rewrite the text every frame, so they can't go
// through writeValue — measure what they're heading for and open the box once,
// up front, instead of letting it snap partway through.
function reserveHeightFor(element, finalText) {
    if (REDUCED_MOTION) return;
    const from = element.getBoundingClientRect().height;
    const current = element.textContent;
    element.style.height = '';
    element.textContent = finalText;
    const to = element.getBoundingClientRect().height;
    element.textContent = current;
    easeHeight(element, from, to);
}

// sets the text but wraps the LAST character in its own span so only that
// character gets the tick animation — the rest of the number just sits
// there unchanged, it never re-counts from zero.
function setStatValueWithTick(element, text) {
    if (!text.length) {
        element.textContent = text;
        return;
    }
    const head = text.slice(0, -1);
    const tail = text.slice(-1);
    element.textContent = '';
    element.appendChild(document.createTextNode(head));
    const tick = document.createElement('span');
    tick.className = 'digit-tick';
    tick.textContent = tail;
    element.appendChild(tick);
}

function refreshVisibleStats() {
    if (!statsRevealed) return; // the board hasn't been scrolled to yet
    document.querySelectorAll('[data-stat]').forEach(el => {
        setStatText(el, statsData[el.dataset.stat]);
    });
}

// Live push handler: an instant swap to the new value, no re-counting.
//
// Whether it flashes is NOT decided by "did the number change". The bot sends
// two different things down this socket: a per-message push carrying epoch_ms,
// and the five-minute heartbeat, which re-reads the true total from Supabase
// and carries no epoch_ms. The heartbeat almost always moves messages_tracked
// — the bot's in-memory tally drifts from the database between reads — so
// flashing on "it changed" meant a blue flash every five minutes for a
// correction nobody sent. The flash means "a message just landed", so only a
// push that says a message just landed is allowed to fire it.
function applyLiveUpdate(before, isMessageEvent) {
    if (!statsRevealed) return; // nothing on screen to update yet
    document.querySelectorAll('[data-stat]').forEach(el => {
        const id = el.dataset.stat;
        const value = statsData[id];
        if (value === before[id]) return; // unchanged — leave it alone

        if (value === null || value === undefined) {
            writeValue(el, () => { el.textContent = MASK; });
            return;
        }
        const cell = el.closest('.stat-soon');
        if (cell) cell.classList.add('is-live');

        const text = typeof value === 'string'
            ? value + (el.dataset.suffix || '')
            : formatStat(Number(value), el.dataset.suffix || '', !FLOAT_STATS.has(id));

        // a silent correction just gets written; a message event ticks and flashes
        writeValue(el, () => {
            if (isMessageEvent) setStatValueWithTick(el, text);
            else el.textContent = text;
        });
        if (isMessageEvent) flashStat(el);
    });
}

// ============================================================
// DATA FETCHING — API first, gist only if the API is unreachable
// ============================================================
async function fetchApiStats() {
    const response = await fetch(`${API_URL}?_=${Date.now()}`);
    if (!response.ok) throw new Error('API unreachable');
    const data = await response.json();

    // The server hands out a zero-valued snapshot until the bot connects to
    // it. That's not data — fall through to the gist rather than paint zeros.
    if (!data.heartbeat_epoch_ms && !data.guild_count) throw new Error('API has no snapshot yet');

    applyStatsPayload(data);
    lastFetchAt = Date.now();
    usingFallback = false;
}

async function fetchGistStats() {
    const response = await fetch(`${GIST_RAW_URL}?_=${Date.now()}`);
    if (!response.ok) throw new Error('Gist unreachable too');
    const data = await response.json();
    applyStatsPayload(data);
    lastFetchAt = Date.now();
    usingFallback = true;

    // If the file predates the timestamp fields entirely, ask GitHub when it
    // was last touched. That is a proxy for "the gist got written", NOT for
    // "the bot is alive" — so when the payload does carry a timestamp we take
    // it at face value, zero included, rather than letting an edit to the file
    // pass for a heartbeat.
    const carriesOwnStamp = 'heartbeat_epoch_ms' in data || 'last_updated' in data;
    if (!lastHeartbeatMs && !carriesOwnStamp) {
        try {
            const meta = await fetch(GIST_API_URL);
            if (meta.ok) {
                const metaData = await meta.json();
                if (metaData.updated_at) lastHeartbeatMs = new Date(metaData.updated_at).getTime();
            }
        } catch (e) {
            console.warn('⚠️ Gist metadata fallback failed.', e);
        }
    }
}

async function loadStats() {
    try {
        await fetchApiStats();
        console.log('✅ live stats loaded from the API.');
    } catch (apiErr) {
        console.warn('⚠️ API unreachable, falling back to the gist.', apiErr);
        try {
            await fetchGistStats();
            console.log('✅ live stats loaded from the Gist fallback.');
        } catch (gistErr) {
            console.error('⚠️ API and Gist both failed — keeping last known numbers.', gistErr);
        }
    }
}

async function fetchCommitCount() {
    const response = await fetch(COMMITS_URL);
    if (!response.ok) throw new Error('Failed to fetch from Shields.io');
    const data = await response.json();
    if (data.value === undefined) throw new Error('Shields.io returned no commit count');
    statsData.updates = parseInt(data.value, 10);
    fillLate('updates');
    document.querySelectorAll('[data-github-commits]').forEach(el => {
        el.textContent = `${statsData.updates.toLocaleString()}+`;
    });
}

async function fetchLastUpdate() {
    const response = await fetch(LAST_UPDATE_URL);
    if (!response.ok) throw new Error('Failed to fetch last update info from Shields.io');
    const data = await response.json();
    if (data.value === undefined) throw new Error('Shields.io returned no last-commit date');
    statsData.lastUpdate = data.value;
    fillLate('lastUpdate');
}

// Keep the loader on and retry rather than resolving the cell to nothing.
// Only once we've genuinely given up does it fall to dashes, which say
// "this was meant to be here" instead of the mask's "nothing yet".
async function loadSideStat(fetcher, statId) {
    for (let attempt = 0; attempt <= SIDE_RETRIES; attempt++) {
        try {
            await withTimeout(fetcher(), SIDE_FETCH_TIMEOUT_MS);
            failedStats.delete(statId);
            return true;
        } catch (err) {
            if (attempt === SIDE_RETRIES) {
                console.warn(`⚠️ ${statId} gave up after ${attempt + 1} tries.`, err);
                failedStats.add(statId);
                fillLate(statId);
                return false;
            }
            await new Promise(resolve => setTimeout(resolve, SIDE_RETRY_MS));
        }
    }
}

// races a fetch against the clock so one slow third party can't hold the
// whole board hostage — it still lands later, via fillLate()
function withTimeout(promise, ms) {
    return Promise.race([
        promise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('timed out')), ms))
    ]);
}

// ============================================================
// WEBSOCKET — live push from the API; the gist/backgroundRefresh
// poll is purely a fallback for when this connection is down
// ============================================================
function connectWebSocket() {
    if (wsConnection && (wsConnection.readyState === WebSocket.OPEN || wsConnection.readyState === WebSocket.CONNECTING)) {
        return;
    }

    wsConnection = new WebSocket(WS_URL);

    wsConnection.onopen = () => {
        console.log('✅ connected to the live stats websocket.');
        wsConnected = true;
        wsSynced = false; // whatever arrives first is catch-up, not news
        wsRetryMs = WS_RECONNECT_MS;
        evaluateStatus();
    };

    wsConnection.onmessage = (event) => {
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (err) {
            console.warn('⚠️ websocket message parse error:', err);
            return;
        }

        const before = { ...statsData };

        // The flash means "a message just landed, while you were watching".
        // Two things have to be true for that, and both were bugs when they
        // weren't checked:
        //
        // 1. The socket has already caught us up. The first push on any
        //    connection is the API handing over its current state, which
        //    covers everything that happened before we were listening — the
        //    gap between the REST snapshot and the socket opening, or on the
        //    gist fallback up to five minutes of messages, arriving as one
        //    jump. That's a sync. It lands silently. (Reconnects too: the
        //    catch-up after a drop isn't news either.)
        //
        // 2. epoch_ms actually MOVED, rather than merely being present. The
        //    bot's per-message push carries only epoch_ms, but the API relays
        //    merged state — every push carries epoch_ms AND heartbeat_epoch_ms
        //    — so a presence test calls the five-minute heartbeat a message.
        //    The heartbeat re-reads the true total from Supabase and almost
        //    always moves the count, so that flashed every five minutes for a
        //    correction nobody sent.
        const isMessageEvent = wsSynced
            && Boolean(data.epoch_ms)
            && data.epoch_ms > (lastMessageMs || 0);
        wsSynced = true;

        applyStatsPayload(data);
        // a push is a snapshot arriving, same as a fetch — while the socket is
        // up, our copy is continuously current and evaluateStatus can trust it
        lastFetchAt = Date.now();
        probeFailures = 0;
        usingFallback = false; // a live push beats anything the gist told us
        applyLiveUpdate(before, isMessageEvent);
        evaluateStatus();
    };

    wsConnection.onclose = () => {
        console.warn(`⚠️ live websocket disconnected. Reconnecting in ${wsRetryMs / 1000}s...`);
        wsConnected = false;
        evaluateStatus();
        setTimeout(connectWebSocket, wsRetryMs);
        wsRetryMs = Math.min(wsRetryMs * 2, WS_RECONNECT_MAX_MS); // stop hammering a dead server
    };

    wsConnection.onerror = (err) => {
        console.error('❌ websocket error:', err);
        wsConnection.close();
    };
}

// ============================================================
// LOAD SEQUENCE
// ============================================================
async function initialLoad() {
    evaluateStatus();      // hasLoadedOnce is still false — shows "connecting" immediately
    startObservingStats(); // watch the board from the start, not just after the fetch

    // Two independent groups, both fired now. The bot's numbers come from the
    // API or the gist; commits and last-update come from Shields.io and have
    // no reason to wait on either.
    const core = loadStats().then(() => {
        hasLoadedOnce = true;
        evaluateStatus();
        // If the board already revealed itself against empty data, write the
        // numbers straight in. Otherwise this is what unblocks the reveal, and
        // overwriting here would kill the count-up before it started.
        if (statsRevealed) refreshVisibleStats();
        else maybeReveal();
    });

    const side = Promise.all([
        loadSideStat(fetchCommitCount, 'updates'),
        loadSideStat(fetchLastUpdate, 'lastUpdate')
    ]);

    await core;
    connectWebSocket();

    if (statsData.serverCount !== null) {
        document.querySelectorAll('[data-cta-servers]').forEach(el => {
            el.textContent = statsData.serverCount.toLocaleString();
        });
    }

    await side;
}

// Safety-net poll: catches a silently-dead websocket, and is the only
// path that fires at all while we're reading from the gist fallback.
async function backgroundRefresh() {
    try {
        await loadStats();
        refreshVisibleStats();
    } catch (e) {
        // network hiccup — staleness timer will flip the status if it persists
    }
    // anything that ran out of retries earlier gets another go from here, so a
    // dashed-out cell can still fill itself in later
    if (failedStats.has('updates')) loadSideStat(fetchCommitCount, 'updates');
    if (failedStats.has('lastUpdate')) loadSideStat(fetchLastUpdate, 'lastUpdate');
    evaluateStatus();
}

// ============================================================
// COUNTERS
// ============================================================
function formatStat(value, suffix, isInt) {
    const text = isInt ? Math.floor(value).toLocaleString() : value.toFixed(2);
    return text + suffix;
}

function setStatText(element, value) {
    if (value === null || value === undefined) {
        // dashes read as "this was meant to say something"; the mask reads as
        // "nothing is coming for this one yet". They aren't the same failure.
        const text = failedStats.has(element.dataset.stat) ? MISSING : MASK;
        writeValue(element, () => { element.textContent = text; });
        return;
    }
    const cell = element.closest('.stat-soon');
    if (cell) cell.classList.add('is-live');

    const text = typeof value === 'string'
        ? value + (element.dataset.suffix || '')
        : formatStat(Number(value), element.dataset.suffix || '', !FLOAT_STATS.has(element.dataset.stat));
    writeValue(element, () => { element.textContent = text; });
}

function animateCounter(element, target, duration = 900, suffix = '', isInt = true) {
    const startTime = performance.now();

    function frame(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        // ease-out so big numbers don't slam to a stop
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = formatStat(target * eased, suffix, isInt);
        // isInt stats now floor + comma every frame — no more fake decimals mid-count
        if (progress < 1) {
            requestAnimationFrame(frame);
        } else {
            element.textContent = formatStat(target, suffix, isInt);
        }
    }
    requestAnimationFrame(frame);
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
            currentText += target[i] === ' ' ? ' ' : chars[Math.floor(Math.random() * chars.length)];
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

// a stat that showed up after the board had already been revealed
function fillLate(statId) {
    if (!statsRevealed) return;
    const el = document.querySelector(`[data-stat="${statId}"]`);
    if (el) setStatText(el, statsData[statId]);
}

// ===== STATS REVEAL (fires once) =====
// Needs both halves: the board on screen, and a first load attempted. The
// observer is armed before the fetch resolves, so whichever happens second
// calls this. A stat with nothing in it yet stays masked and gets written in
// later by fillLate() — nothing waits on Shields.io.
function maybeReveal() {
    if (statsRevealed || !statsInView || !hasLoadedOnce) return;
    statsRevealed = true;

    document.querySelectorAll('[data-stat]').forEach(element => {
        const id = element.dataset.stat;
        const value = statsData[id];

        if (value === null || value === undefined) {
            element.textContent = failedStats.has(id) ? MISSING : MASK;
            return;
        }

        const cell = element.closest('.stat-soon');
        if (cell) cell.classList.add('is-live');

        // count up for numbers, scramble for strings — but open the box to the
        // finished size first, so a value that wraps doesn't snap mid-animation
        const isInt = !FLOAT_STATS.has(id);
        if (typeof value === 'string') {
            const text = value + (element.dataset.suffix || '');
            reserveHeightFor(element, text);
            animateText(element, text, COUNTER_MS);
        } else {
            reserveHeightFor(element, formatStat(Number(value), element.dataset.suffix || '', isInt));
            animateCounter(element, Number(value), COUNTER_MS, element.dataset.suffix || '', isInt);
        }
    });
}

function startObservingStats() {
    const statsSection = document.querySelector('.stats');
    if (!statsSection) return;

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            statsObserver.disconnect();
            statsInView = true;
            maybeReveal();
        });
    }, { threshold: 0.3 });

    statsObserver.observe(statsSection);
}

// ===== KICK EVERYTHING OFF =====
initialLoad();
setInterval(backgroundRefresh, REFRESH_INTERVAL_MS);
setInterval(evaluateStatus, STATUS_TICK_MS);
setInterval(updateLastMessageReadout, 1000); // ticks "Xs ago" smoothly regardless of the slower status check

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
if (REDUCED_MOTION) {
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
