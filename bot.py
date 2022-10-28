import telegram.ext
import telepot
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import json
import fitz
import os.path
import os
import datetime
import pytz
import random

# THINGS THIS BOT CAN DO
# Creating a vocabulary list translating, adding, deleting words, clearing list, showing words
# Sending the menu of my school's cafeteria
# Sends weather stats
# To-Do stuff
# Checks watchlist
# Reminding things perioadically

# FUTURE PLANS

# Creating assets directory
if not os.path.exists("assets"):
    os.mkdir("assets") 

# Your Telegram Bot token
with open("token.txt", "r") as f:
    TOKEN = f.read()

# Passing TOKEN to bot for future use
bot = telepot.Bot(TOKEN)

# Use @userinfobot to find your user id
# You need User Id to make bot personal
with open("user_id.txt", "r") as f:
    USER_ID = f.read()

# Your timezone
timezone = 'Europe/Istanbul'

# The name for bot to call you
name = "Serkan"

# Paths to files
path_to_todo_file = "assets/todo.txt"
path_to_words_file = "assets/words.json"

def start(update, context):
    # It's a personal bot, so we are checking is it really us who writing
    if update.message.from_user["id"] == USER_ID:
        update.message.reply_text(f"Hello {name}, welcome back.\nUse /help to see commands.")
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

def help(update, context):
    if update.message.from_user["id"] == USER_ID:
        update.message.reply_text("""
    The following commands are available:
        
    /start -> Welcome Message
    /help -> This Message
    /menu day -> Sends The Menu Of The Day
    /menu month -> Sends The Menu Of The Month
    /helpvocabulary -> How To Use Vocabulary List
    /helptodo -> How To Use To-Do List
    /weather -> Sends The Weather Stats

    -----------------------------------------------
    Other than above:

    -Sends the weather automatically in the morning.
    -Sends the cafeteria menu automatically.
    -Sends night and morning messages automatically.
    -Sends the lesson schedule automatically.
    -Checks your watchlist to prevent you from adding too much films.
        """)
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

# This function is a need for send_daily_menu and menu functions
# I wanted two things: Bot should send the menu automatically and I should be able to ask it with writing /menu day
# So I'm using this function to make it less repetitive
def get_information_for_menu():
    # Finding p tags that involves photo of menu and the pdf of monthly menu
    url = "http://w3.bilecik.edu.tr/sks/beslenme-hizmetleri-2/yemek-menusu/"

    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    
    pTags = soup.find_all("p")

    return pTags

# A function to send menu
def send_daily_menu(context):
    pTags = get_information_for_menu()

    # Searching the image in other Tags
    for imgTag in pTags:
        if imgTag.img != None:
            img = imgTag.img
            
    img = img["src"]
    bot.sendPhoto(USER_ID, img)

# A function to ask menu with /menu day or /menu month
def menu(update, context):
    if update.message.from_user["id"] == USER_ID:
            # Scraping image and sending it
            try:
                # Checking the type of menu: Day or Month
                if context.args[0] == "day":
                    send_daily_menu(context)

                # Searching the pdf
                elif context.args[0] == "month":
                    pTags = get_information_for_menu()
                    for aTag in pTags:
                        try:
                            if "menu" in aTag.a["href"]:
                                pdf = aTag.a["href"]
                        except:
                            continue
                    
                    response = requests.get(pdf) 
                    # Sometimes my school uploads it as pdf sometimes png so we are checking it
                    if ".pdf" in pdf:
                        # Downloading the pdf file
                        with open("assets/foodmenu.pdf", "wb") as f:
                            f.write(response.content)

                        # Taking a picture of pdf file
                        pdffile = "assets/foodmenu.pdf"
                        doc = fitz.open(pdffile)
                        page = doc.load_page(0)  # Number of page
                        pix = page.get_pixmap()
                        output = "assets/foodmenu.png"
                        pix.save(output)
                    elif ".png" in pdf:
                        with open("assets/foodmenu.png", "wb") as f:
                            f.write(response.content)                                          
                    
                    bot.sendPhoto(USER_ID, photo=open('assets/foodmenu.png', 'rb'))
            except Exception as e:
                print(e)
                update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
                # Todo: If there isn't any photo scrape headings
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

