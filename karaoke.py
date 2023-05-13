# powerpoint-karaoke-generator/1.0
# chrifren@ifi.uio.no

import os
import re
import openai
import datetime
from base64 import b64decode

from apikeys import openai_api_key
from apikeys import openai_organization

openai.organization = openai_organization
openai.api_key = openai_api_key
model = "gpt-3.5-turbo" #"gpt-4"



#
# OpenAI stuff
#

# complete something with openai gpt
def complete(text, grounding=""):
    response = openai.ChatCompletion.create(
        model=model,
        messages = [
            { "role": "system", "content": grounding},
            { "role": "system", "content": text}
        ],
        max_tokens=500,
        temperature=0.9,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response.choices[0].message.content

# create image from text using openai, output to image.png
def create_image(text, file_name):
    response = openai.Image.create(prompt=text,response_format="b64_json",n=1,size="512x512")
    img_data = b64decode( response.data[0].b64_json )
    with open(file_name, "wb") as fh:
        fh.write(img_data)



#
# Document generation stuff
#

# get current directory
def get_current_directory():
    return os.getcwd()

# produce output
def run_docker_pandoc(template_file_name, output_file_name):
    cur_dir = get_current_directory()
    os.system("sudo docker run --rm --volume {}:/data pandoc/latex {} -o {}".format(cur_dir, template_file_name, output_file_name))
    os.system("sudo docker run --rm --volume {}:/data pandoc/latex -t DZSlides -s {} -o output.html".format(cur_dir, template_file_name, output_file_name))



#
# Main control stuff
# 

grounding = """You are a writer producing a script for a speach. Based on the topic
   provided, select a title for the speach. Create five sections for the speach,
   each with three bullet points. Each bullet point should be a sentence or two.
   Output the content in markdown format.
"""

print("Welcome to the powerpoint karaoke generator!")
prompt = input("Prompt: ")
print("Generating slides...")

# title
title = complete("Create a title consisting of maximum 10 words for a speach about " + prompt, "")
title.strip("\n\t\"")
print("Title: " + title)

# main topics
topics = complete("Based on the title \"{}\" create titles of max 10 words for five sections of the talk as a numbered list.".format(title))
topics = re.sub(r"^\d+\.\s+", "", topics, flags=re.MULTILINE)


# content of each topic
p_stored = []
for i, n in enumerate( topics.split("\n") ):
    print("> Topic: " + n)
    points = complete("Based on the title \"{}\" create three bullet points of max 7 words for the section \"{}\", output as a numbered list.".format(title, n))
    points = re.sub(r"^\d+\.\s+", "", points, flags=re.MULTILINE)
    for n in points.split("\n"):
        print("  > " + n)
    p_stored.append(points)

    # create illustration
    image_prompt = complete("Based on the title \"{}\" create an prompt for DALLE to create a creative photo, 3d-art or illustration for the section \"{}\" where the main points are {}.".format(title, n, points), "")
    create_image(image_prompt, "img_{}.png".format(i))

# save text to template.md
date = datetime.datetime.now().strftime("%B %d, %Y") # format todays date as month name day, year
with open("template.md", "w") as fh:
    fh.write("% " + title + "\n")
    fh.write("% DeckDazzle/1.0" + "\n")
    fh.write("% " + date + "\n")
    fh.write("\n")
    
    for i, n in enumerate( topics.split("\n") ):
        fh.write("## " + n + "\n")

        fh.write(":::::::::::::: {.columns}\n")
        fh.write("::: {.column width=\"50%\"}\n")
        
        for m in p_stored[i].split("\n"):
            fh.write("- " + m + "\n")
        fh.write("\n")

        fh.write(":::\n")
        fh.write("::: {.column width=\"50%\"}\n")

        fh.write("![](img_{}.png)\n".format(i))
        fh.write("\n")
        fh.write(":::\n")
        fh.write("::::::::::::::\n")

        fh.write("::: notes\n")
        fh.write(p_stored[i] + "\n")
        fh.write(":::\n")
        fh.write("\n")

# build powerpoint
run_docker_pandoc("template.md", "output.pptx")




