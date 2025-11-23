import discord

async def send_smart_message(destination, text, files=None, is_reply=False):
    """
    Intelligent message sender.
    """
    if not text and not files:
        return

    # Determine the actual send function
    target_send_func = destination.send
    if is_reply and isinstance(destination, discord.Message):
        target_send_func = destination.reply

    # 1. Split by explicit {newmessage} marker
    raw_parts = text.split("{newmessage}")
    total_parts = len(raw_parts)
    
    for i, part in enumerate(raw_parts):
        part = part.strip()
        
        # Only the very last part of the very last split gets the files
        is_last_overall = (i == total_parts - 1)
        current_files = files if is_last_overall else None
        
        if not part and not current_files:
            continue

        # 2. Split by 2000 char limit (The chunker)
        if len(part) <= 2000:
            try:
                await target_send_func(part, files=current_files)
            except discord.HTTPException as e:
                print(f"Error sending message: {e}")
        else:
            await _send_chunked(target_send_func, part, current_files)

async def _send_chunked(send_func, text, files):
    chunks = []
    current_chunk = ""
    in_code_block = False
    code_block_lang = ""
    
    lines = text.split('\n')
    
    for line in lines:
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_lang = line.strip().replace("```", "")
            else:
                if line.strip() == "```":
                    in_code_block = False
        
        if len(current_chunk) + len(line) + 1 > 1900:
            if in_code_block:
                current_chunk += "\n```"
            
            chunks.append(current_chunk)
            
            if in_code_block:
                current_chunk = f"```{code_block_lang}\n{line}"
            else:
                current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line
                
    if current_chunk:
        chunks.append(current_chunk)
        
    for i, chunk in enumerate(chunks):
        is_last = (i == len(chunks) - 1)
        chunk_files = files if is_last else None
        try:
            await send_func(chunk, files=chunk_files)
        except discord.HTTPException as e:
            print(f"Error sending chunk: {e}")