#---VOCABULARY STUFF STARTS---
def helpVocabulary(update, context):
    if update.message.from_user["id"] == USER_ID:
        update.message.reply_text("""
    COMMANDS
    /addword my furniture -> Adds a new word to list.
    /delword my furniture -> Deletes a word from list.
    /showword -> Shows the words.
    /clearword -> Clears the list.
        """)
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

# A function to translate words
def translate(word):
    return GoogleTranslator(source='english', target='tr').translate(word).lower()

# Check if the word exist already
def checkExisting(word):
    with open(path_to_words_file, "r") as f:
        isEmpty = f.readline()
    
    # If the json file empty, checkExisting func will throw an error so
    # We're checking the emptiness
    # I'm pretty sure there are better ways to this but it is what it is
    if isEmpty == "":
        # Returns true if file empty
        return True

    # Loading the json file
    with open(path_to_words_file, "r") as f:
        json_object = json.load(f)
    
    # Searching the new word in json file to check is it already added
    for w in json_object["words"]:
        if w["word"] == word:
            # Returns False if the word is already added
            return False

    return True
    # Returns True if the word is not added

def addWord(update, context):
    try:
        # Getting a full phrase, args are these:
        # /menu arg1 arg2 arg3...
        word = ""
        for i in range(len(context.args)):
            word += context.args[i] + " "

        # Translating the word
        translation = translate(word)
        
        if checkExisting(word):     
            with open(path_to_words_file, "r") as f:
                isEmpty = f.readline()
        
            # Create a sample json structure if the json empty
            if isEmpty == "":
                word_list = {
                    "words": [
                        {
                            "word": word,
                            "translation": translation
                        }
                    ]
                }

                # Dumping and writing the sample
                json_string = json.dumps(word_list, indent=2)

                with open(path_to_words_file, "w") as f:
                    f.write(json_string)
            else:
                with open(path_to_words_file, "r") as f:
                    json_object = json.load(f)

                # If the json file is not empty
                vocabularyTemplate = {'word': word, 'translation': translation}

                # Adding new word to json_object
                json_object["words"].append(vocabularyTemplate)

                json_string = json.dumps(json_object, indent=2)

                # Write the json object as new version
                with open(path_to_words_file, "w") as f:
                    f.write(json_string)
            
            update.message.reply_text(f"Okay, I added {word} -> {translation}.")
        else:
            update.message.reply_text(f"{word} -> {translation} is already in the list.")
    except Exception as e:
        print(e)
        update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")

def delWord(update, context):
    # Pretty much same idea with addWord
    try:
        word = ""
        for i in range(len(context.args)):
            word += context.args[i] + " "

        if checkExisting(word):
            update.message.reply_text(f"{word} is not added to your vocabulary list.")
        else:
            # Deleting the word and creating the new json file
            with open(path_to_words_file, "r") as f:
                json_object = json.load(f)
            
            # Not the best way because it could cause an error if translation changes
            translation = translate(word)

            vocabularyTemplate = {'word': word, 'translation': translation}
            
            json_object["words"].remove(vocabularyTemplate)

            new_json_object = json.dumps(json_object, indent=2)

            # Writing the new version of file
            with open(path_to_words_file, "w") as f:
                f.write(new_json_object)

            update.message.reply_text(f"Okay, I deleted {word} -> {translation}. 🧹")
    except Exception as e:
        print(e)
        update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")

# Cleaning word list
def clearWord(update, context):
    try:
        with open(path_to_words_file, "w") as f:
            update.message.reply_text(f"I cleaned the list, {name}.")
    except Exception as e:
        print(e)
        update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")

