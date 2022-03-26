import curses
from collections import namedtuple
from itertools import count, product, dropwhile
from more_itertools import side_effect, consume, random_product, first_true
from collections import deque


# TODO: move these
def transduce(xf, consumer, signal):
    """Sort of like iterate but with a stream of secondary inputs..."""
    while signal:
        consumer = xf(consumer, next(signal))
        yield consumer


def repeatedly(f):
    while True:
        yield f()

UP, DOWN, LEFT, RIGHT = (
    curses.KEY_UP,
    curses.KEY_DOWN,
    curses.KEY_LEFT,
    curses.KEY_RIGHT,
)
ARROWS = {UP, DOWN, LEFT, RIGHT}

directions = {
        UP: (0, -1),
        DOWN: (0, 1),
        LEFT: (-1, 0),
        RIGHT: (1, 0),
        }

NO_MOVE = -1  # there is probably a curses.KEY for this?
# TODO: uh oh I should refactor this to use dataclass apparently
Game = namedtuple(
    "Game",
    [
        "snake",
        "snakeDirection",
        "W",
        "H",
        "apples",
        "apple",
        "alive",
    ],
)


def initgame(W, H):
    snakeXY = W // 2, H // 2
    snake = deque([snakeXY])
    snakeDirection = (0, 0)
    apples = repeatedly(lambda: random_product(range(W), range(H)))
    apple = next(apples)
    alive = True
    return Game(
            snake, snakeDirection, W, H, apples, apple,
            alive,)


def translate(u, v, wall, ceiling): # vector translation on a 2D torus
    """Returns the vector translation of u by v on a 2D torus of specified dimensions."""
    return (u[0] + v[0]) % wall, (u[1] + v[1]) % ceiling

def turn(G, INPUT):
    """Takes game + input, returns a game whose snake may be oriented to match input"""
    if INPUT not in ARROWS:
        return G
    else:
        vx, vy = directions[INPUT]
        if (vx and vx == -G.snakeDirection[0]) or (vy and vy == -G.snakeDirection[1]):
            return G
        else:
            return G._replace(snakeDirection=(vx, vy))

def step(G):
    move = translate(G.snake[-1], G.snakeDirection, G.W, G.H)
    if move not in G.snake:
        G.snake.append(move)
        return G
    else:
        return G._replace(alive=False)

def play(G, INPUT):  # could dispatch with a dict?
    """Takes game state and INPUT, returns updated game state"""
    G = turn(G, INPUT)
    G = step(G)
    if not G.alive:
        return None
    elif G.snake[-1] == G.apple:
        return G._replace(
                apple=first_true(G.apples, lambda a: a not in set(G.snake)))
    else:
        G.snake.popleft()
        return G


def show(G):  # do I pass curses-specific attributes here?
    # thinking of punting and just adding a "META" field
    """Takes a game state and returns a ready-to-render list of tuples (x, y, symbol)"""
    return (
        (*G.apple, "@"),
        (0, 0, ascii(G)),
    ) + tuple((*_, "&") for _ in G.snake)


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
    inputs = dropwhile(lambda i: i not in ARROWS, repeatedly(lambda: scr.getch()))
    states = transduce(play, initgame(W - 1, H - 1), inputs)
    consume(side_effect(draw(scr), map(show, states), before=initscr(scr)))


core = curses.wrapper(main)
