import argparse

# Define and parse command-line arguments to hide the board
parser = argparse.ArgumentParser(description='Play Tic Tac Toe')
parser.add_argument('--hide-board', action='store_true', help='Hide the game board')
parser.add_argument('--one-player', action='store_true', help='Play against the computer')
args = parser.parse_args()

# Define the game board
board = {
    '1a': ' ', '1b': ' ', '1c': ' ',
    '2a': ' ', '2b': ' ', '2c': ' ',
    '3a': ' ', '3b': ' ', '3c': ' ',
}

# Function to display the board
def display_board():
    print("  a   b   c")
    print("1 {} | {} | {}".format(board['1a'], board['1b'], board['1c']))
    print("  ---------")
    print("2 {} | {} | {}".format(board['2a'], board['2b'], board['2c']))
    print("  ---------")
    print("3 {} | {} | {}".format(board['3a'], board['3b'], board['3c']))

# Function to check for a win
def check_win(player):
    # Check for horizontal wins
    for row in ['1', '2', '3']:
        if board[row+'a'] == board[row+'b'] == board[row+'c'] == player:
            return True
    # Check for vertical wins
    for col in ['a', 'b', 'c']:
        if board['1'+col] == board['2'+col] == board['3'+col] == player:
            return True
    # Check for diagonal wins
    if board['1a'] == board['2b'] == board['3c'] == player:
        return True
    if board['1c'] == board['2b'] == board['3a'] == player:
        return True
    return False

# Function to check if the game is over
def check_game_over():
    # Check for a win
    if check_win('X'):
        print('X wins!')
        return True
    if check_win('O'):
        print('O wins!')
        return True
    # Check for a tie
    if ' ' not in board.values():
        print("It's a tie!")
        return True
    return False

# Function for the computer's move
def computer_move():
    import random
    while True:
        row = str(random.randint(1, 3))
        col = random.choice(['a', 'b', 'c'])
        if board[row+col] == ' ':
            board[row+col] = 'O'
            print("The computer put O at {}{}.".format(row, col))
            break

# Start the game
if not args.hide_board:
    display_board()

while True:
    # Player's move
    while True:
        player_move = input("Enter a move (e.g. 1a or a1): ")
        if player_move[0].isdigit():
            row = player_move[0]
            col = player_move[1]
        else:
            row = player_move[1]
            col = player_move[0]
        if board[row+col] == ' ':
            board[row+col] = 'X'
            print("You put X at {}{}.".format(row, col))
            break
        else:
            print("That square is already taken.")
        if not args.hide_board:
            display_board()
        if check_game_over():
            break
    # Computer's move
    print("The computer is making a move...")
    computer_move()
    if not args.hide_board:
        display_board()
    if check_game_over():
        break
