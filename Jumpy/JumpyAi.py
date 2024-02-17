import pygame
import random
import os
from pygame import mixer
import numpy as np
import torch
import random
from collections import deque

# intialization
mixer.init()
pygame.init()

# reset

# reward system
#every time it reach a new platform we have +10
#every game over we have -10
#else: 0
global reward
reward = 0
milestone_reached = False  # Initialize milestone reached flag
# play(action) -> movement
global action
# gaem_iteration

# collision in the player class

#agent field
MAX_MEMORY = 100000
BATCH_SIZE = 1000
LR = 0.001
# fields
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
MAX_PLATFORM = 10
MAX_ENEMY = 5
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 100)
GRAVITY = 1
SCROLL_THRESH = 300
global scroll
scroll = 0
bg_scroll = 0
game_over = False
score = 0
fade_counter = 0

if os.path.exists('score.txt'):
    with open('score.txt', 'r') as file:
        high_score = int(file.read())
else:
    high_score = 0

font_small = pygame.font.SysFont('Lucida Sans', 20)
font_big = pygame.font.SysFont('Lucida Sans', 24)
# game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("platform jumping with asteroid falling")

# set game tick
clock = pygame.time.Clock()
FPS = 60

# load music
pygame.mixer.music.load('asset/bgmusic.mp3')
pygame.mixer.music.set_volume(0.7)
pygame.mixer.music.play(-1, 0.0)

jump_fx = pygame.mixer.Sound('asset/jump_fx.mp3')
jump_fx.set_volume(0.5)

death_fx = pygame.mixer.Sound('asset/death_fx.mp3')
death_fx.set_volume(0.5)



class SpriteSheet():
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame, width, height, scale, colour):
        image = pygame.surface.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0,0),((frame * width),0, width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(colour)

        return image

# load image
player_image = pygame.image.load("asset/idle1.png").convert_alpha()
run_image = pygame.image.load('asset/Run_animation.png').convert_alpha()
run_image = pygame.transform.scale(run_image, (40, 45))
jump_image = pygame.image.load("asset/Jump_1.png")
jump_image = pygame.transform.scale(jump_image, (40, 45))
bg = pygame.image.load("asset/bg.jpg").convert_alpha()
platform_image = pygame.image.load("asset/pad.png").convert_alpha()
bg = pygame.transform.scale(bg, (400, 600))
asteroid = pygame.image.load("asset/asteroid1.png")
asteroid = pygame.transform.scale(asteroid, (10, 10))
asteroid_sheet = SpriteSheet(asteroid)


def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x, y))


def draw_panel():
    # pygame.draw.line(screen, WHITE, (0,30) , (SCREEN_WIDTH, 30), 2)
    draw_text('SCORE ' + str(score), font_small, WHITE, 0, 0)


def draw_bg(bg_scroll):
    screen.blit(bg, (0, 0 + bg_scroll))
    screen.blit(bg, (0, -600 + bg_scroll))

def check_score_increase_reward(score, old_score, reward, milestone_reached):
    if score > old_score and (score - old_score) >= 100 and not milestone_reached:
        reward += 10
        milestone_reached = True
    return reward, milestone_reached

def track_score_changes(score, old_score, timer):
    # Increment the timer with each tick
    timer += 1

    # Check if 60 ticks have passed
    if timer >= 60:
        # Update the old score with the current score
        old_score = score
        # Reset the timer
        timer = 0

    return old_score, timer



class Enemy(pygame.sprite.Sprite):
    def __init__(self, SCREEN_WIDTH, y, sprite_sheet, scale, score):
        pygame.sprite.Sprite.__init__(self)
        self.x = random.randint(0,400)
        self.dy = random.randint(1,3)
        if score > 1500:
            self.dy = random.randint(3,4)
        elif score > 5000:
            self.dy = random.randint(6,7)
        elif score > 10000:
            self.dy = random.randint(10,16)


        image = sprite_sheet.get_image(0, 32,32 ,scale, (0,0,0))
        image.set_colorkey((0,0,0))
        self.image = image
        self.rect = self.image.get_rect()

        self.rect.x = self.x
        self.rect.y = y

    def update(self, scroll, SCREEN_HEIGHT):
        self.rect.y += scroll

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
        self.rect.y += self.dy
