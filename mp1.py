import os
import sys

import subprocess
import time

from enum import Enum, auto
from typing import Dict, List, Tuple


# constants
TICK_RATE = 0.01
DIRECTIONS = frozenset(('l', 'r', 'f', 'b'))
GRAPHICS = {
    '#': '🧱',
    '.': '🟩',
    '0': '🥚',
    'O': '🪹',
    'P': '🍳',
    '@': '🪺',
}


# classes
class Axis(Enum):
    """Object to be used to group directions."""
    HORIZONTAL = auto()
    VERTICAL = auto()
    POSITIVE = auto()
    NEGATIVE = auto()


class Direction:
    """Handles direction string to arrow or coordinate conversions."""

    DIR_DCT = {
        'l': ((0, -1), '←'),
        'r': ((0, 1),  '→'),
        'f': ((-1, 0), '↑'),
        'b': ((1, 0),  '↓'),
    }


    def __init__(self, direction: str):
        self._direction = direction
        self.coord = Direction.DIR_DCT[direction][0]  # respective (i, j) coord
        self._i = self.coord[0]
        self._j = self.coord[1]

        match direction:                        # categorize direction
                                                # axis and polarity
            case 'l':
                self.axis = Axis.HORIZONTAL
                self.polarity = Axis.NEGATIVE

            case 'r':
                self.axis = Axis.HORIZONTAL
                self.polarity = Axis.POSITIVE

            case 'f':
                self.axis = Axis.VERTICAL
                self.polarity = Axis.NEGATIVE

            case 'b':
                self.axis = Axis.VERTICAL
                self.polarity = Axis.POSITIVE


    def __repr__(self) -> str:
        """Returns the respective arrow."""
        return Direction.DIR_DCT[self._direction][1]


    def get_next(self, coord: Tuple[int, int]) -> Tuple[int, int]:
        """Returns the next coord with respect to the instance's direction."""
        i, j = coord
        return (i + self._i, j + self._j)


class Grid:
    """Handles grid manipulations and grid displays."""

    def __init__(self, grid: List[List[str]]):
        self._grid = [list(i) for i in grid]
        self._rows = len(grid)
        self._cols = len(grid[0])


    def __repr__(self) -> str:
        """Returns the grid in string form."""
        return '\n'.join((''.join(i) for i in self._grid))


    def peek(self, coord: Tuple[int, int]) -> str | None:
        """Returns the object in the grid coord, if any."""

        (i, j) = coord

        if 0 <= i < self._rows and 0 <= j < self._cols:
            return self._grid[i][j]             # in bounds
        else:
            return None                         # out of bounds


    def update(self, coord: Tuple[int, int], char: str) -> None:
        """Places char on grid coord."""
        (i, j) = coord
        self._grid[i][j] = char


class Leaderboard:
    """Leaderboard class which handles leaderboard 
    manipulation, file appends, and displaying of leaderboard.
    """

    LENGTH = 10          # amount of scores to be kept
    PADDING = 1          # gap between text and dividers when displaying

    def __init__(self, player_w_scores: List[Tuple[str, int]]):
        self.player_w_scores = player_w_scores
        self._scores = [s for p, s in player_w_scores]
        self.min_score = min(self._scores) if self._scores else 0
        self.sort()


    def __repr__(self) -> str:
        """Returns the string representation of how the 
        leaderboard will be printed on the level file
        """
        str_rep = (f'{p} - {s}' for p, s in self.player_w_scores)
        return '\n'.join(str_rep)


    def sort(self) -> None:
        """Sorts the leaderboard by scores in decreasing order in place."""
        self.player_w_scores.sort(key=(lambda tup: tup[::-1]), reverse=True)
        self._scores.sort(reverse=True)


    def file_append(self) -> None:
        """Appends the scores at the end of the level file."""

        path = os.path.join('.', 'level', sys.argv[1])

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        r = int(lines[0])                       # amount of level rows

        if '\n' not in lines[r + 1]:            # avoids concatenation of last
            lines[r + 1] += '\n'                # level row and leaderboards

        lines[r + 2:] = repr(self)

        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)


    def evaluate(self, score: int) -> None:
        """If the score is above the minimum score in the leaderboards,
        or there are less than Leaderboard.LENGTH scores in the leaderboards,
        update and sort the leaderboard after prompting the name of the player.
        """

        LENGTH = Leaderboard.LENGTH
        score_len = len(self.player_w_scores)

        if score_len < LENGTH or self.min_score < score:

            player_name = input('Please input your name: ')

            self.player_w_scores.append((player_name, score))
            self._scores.append(score)
            self.sort()

            while score_len > LENGTH:           # remove excess scores
                self.player_w_scores.pop()
                self._scores.pop()

            self.min_score = min(self._scores)
            self.file_append()                  # append scores to level file


    def clear(self) -> None:
        """Clears the leaderboards."""

        path = os.path.join('.', 'level', sys.argv[1])

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        r = int(lines[0])
        lines = lines[:r + 2]                   # trim level file lines

        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)


    def display(self) -> None:
        """Displays scores in table form."""

        plyr_w_scre = self.player_w_scores
        PADDING = Leaderboard.PADDING           # gap between text and divider

        max_p_width = max((len(p) for p, s in plyr_w_scre))
        max_s_width = max((len(str(s)) for p, s in plyr_w_scre))
        max_s_width = max(max_s_width, len('SCORES'))

        max_p_width += PADDING                  # max player string width
        max_s_width += PADDING                  # max score string width

        header = [('PLAYER', 'SCORES')]   # include header with scores

        for i, (plyr, scre) in enumerate((*header, *plyr_w_scre)):

            plyr_width = len(plyr)

            plyr_space = max_p_width - plyr_width
            scre_space = PADDING

            p_col = f'{plyr}{' '*plyr_space}'
            s_col = f'{' '*scre_space}{scre}'

            print(f'{p_col}|{s_col}')           # print player and score

            if i == 0:                          # check if printing headers
                p_col = '-'*max_p_width
                s_col = '-'*max_s_width
                print(f'{p_col}+{s_col}')       # print dividers after headers
            

