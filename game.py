import pygame, sys
import ctypes
ctypes.windll.user32.SetProcessDPIAware()



GAME_SHAPE = (1600, 900)
TOP_LEFT_WINDOW_SHAPE = (310, 600)
BOTTOM_LEFT_WINDOW_SHAPE = (310, 300)
RIGHT_WINDOW_SHAPE = (1290, 900)
GRID_WIDTH = 30
GRID_HEIGHT = 30
IMAGE_DIRECTORY = "images/"



def load_image(name):
    image = pygame.image.load(IMAGE_DIRECTORY + name + ".png").convert()
    return image


class Display:
    #self, string, pixel count, pixel count
    def __init__(self):
        self.screen = pygame.display.set_mode()
        self.play_screen = pygame.Surface(GAME_SHAPE)
        
    def draw(self):
        x = (self.screen.get_width() - self.play_screen.get_width()) // 2
        y = (self.screen.get_height() - self.play_screen.get_height()) // 2
        self.screen.blit(self.play_screen, (x, y))
        pygame.display.flip()



if __name__=='__main__':
    pygame.init()
    display = Display()

    top_left_window = pygame.Surface(TOP_LEFT_WINDOW_SHAPE)
    top_left_window.fill((60, 30, 30))

    bottom_left_window = pygame.Surface(BOTTOM_LEFT_WINDOW_SHAPE)
    bottom_left_window.fill((30, 60, 30))

    right_window = pygame.Surface(RIGHT_WINDOW_SHAPE)
    right_window.fill((30, 30, 60))
    light_square = load_image("light_square")
    dark_square = load_image("dark_square")
    for x in range(43):
        for y in range(30):
            square = light_square if (x+y)%2==0 else dark_square
            right_window.blit(square, (x*GRID_WIDTH, y*GRID_HEIGHT))

    display.play_screen.blit(top_left_window, (0, 0))
    display.play_screen.blit(bottom_left_window, (0, TOP_LEFT_WINDOW_SHAPE[1]))
    display.play_screen.blit(right_window, (TOP_LEFT_WINDOW_SHAPE[0], 0))

    display.draw()

    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
