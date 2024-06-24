from PIL import Image, ImageDraw, ImageFont


pfp_1 = Image.open('pfp_1.png')
pfp_2 = Image.open('pfp_2.png')
bg = Image.open('bg.png')


bg_img = bg.convert("RGBA")
pfp_1_img = pfp_1.convert("RGBA")
pfp_2_img = pfp_2.convert("RGBA")


pos1 = (0, 250)
pos2 = (1000, 250)


bg_img.paste(pfp_1_img, pos1, pfp_1_img)
bg_img.paste(pfp_2_img, pos2, pfp_2_img)


bg_img.save('result_image.png')

image = Image.open("result_image.png")
draw = ImageDraw.Draw(image)
text = "Hello, World!"
font_size = 360  # Specify the font size in points
font = ImageFont.load_default()  # Default font
# If you have a TrueType font file (.ttf), you can load it like this:
# font = ImageFont.truetype("arial.ttf", size=36)
position = (750, 250)  # Top-left corner
draw.text(position, text, fill="white", font=font,)
image.save('image_with_text.png')
