from flask import Flask, redirect, render_template, render_template_string

import requests

from flask import request

app = Flask(__name__)

game_template = """
<!doctype html>
<body>
    <link rel="stylesheet" href="../static/style.css">
    <title>Adventure Game</title>
    <h1>Welcome to the Adventure Game!</h1>
    <h2>What's your name fair traveler?</h2>
    <form method="post">
        <input type="text" name="choice" />
        <input class="btn1" type="submit" value="Submit" />
    </form>
    
    <p>{{ response }}</p>
    <a href="/home">
        <button class="btn">Yes!</button>
    </a>
    
</body>
"""

class WorldState:
    def __init__(self):
        self.name=""
        self.location=""
        self.morality = 0  # -5 pragmatic, +5 compassionate
        self.curse_stage = 1
        self.npc_trust = {
            "Mira": 0,
            "Kael": 0,
            "Elowen": 0,
        }
        self.last_choice=""

world = WorldState()

@app.route('/', methods=['GET', 'POST'])
def index():
    response = ""
    if request.method == 'POST':
        choice = request.form['choice']
        response = f"Your name is {choice}, is that correct?"
        world.name=choice
    return render_template_string(game_template, response=response)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/tck')
def tck():
    location="Your Home"
    return render_template('tck.html')

@app.route('/story1', methods=["GET", "POST"])
def s1():
    world.location="Village of Greybrook"
    if request.method == "POST":
        choice = request.form.get("choice")

        if choice == "comfort":
            world.morality += 2
            world.npc_trust["Mira"] += 2
            world.last_choice = "comfort"

        elif choice == "questions":
            world.morality -= 1
            world.last_choice = "questions"

        elif choice == "crown":
            world.morality -= 2
            world.npc_trust["Mira"] -= 2
            world.last_choice = "crown"
            
        return redirect("/story2")

    return render_template('story1.html', name=world.name, location=world.location, morality=world.morality, trusts=world.npc_trust, curse_stage=world.curse_stage)

@app.route('/story2', methods=["GET", "POST"])
def s2():
    world.curse_stage += 1
    world.location="Village of Greybrook"
    if request.method == "POST":
        choice = request.form.get("choice")

        if choice == "speak":
            world.morality += 1
            world.npc_trust["Mira"] += 1
            world.last_choice = "speak"

        elif choice == "leave":
            world.last_choice = "leave"

        return redirect("/story3")
    
    return render_template(
        "story2.html",
        world=world
    )

@app.route('/story3', methods=["GET", "POST"])
def s3():
    world.curse_stage += 1
    world.location="Village of Greybrook"
    if request.method == "POST":
        choice = request.form.get("choice")

        if choice == "stay":
            world.morality += 2
            world.npc_trust["Mira"] += 2
            world.last_choice = "stay"

        elif choice == "capital":
            world.location="On the Road"
            world.morality += 1 
            world.last_choice = "capital"
            
        elif choice == "shrine":
            world.location="Shrine of Greybrook"
            world.morality += 2
            world.npc_trust["Elowen"] += 2
            world.last_choice = "shrine"

        return redirect("/story4")
    
    return render_template(
        "story3.html",
        world=world
    )
    
@app.route('/story4', methods=["GET", "POST"])
def s4():
    world.curse_stage += 1
    if request.method == "POST":
        choice = request.form.get("choice")

        if choice == "elaria":
            world.location="Capital of Elaria"
            world.morality += 2
            world.last_choice = "elaria"

        elif choice == "investigate":
            world.morality += 2 
            world.npc_trust["Elowen"] += 2
            world.last_choice = "investigate"
            

        return redirect("/story5")
    
    return render_template(
        "story4.html",
        world=world
    )


if __name__ == '__main__':
    app.run(debug=True)