# utility functions
def get_level_info() -> Tuple[int, int, List[str], List[str]]:
    """This function extracts the rows, number of moves,
    the stage layout, and scores from the level file, if any.

    Returns the extracted data.
    """
    if len(sys.argv) < 2:
        prompt = 'Please input a level file from the level directory.'
        raise FileNotFoundError(prompt)

    path = os.path.join('.', 'level', sys.argv[1])
    
    with open(path, encoding='utf-8') as f:
        rows = int(f.readline())
        moves = int(f.readline())

        grid = []
        for i in range(rows):
            grid.append(f.readline().replace('\n', ''))

        scores = []
        for i in range(Leaderboard.LENGTH):
            scores.append(f.readline().replace('\n', ''))
    
    return rows, moves, grid, scores


def process_stage() -> Tuple[Grid, int, List[Tuple[int, int]], Leaderboard]:
    """This function processes the stage grid, number of moves,
    egg coordinates, and scores from the level file, if any.

    Returns the processed data.
    """
    moves, grid_, scores_ = get_level_info()[1:]

    grid = process_grid(grid_)
    egg_coords = get_coords(grid, '🥚')
    scores = process_scores(scores_)
    return grid, moves, egg_coords, scores


def process_grid(grid: List[str]) -> Grid:
    """Processes raw characters from the stage grid
    into their respective emoji versions.

    Returns a Grid.
    """
    return Grid([[GRAPHICS[j] if j in GRAPHICS else j
                  for j in i]
                  for i in grid])


def process_scores(scores: List[str]) -> Leaderboard:
    """Returns a list of Leaderboard.LENGTH or less pairs of player names and
    their scores from the raw scores list. The list will be sorted
    according to the player scores in decreasing order.
    """

    assert len(scores) <= Leaderboard.LENGTH

    leaderboard = []

    for line in scores:

        if line:                                # if line is not empty

            (*plyr_, scre_) = line.split(' - ') # handles cases where player name
            plyr = ''.join(plyr_)               # contains ' - '
            scre = int(scre_)

            leaderboard.append((plyr, scre))    # player - score tuple pair

    leaderboard.sort(key=lambda tup: tup[::-1], reverse=True)

    return Leaderboard(leaderboard)


def process_input(input_dir: str) -> Direction | None:
    """Checks if the input string is 'quit',
    else finds the first valid character in the input string.
    """
    assert is_valid(input_dir)

    input_dir = input_dir.lower().strip()

    if input_dir == 'quit':
        return None

    for i in input_dir:
        if i in DIRECTIONS:
            direction = Direction(i)
            break

    return direction


def is_valid(input_dir: str) -> bool:
    """Checks if the input string is 'quit',
    else checks if 'l', 'r', 'f', or 'b' is in the input string.
    """
    input_dir = input_dir.lower().strip()

    if input_dir == 'quit':
        return True

    return any((i in input_dir for i in DIRECTIONS))


# display functions
def clear_screen() -> None:
    """Clears the terminal screen, if any."""
    try:
        if sys.stdout.isatty():
            clear_cmd = 'cls' if os.name == 'nt' else 'clear'
            subprocess.run([clear_cmd])
    except FileNotFoundError:
        os.system('cls')


