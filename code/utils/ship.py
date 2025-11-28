import asyncio
import random
from discord import Member, Guild
from utils.logger import bot_log
from utils.ai_interface import query_ai

async def calculate_ship_percentage(user1: Member, user2: Member, guild: Guild):
    # 1. Start with a chaotic neutral base
    base_score = random.randint(30, 70)
    modifiers = 0
    log = [] # We will pass this to the AI later for context

    # --- 1. The "Self-Love" Check ---
    if user1.id == user2.id:
        return 100, ["Narcissism is the purest love."]

    # --- 2. The "Bot" Check ---
    if user1.bot or user2.bot:
        modifiers -= 15
        log.append("Robophobia (Human-AI relations are complicated)")

    # --- 3. Activity Sync (The "Vibe" Check) ---
    # Check if both have activities
    if user1.activity and user2.activity:
        if user1.activity.name == user2.activity.name:
            modifiers += 25
            log.append(f"Gaming Soulmates (Both playing {user1.activity.name})")
        elif str(user1.status) == str(user2.status):
            modifiers += 5
            log.append(f"Status Sync (Both are {user1.status})")
    
    # Special: Both on DND
    if str(user1.status) == "dnd" and str(user2.status) == "dnd":
        modifiers += 10
        log.append("Do Not Disturb... us")

    # --- 4. Historical Data (The "Timeline" Check) ---
    # Joined Server close together
    if user1.joined_at and user2.joined_at:
        days_diff = abs((user1.joined_at - user2.joined_at).days)
        if days_diff < 7:
            modifiers += 20
            log.append("Joined at the hip (Joined same week)")
        elif days_diff < 30:
            modifiers += 10
            log.append("Newbie Buddies")

    # Account Age Similarity
    if abs((user1.created_at - user2.created_at).days) < 30:
        modifiers += 10
        log.append("Born under the same star (Accounts created same month)")

    # --- 5. Social Hierarchy (The "Role" Check) ---
    # Shared Roles (excluding @everyone)
    shared_roles = set(user1.roles) & set(user2.roles)
    shared_roles = [r for r in shared_roles if not r.is_default]
    
    if len(shared_roles) > 5:
        modifiers += 15
        log.append("Role Mates (Inseparable social circles)")
    
    # Power Dynamic
    u1_admin = user1.guild_permissions.administrator
    u2_admin = user2.guild_permissions.administrator
    
    if u1_admin and u2_admin:
        modifiers += 20
        log.append("Power Couple (Both Admins)")
    elif (u1_admin and not u2_admin) or (u2_admin and not u1_admin):
        modifiers -= 10
        log.append("Boss/Employee Dynamic (Scandalous!)")

    # --- 6. Nitro/Booster Status ---
    if user1.premium_since and user2.premium_since:
        modifiers += 15
        log.append("Sugar Daddies/Mommies (Both Boosters)")

    # --- 7. Name Compatibility (Numerology-ish) ---
    if user1.display_name[0].lower() == user2.display_name[0].lower():
        modifiers += 5
        log.append("Alliteration Attraction")
    
    if len(user1.display_name) == len(user2.display_name):
        modifiers += 5
        log.append("Perfectly Balanced Names")

    # --- Final Calculation ---
    final_score = base_score + modifiers
    final_score = max(0, min(100, final_score))
    
    ai_comment = await query_ai(prompt = f"""
    Write a short, funny, and edgy comment (max 20 words) for a compatibility test between {user1} and {user2}.
    
    The Score: {final_score}%
    The Factors: {log}
    
    If the score is low, be savage. If high, be hype. Mention the factors if they are funny.
    """)
    return final_score, log, ai_comment
    