# Player class
class Player:

    def __init__(self, x, y, player_image, score):

        self.image = pygame.transform.scale(player_image, (20, 45))
        self.width = 15
        self.height = 45
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.vel_x = 0
        self.flip = False
        self.on_ground = False
        self.frame_iteration = 0
        self.score = score

    def jump(self):
        if self.on_ground:  # Only jump if player is on the ground
            self.vel_y = -18  # Set the vertical velocity to make the player jump
            self.on_ground = False  # Update the on_ground flag
            jump_fx.play()

    def move(self, action):
        global reward
        dx = 0
        old_score = 0
        dy = 0
        scroll = 0
        self.action  = action
        key = pygame.key.get_pressed()

        if self.action == 1:
            dx -= 8
            self.flip = True

        if self.action == 2:
            dx += 8
            self.flip = False

        if self.action == 0:
            self.jump()
            self.image = jump_image

        self.vel_y += GRAVITY

        dy += self.vel_y

        if self.rect.left + dx < 0:
            dx = 0 - self.rect.left
        if self.rect.right + dx > SCREEN_WIDTH:
            dx = SCREEN_WIDTH - self.rect.right

        last_touched_platform = None  # Variable to keep track of the last platform touched by the player

        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = 0
                        self.on_ground = True

                        # Check if the player touched a new platform
                        if platform != last_touched_platform:
                            #reward += 10
                            last_touched_platform = platform

        # Update the old score to prevent earning points for staying on the same platform too long
        old_score = self.score




        if self.rect.top <= SCROLL_THRESH:
            if self.vel_y < 0:
                scroll = -dy

        self.rect.x += dx
        self.rect.y += dy + scroll

        return scroll

    def draw(self, screen):

        if self.vel_x == 0 and self.vel_y == 0:
            self.image = pygame.transform.scale(player_image, (20, 45))
            screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        elif self.vel_y != 0:
            self.image = jump_image
            screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

        # pygame.draw.rect(screen,BLACK, self.rect, 1)

# class to create platform
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, platform_image, moving):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(platform_image, (width, 25))
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        if score > 1500:
            self.speed = random.randint(1, 3)
        elif score > 5000:
            self.speed = random.randint(4, 5)
        elif score > 10000:
            self.speed = random.randint(5, 6)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        if self.moving == True:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed

        if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.direction *= -1
            self.move_counter = 0

        self.rect.y += scroll

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


platform_group = pygame.sprite.Group()
asteroid_group = pygame.sprite.Group()

player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150, player_image, score)

platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 120, 100, platform_image, False)
platform_group.add(platform)

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # Randomness
        self.gamma = 0  # Discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # Replay memory

    def get_game_state(self, player, asteroids, platforms, high_score, game_over):
        # Get player position and velocity
        player_position = (player.rect.x, player.rect.y)
        player_velocity = (player.vel_x, player.vel_y)

        # Get asteroid positions and speeds
        asteroid_positions = []
        asteroid_speeds = []
        for asteroid in asteroids:
            asteroid_positions.append((asteroid.rect.x, asteroid.rect.y))
            asteroid_speeds.append(asteroid.dy)

        # Get platform positions and moving states
        platform_positions = [(platform.rect.x, platform.rect.y) for platform in platforms]
        platform_moving_states = [platform.moving for platform in platforms]

        # Create the game state dictionary
        game_state = {
            "player_position": player_position,
            "player_velocity": player_velocity,
            "asteroid_positions": asteroid_positions,
            "asteroid_speeds": asteroid_speeds,
            "platform_positions": platform_positions,
            "platform_moving_states": platform_moving_states,
            "high_score": high_score,
            "game_over": game_over
        }

        return game_state

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        pass  # Implement this method to train the agent's long-term memory

    def train_short_memory(self, state, action, reward, next_state, done):
        pass  # Implement this method to train the agent's short-term memory

    def get_action(self, state):
        player_position = state["player_position"]
        asteroid_positions = state["asteroid_positions"]
        platform_positions = state["platform_positions"]
        game_over = state["game_over"]

        # If the game is over, don't take any action
        if game_over:
            return 0  # No action

        player_x, player_y = player_position

        # Find the nearest asteroid below the player and get its position
        nearest_asteroid = min(asteroid_positions,
                               key=lambda pos: (pos[0] - player_x) ** 2 if pos[1] > player_y else float('inf'))
        asteroid_x, asteroid_y = nearest_asteroid

        # If the asteroid's y value is less than 100 units below the player's y value, move left or right
        if abs(asteroid_y - player_y) < 100:
            if asteroid_x < player_x:
                return 1  # Move left
            else:
                return 2  # Move right

        # If a platform is near and player is on the ground, jump to the platform
        platform_y = min(platform_positions, key=lambda pos: abs(pos[0] - player_x))[1]  # Get the nearest platform
        if abs(platform_y - player_y) < 10:
            return 0  # Jump

        return 0  # No action by default




