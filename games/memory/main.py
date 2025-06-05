import tkinter as tk
import random
import time

# Game Constants
GRID_ROWS = 4
GRID_COLS = 4
CARD_WIDTH = 100
CARD_HEIGHT = 100
CARD_COLOR = "#ADD8E6"  # Light Blue
CARD_BACK_COLOR = "#B0E0E6" # Powder Blue
TEXT_COLOR = "#333333"
BACKGROUND_COLOR = "#F0F8FF" # Alice Blue
MATCH_COLOR = "#90EE90" # Light Green
FONT_FAMILY = "Arial"

# Symbols for cards (ensure there are enough unique pairs for GRID_ROWS * GRID_COLS / 2)
SYMBOLS = ['★', '●', '♦', '♥', '♠', '♣', '▲', '▼', '⬟', '⬠', '✚', '✜']


class MemoryGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Memory Game")
        self.master.configure(bg=BACKGROUND_COLOR)

        # Calculate window size based on grid
        window_width = GRID_COLS * (CARD_WIDTH + 10) + 10
        window_height = GRID_ROWS * (CARD_HEIGHT + 10) + 80 # Extra for status/restart
        self.master.geometry(f"{window_width}x{window_height}")
        self.master.resizable(False, False)

        self.status_var = tk.StringVar(value="Attempts: 0 | Matches: 0")
        self.status_label = tk.Label(self.master, textvariable=self.status_var, font=(FONT_FAMILY, 14), bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
        self.status_label.pack(pady=10)

        self.card_frame = tk.Frame(self.master, bg=BACKGROUND_COLOR)
        self.card_frame.pack()

        self.restart_button = tk.Button(self.master, text="Restart Game", font=(FONT_FAMILY, 12), command=self.restart_game)
        self.restart_button.pack(pady=10)

        self.init_game()

    def init_game(self):
        self.attempts = 0
        self.matches = 0
        self.first_card = None
        self.second_card = None
        self.buttons = []
        self.card_values = []
        self.matched_pairs_indices = [] # Keep track of matched cards' button indices

        self.update_status_display()
        self.generate_cards()
        self.create_card_widgets()

    def generate_cards(self):
        num_pairs = (GRID_ROWS * GRID_COLS) // 2
        if num_pairs > len(SYMBOLS):
            # Fallback if not enough symbols, though SYMBOLS should be sufficient for typical grids
            selected_symbols = (SYMBOLS * (num_pairs // len(SYMBOLS) +1))[:num_pairs]
        else:
            selected_symbols = random.sample(SYMBOLS, num_pairs)

        self.card_values = selected_symbols * 2
        random.shuffle(self.card_values)

    def create_card_widgets(self):
        # Clear previous cards if any (for restart)
        for widget in self.card_frame.winfo_children():
            widget.destroy()

        self.buttons = []
        for r in range(GRID_ROWS):
            row_buttons = []
            for c in range(GRID_COLS):
                idx = r * GRID_COLS + c
                button = tk.Button(self.card_frame, text="", width=10, height=4,
                                   bg=CARD_BACK_COLOR, relief=tk.RAISED,
                                   font=(FONT_FAMILY, 16, "bold"),
                                   command=lambda i=idx: self.on_card_click(i))
                button.grid(row=r, column=c, padx=5, pady=5)
                row_buttons.append(button)
            self.buttons.append(row_buttons)

    def on_card_click(self, index):
        button = self.buttons[index // GRID_COLS][index % GRID_COLS]

        # Ignore clicks on already matched cards or if two cards are already revealed
        if index in self.matched_pairs_indices or (self.first_card and self.second_card):
            return

        # Reveal card
        button.config(text=self.card_values[index], bg=CARD_COLOR, relief=tk.SUNKEN)

        if self.first_card is None:
            self.first_card = (index, self.card_values[index], button)
        elif self.first_card[0] != index: # Ensure not clicking the same card twice
            self.second_card = (index, self.card_values[index], button)
            self.attempts += 1
            self.update_status_display()
            self.master.after(50, self.check_match) # Short delay before checking

    def check_match(self):
        if not self.first_card or not self.second_card: # Should not happen
            return

        idx1, val1, btn1 = self.first_card
        idx2, val2, btn2 = self.second_card

        if val1 == val2: # Match!
            self.matches += 1
            btn1.config(bg=MATCH_COLOR, state=tk.DISABLED) # Keep revealed and disable
            btn2.config(bg=MATCH_COLOR, state=tk.DISABLED) # Keep revealed and disable
            self.matched_pairs_indices.extend([idx1, idx2])
            if self.matches == (GRID_ROWS * GRID_COLS) // 2:
                self.game_over()
        else: # No match
            # Hide cards after a delay
            self.master.after(800, self.hide_cards, btn1, btn2)

        self.first_card = None
        self.second_card = None
        self.update_status_display()

    def hide_cards(self, btn1, btn2):
        # Only hide if they haven't been matched in the meantime by a very quick player (unlikely)
        if btn1['state'] != tk.DISABLED:
             btn1.config(text="", bg=CARD_BACK_COLOR, relief=tk.RAISED)
        if btn2['state'] != tk.DISABLED:
             btn2.config(text="", bg=CARD_BACK_COLOR, relief=tk.RAISED)


    def update_status_display(self):
        self.status_var.set(f"Attempts: {self.attempts} | Matches: {self.matches}")

    def game_over(self):
        # Optionally, display a "Game Over" message or enhance the status
        self.status_var.set(f"Awesome! All matched in {self.attempts} attempts!")
        # Could add a tk.messagebox.showinfo here if desired

    def restart_game(self):
        self.matched_pairs_indices = []
        self.init_game()

def main():
    root = tk.Tk()
    game = MemoryGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
