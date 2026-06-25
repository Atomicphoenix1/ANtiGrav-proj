from turtle import Turtle
import json

ALIGNMENT = "center"
FONT = ("Courier", 24, "normal")


class Scoreboard(Turtle):

    def __init__(self, mode):
        super().__init__()
        self.score = 0
        self.level = 1
        self.mode = mode  # "normal_mode" or "competitive_mode"
        self.highscores = self.load_highscores()
        self.highscore = self.highscores.get(self.mode, 0)
        self.color("white")
        self.penup()
        self.goto(0, 365)
        self.hideturtle()
        self.update_scoreboard()

    def load_highscores(self):
        try:
            with open("highscore.json", "r") as file:
                return json.load(file)  # Load the dictionary from the file
        except (FileNotFoundError, json.JSONDecodeError):
            # Default structure if file is missing or corrupt
            return {"normal_mode": 0, "competitive_mode": 0}

    def save_highscores(self):
        self.highscores[self.mode] = self.highscore  # Update the high score for the current mode
        with open("highscore.json", "w") as file:
            json.dump(self.highscores, file)  # Save the dictionary to the file

    def update_scoreboard(self):
        self.clear()
        self.write(f"Score: {self.score}  High Score: {self.highscore}  Level: {self.level}",
                   align=ALIGNMENT, font=FONT)

    def increase_level(self):
        self.level += 1

    def game_over(self):
        if self.score > self.highscore:
            self.highscore = self.score
            self.save_highscores()
        self.goto(0, 0)
        self.write("Game Ωver", align=ALIGNMENT, font=FONT)

    def increase_score(self, amount):
        self.score += amount
        self.update_scoreboard()
