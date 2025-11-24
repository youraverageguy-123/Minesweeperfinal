
# *Minesweeper – Python Project*

## *Overview*

This project is a Python implementation of *Minesweeper* using *Tkinter*.
It follows the assignment requirements: modular code, GUI, save/load system, and correct gameplay logic.

The objective is to reveal all non-mine cells without triggering a mine.


## *Features*

* 9×9 default board (custom sizes supported)
* Random mine placement with saved RNG seed
* Recursive reveal for empty tiles
* Flag/unflag cells
* Win/loss detection
* Timer and click counter
* Three save slots with load support
* Score tracking (time, clicks, board size, result)


## *Directory Structure*


main.py            # Entry point and main menu
board.py           # Board generation, reveal logic, mine placement
game_logic.py      # Game flow, event handling, win/loss process
file_manager.py    # Save/load files and leaderboard
saves/             # Auto-created save slot files
scores.csv         # Auto-generated score log
README.md



## *How to Run*

1. Install Python 3.x
2. Open a terminal in the project folder
3. Run:


python main.py


No external libraries are required.


## *Gameplay Instructions*

* *Left Click:* reveal a cell
* *Right Click:* flag/unflag
* Clear all safe cells to win
* Hitting a mine ends the game

You can start:

* Default board
* Quick preset
* Custom board
* Or load a saved game


## *Save/Load*

* Click *Save* during gameplay to store the current state
* Up to three slots
* Load from the main menu


## *Leaderboard*

Tracks:

* Player name
* Time
* Clicks
* Board size
* Mines
* Result

Viewable from the main menu.


## *Notes*

* All saves and scores are stored locally
* GUI built entirely with Tkinter
* Fully modular code structure as required
