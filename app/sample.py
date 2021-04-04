from flask import Flask, request, jsonify
from pymongo import MongoClient
import os, json, redis

# App
application = Flask(__name__)

# connect to MongoDB
mongoClient = MongoClient('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_AUTHDB'])
db = mongoClient[os.environ['MONGODB_DATABASE']]

# connect to Redis
redisClient = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379), db=os.environ.get("REDIS_DB", 0))

gameCollection = db.game

@application.route('/')
def index():
    body = '<h2>Guessing Game</h2>'
    # body += '<a>Start</a>'
    body += '<a href="http://localhost/game">Start</a>'
    return body


@application.route('/game', methods=['GET', 'POST'])
def game():
    body = ''
    body += '<form method="post">'

    
    input = request.form.get('submit_button')  # check for button input
    mydoc = gameCollection.find_one()

    if input:  # if there is an input
        mode = mydoc['mode']
        if input == "finish":
            mode = "guess"
            updated_content = {'$set': {'mode' : mode}}    
            gameCollection.update_one(mydoc, updated_content)
        elif input in ['A','B','C','D']:
            press_letter(input, mydoc, mode)
        elif input == "reset":
            reset_game(mydoc)
    else:
        reset_game(mydoc)

    mydoc = gameCollection.find_one()
    word = mydoc['word']
    size = len(word)
    mode = mydoc['mode']
    count = mydoc['count']
    index = mydoc['index']
    dword = word

    if mode == "guess":
        dword = word[0:index]    # characters correct so far
        dword += '*'*(size-index)  # characters remaining

    if mode == 'input':
        body += '<div>input 4 or more letters</div>'
    display_word = f'<div><textarea name="display_word" rows="4" cols="50" readonly>{dword}</textarea></div>'
    
    body += display_word
    body += '<input type="submit" name="submit_button" value="A">' 
    body += '<input type="submit" name="submit_button" value="B">'
    body += '<input type="submit" name="submit_button" value="C">' 
    body += '<input type="submit" name="submit_button" value="D">'
    body += '<div>'

    if  mode == "input" and size >= 4:  # need to input at least 4 letters
        body += '<input type="submit" name="submit_button" value="finish">'  
    if size > 0:  # need to input at least 1 letter
        body += '<input type="submit" name="submit_button" value="reset">'
    body += '</div>'  
    body += '</form>'

    if mode == 'guess':
        body += f'<div>count = {count}</div>'
        if  index == size:  # Do you win yet?
            body += '<div><h2>You Win!</h2></div>'
    return body



def press_letter(input, mydoc, mode):
    word = mydoc['word']
    size = len(word)
    if mode == 'input':
        word += input
        updated_content = {'$set': {'word' : word}}
        gameCollection.update_one(mydoc, updated_content)
    elif mode == 'guess':
        index = mydoc['index']
        count = mydoc['count']
        if index < size:
            if input == word[index]:
                index += 1
            count += 1 
            updated_content = {'$set': {'index' : index, 'count' : count}}    
            gameCollection.update_one(mydoc, updated_content)



def reset_game(mydoc):
    if mydoc == None:
        mydoc = {
                "count": 0,			# number of attempts
                "word": "",			
                "index": 0,			# current letter to guess/correct characters so far
                "mode": "input"
            }
        gameCollection.insert_one(mydoc)
    else:  # document already exist
        updated_content = {"$set": {
                "count": 0,			
                "word": "",						
                "index": 0,
                "mode": "input"
            }}
        gameCollection.update_one(mydoc, updated_content)  # reuse document


# Collection WordGuess
# {
# 	count: integer,			# number of attempts
# 	word: string,			
# 	size: integer,			# the size of the word array
# 	index: integer,			# current letter to guess/correct characters so far
# }



@application.route('/sample')
def sample():
    doc = db.test.find_one()
    # return jsonify(doc)
    body = '<div style="text-align:center;">'
    body += '<h1>Python</h1>'
    body += '<p>'
    body += '<a target="_blank" href="https://flask.palletsprojects.com/en/1.1.x/quickstart/">Flask v1.1.x Quickstart</a>'
    body += ' | '
    body += '<a target="_blank" href="https://pymongo.readthedocs.io/en/stable/tutorial.html">PyMongo v3.11.2 Tutorial</a>'
    body += ' | '
    body += '<a target="_blank" href="https://github.com/andymccurdy/redis-py">redis-py v3.5.3 Git</a>'
    body += '</p>'
    body += '</div>'
    body += '<h1>MongoDB</h1>'
    body += '<pre>'
    body += json.dumps(doc, indent=4)
    body += '</pre>'
    res = redisClient.set('Hello', 'World')
    if res == True:
      # Display MongoDB & Redis message.
      body += '<h1>Redis</h1>'
      body += 'Get Hello => '+redisClient.get('Hello').decode("utf-8")
    
    # body += '<input class="my-btn submit-btn" type="submit" name="" id=""/>'


    return body

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("FLASK_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("FLASK_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)