def showWord(update, context):
    try:
        with open(path_to_words_file, "r") as f:
            isEmpty = f.readline()

        if isEmpty != "":
            # Loading word list
            with open(path_to_words_file, "r") as f:
                json_object = json.load(f)

            string = ""
            message = f"There are {len(json_object['words'])} words in the list.\n"

            # Writing word list
            for keyValue in json_object["words"]:
                string = f"{keyValue['word']} -> {keyValue['translation']}\n"
                message+=string
            
            update.message.reply_text(message)
        else:
            # If it is empty
            update.message.reply_text("There is nothing to show.")
    except Exception as e:
        print(e)
        update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
#---VOCABULARY STUFF ENDS---

# Seperating weather and weather_daily is a must as I understand to make it work properly with /weather and job_queue
def weather_daily(context):
    # Your OPEN API key
    with open("key.txt", "r") as f:
        KEY = f.read()

    # Your lat and lon
    lat = "40.144691"
    lon = "29.982059"

    API = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&appid={KEY}"
    
    r = requests.get(API)
    
    json_object = json.loads(r.content)
    
    current_temp = round(int(json_object["current"]["temp"]))
    feels_like = round(int(json_object["current"]["feels_like"]))
    daily_temp_max = round(int(json_object["daily"][0]["temp"]["max"]))
    daily_temp_min = round(int(json_object["daily"][0]["temp"]["min"]))
    description = json_object["daily"][0]["weather"][0]["description"]

    message = f"""
WEATHER
Current Tempature: {current_temp}°
Feels Like: {feels_like}°
Maximum Tempature: {daily_temp_max}°
Minimum Tempature: {daily_temp_min}°
Description: {description.capitalize()} 
        """
    
    bot.sendMessage(USER_ID, message) 

# A function to send weather daily
def weather(update, context):
    if update.message.from_user["id"] == USER_ID:
        try:
            weather_daily(context)
        except Exception as e:
            print(e)
            update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

#---TO DO STUFF STARTS---
def helpTodo(update, context):
    if update.message.from_user["id"] == USER_ID:
        update.message.reply_text("""
    COMMANDS
    /addtodo odayı temizle -> Adds a new to-do to list.
    /deltodo bulaşıkları yıka -> Deletes a to-do from list.
    /showtodo -> Shows the to-do list.
    /cleartodo -> Clears the to-do list.
        """)
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

def addTodo(update, context):
    if update.message.from_user["id"] == USER_ID:
        try:
            # Check if txt file already exist
            if not os.path.exists(path_to_todo_file):
                with open(path_to_todo_file, "w") as f:
                    f.write("")

            # Read the todo items
            with open(path_to_todo_file, "r") as f:
                    items = len(f.readlines())

            todo = ""

            # Add items to todo string and put a space between words
            for i in range(len(context.args)):
                todo += context.args[i]
                if i != len(context.args) - 1:
                    todo += " "

            # Add new todo to txt
            with open (path_to_todo_file, "a", encoding="utf-8") as f:
                f.write(f"{items+1}- {todo}\n")
                # Editing it to make it look better

            update.message.reply_text(f"Okay, I added {todo}.")
        except Exception as e:
            print(e)
            update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
    else:
        update.message.reply_text("You are not worthy to use this Bot.")


