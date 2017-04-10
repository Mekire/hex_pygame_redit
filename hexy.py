import sys
import random
import pygame as pg
import opensimplex as simp


BACKGROUND = pg.Color("darkslategray")
TRANSPARENT = (0, 0, 0, 0)
SCREEN_SIZE = (1200, 525)
FPS = 60


TERRAIN = [("Water", 0.3), ("Beach", 0.35), ("Desert", 0.45), ("Jungle", 0.5),
           ("Forest", 0.65), ("Savannah", 0.8), ("Snow", 1)]


TERRAIN_COLORS = {"Water" : pg.Color("lightblue3"),
                  "Beach" : pg.Color("tan"),
                  "Forest" : pg.Color("Forestgreen"),
                  "Jungle" : pg.Color("darkgreen"),
                  "Savannah" : pg.Color("sienna"),
                  "Desert" : pg.Color("gold"),
                  "Snow" : pg.Color("white")}


TERRAIN_HEIGHTS = {"Water" : 5,
                   "Beach": 10,
                   "Forest": 20,
                   "Jungle": 30,
                   "Savannah": 40,
                   "Desert": 15,
                   "Snow": 50}


class MapGen(object):
    WIDTH, HEIGHT = 15, 20
    
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
        mapping = [["biome"]*self.HEIGHT for _ in range(self.WIDTH)]
        for x,y in noise:
            for biome, tolerance in TERRAIN:
                if noise[x,y] < tolerance:
                    mapping[y][x] = biome
                    break
        return mapping


class HexTile(pg.sprite.Sprite):
    FOOTPRINT_SIZE = (65, 32)
    
    def __init__(self, pos, biome, *groups):
        super(HexTile, self).__init__(*groups)
        self.color =  TERRAIN_COLORS[biome]
        self.height = TERRAIN_HEIGHTS[biome]
        self.image = self.make_tile(biome)
        self.rect = self.image.get_rect(bottomleft=pos)
        self.mask = self.make_mask()
        self.biome = biome
        self.layer = 0

    def make_tile(self, biome):
        h = self.height
        points = (8,4), (45,0), (64,10), (57,27), (20,31), (0,22)
        bottom = [points[-1], points[2]] + [(x, y+h) for x,y in points[2:]]
        image = pg.Surface((65,32+h)).convert_alpha()
        image.fill(TRANSPARENT)
        bottom_col = [.7*col for col in self.color[:3]]
        pg.draw.polygon(image, bottom_col, bottom)
        pg.draw.polygon(image, self.color, points)
        pg.draw.lines(image, pg.Color("black"), 1, points, 2)
        ##for start, end in zip(points[2:],bottom[2:]):
            ##pg.draw.line(image, pg.Color("black"), start, end, 1)
        pg.draw.lines(image, pg.Color("black"), 0, bottom[2:], 2)
        return image

    def make_mask(self):
        points = (8,4), (45,0), (64,10), (57,27), (20,31), (0,22)
        temp_image = pg.Surface(self.image.get_size()).convert_alpha()
        temp_image.fill(TRANSPARENT)
        pg.draw.polygon(temp_image, pg.Color("red"), points)
        return pg.mask.from_surface(temp_image)
        

class CursorHighlight(pg.sprite.Sprite):
    FOOTPRINT_SIZE = (65, 32)
    COLOR = (0, 0, 150, 100)
    
    def __init__(self, *groups):
        super(CursorHighlight, self).__init__(*groups) 
        points = (8,4), (45,0), (64,10), (57,27), (20,31), (0,22)
        self.image = pg.Surface(self.FOOTPRINT_SIZE).convert_alpha()
        self.image.fill(TRANSPARENT)
        pg.draw.polygon(self.image, self.COLOR, points)
        self.rect = pg.Rect((0,0,1,1))
        self.mask = pg.Mask((1,1))
        self.mask.fill()
        self.target = None
        self.do_draw = False
        self.biome = None
        self.label_image = None
        self.label_rect = None

    def update(self, pos, tiles):
        self.rect.topleft = pos
        hits = pg.sprite.spritecollide(self, tiles, 0, pg.sprite.collide_mask)
        if hits:
            true_hit = max(hits, key=lambda x: x.rect.bottomleft)
            self.target = true_hit.rect.topleft
            self.biome = true_hit.biome
            self.label_image = FONT.render(self.biome, 1, pg.Color("white"))
            self.label_rect = self.label_image.get_rect(midbottom=pos)
            self.do_draw = True
        else:
            self.biome = None
            self.do_draw = False

    def draw(self, surface):
        if self.do_draw:
            surface.blit(self.image, self.target)
            surface.blit(self.label_image, self.label_rect)
        

class App(object):
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()
        self.done = False
        self.tiles = self.make_map()
        self.cursor = CursorHighlight()

    def make_map(self):
        tiles = pg.sprite.LayeredUpdates()
        self.mapping = MapGen()
        width, height = self.mapping.WIDTH, self.mapping.HEIGHT
        start_x, start_y = self.screen_rect.midtop
        start_x -= 100
        start_y += 100
        row_offset = -45, 22
        col_offset = 57, 5
        for i in range(width):
            for j in range(height):
                biome = self.mapping.terrain[i][j]
                pos = (start_x + row_offset[0]*i + col_offset[0]*j,
                       start_y + row_offset[1]*i + col_offset[1]*j)
                HexTile(pos, biome, tiles)
        return tiles
        
    def update(self):
        for sprite in self.tiles:
            if sprite.layer != sprite.rect.bottom:
                self.tiles.change_layer(sprite, sprite.rect.bottom)
        self.cursor.update(pg.mouse.get_pos(), self.tiles)

    def render(self):
        self.screen.fill(BACKGROUND)
        self.tiles.draw(self.screen)
        self.cursor.draw(self.screen)
        pg.display.update()

    def event_loop(self):
        for event in pg.event.get():
           if event.type == pg.QUIT:
               self.done = True

    def main_loop(self):
        while not self.done:
            self.event_loop()
            self.update()
            self.render()
            self.clock.tick(FPS)


def main():
    global FONT
    pg.init()
    pg.display.set_mode(SCREEN_SIZE)
    FONT = pg.font.Font(None, 30)
    App().main_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
