from turtle import Turtle
import random


class Food(Turtle):

    def __init__(self):
        super().__init__()
        self.shape("circle")
        self.penup()
        self.shapesize(stretch_len=0.5, stretch_wid=0.5)
        self.color("cyan")
        self.speed("fastest")
        self.refresh()

    def refresh(self):
        random_x = random.randint(-470, 470)
        random_y = random.randint(-380, 380)
        self.goto(random_x, random_y)


class EnhancedFood(Food):
    def __init__(self):
        super().__init__()
        self.color("gold")  # Make it visually distinct
        self.hideturtle()  # Initially hide the enhanced food

    def appear(self):
        self.refresh()
        self.showturtle()  # Make it visible

    def disappear(self):
        self.hideturtle()  # Make it invisible again
