# import libraries and modules
import pygame
import neat
import time
import os
import random # to be used to randomly set the height of the pipes
pygame.font.init()

# set the dimensions for the window
# we use capital letters for constant variables as a standard convention
WIN_WIDTH = 550
WIN_HEIGHT = 800

# initializing the generation count 
GEN = 0

# load all images
# pygame.transform.scale2x(): scales the image to be twice of its original size
# pygame.image.load(): loads the image
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), 
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), 
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 40) # defining the font style and size for the score


# BIRD CLASS - represents the bird objects moving in the game window
class Bird:
    # class variables (going to be constant)
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25 # represents the degree by which the bird will rotate when going up or down
    ROT_VEL = 20 # represents how much we are going to rotate on each frame every time we move the bird
    ANIMATION_TIME = 5 # represents how long we are going to show each bird animation which creates a flapping effect

    def __init__(self, x, y): # here, x and y represent the starting position of our bird
        self.x = x
        self.y = y
        self.tilt = 0 # represents how much the bird is actually tilted at the start position
        self.tick_count = 0 # will be used to figure out the physics of our bird when it jumps or falls
        self.vel = 0 # set as 0 since the bird would be at rest in the starting position
        self.height = self.y       
        self.img_count = 0 # represents the image of the bird currently in use, so that we can animate it and keep a track of it
        self.img = self.IMGS[0] # represents the first image from the list of bird images
    
    def jump(self): # will be called when we want the bird to move up
        self.vel = -10.5 
        '''
        In pygame, the topmost corner on the left of our game window is the origin (ie. (0,0)).
        Therefore, if we want to move in 
            upward direction, we would require -ve values
            downward direction, we would require +ve values
            forward direction (right), we would require +ve values
            backward direction (left), we would require -ve values
        '''
        self.tick_count = 0 # keeps the count of when we last jumped
        ''' 
        The reason why we are resetting the tick_count to 0 is because we need to know when we are changing directions or velocities
        for our physics formulas (to be used later) to work.
        '''
        self.height = self.y # keeps track of where the bird jumped from or started moving from
    
    def move(self): # will be used to call every single frame to move our bird
        self.tick_count += 1 # keeps track of number of times we have jumped since the last jump

        # define displacement (based on our bird's velocity, how many pixels we are moving up or down this frame)
        # this will be what we end up moving when we change the y-position of the bird
        d =  self.vel*self.tick_count + 1.5*self.tick_count**2
        
        # setting terimal velocity to avoid having velocity way too up or down
        if d >= 16: # for bottom 
            d = 16
        if d < 0: # for top (tells us that if we are moving up, lets just move a little bit more)
            d -= 2
        
        # change y-position based on this displacement
        self.y = self.y + d 

        # tilting our bird
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win): # win represents the window we are drawing our game into
        self.img_count += 1
        '''
        to animate our bird, we need to keep track of how many ticks we have shown at current image for
        by ticks we mean how many times our game loop ran and how many times we have shown one image
        ''' 

        # checking which image we should show based on current img_count
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # in case of the bird falling down, we do not want the bird to flap
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2 # this will set the img_count to our 2nd case above when we jump upwards

        # rotate image about its center
        rotated_img = pygame.transform.rotate(self.img, self.tilt) # image, angle
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_img, new_rect .topleft)
    
    def get_mask(self): # used for collision with objects
        return pygame.mask.from_surface(self.img) # creates mask for the bird (2D list of pixels)
    
# Pipe Class - represents the operations associated to the pipes
class Pipe:
    GAP = 200
    VEL = 1

    def __init__(self, x): # not considering 'y' because the position of the pipe in y-axis will be completely random
        self.x = x
        self.height = 0

        self.top = 0 # keeps track of where the top pipe will be drawn
        self.bottom = 0 # keeps track of where the bottom pipe will be drawn
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False # indicates whether the bird has crossed the pipe or not (mainly for the purpose of detecting collision and AI)
        self.set_height() # defines where the top and bottom pipes are and how tall they are (defined randomly)
    
    def set_height(self):
        self.height = random.randrange(50, 450) # where the top pipe should appear
        self.top = self.height - self.PIPE_TOP.get_height() 
        '''
        To position the top pipe,
        Height (we want the top pipe should appear - Total height of the Pipe Image)
        '''
        self.bottom = self.height + self.GAP # for the bottom pipe
     
    def move(self): # defines movement of the pipes by changing its x-position based on the velocity that the pipe should move each frame
        self.x -= self.VEL # moves the pipe a little bit to the left, based on the velocity
    
    def draw(self, win): # draws the pipes on the game window
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    '''
    MASKING IN PYGAME:
    - it looks at the image and locates where the pixels actually are
    - since these images have a transparent background, it is able to check if the pixel is transparent or not
    - it then creates a 2D list which contains as many rows as there are pixels going down and as many columns as there are pixels 
      going across.
    
    We will have the 2D lists defined for both our BIRD and our PIPES.
    To check if there has been any collision between the two, we will compares these lists together and we will see if there is any
    pixels in each list that maps with each other (ie. sit in kind of the same area)
    In this way, we can determine if we had PICTURE-PERFECT COLLISION or not.
    '''
    def collide(self, bird): # used for the detection of PICTURE-PERFECT COLLISION
        bird_mask = bird.get_mask() # mask for the bird
        top_mask = pygame.mask.from_surface(self.PIPE_TOP) # mask for the top pipe
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM) # mask for the bottom pipe

        # offset: calculates how far these masks are from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y)) # offset for bird and top pipe
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y)) # offset for bird and bottom pipe

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) # for bottom pipe
        t_point = bird_mask.overlap(top_mask, top_offset) # for top pipe
        '''
        bird_mask.overlap(bottom_mask, bottom_offset): tells us the first point of collision between the bird mask and the bottom pipe, 
        using bottom offset (ie. how far the bird is from the bottom pipe) 
        in case the two does not collide, it returns 'None'.
        '''
        # checking if b_point and t_point actually exist (if they are not colliding, both the points will be 'None')
        if t_point or b_point: # means they are not 'None'
            return True
        
        return False

