import time
import random
from turtle import Screen, Turtle

# Import your other modules
from snake import Snake
from food  import Food, EnhancedFood
from scoreboard import Scoreboard





# ----- SETUP THE SCREEN -----

screen = Screen()
screen.setup(width=1000, height=800)
screen.bgcolor("black")
screen.title("Zippy")
# tracer(0) stops auto-updating, so we must call screen.update() manually
screen.tracer(0)


# ----- CREATE TIMER DISPLAY -----
timer_turtle = Turtle()
timer_turtle.color("white")
timer_turtle.hideturtle()
timer_turtle.penup()
timer_turtle.goto(0, 270)


# ----- GLOBAL GAME VARIABLES -----
game_time = 60      # Total game time in seconds (used if Competitive Mode)
is_competitive = False
is_paused = False
game_is_on = False  # We will set this to True after choosing the mode
timer_stop = False
# ----- TOGGLE PAUSE FUNCTION -----
def toggle_pause():
    global is_paused
    is_paused = not is_paused
    update_timer()
    print(f"[DEBUG] Toggled pause. Now is_paused = {is_paused}")




# ----- TIMER FUNCTION -----
def update_timer():
    """
    Decrements the game_time by 1 second.
    If game_time reaches 0, stops the game and shows game over.
    """
    global game_time, game_is_on
    if not is_paused:
         if game_time > 0 and not timer_stop:
            timer_turtle.clear()
            timer_turtle.write(
                f"Time Left: {game_time}s",
                align="center",
                font=("Courier", 24, "normal")
            )
            game_time -= 1
            # Schedule the next call after 1 second
            screen.ontimer(update_timer, 1000)
         else:
            print("[DEBUG] Timer reached 0. Stopping game.")
            game_is_on = False
            scoreboard.game_over()


# ----- SHOW ENHANCED FOOD FUNCTION -----
def show_enhanced_food():
    """
    Makes the EnhancedFood appear and then disappear after 7 seconds.
    """
    global enhanced_food
    enhanced_food.appear()
    screen.update()

    # Make the enhanced food disappear after 7 seconds
    screen.ontimer(enhanced_food.disappear, 7000)


# ----- GAME MENU FUNCTION -----

def game_menu():
    """
    Displays a menu asking the user to pick a mode.
    Returns "1" for Normal Mode or "2" for Competitive Mode.
    """
    print("[DEBUG] Entering game_menu()...")
    screen.clear()  # Clear any previous screen content
    screen.bgcolor("black")
    screen.title("Snake Game Menu")

    # Create menu turtle
    menu_turtle = Turtle()
    menu_turtle.color("yellow")
    menu_turtle.hideturtle()
    menu_turtle.penup()
    menu_turtle.goto(0, 100)

    # Display menu options
    menu_text = (
        "Choose Mode:\n"
        "1. Normal Mode\n"
        "2. Competitive Mode (Timed)\n"
        "3. Show Game instructions"
    )
    menu_turtle.write(menu_text, align="center", font=("Courier", 24, "normal"))
    screen.update()

    # Get user input
    mode_chosen = screen.textinput("Game Mode", "Enter 1, 2 or 3:")
    while mode_chosen not in ["1", "2", "3"]:
        mode_chosen = screen.textinput("Invalid Input", "Please enter 1, 2 or 3:")

    print(f"[DEBUG] User selected mode: {mode_chosen}")

    # Clear menu and reset screen for the game
    menu_turtle.clear()
    del menu_turtle
    screen.clear()
    screen.bgcolor("black")
    screen.title("Zippy The Viper")
    screen.tracer(0)  # Disable auto-updates for better performance
    screen.update()

    return mode_chosen