# main game loop
def JumpyAi():
    global bg_scroll
    global score
    global reward
    global milestone_reached
    global platform
    global high_score
    run = True
    timer = 0  # Initialize the timer
    old_score = 0  # Initialize the old score
    game_over = False
    agent = Agent()

    while run:
        clock.tick(FPS)

        if not game_over:

            #scroll = player.move(action)
            scroll = player.move(agent.get_action)

            bg_scroll += scroll
            if bg_scroll >= 768:
                bg_scroll = 0
            draw_bg(bg_scroll)
            reward, milestone_reached = check_score_increase_reward(score, old_score, reward, milestone_reached)

            platform_group.draw(screen)
            asteroid_group.draw(screen)
            player.draw(screen)
            print(reward)

            # death scenario and danger state
            if player.rect.top > SCREEN_HEIGHT:
                game_over = True
                death_fx.play()
                reward -= 10

            if pygame.sprite.spritecollide(player, asteroid_group, False):
                if pygame.sprite.spritecollide(player, asteroid_group, False, pygame.sprite.collide_mask):
                    game_over = True
                    death_fx.play()
                    reward -= 10

            if len(platform_group) < MAX_PLATFORM:
                p_w = random.randint(50, 100)
                p_x = random.randint(0, SCREEN_WIDTH - p_w)
                p_y = platform.rect.y - random.randint(80, 120)
                p_type = random.randint(1, 2)
                if p_type == 1 and score > 500:
                    p_moving = True
                else:
                    p_moving = False
                platform = Platform(p_x, p_y, p_w, platform_image, p_moving)
                platform_group.add(platform)

            platform_group.update(scroll)

            if len(asteroid_group) < MAX_ENEMY:
                asteroid = Enemy(SCREEN_WIDTH, 10, asteroid_sheet, 3, score)
                asteroid_group.add(asteroid)

            asteroid_group.update(scroll, SCREEN_HEIGHT)

            if scroll > 0:
                score += scroll

            pygame.draw.line(screen, WHITE, (0, score - high_score + SCROLL_THRESH),
                             (SCREEN_WIDTH, score - high_score + SCROLL_THRESH), 3)
            draw_text('HIGH_SCORE', font_small, WHITE, SCREEN_WIDTH - 130, score - high_score + SCROLL_THRESH)
            draw_panel()

        else:
            # Reset game state
            game_over = False
            score = 0
            scroll = 0
            fade_counter = 0
            player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
            asteroid_group.empty()
            platform_group.empty()
            platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 120, 100, platform_image, False)
            platform_group.add(platform)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if score > high_score:
                    high_score = score
                    with open('score.txt', 'w') as file:
                        file.write(str(high_score))
                run = False

        pygame.display.update()

    pygame.quit()

# Call the main function



def train():
    global score, high_score, game_over, action, scroll
    plot_scores = []
    plot_mean_scores = []
    agent = Agent()
    game = JumpyAi()
    game_over = False

    while True:
        state_old = agent.get_game_state(player, asteroid, platform, high_score, game_over)

        final_move = agent.get_action(state_old)  # Pass the game state to get_action
        action = agent.get_action(game_state)
        scroll = player.move(action)
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

if __name__ == '__main__':
    train()
