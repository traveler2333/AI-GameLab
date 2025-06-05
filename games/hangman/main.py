import tkinter as tk
from tkinter import simpledialog, messagebox
import random

# Game Constants
BACKGROUND_COLOR = "#E6E6FA"  # Lavender
TEXT_COLOR = "#333333"
BUTTON_COLOR = "#D8BFD8" # Thistle
CORRECT_GUESS_COLOR = "#90EE90" # LightGreen
INCORRECT_GUESS_COLOR = "#FFB6C1" # LightPink
FONT_FAMILY = "Arial"

WORD_LIST = {
    "easy": ["cat", "sun", "dog", "big", "red", "cup", "run", "hat", "pen", "sky"],
    "medium": ["python", "banana", "coffee", "window", "summer", "flower", "guitar", "planet", "purple"],
    "hard": ["programming", "adventure", "technology", "xylophone", "knowledge", "discovery", "challenge"]
}

MAX_INCORRECT_GUESSES = 7 # For drawing hangman, HANGMAN_PICS has 8 stages (0-7)

HANGMAN_PICS = [
    # Stage 0: Empty gallows
    """
     -----
     |   |
     |
     |
     |
     |
    ---""",
    # Stage 1: Head
    """
     -----
     |   |
     |   O
     |
     |
     |
    ---""",
    # Stage 2: Body
    """
     -----
     |   |
     |   O
     |   |
     |
     |
    ---""",
    # Stage 3: One arm
    """
     -----
     |   |
     |   O
     |  /|
     |
     |
    ---""",
    # Stage 4: Other arm
    """
     -----
     |   |
     |   O
     |  /|\
     |
     |
    ---""",
    # Stage 5: One leg
    """
     -----
     |   |
     |   O
     |  /|\
     |  /
     |
    ---""",
    # Stage 6: Other leg
    """
     -----
     |   |
     |   O
     |  /|\
     |  / \
     |
    ---""",
    # Stage 7: Dead (Final stage)
    """
     -----
     |   |
     |   X
     |  /|\
     |  / \
     |
    ---"""
]


class HangmanGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Hangman Game")
        self.master.configure(bg=BACKGROUND_COLOR)
        self.master.geometry("550x650")
        self.master.resizable(False, False)

        self.difficulty = tk.StringVar(value="medium")

        self.setup_ui()
        self.start_new_game()

    def setup_ui(self):
        # Difficulty Selection Frame
        difficulty_frame = tk.Frame(self.master, bg=BACKGROUND_COLOR)
        difficulty_frame.pack(pady=10)
        tk.Label(difficulty_frame, text="Difficulty:", font=(FONT_FAMILY, 14), bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
        for level in ["easy", "medium", "hard"]:
            rb = tk.Radiobutton(difficulty_frame, text=level.capitalize(), variable=self.difficulty,
                                value=level, command=self.start_new_game, bg=BACKGROUND_COLOR, fg=TEXT_COLOR,
                                activebackground=BACKGROUND_COLOR, selectcolor=BUTTON_COLOR, font=(FONT_FAMILY, 12))
            rb.pack(side=tk.LEFT)

        self.hangman_canvas = tk.Label(self.master, text="", font=("Courier", 12, "bold"), justify=tk.LEFT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
        self.hangman_canvas.pack(pady=10)

        self.word_display_var = tk.StringVar()
        tk.Label(self.master, textvariable=self.word_display_var, font=(FONT_FAMILY, 24, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(pady=10)

        self.guessed_letters_var = tk.StringVar()
        tk.Label(self.master, textvariable=self.guessed_letters_var, font=(FONT_FAMILY, 14), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, wraplength=500).pack(pady=5)

        self.incorrect_guesses_var = tk.StringVar()
        tk.Label(self.master, textvariable=self.incorrect_guesses_var, font=(FONT_FAMILY, 14), bg=BACKGROUND_COLOR, fg="red").pack(pady=5)

        self.input_frame = tk.Frame(self.master, bg=BACKGROUND_COLOR)
        self.input_frame.pack(pady=10)
        self.letter_buttons = {}
        self.create_letter_buttons()

        self.restart_button = tk.Button(self.master, text="New Game", font=(FONT_FAMILY, 12), bg=BUTTON_COLOR, command=self.start_new_game)
        self.restart_button.pack(pady=10)


    def create_letter_buttons(self):
        for widget in self.input_frame.winfo_children():
            widget.destroy()

        self.letter_buttons = {}
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        # Arrange letters in a more compact way, e.g. 4 rows
        rows = [alphabet[i:i+7] for i in range(0, 21, 7)] + [alphabet[21:]]


        for r_idx, row_letters in enumerate(rows):
            row_frame = tk.Frame(self.input_frame, bg=BACKGROUND_COLOR)
            row_frame.pack()
            for letter in row_letters:
                btn = tk.Button(row_frame, text=letter.upper(), width=3, height=1,
                                font=(FONT_FAMILY, 12, "bold"), bg=BUTTON_COLOR,
                                command=lambda l=letter: self.guess_letter(l))
                btn.pack(side=tk.LEFT, padx=2, pady=2)
                self.letter_buttons[letter] = btn


    def start_new_game(self):
        self.word_to_guess = random.choice(WORD_LIST[self.difficulty.get()]).lower()
        self.guessed_letters = set()
        self.incorrect_guesses = 0
        self.game_over = False

        self.update_word_display()
        self.update_hangman_drawing()
        self.update_guessed_letters_display()
        self.update_incorrect_guesses_display()
        self.enable_all_letter_buttons()


    def update_word_display(self):
        display = ""
        for letter in self.word_to_guess:
            if letter in self.guessed_letters:
                display += letter.upper() + " "
            else:
                display += "_ "
        self.word_display_var.set(display.strip())

    def update_hangman_drawing(self):
        # Ensure incorrect_guesses doesn't exceed HANGMAN_PICS bounds
        pic_index = min(self.incorrect_guesses, len(HANGMAN_PICS) -1)
        self.hangman_canvas.config(text=HANGMAN_PICS[pic_index])


    def update_guessed_letters_display(self):
        sorted_guesses = sorted(list(self.guessed_letters))
        self.guessed_letters_var.set(f"Guessed: {', '.join(sorted_guesses).upper()}")

    def update_incorrect_guesses_display(self):
        self.incorrect_guesses_var.set(f"Incorrect Guesses: {self.incorrect_guesses}/{MAX_INCORRECT_GUESSES}")


    def guess_letter(self, letter):
        if self.game_over or letter in self.guessed_letters:
            return

        self.guessed_letters.add(letter)
        self.letter_buttons[letter].config(state=tk.DISABLED, bg="#AAAAAA")

        if letter in self.word_to_guess:
            self.letter_buttons[letter].config(bg=CORRECT_GUESS_COLOR)
            if all(l in self.guessed_letters for l in self.word_to_guess):
                self.end_game(win=True)
        else:
            self.letter_buttons[letter].config(bg=INCORRECT_GUESS_COLOR)
            self.incorrect_guesses += 1
            if self.incorrect_guesses >= MAX_INCORRECT_GUESSES:
                self.end_game(win=False)

        self.update_word_display()
        self.update_hangman_drawing() # Update drawing after guess
        self.update_guessed_letters_display()
        self.update_incorrect_guesses_display()


    def enable_all_letter_buttons(self):
        for letter, button in self.letter_buttons.items():
            button.config(state=tk.NORMAL, bg=BUTTON_COLOR)

    def disable_all_letter_buttons(self):
         for button in self.letter_buttons.values():
            button.config(state=tk.DISABLED)


    def end_game(self, win):
        self.game_over = True
        self.disable_all_letter_buttons()

        final_display = ""
        for letter_in_word in self.word_to_guess: # Renamed to avoid conflict
            if letter_in_word in self.guessed_letters or not win:
                final_display += letter_in_word.upper() + " "
            elif win: # This case is for when player wins
                 final_display += letter_in_word.upper() + " "
            else:
                final_display += "_ "
        self.word_display_var.set(final_display.strip())

        self.update_hangman_drawing() # Ensure final hangman pic is shown, especially on loss

        if win:
            messagebox.showinfo("Hangman", "Congratulations! You guessed the word!")
        else:
            messagebox.showinfo("Hangman", f"Game Over! The word was: {self.word_to_guess.upper()}")


def main():
    root = tk.Tk()
    game = HangmanGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
