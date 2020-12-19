import pyglet
import random
import pickle
import atexit
import os
from pybird.game import Game

MAGIC_POS = (9999, 9999)
log_file = "./log.txt"

class Bot:
    def __init__(self, game):
        self.game = game
        # constants
        self.WINDOW_HEIGHT = Game.WINDOW_HEIGHT
        self.PIPE_WIDTH = Game.PIPE_WIDTH
        # this flag is used to make sure at most one tap during
        # every call of run()
        self.tapped = False

        self.game.play ()

        # variables for plan
        self.Q = {}
        self.alpha = 0.6
        self.discount = 0.8
        self.explore = 0
        self.pre_s = MAGIC_POS
        self.pre_a = 0

        self.chunk = 4
        self.xchunk = 2
        self.try_times = 0

        self.to_reward_passing=3
        self.initialize ()

        if os.path.isfile ('dict_Q'):
            self.Q = pickle.load (open ('dict_Q', 'rb'))

        def do_at_exit():
            pickle.dump (self.Q, open ('dict_Q', 'wb'))
            print ('wirte to dict_Q')

        atexit.register (do_at_exit)

    # this method is auto called every 0.05s by the pyglet
    def run(self):
        if self.game.state == 'PLAY':
            self.tapped = False
            # call plan() to execute your plan
            self.plan (self.get_state ())
        else:
            state = self.get_state ()
            bird_state = list (state['bird'])
            bird_state[2] = 'dead'
            state['bird'] = bird_state
            # do NOT allow tap
            self.tapped = True
            self.plan (state)
            # restart game
            print ('score:', self.game.record.get (), 'best: ', self.game.record.best_score)
            with open(log_file,'a') as f:
                f.write(f"({self.try_times}-{self.game.record.get ()}) score: {self.game.record.get ()} best: {self.game.record.best_score}\n")
            self.game.restart ()
            self.game.play ()

    def initialize(self):
        self.last_score = 0
        self.last_alive_state = 'alive'
        self.pre_s = MAGIC_POS

    # get the state that robot needed
    def get_state(self):
        state = {}
        # bird's position and status(dead or alive)
        state['bird'] = (int (round (self.game.bird.x)), \
                         int (round (self.game.bird.y)), 'alive')
        state['pipes'] = []
        # pipes' position
        for i in range (1, len (self.game.pipes), 2):
            p = self.game.pipes[i]
            if p.x < Game.WINDOW_WIDTH:
                # this pair of pipes shows on screen
                x = int (round (p.x))
                y = int (round (p.y))
                state['pipes'].append ((x, y))
                state['pipes'].append ((x, y - Game.PIPE_HEIGHT_INTERVAL))
        return state

    # simulate the click action, bird will fly higher when tapped
    # It can be called only once every time slice(every execution cycle of plan())
    def tap(self):
        if not self.tapped:
            self.game.bird.jump ()
            self.tapped = True

    def calculate_parameter(self, state):
        x = state['bird'][0]
        y = state['bird'][1]

        pipes = [pipe for pipe in state['pipes'] if pipe[0] + self.PIPE_WIDTH + 10 >= x][:2]

        max_y = self.WINDOW_HEIGHT
        min_y = 0
        pipe_x = 9999

        if len (pipes) != 0:
            max_y = max ([pipe[1] for pipe in pipes])
            min_y = min ([pipe[1] for pipe in pipes])
            assert pipes[0][0] == pipes[1][0]
            pipe_x = pipes[0][0]

        half_y = min_y + int ((max_y - min_y) * 2 / 5)

        dy_up = (max_y - y) // self.chunk
        dy_down = (y - min_y) // self.chunk
        dx = (pipe_x - x) // self.xchunk
        dy_half = (half_y - y) // self.chunk
        return dy_up, dy_down, dx, dy_half

    def reward(self, next_state):
        _, _, _, dy_half = self.calculate_parameter (next_state)
        is_alive = next_state['bird'][2] == 'alive'
        reward = 0 if is_alive else -10000
        if dy_half < 0:
            reward -= abs (dy_half)
            if self.pre_a == 0:
                reward += abs (dy_half) * 10
        if dy_half > 0:
            reward -= abs (dy_half)
            if self.pre_a == 1:
                reward += abs (dy_half) * 10
        record = self.game.record.get ()
        if record > self.last_score:
            print (f"\r({self.try_times}-{record}) ", end="")
            self.last_score = record
            if self.to_reward_passing > 0:
                reward += 500
                self.to_reward_passing -= 1
        return reward

    # That's where the robot actually works
    # NOTE Put your code here
    def plan(self, state):

        if self.last_alive_state == 'dead':
            self.initialize ()

        if state['bird'][2] == 'dead':
            self.try_times += 1

        n_dy_up, n_dy_down, n_dx, _ = self.calculate_parameter (state)

        self.Q.setdefault ((n_dy_down, n_dx), {0: 0, 1: 0})

        if random.random () < self.explore and self.try_times:
            action = 0 if random.random () < 0.5 else 1
        else:
            action = 0
            if self.Q[(n_dy_down, n_dx)][1] > self.Q[(n_dy_down, n_dx)][0]:
                self.tap ()
                action = 1

        reward = self.reward (next_state=state)

        # update if is not initial state
        if self.pre_s != MAGIC_POS:
            self.Q[(self.pre_s)][self.pre_a] = (1 - self.alpha) * self.Q[self.pre_s][
                self.pre_a] + self.alpha * (reward + self.discount * max (
                self.Q[(n_dy_down, n_dx)][0],self.Q[(n_dy_down, n_dx)][1]))

        self.pre_s = (n_dy_down, n_dx)
        self.pre_a = action

        # self.last_state = state
        self.last_alive_state = state['bird'][2]


if __name__ == '__main__':
    show_window = True
    enable_sound = False
    game = Game ()
    game.set_sound (enable_sound)
    bot = Bot (game)


    def update(dt):
        game.update (dt)
        bot.run ()


    pyglet.clock.schedule_interval (update, Game.TIME_INTERVAL)

    if show_window:
        window = pyglet.window.Window (Game.WINDOW_WIDTH, Game.WINDOW_HEIGHT, vsync=False)

        @window.event
        def on_draw():
            window.clear ()
            game.draw ()

        pyglet.app.run ()
    else:
        pyglet.app.run ()
