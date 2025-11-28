import PIL
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import aiohttp
from html2image import Html2Image


from utils.logger import bot_log

htmltoimage = Html2Image(size=(900,350), browser_executable=r"F:\vivaldi\Application\vivaldi.exe")  # Path to your browser executable



def generateimage(avatar1, avatar2, name1, name2, percent, comment):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,600;0,800;1,500&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
                /* This ensures no white borders around the capture */
                display: flex;
                justify-content: center;
                align-items: center;
                background: #000; /* Just so you can see the edges in browser */
            }}

            /* THE MAIN CANVAS - MATCH THIS TO YOUR IMAGE SIZE */
            .card {{
                width: 900px;   /* <--- CHANGE TO BG.PNG WIDTH */
                height: 350px;  /* <--- CHANGE TO BG.PNG HEIGHT */
                
                /* Background Logic */
                background-image: url('D:/HAX/python/discord bots/Nirupama/bg.png');
                background-size: cover; 
                background-position: center;
                background-repeat: no-repeat;
                
                /* Layout Logic */
                display: flex;
                flex-direction: column; /* Stack top (avatars) and bottom (text) */
                justify-content: center; /* Center vertically */
                align-items: center;     /* Center horizontally */
                overflow: hidden;        /* Cut off anything sticking out */
                font-family: 'Poppins', sans-serif;
                position: relative;
            }}

            /* --- TOP SECTION: Avatars & Score --- */
            .top-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 80%; /* Width of the content area */
                margin-bottom: 20px; /* Space between avatars and text box */
            }}

            .user-group {{
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }}

            .pfp {{
                width: 130px;
                height: 130px;
                border-radius: 50%;
                border: 5px solid rgba(255,255,255,0.9);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                object-fit: cover;
            }}

            .name-tag {{
                margin-top: 8px;
                background: rgba(0,0,0,0.6);
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
            }}

            .center-score {{
                text-align: center;
                color: white;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }}

            .percent-text {{
                font-size: 90px;
                font-weight: 800;
                line-height: 1;
                margin: 0;
            }}

            .status-text {{
                background: white;
                color: #b30000;
                padding: 2px 10px;
                border-radius: 4px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1px;
                display: inline-block;
            }}

            /* --- BOTTOM SECTION: The Quote Box --- */
            .quote-container {{
                width: 700px;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 15px 30px;
                position: relative; /* Needed for the quote marks */
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                
                /* Text Styling */
                color: #555;        /* Dark Grey */
                font-size: 18px;
                font-style: italic; /* Italics */
                text-align: center;
                line-height: 1.4;
            }}

            /* The Big Quote Mark Visual */
            .quote-container::before {{
                content: "“";
                position: absolute;
                top: -20px;
                left: 20px;
                font-size: 80px;
                color: #b30000; /* Match your red theme */
                font-family: serif;
                line-height: 1;
            }}
        </style>
    </head>
    <body>

        <div class="card">
            
            <div class="top-row">
                <div class="user-group">
                    <img class="pfp" src="{avatar1}">
                    <div class="name-tag">"{name1}""</div>
                </div>

                <div class="center-score">
                    <div class="percent-text">"{percent}%"</div>
                    <div class="status-text"></div>
                </div>

                <div class="user-group">
                    <img class="pfp" src="{avatar2}">
                    <div class="name-tag">"{name2}"</div>
                </div>
            </div>

            <div class="quote-container">
                comment
            </div>

        </div>

    </body>
    </html>
    """

    outputfile = "ship_result.png"
    try:
        htmltoimage.screenshot(get_html=html_content, save_as=outputfile, size=(900,350))
        return outputfile
    except Exception as e:
        bot_log(f"Error generating ship image: {e}", level="error")
        return None