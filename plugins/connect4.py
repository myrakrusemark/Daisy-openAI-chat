import numpy as np

ROWS = 6
COLUMNS = 7

# Create the game board
board = np.zeros((ROWS, COLUMNS), dtype=int)

# Function to print the game board
def print_board(board):
    print(np.flip(board, 0))

# Function to check if a player has won
def check_win(board, player):
    # Check horizontally
    for i in range(ROWS):
        for j in range(COLUMNS-3):
            if board[i][j] == player and board[i][j+1] == player and board[i][j+2] == player and board[i][j+3] == player:
                return True
    # Check vertically
    for i in range(ROWS-3):
        for j in range(COLUMNS):
            if board[i][j] == player and board[i+1][j] == player and board[i+2][j] == player and board[i+3][j] == player:
                return True
    # Check diagonally (top left to bottom right)
    for i in range(ROWS-3):
        for j in range(COLUMNS-3):
            if board[i][j] == player and board[i+1][j+1] == player and board[i+2][j+2] == player and board[i+3][j+3] == player:
                return True
    # Check diagonally (bottom left to top right)
    for i in range(3, ROWS):
        for j in range(COLUMNS-3):
            if board[i][j] == player and board[i-1][j+1] == player and board[i-2][j+2] == player and board[i-3][j+3] == player:
                return True
    return False

# Function to drop a checker into the board
def drop_checker(board, row, col, player):
    board[row][col] = player

# Function to get the next available row in a column
def get_next_row(board, col):
    for row in range(ROWS-1, -1, -1):
        if board[row][col] == 0:
            return row
    return -1

# Main game loop
game_over = False
turn = 1
while not game_over:
    # Print the board
    print_board(board)

    # Get input from the user
    if turn == 1:
        col = int(input("Player 1's turn. Choose a column (0-6): "))
    else:
        col = int(input("Player 2's turn. Choose a column (0-6): "))

    # Drop the checker into the board
    row = get_next_row(board, col)
    if row == -1:
        print("Column is full. Try again.")
        continue
    drop_checker(board, row, col, turn)

    # Check if the player has won
    if check_win(board, turn):
        print_board(board)
        print("Player", turn, "wins!")
        game_over = True

    # Check if the board is full (tie game)
    if np.count_nonzero(board == 0) == 0:
        print_board(board)
        print("Tie game!")
        game_over = True

    # Switch to the other player's turn
    turn = 3 - turn  # alternates between 1 and 