def display(grid: Grid, moves: int = 0, all_moves: List[str] = [],
            points: int = 0, is_moving: bool = False) -> None:
    """Clears the terminal and displays the grid
    followed by the stats, if no eggs are moving, for TICK_RATE seconds
    """
    clear_screen()
    display_grid(grid)
    if not is_moving:
        display_stats(moves, all_moves, points)
    time.sleep(TICK_RATE)


def display_grid(grid: Grid) -> None:
    """Displays the current state of the stage grid."""
    print(grid)


def display_stats(moves: int, all_moves: List[str], points: int) -> None:
    """Displays the current stats of the game."""
    print(f'Previous Moves: {''.join(all_moves)}')
    print(f'Remaining Moves: {moves}')
    print(f'Points: {points}')


def display_leaderboard(leaderboard: Leaderboard) -> None:
    """Displays the top Leaderboard.LENGTH scores for the level."""
    clear_screen()
    print(f'TOP {Leaderboard.LENGTH} SCORES\n')
    leaderboard.display()
    print()


# game functions
def get_coords(grid: Grid, char: str) -> List[Tuple[int, int]]:
    """Returns a list of tuple-coordinates of all char in the grid."""
    lgrid = grid._grid
    (r, c) = (grid._rows, grid._cols)
    return [(i, j) for i in range(r) if char in lgrid[i]
                   for j in range(c) if lgrid[i][j] == char]


def game_logic(
        input_dir: Direction, grid: Grid, moves: int,
        egg_coords: List[Tuple[int, int]], points: int,
    ) -> Tuple[bool, int, List[Tuple[int, int]], int]:
    """This is the main logic of the egg rolling game.

    The list of egg_coords will be sorted based on axis
    and polarity to avoid overlapping eggs.

    Then, each moveable egg will be moved according to the
    input_dir until it hits an immovable character.

    Returns the game variables once there are no moveable eggs.
    """

    axis = input_dir.axis                       # axis of direction
    polarity = input_dir.polarity               # sign of direction

    if axis is Axis.HORIZONTAL:                 # sort using col/row if axis
        sort_key = (lambda tup: tup[::-1])      # is horizontal/vertical
    else:
        sort_key = None
    is_rev = polarity is Axis.NEGATIVE          # set list popping order

    while egg_coords:                           # loop while eggs are moveable

        new_egg_coords = []
        egg_coords.sort(key=sort_key,           # avoids egg overlaps
                        reverse=is_rev)

        while egg_coords:                       # process each moveable egg

            cur = egg_coords.pop()              # current egg coords
            nxt = input_dir.get_next(cur)       # adjacent coords
            adj = grid.peek(nxt)                # object adjacent to egg

            if adj == '🟩':
                grid.update(nxt, '🥚')
                grid.update(cur, '🟩')

                new_egg_coords.append(nxt)      # egg can still move

            else:
                if adj == '🍳':
                    grid.update(nxt, '🍳')     # cook egg
                    grid.update(cur, '🟩')
                    points -= 5
                elif adj == '🪹':
                    grid.update(nxt, '🪺')     # close nest
                    grid.update(cur, '🟩')
                    points += 10 + moves

        egg_coords = new_egg_coords

        if __name__ == '__main__':              # doesn't display the grid
            display(grid, is_moving=True)       # when file is imported

    egg_coords = get_coords(grid, '🥚')        # update coords

    state = bool(moves-1 and egg_coords)        # game ends when there are
                                                # no more eggs or no more moves
    return state, moves, egg_coords, points


# main function
def main() -> None:
    """Main driver code. This function contains the initialization of
    variables, the main loop, and the exit state.
    """

    # initialization of game variables
    all_moves: List[str] = []                   # all moves in arrow form
    state = True
    (grid, moves, egg_coords, leaderboard) = process_stage()
    points = 0

    # main game loop
    while state:

        display(grid, moves, all_moves, points)

        user_input = input('Enter a move: ')
        if not is_valid(user_input):
            continue

        input_dir = process_input(user_input)   # convert input string to 
                                                # Direction or None type
        if input_dir is None:
            break
        else:
            all_moves.append(repr(input_dir))
            moves -= 1
            vars_ = game_logic(input_dir, grid, moves, egg_coords, points)
            (state, moves, egg_coords, points) = vars_

    # after game has ended
    display(grid, moves, all_moves, points)     # display final game state
    
    if not state:                               # only evaluate score if
        leaderboard.evaluate(points)            # the game properly ended

    prompt = 'Show leaderboard? [Y/n/clear]: '

    while True:                                 # loop until input is y or n

        display(grid, moves, all_moves, points)
        show_leaderboard = input(prompt)

        match show_leaderboard.lower():

            case 'y':
                display_leaderboard(leaderboard)
                break
            
            case 'n':
                break
            
            case 'clear':
                leaderboard.clear()
                break
            
            case _:
                clear_screen()


if __name__ == '__main__':
    main()