def show_game_instructions():
    screen.clear()
    screen.bgcolor("black")
    screen.title("Zippy Instructions")

    instructions_turtle = Turtle()
    instructions_turtle.color("white")
    instructions_turtle.hideturtle()
    instructions_turtle.penup()
    instructions_turtle.goto(20, 100)

    global exit_game_instruction_flag  # Declare the flag as global
    exit_game_instruction_flag = False  # Ensure the flag is initialized here

    instructions = (
        "How to Play:\n"
        "1. Use the Arrow Keys to control the snake.\n"
        "2. Eat the blue food to gain points.\n"
        "3. Avoid the walls and your own tail.\n"
        "4. In Competitive Mode, survive before the timer ends!\n"
        "5. After each 5 levels, the speed of the snake increases, \n and a golden food shows up.\n"
        "6. The Golden Food is worth 10 points and appears for 7 seconds!\n\n"
        "Press 'Enter' to return to the menu."
    )

    def return_to_menu():
        global exit_game_instruction_flag  # Access the global flag
        exit_game_instruction_flag = True  # Set the flag to True
    instructions_turtle.write(instructions, align="center", font=("Courier", 18, "normal"))
    screen.listen()
    screen.onkey(return_to_menu, "Return")  # Close instructions when Enter is pressed
    while not exit_game_instruction_flag:
        screen.update()
    print("[DEBUG] loop exit")

mode = game_menu()
while mode == '3':
    show_game_instructions()
    mode = game_menu()

if mode == "2":
    is_competitive = True
    print("[DEBUG] Competitive Mode selected.")

else:
    print("[DEBUG] Normal Mode selected.")


# If Competitive Mode, start timer
if is_competitive:
    game_time = 60
    update_timer()
    game_mode = "normal_mode"
else:
    game_mode = "competitive_mode"


# ----- CREATE GAME OBJECTS -----
snake = Snake()          # The main snake
food = Food()            # Regular food
enhanced_food = EnhancedFood()  # Special food
scoreboard = Scoreboard(game_mode)       # Scoreboard


# ----- KEY LISTENERS -----
screen.listen()
screen.onkey(snake.up, "Up")
screen.onkey(snake.down, "Down")
screen.onkey(snake.left, "Left")
screen.onkey(snake.right, "Right")
screen.onkey(toggle_pause, "p")

# ----- MAIN GAME LOOP -----
game_is_on = True
speed = 0.1
initial_score = scoreboard.score

print("[DEBUG] Starting main game loop...")
# Debug: Print snake's initial head position
print(f"[DEBUG] Snake starting head coords: {snake.head.xcor()}, {snake.head.ycor()}")

while game_is_on:
    screen.update()
    time.sleep(speed)

    if not is_paused:
        snake.move()

    # Detect collision with food
    if snake.head.distance(food) < 15:
        print("[DEBUG] Collision with regular food.")
        food.refresh()
        snake.extend()
        
        scoreboard.increase_score(1)
        
        # change_background_color() 

    # Show enhanced food if score is multiple of 3 and greater than the initial check
    if scoreboard.score % 5 == 0 and scoreboard.score > initial_score:
        initial_score = scoreboard.score
        show_enhanced_food()

    # Detect collision with enhanced food
    if enhanced_food.isvisible() and snake.head.distance(enhanced_food) < 15:
        print("[DEBUG] Collision with enhanced food.")
        enhanced_food.disappear()
        for i in range(0,10):
            snake.extend()
        
        

        scoreboard.increase_score(10)

    # Level up every time score is multiple of 5 (after initial_score check)
    if scoreboard.score % 5 == 0 and scoreboard.score > initial_score:
        initial_score = scoreboard.score
        scoreboard.increase_level()
        speed *= 0.9
        screen.bgcolor("blue")  # Flash screen on level-up
        screen.update()
        time.sleep(0.5)
        screen.bgcolor("black")
        screen.update()

    # Detect collision with wall
    if (snake.head.xcor() > 480 or snake.head.xcor() < -480 or
            snake.head.ycor() > 380 or snake.head.ycor() < -380):
        print("[DEBUG] Collision with wall. Game Over.")
        game_is_on = False
        timer_stop = True
        scoreboard.game_over()

    # Detect collision with tail
    for segment in snake.segments[1:]:  # skip the head
        if snake.head.distance(segment) < 10:
            print("[DEBUG] Collision with tail. Game Over.")
            game_is_on = False
            timer_stop = True
            scoreboard.game_over()
            break

# ----- EXIT -----
print("[DEBUG] Exiting game. Click screen to close.")
screen.exitonclick()
