import tkinter as tk
import random

# Game Constants
WIDTH = 600
HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SNAKE_COLOR = "#33CC33"  # Green
FOOD_COLOR = "#FF0000"   # Red
BACKGROUND_COLOR = "#F0F0F0" # Light Gray
GAME_SPEED = 150  # Milliseconds

class SnakeGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Snake Game")
        self.master.geometry(f"{WIDTH}x{HEIGHT+50}") # Extra space for score
        self.master.resizable(False, False)
        self.master.configure(bg=BACKGROUND_COLOR)

        self.canvas = tk.Canvas(self.master, width=WIDTH, height=HEIGHT, bg=BACKGROUND_COLOR, bd=0, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.score_var = tk.StringVar(value="Score: 0")
        self.score_label = tk.Label(self.master, textvariable=self.score_var, font=("Arial", 14), bg=BACKGROUND_COLOR)
        self.score_label.pack(pady=5)

        self.start_button = tk.Button(self.master, text="Start Game", font=("Arial", 14), command=self.start_game_pressed)
        self.start_button.pack(pady=10)

        self.game_over_label = None
        self.restart_button = None

        self.show_start_screen()

    def show_start_screen(self):
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 3, text="Snake Game", font=("Arial", 30, "bold"), fill=SNAKE_COLOR)
        self.start_button.pack(pady=20)
        if self.restart_button:
            self.restart_button.pack_forget()
        if self.game_over_label:
            self.game_over_label.pack_forget()


    def initialize_game_state(self):
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.snake_direction = "Right"
        self.food_pos = self.generate_food()
        self.score = 0
        self.game_over = False
        self.update_score_display()

    def start_game_pressed(self):
        self.start_button.pack_forget()
        self.initialize_game_state()
        self.master.bind("<KeyPress>", self.on_key_press)
        self.run_game()

    def generate_food(self):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake:
                return (x, y)

    def draw_grid_item(self, pos, color):
        x, y = pos
        self.canvas.create_rectangle(x * GRID_SIZE, y * GRID_SIZE,
                                     (x + 1) * GRID_SIZE, (y + 1) * GRID_SIZE,
                                     fill=color, outline=BACKGROUND_COLOR)

    def draw_game(self):
        self.canvas.delete("all")
        # Draw snake
        for segment in self.snake:
            self.draw_grid_item(segment, SNAKE_COLOR)
        # Draw food
        self.draw_grid_item(self.food_pos, FOOD_COLOR)

    def move_snake(self):
        if self.game_over:
            return

        head_x, head_y = self.snake[0]

        if self.snake_direction == "Up":
            new_head = (head_x, head_y - 1)
        elif self.snake_direction == "Down":
            new_head = (head_x, head_y + 1)
        elif self.snake_direction == "Left":
            new_head = (head_x - 1, head_y)
        elif self.snake_direction == "Right":
            new_head = (head_x + 1, head_y)
        else: # Should not happen
            return

        self.snake.insert(0, new_head)

        # Check for collision with food
        if new_head == self.food_pos:
            self.score += 10
            self.update_score_display()
            self.food_pos = self.generate_food()
        else:
            self.snake.pop()

        # Check for collisions (wall or self)
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT or
            new_head in self.snake[1:]):
            self.end_game()

    def update_score_display(self):
        self.score_var.set(f"Score: {self.score}")

    def on_key_press(self, event):
        new_direction = event.keysym
        if new_direction == "Up" and self.snake_direction != "Down":
            self.snake_direction = "Up"
        elif new_direction == "Down" and self.snake_direction != "Up":
            self.snake_direction = "Down"
        elif new_direction == "Left" and self.snake_direction != "Right":
            self.snake_direction = "Left"
        elif new_direction == "Right" and self.snake_direction != "Left":
            self.snake_direction = "Right"

    def run_game(self):
        if self.game_over:
            return
        self.move_snake()
        self.draw_game()
        self.master.after(GAME_SPEED, self.run_game)

    def end_game(self):
        self.game_over = True
        self.master.unbind("<KeyPress>")
        self.canvas.delete("all")
        self.game_over_label = tk.Label(self.master, text=f"Game Over! Your Score: {self.score}", font=("Arial", 18, "bold"), fg="red", bg=BACKGROUND_COLOR)
        self.game_over_label.pack(pady=20)

        self.restart_button = tk.Button(self.master, text="Restart", font=("Arial", 14), command=self.restart_game)
        self.restart_button.pack(pady=10)

    def restart_game(self):
        self.game_over_label.pack_forget()
        self.restart_button.pack_forget()
        self.score_label.pack_forget() # Remove old score label

        # Re-create score label to ensure it's below canvas
        self.score_var = tk.StringVar(value="Score: 0")
        self.score_label = tk.Label(self.master, textvariable=self.score_var, font=("Arial", 14), bg=BACKGROUND_COLOR)
        self.score_label.pack(pady=5)

        self.show_start_screen()


def main():
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
