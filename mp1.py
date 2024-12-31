import os
import sys

import subprocess
import time

from enum import Enum, auto
from typing import List, Tuple


# constants
TICK_RATE = 0.05
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
    VERTICAL = auto()
    HORIZONTAL = auto()
    POSITIVE = auto()
    NEGATIVE = auto()


class Direction:
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

        match direction:
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

        if (0 <= i < self._rows and
            0 <= j < self._cols):
            return self._grid[i][j]             # in bounds
        else:
            return None                   # out of bounds


    def update(self, coord: Tuple[int, int], char: str) -> None:
        """Places char on grid coord."""
        (i, j) = coord
        self._grid[i][j] = char


# utility functions
def get_level_info() -> Tuple[Grid, int, List[Tuple[int, int]]]:
    """This function extracts and processes the stage grid,
    number of moves, and egg coordinates from the level file, if any.

    Returns the extracted data.
    """

    if len(sys.argv) < 2:
        raise FileNotFoundError('Please input a level file '
                                + 'from the level directory.')

    level_path = os.path.join('.', 'level', sys.argv[1])
    
    with open(level_path, encoding='utf-8') as f:
        r = int(f.readline().replace('\n', ''))
        moves = int(f.readline().replace('\n', ''))
        grid_ = []
        for i in range(r):
            grid_.append(f.readline().replace('\n', ''))

    grid = process_grid(grid_)

    return grid, moves, get_coords(grid, '🥚')


def process_grid(grid: List[str]) -> Grid:
    """Processes raw characters from the stage grid
    into their respective emoji versions.

    Returns a Grid.
    """
    return Grid([[GRAPHICS[j] if j in GRAPHICS else j
                  for j in i]
                  for i in grid])


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

    axis = input_dir.axis                    # axis of direction
    polarity = input_dir.polarity            # sign of direction

    if axis is Axis.HORIZONTAL:              # sort using column/row if axis is
        sort_key = (lambda tup: tup[::-1])   # horizontal/vertical repectively
    else:
        sort_key = None
    is_rev = polarity is Axis.NEGATIVE       # set list popping order

    while egg_coords:                        # loop if there is a moveable egg

        new_egg_coords = []

        egg_coords.sort(key=sort_key,        # avoids egg overlaps
                        reverse=is_rev)

        while egg_coords:                    # process each moveable egg

            cur = egg_coords.pop()           # current egg coords
            nxt = input_dir.get_next(cur)    # adjacent coords
            adj = grid.peek(nxt)             # object adjacent to egg

            if adj == '🟩':
                grid.update(nxt, '🥚')
                grid.update(cur, '🟩')

                new_egg_coords.append(nxt)   # egg can still move

            else:
                if adj == '🍳':
                    grid.update(nxt, '🍳')  # cook egg
                    grid.update(cur, '🟩')
                    points -= 5
                elif adj == '🪹':
                    grid.update(nxt, '🪺')  # close nest
                    grid.update(cur, '🟩')
                    points += 10 + moves

        egg_coords = new_egg_coords

        if __name__ == '__main__':           # doesn't display the grid
            display(grid, is_moving=True)    # when imported

    egg_coords = get_coords(grid, '🥚')     # update coords

    state = bool(moves-1 and egg_coords)     # game ends when there are
                                             # no more eggs or no more moves

    return state, moves, egg_coords, points


def main() -> None:
    """Main driver code. This function contains the initialization of
    variables, the main loop, and the exit state.
    """

    # game variable initialization
    all_moves: List[str] = []                     # all previous moves in arrow form
    state = True
    (grid, moves, egg_coords) = get_level_info()
    points = 0

    # main game loop
    while state:

        display(grid, moves, all_moves, points)

        user_input = input('Enter a move: ')
        if not is_valid(user_input):
            continue

        input_dir = process_input(user_input)     # convert input string to 
                                                  # Direction or None type

        if input_dir is None:
            break
        else:
            all_moves.append(repr(input_dir))
            moves -= 1
            vars_ = game_logic(input_dir, grid, moves, egg_coords, points)
            (state, moves, egg_coords, points) = vars_

    display(grid, moves, all_moves, points)       # display final state of the game


if __name__ == '__main__':
    main()