import torch
import random
from collections import deque
from JumpyAi import player, reward, platform, asteroid, game_over, high_score, JumpyAi, score, action

MAX_MEMORY = 100000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 #randomness
        self.gamma = 0 #discount rate
        self.memory = deque(maxlen=MAX_MEMORY) #pop_left
        # TODO: model , trainer

    def get_game_state(player, asteroids, platforms, score, high_score, game_over):
        # Get player position and velocity

        player_position = (player.position.x, player.position.y)
        player_velocity = (player.velocity.x, player.velocity.y)

        # Check if player is on the ground (assuming the Agent class has a method for this)
        player_on_ground = player.is_on_ground()

        # Get asteroid positions and speeds
        asteroid_positions = [(asteroid.position.x, asteroid.position.y) for asteroid in asteroids]
        asteroid_speeds = [asteroid.speed for asteroid in asteroids]

        # Get platform positions and moving states
        platform_positions = [(platform.position.x, platform.position.y) for platform in platforms]
        platform_moving_states = [platform.is_moving for platform in platforms]

        # Create the game state dictionary
        game_state = {
            "player_position": player_position,
            "player_velocity": player_velocity,
            "player_on_ground": player_on_ground,
            "asteroid_positions": asteroid_positions,
            "asteroid_speeds": asteroid_speeds,
            "platform_positions": platform_positions,
            "platform_moving_states": platform_moving_states,
            "score": score,
            "high_score": high_score,
            "game_over": game_over
        }

        return game_state

    def remember(self, state, action, reward, next_state, done):
        pass

    def train_long_memory(self):
        pass

    def train_short_memory(self, state, action, reward, next_state, done):
        pass

    def get_action(self, state):
        player_position = game_state["player_position"]
        asteroid_positions = game_state["asteroid_positions"]
        platform_positions = game_state["platform_positions"]
        player_on_ground = game_state["player_on_ground"]
        game_over = game_state["game_over"]

        # If the game is over, don't take any action
        if game_over:
            return 0  # No action

        player_x, player_y = player_position
        asteroid_x, asteroid_y = max(asteroid_positions, key=lambda pos: pos[1])  # Get the lowest asteroid
        platform_y = min(platform_positions, key=lambda pos: abs(pos[0] - player_x))[1]  # Get the nearest platform

        # If the asteroid is directly under the player, move left or right
        if abs(asteroid_x - player_x) < 20:
            if asteroid_x < player_x:
                return 1  # Move left
            else:
                return 2  # Move right

        # If a platform is near and player is on the ground, jump to the platform
        if abs(platform_y - player_y) < 10 and player_on_ground:
            return 0  # Jump

        return 0

def train():
    global score, high_score, game_over
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = JumpyAi()

    while True:
        state_old = agent.get_game_state(player, asteroid, platform, high_score, game_over)

        final_move = agent.get_action(state_old)  # Pass the game state to get_action
        JumpyAi.action = agent.get_action(game_state)
        reward, done = game.move(final_move)
        state_new = agent.get_game_state(player, asteroid, platform, high_score, game_over)

        agent.train_short_memory(state_old, final_move, reward, state_new, done)  # Pass final_move as action

        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # Train long memory, plot result
            game_over = True  # Fix typo
            agent.train_long_memory()

            print('Game', agent.n_games, 'Score', score, 'High Score', high_score)

            # Reset game state
            score = 0
            game_over = False

if __name__ == '__main__':
    train()
