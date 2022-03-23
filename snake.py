import curses
from collections import namedtuple
from itertools import count, product
from more_itertools import side_effect, consume, random_product
from collections import deque


def transduce(xf, consumer, signal):
    """Sort of like iterate but with a stream of secondary inputs..."""
    while signal:
        consumer = xf(consumer, next(signal))
        yield consumer


# TODO: move these
def repeatedly(f):
    while True:
        yield f()


UP, DOWN, LEFT, RIGHT = (
    curses.KEY_UP,
    curses.KEY_DOWN,
    curses.KEY_LEFT,
    curses.KEY_RIGHT,
)
NO_MOVE = -1  # there is probably a curses.KEY for this?
# TODO: uh oh I should refactor this to use dataclass apparently
Game = namedtuple(
    "Game",
    [
        "snakeXY",
        "snakeSize",
        "snakeTail",
        "lastKey",
        "W",
        "H",
        "apples",
        "appleXY",
    ],
)


def initgame(W, H):
    snakeXY = W // 2, H // 2
    apples = repeatedly(lambda: random_product(range(W), range(H)))
    appleXY = next(apples)
    snakeSize = 1
    snakeTail = deque()
    return Game(snakeXY, snakeSize, snakeTail, NO_MOVE, W, H, apples, appleXY)


def move(G, INPUT):  # assumes origin is top left which comes from curses, hmm
    x = (G.snakeXY[0] + (INPUT == RIGHT) - (INPUT == LEFT)) % G.W
    y = (G.snakeXY[1] - (INPUT == UP) + (INPUT == DOWN)) % G.H

    if (x, y) in G.snakeTail:
        return G  # TODO: no op if walking backwards, event loss if tripping
    G.snakeTail.append(G.snakeXY)  # mutable state!!!
    if len(G.snakeTail) >= G.snakeSize:
        G.snakeTail.popleft()

    return G._replace(snakeXY=(x, y))


def play(G, INPUT):  # could dispatch with a dict?
    """Takes game state and INPUT, returns updated game state"""
    if INPUT != NO_MOVE:
        G = G._replace(lastKey=INPUT)
    else:
        INPUT = G.lastKey
    if INPUT in {UP, DOWN, LEFT, RIGHT}:
        G = move(G, INPUT)
        if G.snakeXY == G.appleXY:
            G = G._replace(appleXY=next(G.apples), snakeSize=G.snakeSize + 1)
    return G


def show(G):  # do I pass curses-specific attributes here?
    # thinking of punting and just adding a "META" field
    """Takes a game state and returns a ready-to-render list of tuples (x, y, symbol)"""
    return (
        (*G.snakeXY, "&"),
        (*G.appleXY, "@"),
        # (0, 0, ascii(G)),
    ) + tuple((*_, "&") for _ in G.snakeTail)


INPUT_TIMEOUT_MS = 70


def initscr(scr):
    def handler():
        curses.curs_set(0)
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        scr.timeout(INPUT_TIMEOUT_MS)

    return handler


def draw(scr):
    def handler(serialized):
        scr.clear()
        for x, y, symbol in serialized:
            scr.addstr(y, x, symbol)

    return handler


def main(scr):
    H, W = scr.getmaxyx()
    inputs = repeatedly(lambda: scr.getch())
    states = transduce(play, initgame(W - 1, H - 1), inputs)
    frames = map(show, states)
    consume(side_effect(draw(scr), frames, before=initscr(scr)))


core = curses.wrapper(main)