def delTodo(update, context):
    if update.message.from_user["id"] == USER_ID:
        try:
            # Check if txt file already exist
            if os.path.exists(path_to_todo_file):
                # Item's number to delete
                delIndex = context.args[0]

                # Todo items
                with open(path_to_todo_file, "r", encoding = "utf-8") as f:
                    todos = f.readlines()

                # Removing item
                for i in todos:
                    # i[0:3] checking first 3 letters like 12-
                    if delIndex in i[0:3]:
                        todos.remove(i)
                        item = i

                # Rearanging the numbers
                j = 1
                new_array = []
                for todo in todos:
                    rank = ""
                    # Getting the current rank of todo so we can replace it
                    for letter in todo:
                        if letter == "-":
                            break
                        else:
                            rank += letter
                    new_array.append(todo.replace(rank, str(j)))
                    j+=1


                # Writing the file again
                with open(path_to_todo_file, "w", encoding = "utf-8") as f:
                    for todo in new_array:
                        f.write(todo)

                # Deleting item's last word(\n) and number to make it look better
                item = item.replace(item[-1], "")
                item = item.replace(item[0:3], "")
                update.message.reply_text(f"Okay, I deleted {item}. 🧹")
            else:
                update.message.reply_text("You didn't create a to-do list yet.")
        except Exception as e:
            print(e)
            update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

# I thinked this function is not neccessariy but can be used.
def checkExistingTodo(update, context):
    pass

def clearTodo(update, context):
    if update.message.from_user["id"] == USER_ID:
        try:
            # Check if txt file already exist
            if os.path.exists(path_to_todo_file):
                with open(path_to_todo_file, "w") as f:
                    pass
                
                update.message.reply_text("Okay, I cleaned the to-do list. 🧹")
            else:
                update.message.reply_text("You didn't create a to-do list yet.")
        except Exception as e:
            print(e)
            update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
    else:
        update.message.reply_text("You are not worthy to use this Bot.")

def showTodo(update, context):
    if update.message.from_user["id"] == USER_ID:
        try:
            # Check if txt file already exist
            if os.path.exists(path_to_todo_file):
                with open(path_to_todo_file, "r", encoding="utf-8") as f:
                    todos = f.read()

                update.message.reply_text(f"""To-Do:
{todos}""")          
            else:
                update.message.reply_text("You didn't create a to-do list yet.")
        except Exception as e:
            print(e)
            update.message.reply_text(f"I'm sorry {name}, I'm afraid I can't do that.")
    else:
        update.message.reply_text("You are not worthy to use this Bot.")
#---TO DO STUFF ENDS---

# A function to check my letterboxd watchlist and send a warning if it has more than 30 movies because
# I add movies constantly and never watch them 😐
def checkWatchlist(context):
    # Your watchlist link, it should be public
    url = "https://letterboxd.com/serkanbayram/watchlist/"

    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")

    # Finds the text
    text = soup.find("h1", class_="section-heading").text

    number = ""

    # Checking the movie number
    for letter in text:
        if letter.isdigit():
            number += letter
    
    if int(number) >= 30:
        bot.sendMessage(USER_ID, f"You should remove {int(number)-29} films from your watchlist to keep it below 30 {name}.")

# A function to send lesson schedule
# You should create a schedule sample within a json file first to use this function just like mine
# It doesn't create a one if it doesn't exist
def sendLessonSchedule(context):
    with open("assets/lessons.json", "r", encoding="utf-8") as f:
        json_file = json.load(f)

    # Timezone is a must because when you put the code in server it has a different timezone
    tz = pytz.timezone(timezone)

    # Getting the next day
    now = datetime.datetime.now(tz) + datetime.timedelta(days=1)

    # %A is makes the return value monday instead of 1
    nextDay = now.strftime("%A").lower()

    schedule = f"Here is tomorrow's lesson schedule {name}.\n"

    # Searching the schedule
    for day in json_file["lessons"]:
        if day["day"] == nextDay:
            for lesson in day["schedule"]:
                schedule += lesson + "\n"

    bot.sendMessage(USER_ID, schedule)

# Two functions to send morning and night messages
# Can be improved
def morningMessage(context):
    messages = [f"Good morning {name}!", f"Good morning {name}, hope you got your sleep well.", "Good morning! 🌅", f"Good morning {name}, was it a good sleep?"]

    message = random.choice(messages)

    bot.sendMessage(USER_ID, message)

def nightMessage(context):
    messages = [f"Good night {name}!", f"Good night {name}, hope you'll get your sleep well.", "Good night! 🌃"]

    message = random.choice(messages)

    bot.sendMessage(USER_ID, message)