# Base class: represent the operations associated to the base
class Base:
    VEL = 1 # velocity of both the pipe and the base should be same, otherwise they will appear to move at different speeds
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y): # not considering 'x' as the base will be moving to the left, thus 'x' need not to be defined
        self.y = y
        self.x1 = 0 # for the first base image
        self.x2 = self.WIDTH # for the second base image

    def move(self):
        self.x1 -= self.VEL # moving the first base image
        self.x2 -= self.VEL # moving the second base image

        if self.x1 + self.WIDTH < 0: # checks if the first base image is completely out of the game window
            self.x1 = self.x2 + self.WIDTH # if true, we cycle it back
        
        if self.x2 + self.WIDTH < 0: # checks if the second base image is completely out of the game window
            self.x2 = self.x1 + self.WIDTH # if true, we cycle it back
    
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y)) # draws the first base image
        win.blit(self.IMG, (self.x2, self.y)) # draws the second base image

def draw_window(win, birds, pipes, base, score, gen): # used to draw background image and then the bird on top of it just to see how the bird works when it is moving
    win.blit(BG_IMG, (0,0)) # blit() simply means draw. it simply draws whatever is passed in it on the game window
    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score : " + str(score), 1,(255,255,255)) # for the score text
    win.blit(text, (WIN_WIDTH-10-text.get_width(), 10)) # creates a score text on the game window

    text = STAT_FONT.render("Gen : " + str(gen), 1,(255,255,255)) # for the Generation text
    win.blit(text, (10, 10)) # creates a Generation text on the game window

    base.draw(win)

    for bird in birds:
        bird.draw(win) # calls user-defined function draw() which will handle all the animation, tilting for us and also draws the bird

    pygame.display.update() # simply updates the display and refreshes it

'''
We are using NEAT neural network as an AI that plays on game.
INPUTS: position of bird along y-axis (not x as the bird will not be moving along x-axis),
        distance between bird and top pipe
        distance between bird and bottom pipe
OUTPUTS: whether bird should jump or not?
ACTIVATION FUNCTION: TanH (activation function for the output layer. Here we are going to let NEAT algorithm decide the
                     activation function for the hidden layers.)
POPULATION SIZE: 100 (although we can have an arbitrary value here)
in case of flappy bird,
- we start by taking 100 birds (lets say, GEN0). we then select best performing birds and breed them to get 100 birds.
- these 100 birds (lets say, GEN1) will perform better than previous generation. we then select the best performing birds and 
  the process is repeated for certain number of iterations.
FITNESS FUNCTION: (defines how we are actually going to grow and how these birds are going to get better)
                  Distance that our birds traveled along x-direction
MAX GENERATIONS: 30 (indicates that if even after 30 generations, the AI does not perform well, we will terminate it and start over.)
'''

