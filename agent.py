import torch
import random
import numpy as np
from collections import deque
from game_copy import Game, Direction
from model import Linear_QNet, QTrainer
from helper import plot
from collections import namedtuple

Point = namedtuple('Point', 'x,y')
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.7 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.model = Linear_QNet(6, 128, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def getSpriteByPosition(self, game, position, group):
        for index,spr in enumerate(group):
            if (index == position):
                return spr
        return False


    def get_state(self, game):
        Player = Point(game.player.rect.x,game.player.rect.y)
        lane = game.lane

        lane_l = game.lane == 150
        lane_r = game.lane == 250
        lane_m = game.lane == 350

        Vehbool = True

        vehicle = self.getSpriteByPosition(game, 0, game.vehicle_group)
        vehicle.lane = vehicle.rect.center[0]

        
        if Vehbool:
            state = [
            # Danger Straight
            (game.lane == vehicle.lane),

            # Danger right
            (lane_l and (vehicle.lane == 250)) or 
            (lane_m and (vehicle.lane == 350)),

             # Danger left
            (lane_r and (vehicle.lane == 250)) or 
            (lane_m and (vehicle.lane == 150)),

            # Move direction
            lane_l,
            lane_r,
            lane_m
            
            #Second car if I wanna do that too
            ]
        else:
            state = [
                False,
                False,
                False,
                lane_l,
                lane_r,
                lane_m
            ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        #for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 1000 - self.n_games
        final_move = [0,0,0]
        if random.randint(0, 2000) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = Game()
    while True:
        # get old state
        state_old = agent.get_state(game)
        
        if game.frame_iterations % 100 == 0:
            print(state_old)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        if game.frame_iterations % 100 == 0:
            print(reward)
        
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()