import curses
from collections import namedtuple
from itertools import count, product, dropwhile, takewhile
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

def subtract(u, v):
    return v[0] - u[0], v[1] - u[1]

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
        "input",
    ],
)
def initgame(W, H):
    global SCORE
    SCORE = 0

    snakeXY = W // 2, H // 2
    snake = deque([snakeXY])
    snakeDirection = (0, 0)
    apples = repeatedly(lambda: random_product(range(W), range(H)))
    apple = next(apples)
    alive = True
    input = None
    return Game(
            snake, snakeDirection, W, H, apples, apple,
            alive,
            input,
            )


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
    G = G._replace(input=INPUT)
    G = turn(G, INPUT)
    G = step(G)
    if G.snake[-1] == G.apple:
        global SCORE
        SCORE += 1
        return G._replace(
                apple=first_true(G.apples, lambda a: a not in G.snake))
    else:
        G.snake.popleft()
        return G

APPLE_SYMBOL = "@"
SNAKE_SYMBOL = "&"


def show(G):  # do I pass curses-specific attributes here?
    # thinking of punting and just adding a "META" field
    """Takes a game state and returns a ready-to-render list of tuples (x, y, symbol)"""
    center = G.snake[-1]
    ret = (
        (G.apple,APPLE_SYMBOL),
        # (0, 0, ascii(G)),
        # (1,1, ascii(G.input)),
    ) + tuple((_,SNAKE_SYMBOL) for _ in G.snake)
    return ((*translate(subtract(center, u), (G.W // 2, G.H // 2), G.W, G.H), sym) for u, sym in ret)


INPUT_TIMEOUT_MS = 70


def initscr(scr):
    def handler():
        curses.curs_set(0)
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        scr.timeout(INPUT_TIMEOUT_MS)
        scr.addstr(10, 10, "Badger's Snake ⾘的⺒", curses.A_BOLD)

    return handler

def bye(scr):
    def handler():
        curses.flash()
        global SCORE
        scr.addstr(10, 10, "Thanks for playing! Score: %d" % (SCORE))
        scr.addstr(12, 12, "Press q to quit the game.")
        consume(takewhile(lambda i: i != ord("q"), repeatedly(lambda:scr.getch())))

    return handler


def draw(scr):
    ATTRIBUTES = {
        APPLE_SYMBOL: curses.A_BOLD | curses.color_pair(197),
        SNAKE_SYMBOL: curses.A_BOLD | curses.color_pair(47),
            }
    def handler(serialized):
        scr.clear()
        for x, y, symbol in serialized:
            scr.addstr(y, x, symbol, ATTRIBUTES[symbol])

    return handler


def main(scr):
    H, W = scr.getmaxyx()
    G = initgame(W - 1, H - 1)
    inputs = dropwhile(lambda i: i not in ARROWS, repeatedly(lambda: scr.getch()))
    states = takewhile(lambda g: g.alive, transduce(play, G, inputs))
    run = side_effect(draw(scr), map(show, states), before=initscr(scr), after=bye(scr))
    consume(run)

core = curses.wrapper(main)
