// ===== CONFIGURATION =====
const GIST_RAW_URL = 'https://gist.githubusercontent.com/Mistromy/cdb82a1247ae6095f5d43098eb074dba/raw/stats.json';
const DISCORD_INVITE_URL = 'https://discord.com/oauth2/authorize?client_id=1209887142839586876&permissions=8&integration_type=0&scope=bot';

let statsData = {
    serverCount: null,
    userCount: null,
    uptime: null,
    updates: null
};

// ===== MODAL LOGIC =====
const modal = document.getElementById('invite-modal');
const openModalBtn = document.getElementById('open-modal-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const tosCb = document.getElementById('tos-cb');
const adminCb = document.getElementById('admin-cb');
const proceedBtn = document.getElementById('proceed-btn');

openModalBtn.addEventListener('click', () => {
    modal.classList.remove('hidden');
});

closeModalBtn.addEventListener('click', () => {
    modal.classList.add('hidden');
});

// Close modal when clicking outside the content box
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.add('hidden');
    }
});

function validateCheckboxes() {
    if (tosCb.checked && adminCb.checked) {
        proceedBtn.classList.remove('disabled');
        proceedBtn.href = DISCORD_INVITE_URL;
    } else {
        proceedBtn.classList.add('disabled');
        proceedBtn.removeAttribute('href');
    }
}

tosCb.addEventListener('change', validateCheckboxes);
adminCb.addEventListener('change', validateCheckboxes);


// ===== STATS LOGIC =====
function initPlaceholders() {
    ['serverCount', 'userCount', 'uptime', 'updates'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.textContent = '---';
    });
}
initPlaceholders();

function animateCounter(element, target, duration = 800, suffix = '') {
    const start = 0;
    const increment = target / (duration / 16); 
    let current = start;
    const isFloat = target % 1 !== 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        const formatted = isFloat ? current.toFixed(1) : Math.floor(current).toLocaleString();
        element.textContent = formatted + suffix;
    }, 16);
}

function startObservingStats() {
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                statsObserver.disconnect();
                Object.keys(statsData).forEach(key => {
                    const element = document.getElementById(key);
                    if (element) {
                        if (statsData[key] === null || statsData[key] === undefined) {
                            element.textContent = '---';
                        } else {
                            const suffix = key === 'uptime' ? '%' : '';
                            animateCounter(element, statsData[key], 800, suffix);
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

async function fetchLiveStats() {
    try {
        const response = await fetch(`${GIST_RAW_URL}?_=${Date.now()}`);
        if (!response.ok) throw new Error('Failed to fetch from Gist');
        
        const data = await response.json();
        if (data.guild_count !== undefined) statsData.serverCount = data.guild_count;
        if (data.user_count !== undefined) statsData.userCount = data.user_count;
        if (data.uptime !== undefined) statsData.uptime = data.uptime;
    } catch (error) {
        console.error('Could not load live stats.', error);
    }

    try {
        const commitsUrl = 'https://img.shields.io/github/commit-activity/t/Mistromy/NIrupama.json';
        const response = await fetch(commitsUrl);
        if (!response.ok) throw new Error('Failed to fetch from Shields.io');
        
        const data = await response.json();
        if (data.value !== undefined) {
            statsData.updates = parseInt(data.value, 10);
        }
    } catch (error) {
        console.error('Could not load commit stats.', error);
    } finally {
        startObservingStats();
    }
}

fetchLiveStats();