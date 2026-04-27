Battleship skeleton submission

Files used from the skeleton structure:
- battleship.py
- cell.py
- gameboard.py
- gamegui.py
- player.py
- ship.py

Implemented:
- console mode and Tkinter GUI
- classic fleet A5, B4, C3, S3, D2
- planning board and attack board
- random/manual placement for player, random placement for computer
- inside-grid and non-overlap validation
- A-J column labels and 0-9 row labels in console
- red hits and white misses in console
- 2-second Thinking... delay for computer
- extra turn on hit
- difficulty modes: easy, medium, hard
- medium/hard computer follow-up targeting after hits
- hard mode uses a simple probability-style hunt for remaining ship sizes
- save button in GUI and basic metadata save helper in console code
- sunk ship message and winner message
- simple sunk-ship flash animation in GUI

Notes:
- Enemy ships stay hidden in medium/hard and are more visible in easy mode.
- The GUI uses lightweight canvas-drawn ship shapes rather than external image files.
