import pygame
from pygame.locals import *
import random
from enum import Enum
from collections import namedtuple
import numpy as np

class Direction(Enum):
    RIGHT = 1
    MID = 2
    LEFT = 3

pygame.init()


# colors
gray = (100, 100, 100)
green = (76, 208, 56)
red = (200, 0, 0)
white = (255, 255, 255)
yellow = (255, 232, 0)

SPEED = 200

# road and marker sizes
road_width = 300
marker_width = 10
marker_height = 50
# lane coordinates
left_lane = 150
center_lane = 250
right_lane = 350
# road and edge markers
h = 480
w = 640
road = (100, 0, road_width, h)
left_edge_marker = (95, 0, marker_width, h)
right_edge_marker = (395, 0, marker_width, h)

# for animating movement of the lane markers
lane_marker_move_y = 0

class Vehicle(pygame.sprite.Sprite):
    
    def __init__(self, image, x, y):
        pygame.sprite.Sprite.__init__(self)
        
        # scale the image down so it's not wider than the lane
        image_scale = 45 / image.get_rect().width
        new_width = image.get_rect().width * image_scale
        new_height = image.get_rect().height * image_scale
        self.image = pygame.transform.scale(image, (new_width, new_height))

        
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        
class PlayerVehicle(Vehicle):
    
    def __init__(self, x, y):
        image = pygame.image.load('images/car.png')
        super().__init__(image, x, y)

