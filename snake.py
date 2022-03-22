import curses
from collections import namedtuple
from itertools import count
from more_itertools import side_effect, consume

UP, DOWN, LEFT, RIGHT = curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT

Game = namedtuple("Game", ["snakex", "snakey"])

def move(G, INPUT): # assumes origin is top left which comes from curses, hmm
    x = G.snakex + (INPUT == RIGHT) - (INPUT == LEFT)
    y = G.snakey - (INPUT == UP) + (INPUT == DOWN)
    return G._replace(snakex=x, snakey=y)
    
def play(G, INPUT): # could dispatch with a dict?
    """Takes game state and INPUT, returns updated game state"""
    if INPUT in {UP, DOWN, LEFT, RIGHT}:
        G = move(G, INPUT)
    return G

def show(G): # attributes?
    """Takes a game state and returns a ready-to-render list of tuples (x, y, symbol)"""
    return [(G.snakex, G.snakey, "&")]

INPUT_TIMEOUT_MS = -1

def initscr(scr):
    curses.curs_set(0)
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    scr.timeout(INPUT_TIMEOUT_MS)

def draw(scr):
    def handler(serialized):
        scr.clear()
        for x, y, symbol in serialized:
            scr.addstr(y, x, symbol)
    return handler

def transduce(xf, consumer, signal):
    """Sort of like iterate but with a stream of secondary inputs..."""
    while signal:
        consumer = xf(consumer, next(signal))
        yield consumer

def main(scr):
    initscr(scr)
    G = Game(10, 10)
    inputs = (scr.getch() for _ in count())
    states = transduce(play, G, inputs)
    frames = map(show, states)
    consume(side_effect(draw(scr), frames))

core = curses.wrapper(main)