# A function to remind drink water
def drinkWater(context):
    tz = pytz.timezone(timezone)

    now = datetime.datetime.now(tz)

    # Starts reminding after 5 pm until 10 pm every half hour, the timezone that I'm at home
    if now.hour > 17 and now.hour < 22:
        bot.sendMessage(USER_ID, "Drink 1 glass of water.")

    # Stopping the function at 10pm
    if now.hour == 22 and now.minute == 00:
        bot.sendMessage(USER_ID, "Great! You drank 2 liters of water approximately. 🎉")

# Repeating functions
def setTimer(update, context):
    try:
        # 0: Monday 1: Tuesday ...
        # Weather
        context.job_queue.run_daily(weather_daily, context=USER_ID, days=(0, 1, 2, 3, 4, 5, 6), time=datetime.time(hour=6, minute=5, second=00, tzinfo=pytz.timezone(timezone)))
        # Cafeteria menu
        context.job_queue.run_daily(send_daily_menu, context=USER_ID, days=(0, 1, 2, 3, 4), time=datetime.time(hour=11, minute=00, second=00, tzinfo=pytz.timezone(timezone)))
        # Lesson schedule
        context.job_queue.run_daily(sendLessonSchedule, context=USER_ID, days=(0, 1, 2, 3, 6), time=datetime.time(hour=21, minute=00, second=30, tzinfo=pytz.timezone(timezone)))
        # Morning and night messages
        context.job_queue.run_daily(morningMessage, context=USER_ID, days=(0, 1, 2, 3, 4, 5, 6), time=datetime.time(hour=6, minute=00, second=00, tzinfo=pytz.timezone(timezone)))
        context.job_queue.run_daily(nightMessage, context=USER_ID, days=(0, 1, 2, 3, 4, 5, 6), time=datetime.time(hour=23, minute=00, second=00, tzinfo=pytz.timezone(timezone)))


        context.job_queue.run_repeating(checkWatchlist, 3600, context=USER_ID, first=1)    
        context.job_queue.run_repeating(drinkWater, 1800, context=USER_ID, first=1)    
    except Exception as e:
        print(e)
        context.bot.send_message(USER_ID, f"I'm afraid there is a problem about one of the repeating functions {name}.")

# You can modify here like what you want
def handle_message(update, context):
    if update.message.from_user["id"] == USER_ID:
        pass
    else:
        update.message.reply_text("You are not worthy to use this Bot.")


updater = telegram.ext.Updater(TOKEN, use_context=True)
disp = updater.dispatcher

# Starting timers
# I'm not pretty sure about the parameters
setTimer(disp, updater)

# Adding commands to the dispatcher
disp.add_handler(telegram.ext.CommandHandler("start", start))
disp.add_handler(telegram.ext.CommandHandler("help", help))
disp.add_handler(telegram.ext.CommandHandler("menu", menu))
disp.add_handler(telegram.ext.CommandHandler("helpvocabulary", helpVocabulary))
disp.add_handler(telegram.ext.CommandHandler("addword", addWord))
disp.add_handler(telegram.ext.CommandHandler("showword", showWord))
disp.add_handler(telegram.ext.CommandHandler("clearword", clearWord))
disp.add_handler(telegram.ext.CommandHandler("delword", delWord))
disp.add_handler(telegram.ext.CommandHandler("weather", weather))
disp.add_handler(telegram.ext.CommandHandler("helptodo", helpTodo))
disp.add_handler(telegram.ext.CommandHandler("addtodo", addTodo))
disp.add_handler(telegram.ext.CommandHandler("deltodo", delTodo))
disp.add_handler(telegram.ext.CommandHandler("showtodo", showTodo))
disp.add_handler(telegram.ext.CommandHandler("cleartodo", clearTodo))
disp.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, handle_message))

updater.start_polling()
updater.idle()