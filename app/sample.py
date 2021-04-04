from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os, json, redis

# App
application = Flask(__name__)

# connect to MongoDB
mongoClient = MongoClient('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_AUTHDB'])
db = mongoClient[os.environ['MONGODB_DATABASE']]

# connect to Redis
redisClient = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379), db=os.environ.get("REDIS_DB", 0))

@application.route('/')
def index():
    db.games.delete_many({})
    db.games.insert_one({
        "step":0,
        "guessing": [],
        "answer": [],
        "win": False
    })
    return render_template('index.html')

@application.route('/start', methods=["POST", "GET"])
def start():
    game = db.games.find_one()
    if request.method == 'POST':
        if (game['step'] <= 3):
            choice = request.form['qchoice']
            game['answer'].append(choice)
            db.games.update_one({},{
                '$set':{
                    "step": game['step'] + 1,
                    "answer": game['answer']
                }
            })
    return render_template('start.html', game=game)

@application.route('/play', methods=["POST", "GET"])
def play():
    game = db.games.find_one()
    hint = ['*', '*', '*', '*']
    if request.method == 'POST':
        choice = request.form['achoice']
        game['guessing'].append(choice)
        db.games.update_one({},{
            '$set':{
                "step": game['step'] + 1,
                "guessing": game['guessing']
            }
        })
    return render_template('play.html', game=game, hint=hint)

@application.route('/check', methods=["POST", "GET"])
def check():
    game = db.games.find_one()

    ans = game['answer']
    guessing = game['guessing']
    check_guessing = []
    hint = []
    correct = True

    for i in range(4):
        if ans[i] != guessing[i]:
            correct = False
            hint.append('*')
        else:
            hint.append(guessing[i])

    db.games.update_one({},{
        '$set':{
            "guessing": [],
        }
    })
    if correct:
        db.games.update_one({},{
        '$set':{
            "win": True,
        }
    })
        return render_template('index.html', game=game)
    return render_template('play.html', game=game, hint=hint)
        
# @application.route('/sample')
# def sample():
#     doc = db.test.find_one()
#     # return jsonify(doc)
#     body = '<div style="text-align:center;">'
#     body += '<h1>Python</h1>'
#     body += '<p>'
#     body += '<a target="_blank" href="https://flask.palletsprojects.com/en/1.1.x/quickstart/">Flask v1.1.x Quickstart</a>'
#     body += ' | '
#     body += '<a target="_blank" href="https://pymongo.readthedocs.io/en/stable/tutorial.html">PyMongo v3.11.2 Tutorial</a>'
#     body += ' | '
#     body += '<a target="_blank" href="https://github.com/andymccurdy/redis-py">redis-py v3.5.3 Git</a>'
#     body += '</p>'
#     body += '</div>'
#     body += '<h1>MongoDB</h1>'
#     body += '<pre>'
#     body += json.dumps(doc, indent=4)
#     body += '</pre>'
#     res = redisClient.set('Hello', 'World')
#     if res == True:
#       # Display MongoDB & Redis message.
#       body += '<h1>Redis</h1>'
#       body += 'Get Hello => '+redisClient.get('Hello').decode("utf-8")
#     return body

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("FLASK_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("FLASK_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)