# modifying the main() to work properly for more than 1 bird as it will take all our genomes and evaluate them (ie. check their fitness)
def main(genomes, config): # it is a must to Genomes and Config as parameters, whenever we define the fitness function for NEAT
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []
    '''
    We use above lists to:
    - keep a track of neural network that controls each bird because they genomes, when they come are just a bunch of neural
      networks that are going to control each of our birds.
    - keep track of the genomes so that we can change their fitness based on how far they move or if they hit a pipe etc.
    - keep track of the bird that that neural network is controlling, so where that position is in the screen.

    The reason we are using 3 lists is so that each position in this list will correspond to the same bird, ie.
    Index 0 -> will have the neural network for Bird0, the genome for Bird0 and the actual bird object (that we have created for Bird0 to
               keep a track of where it is).
    '''

    for _, g in genomes:
        '''
        We are going to setup a neural network for that genome and a bird object for it and then just keep track of that genome
        in a list.
        '''
        # set up the neural network for our genome
        net = neat.nn.FeedForwardNetwork.create(g, config)

        # append it to the list
        nets.append(net)

        # append a bird object to the list which will be with the above neural network
        birds.append(Bird(230, 350)) # create a standard Bird object that is going to start at the same position 
                                     # of all of our other bird objects.

        g.fitness = 0
        # append the actual genome to the list in the same object as the bird object and the neural network 
        # (to keep a track of its fitness and change it as we desire)
        ge.append(g)



    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock() # clock object
    run = True
    score = 0

    # setup the main game loop for our pygame window
    while run:
        for event in pygame.event.get(): 
            clock.tick(30) # atmost 30 ticks every second
            '''
            this loop keeps track of whenever something happens like whenever user clicks the mouse 
            it will run this loop and loop through all the events and then do something with that
            '''
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        '''
        We have to move the birds based on their neural network.
        The inputs given to the neural network are:
        - distance between the bird and the top pipe.
        - distance between the bird and the bottom pipe.
        - y-position of the bird.

        As there will be 2 pipes (at max), we need to look out for which pipe we are feeding to the neural network.
        '''
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else: # if there are no birds left -> quit the game
            run = False 
            break

        # move the bird (jumping) 
        # we will check the output of the neural network associated to the bird and if it is greater than 0.5, we will make the bird jump.
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1 # set the fitness of the bird
            # we are giving it a little bit of fitness for surviving this long
            # this way we are encouraging the bird to keep moving forward and stay on the screen, rather than fly off the screen

            # activate neural network with our inputs (tuple of inputs)
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # check if the ouput is greater than 0.5. If yes, make the bird JUMP
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds): # this way we can get the position in the list of where this bird is
                if pipe.collide(bird):
                    ge[x].fitness -= 1 
                    '''
                    everytime bird hits a pipe, it is going to have 1 removed from its fitness score, 
                    so that we do not favor birds that make it far but just ram themselves into the pipe all the time.
                    we want to make sure that if a bird hits a pipe and another bird (which is at the same level, but did not 
                    hit the pipe), then the bird that did not hit should have a higher fitness score, that we encourage it to go
                    in between pipes.
                    '''
                    # remove the bird, the neural network associated with it and genome from the lists 
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                if not pipe.passed and pipe.x < bird.x: # checks if we have passed the pipes or not
                    pipe.passed = True
                    add_pipe = True # as soon as we pass the pipe, generate a new one

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: # remove the pipe that is not in window
                rem.append(pipe)
                
        
            pipe.move()

        if add_pipe:
            score +=1 # update the score every time the bird passes the pipes
            
            '''
            - increase the fitness of the bird by a fair amount.
            - in this case, if they actually get through the pipe, we will assign an extra 5 fitness score to them.
            - the reason we are doing this is to encourage the bird to go through the pipes, rather than just making it
              further in the level, but ramming themselves into the pipe.
            '''
            for g in ge:
                g.fitness += 5
            '''
            - the reason we can do this, without having to loop through the bird is because if we have to remove a bird,
              we are removing its genome as well from that list.
            - so any genome that is actually in this list is still alive and if it made it through the pipe, then it will gain
              5 to its fitness score.  
            '''
            pipes.append(Pipe(700)) # add new pipes after the bird has passed the previous ones
            
        for r in rem: # remove the pipes that were out of the window
            pipes.remove(r)

        for x, bird in enumerate(birds):
            # checks if any of our birds hits the ground or if the bird has flown off the screen -> make them die
            if bird.y + bird.img.get_height() > 730 or bird.y < 0: 
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)

def run(config_path):
    # load the configuration file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, 
                                config_path) # defines all the sub-headings used in the config file
    
    # set the population
    p = neat.Population(config) # generates population based on the info in the config file
    
    # adding stats reporters / set up the output that we are going to see
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    '''
    Whenever we are running the algorithm, rather than not seeing anything happen in the console, we will see
    detailed statistics of each generation (like best fitness etc.)
    '''

    # set the fitness function that we are going to run for 50 generations
    winner = p.run(main, 50) # calls main() 50 times and passes it the genomes (ie. current generation population and config file every time)
    # it then later generates the game based on all the birds/genomes we are given.
    '''
    The way that we determine our bird's fitness is by how far it moves in the game.
    So it actually only makes sense that this main() is going to be the fitness function for our NEAT Algorithm.
    A fitness function simply sets the fitness of our bird.
    '''

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__) # provides the path to the directory we are currently inside of
    config_path = os.path.join(local_dir, "config-feedforward.txt") # absolute path to our config file
    run(config_path)