class Game:

    def __init__(self, w=640, h=480):
        #Create Window
        self.w = w
        self.h = h
        # init display
        self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
        pygame.display.set_caption('Car Game')
        self.clock = pygame.time.Clock()
        self.lane = 250
        self.lanes = [left_lane, center_lane, right_lane]
        self.lane_marker_move_y = 0


        # frame settings
        clock = pygame.time.Clock()
        fps = 120
        # load the vehicle images
        image_filenames = ['pickup_truck.png', 'semi_trailer.png', 'taxi.png', 'van.png']
        self.vehicle_images = []
        for image_filename in image_filenames:
            image = pygame.image.load('images/' + image_filename)
            self.vehicle_images.append(image)
            
        # load the crash image
        crash = pygame.image.load('images/crash.png')
        self.crash_rect = crash.get_rect()
        self.reset()

    def getSpriteByPosition(self, position, group):
        for index,spr in enumerate(group):
            if (index == position):
                return spr
        return False  
     
    def reset(self):        
        self.frame_iterations = 0
        self.kill_count = 0
        # game settings
        gameover = False
        self.speed = 200
        self.score = 0
        # sprite groups
        self.player_group = pygame.sprite.Group()
        self.vehicle_group = pygame.sprite.Group()

        # player's starting coordinates
        player_x = 250
        player_y = 400

        self.lane = 250

        # create the player's car
        self.player = PlayerVehicle(player_x, player_y)
        self.player_group.add(self.player)
        self.add_vehicle()
        self.update_ui()


    def _move(self, action, reward):
        # [straight, right, left]
        clock_wise = [Direction.LEFT, Direction.MID, Direction.RIGHT]

        if np.array_equal(action, [1, 0, 0]):
            new_dir = Direction.LEFT
            self.direction = new_dir
            if self.lane == 350:
                if self.player.rect.center[0]> 150 :
                    self.player.rect.x -= 100
                    self.lane = 250
            elif self.lane == 250:
                if self.player.rect.center[0] > 150 :
                    self.player.rect.x -= 100
                    self.lane = 150

        elif np.array_equal(action,[0, 0, 1]):
            new_dir = Direction.RIGHT
            self.direction = new_dir
            if self.lane == 250:
                if self.player.rect.center[0] < 350:
                    self.player.rect.x += 100
                    self.lane = 350
            elif self.lane == 150:
                if self.player.rect.center[0]< 350:
                    self.player.rect.x += 100
                    self.lane = 250
        return reward            

            

    def add_vehicle(self):
        if len(self.vehicle_group) < 2:
            # ensure there's enough gap between vehicles
            add_vehicle = True
            for vehicle in self.vehicle_group:
                if vehicle.rect.top < vehicle.rect.height * 1.5:
                    add_vehicle = False
                    
            if add_vehicle:
                # select a random lane
                lane = random.choice(self.lanes)
                
                # select a random vehicle image
                image = random.choice(self.vehicle_images)
                vehicle = Vehicle(image, lane, self.h / -2)
                self.vehicle_group.add(vehicle)
            
    def play_step(self, action):
        reward = 0.01
        self.frame_iterations+=1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        
        
        #if len(vehicles)>0:
        #   Vehbool = True
        #    vehicle = vehicles[0]
        #    if self.frame_iterations % 100 == 0:
        #        print(vehicles)
        #        print ("Player : ",self.player.rect.center[0])
        #        print("Vehicle : " , vehicle.rect.center[0])


        #    if vehicle.rect.center[0] == 150:
        #        vehicle.lane = 150
        #    elif vehicle.rect.center[0] == 250:
        #        vehicle.lane = 250
        #    else:
        #        vehicle.lane = 350
        #else:
        #    Vehbool = False
        self.add_vehicle()
        vehicle = self.getSpriteByPosition(0, self.vehicle_group)
        vehicle.lane = vehicle.rect.center[0]
        if self.frame_iterations % 100 == 0:
            print ("Player : ", self.lane)
            print("Vehicle : " , vehicle.lane)
        #move
        reward = self._move(action, reward)
        
        #gameover
        gameover = self.is_collision()
        if gameover:
            reward = -100
            return reward, gameover, self.score
        
        reward = self.move_vehicle(reward)
        
        if self.lane == vehicle.lane:
            reward -= 10
        
        # 5. update ui and clock
        self.update_ui()
        self.clock.tick(SPEED)

        # 6. return game over and score
        return reward, gameover, self.score
        
    def move_vehicle(self,reward):
        for vehicle in self.vehicle_group:
            vehicle.rect.y += self.speed
            # remove vehicle once it goes off screen
            if vehicle.rect.bottom >= self.player.rect.bottom:
                vehicle.kill()
                self.score+=1
                reward += 10
                
                # speed up the game after passing 5 vehicles
                if self.score > 0 and self.score % 5 == 0:
                    self.speed += 0
        return reward


    def is_collision(self):
        # check if there's a head on collision
        gameover = False
        if pygame.sprite.spritecollide(self.player, self.vehicle_group, True):
            gameover = True
            self.crash_rect.center = [self.player.rect.center[0], self.player.rect.top]
            print("Has collided")

        for vehicle in self.vehicle_group:
            if pygame.sprite.collide_rect(self.player, vehicle):
                gameover = True
                print("collided up front")
        
        return gameover

    def update_ui(self):
        # draw the grass
        self.screen.fill(green)
        
        # draw the road
        pygame.draw.rect(self.screen, gray, road)
        
        # draw the edge markers
        pygame.draw.rect(self.screen, yellow, left_edge_marker)
        pygame.draw.rect(self.screen, yellow, right_edge_marker)
        
        # draw the lane markers
        self.lane_marker_move_y += self.speed * 2
        if self.lane_marker_move_y >= marker_height * 2:
            self.lane_marker_move_y = 0
        for y in range(marker_height * -2, h, marker_height * 2):
            pygame.draw.rect(self.screen, white, (left_lane + 45, y + self.lane_marker_move_y, marker_width, marker_height))
            pygame.draw.rect(self.screen, white, (center_lane + 45, y + self.lane_marker_move_y, marker_width, marker_height))
            
        # draw the player's car
        self.player_group.draw(self.screen)

        # draw the vehicles
        self.vehicle_group.draw(self.screen)
        
        # display the score
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        text = font.render('Score: ' + str(int(self.score)), True, white)
        text_rect = text.get_rect()
        text_rect.center = (50, 400)
        self.screen.blit(text, text_rect)

        pygame.display.update()

game = Game()
game.reset()