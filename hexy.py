import sys
import random
import pygame as pg
import opensimplex as simp


BACKGROUND = pg.Color("darkslategray")
SCREEN_SIZE = (1200, 500)
FPS = 60


TERRAIN = [("water", 0.2), ("beach", 0.3), ("desert", 0.4), ("jungle", 0.5),
           ("savannah", 0.65), ("forest", 0.8), ("snow", 1)]


TERRAIN_COLORS = {"water" : pg.Color("lightblue3"),
                  "beach" : pg.Color("tan"),
                  "forest" : pg.Color("forestgreen"),
                  "jungle" : pg.Color("darkgreen"),
                  "savannah" : pg.Color("sienna"),
                  "desert" : pg.Color("gold"),
                  "snow" : pg.Color("white")}


TERRAIN_HEIGHTS = {tuple(TERRAIN_COLORS["water"]) : 5,
                   tuple(TERRAIN_COLORS["beach"]): 15,
                   tuple(TERRAIN_COLORS["forest"]): 20,
                   tuple(TERRAIN_COLORS["jungle"]): 30,
                   tuple(TERRAIN_COLORS["savannah"]): 40,
                   tuple(TERRAIN_COLORS["desert"]): 25,
                   tuple(TERRAIN_COLORS["snow"]): 50}


class MapGen(object):
    MAP_SIZE = 15, 20
    TILE_SIZE = 1,1
    WIDTH = MAP_SIZE[0]//TILE_SIZE[0]
    HEIGHT = MAP_SIZE[1]//TILE_SIZE[1]
    
    def __init__(self):
        self.seed = random.randrange(2**32)
        freq = random.randrange(5, 10)
        noise = self.gen_noise(simp.OpenSimplex(self.seed), freq)
        self.terrain = self.gen_map(noise) 

    def noise(self, gen, nx, ny, freq=10):
        # Rescale from -1.0:+1.0 to 0.0:1.0
        return gen.noise2d(freq*nx, freq*ny) / 2.0 + 0.5

    def gen_noise(self, gen, freq=10):
        vals = {}
        for y in range(self.WIDTH):
            for x in range(self.HEIGHT):
                nx = float(x)/self.WIDTH - 0.5
                ny = float(y)/self.HEIGHT - 0.5
                vals[x,y] = self.noise(gen, nx, ny, freq)
        return vals


    def gen_map(self, noise):
        mapping = pg.Surface(self.MAP_SIZE).convert()
        for x,y in noise:
            pos = self.TILE_SIZE[0]*x, self.TILE_SIZE[1]*y
            for biome, tolerance in TERRAIN:
                if noise[x,y] < tolerance:
                    mapping.fill(TERRAIN_COLORS[biome], (pos, self.TILE_SIZE))
                    break
        return mapping


class HexTile(pg.sprite.Sprite):
    def __init__(self, pos, color, height, *groups):
        super(HexTile, self).__init__(*groups)
        self.image = self.make_tile(color, height)
        self.rect = self.image.get_rect(bottomleft=pos)
        self.layer = 0

    def make_tile(self, color, h):
        points = (8,4), (45,0), (64,10), (57,27), (20,31), (0,22)
        bottom = [points[-1], points[2]] + [(x, y+h) for x,y in points[2:]]
        image = pg.Surface((65,32+h)).convert_alpha()
        image.fill((0,0,0,0))
        bottom_col = [.5*col for col in color[:3]]
        pg.draw.polygon(image, bottom_col, bottom)
        pg.draw.polygon(image, color, points)
        pg.draw.lines(image, pg.Color(" black"), 1, points, 2)
        for start, end in zip(points[2:],bottom[2:]):
            pg.draw.line(image, pg.Color("black"), start, end, 1)
        pg.draw.lines(image, pg.Color(" black"), 0, bottom[2:], 2)
        return image

    def draw(self, surface):
        surface.blit(self.image, self.rect)
         
    
class App(object):
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()
        self.done = False
        self.tiles = self.make_map()

    def make_map(self):
        tiles = pg.sprite.LayeredUpdates()
        self.mapping = MapGen()
        width, height = self.mapping.MAP_SIZE
        start_x, start_y = self.screen_rect.midtop
        start_x -= 100
        start_y += 100
        row_offset = -45, 22
        col_offset = 57, 5
        for i in range(width):
            for j in range(height):
                color = self.mapping.terrain.get_at((i,j))
                if color == (0,0,0):
                    break
                pos = (start_x + row_offset[0]*i + col_offset[0]*j,
                       start_y + row_offset[1]*i + col_offset[1]*j)
                h = TERRAIN_HEIGHTS[tuple(color)]
                HexTile(pos, color, h, tiles)
        return tiles
        
    def update(self):
        """
        All updates to all actors occur here.
        Exceptions include things that are direct results of events which
        may occasionally occur in the event loop.

        For example, updates based on held keys should be found here, but
        updates to single KEYDOWN events would be found in the event loop.
        """
        for sprite in self.tiles:
            if sprite.layer != sprite.rect.bottom:
                self.tiles.change_layer(sprite, sprite.rect.bottom)

    def render(self):
        """
        All calls to drawing functions here.
        No game logic.
        """
        self.screen.fill(BACKGROUND)
        self.tiles.draw(self.screen)
        pg.display.update()

    def event_loop(self):
        """
        Event handling here.  Only things that are explicit results of the
        given events should be found here.  Do not confuse the event and update
        phases.
        """
        for event in pg.event.get():
           if event.type == pg.QUIT:
               self.done = True

    def main_loop(self):
        """
        Main loop for your whole app.  This doesn't need to be touched until
        you start writing framerate independant games.
        """
        while not self.done:
            self.event_loop()
            self.update()
            self.render()
            self.clock.tick(FPS)


def main():
    """
    Prepare pygame and the display and create an App instance.
    Call the app instance's main_loop function to begin the App.
    """
    pg.init()
    pg.display.set_mode(SCREEN_SIZE)
    App().main_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
