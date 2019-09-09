import pygame

import random
import sys
from math import sqrt

import pygame
from pygame.locals import Rect, DOUBLEBUF, QUIT, K_ESCAPE, KEYDOWN, K_DOWN, \
    K_LEFT, K_UP, K_RIGHT, KEYUP, K_LCTRL, K_RETURN, FULLSCREEN

# import Bonuses, Bullets, Enemies, Ship

X_MAX = 800
Y_MAX = 600

LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3
START, STOP = 0, 1

everything = pygame.sprite.Group()

status = 0
game_over = False
stars = 0

enemies = 0
weapon_fire = 0
screen = 0
empty = 0
transition_timer = 0
level_up = False
stage = 1
ship = 0
enemies_alive = 10

bullet = 0
bonus_on_time = 300
bonus_off_time = 400
bonus_timer = bonus_off_time
bonus = 0


def start_game():
    global status
    global game_over
    global stars
    global enemies
    global weapon_fire
    global screen
    global empty
    global transition_timer
    global level_up
    global stage
    global ship
    global enemies_alive
    global bonus_timer
    global bonus

    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    pygame.display.set_caption('Space Invaders')
    screen = pygame.display.set_mode((X_MAX, Y_MAX), DOUBLEBUF)
    empty = pygame.Surface((X_MAX, Y_MAX))
    clock = pygame.time.Clock()
    enemies = pygame.sprite.Group()
    weapon_fire = pygame.sprite.Group()
    bonuses = pygame.sprite.Group()

    ship = ShipSprite(everything, weapon_fire)
    ship.add(everything)

    status = StatusSprite(ship, everything)

    deadtimer = 50

    bonus_object = 0

    # Get some music
    if pygame.mixer.get_init():
        pygame.mixer.music.load("Assets/Sound/DST-AngryMod.mp3")
        pygame.mixer.music.set_volume(0.8)

    start_stage()

    while True:
        clock.tick(60)

        bonus_timer -= 1
        # place drop if needed
        if bonus_timer == bonus_on_time:
            bonus_object = place_bonus(random.randint(1, 3))
        elif bonus_timer <= 0:
            bonus_object.kill()
            bonus_timer = bonus_off_time
            bonus = 0

        # Check for input
        for event in pygame.event.get():
            handle_event(event, game_over, ship, enemies)

        # Check for impact
        if bonus != 3:
            hit_ships = pygame.sprite.spritecollide(ship, enemies, True, pygame.sprite.collide_mask)
            for i in hit_ships:
                ship.health -= 10

        # Check if got bonus
        if bonus_object and pygame.sprite.collide_mask(ship, bonus_object):
            bonus = bonus_object.bonus_type
            bonus_object.kill()
            if bonus == 1:
                ship.health = 100

        # Check for successful attacks
        hit_ships = pygame.sprite.groupcollide(enemies, weapon_fire, False, True)
        for k, v in hit_ships.items():
            k.hurt()
            if bonus == 2:
                k.hurt()
            # for i in v:
            #     # i.hurt()

        # makes sure enemies are alive
        if len(enemies) < enemies_alive and not game_over and not transition_timer:
            pos = random.randint(0, X_MAX)
            EnemySprite(pos, [everything, enemies], stage)

        # Check for level up
        if ship.score > 500:
            if stage >= 5:
                ship.score = 0
                ship.health = 0
            ship.score = 0
            stage += 1
            level_up = True
            transition_animation()

        if transition_timer:
            transition_timer -= 1
            for star in stars:
                star.accelerate()
        elif level_up:
            level_up = False
            start_stage()

        # Checks if dead
        if ship.health <= 0:
            freeze_all()
            ship.explode()
            if deadtimer:
                deadtimer -= 1
                for star in stars:
                    star.accelerate()
            else:
                game_over = True

        # Game over
        if game_over:
            break

        # update frame
        update_frame()
    sys.exit()


def place_bonus(bonus):
    pos = random.randint(0, X_MAX)
    return Bonus(pos, [everything], bonus)


class Bonus(pygame.sprite.Sprite):
    def __init__(self, x_pos, groups, bonus_type):
        super(Bonus, self).__init__()
        self.image = pygame.image.load("Assets/Drops/" + str(bonus_type) + ".png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x_pos, 0)
        self.bonus_type = bonus_type
        self.velocity = random.randint(3, 6)

        self.add(groups)
        self.sound = pygame.mixer.Sound("Assets/Sound/enemy_explosion.wav")
        self.sound.set_volume(0.4)

    def update(self):
        x, y = self.rect.center

        if y > Y_MAX:
            x, y = random.randint(0, X_MAX), 0
            self.velocity = random.randint(3, 6)
        else:
            x, y = x, y + self.velocity

        self.rect.center = x, y

    def freeze(self):
        self.velocity = 0

    def kill(self):
        x, y = self.rect.center
        if pygame.mixer.get_init():
            self.sound.play(maxtime=1000)
        super(Bonus, self).kill()


def freeze_all():
    ship.freeze()
    for star in stars:
        star.freeze()
    for enemy in enemies:
        enemy.freeze()


def update_frame():
    everything.clear(screen, empty)
    everything.update()
    everything.draw(screen)
    pygame.display.flip()


def start_stage():
    global ship
    global stage
    global stars
    global enemies
    global weapon_fire
    global enemies_alive

    enemies_alive += 1

    # reset ship position
    ship.reset()

    # remove old stars
    if stars:
        for star in stars:
            everything.remove(star)

    # place new stars
    stars = create_starfield(everything)

    # init enemies
    for i in range(10):
        pos = random.randint(0, X_MAX)
        EnemySprite(pos, [everything, enemies], stage)

    pygame.mixer.music.play(loops=-1)


def distance(pos1, pos2):
    return sqrt(pow(pos1[0] - pos2[0], 2) + pow(pos1[1] - pos2[1], 2))


def transition_animation():
    global transition_timer
    global enemies
    global ship
    transition_timer = int(abs(ship.rect.center[0] - X_MAX / 2) / 2 + 50)
    pygame.mixer.music.fadeout(8000)
    for enemy in enemies:
        enemy.kill()

    ship.autopilot = True
    ship.shoot(STOP)


def handle_event(event, game_over, ship, enemies):
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        sys.exit()
    if not game_over:
        if event.type == KEYDOWN:
            if event.key == K_DOWN:
                ship.steer(DOWN, START)
            if event.key == K_LEFT:
                ship.steer(LEFT, START)
            if event.key == K_RIGHT:
                ship.steer(RIGHT, START)
            if event.key == K_UP:
                ship.steer(UP, START)
            if event.key == pygame.K_SPACE:
                ship.shoot(START)
            if event.key == K_RETURN:
                if ship.mega:
                    ship.mega -= 1
                    for i in enemies:
                        i.kill()

        if event.type == KEYUP:
            if event.key == K_DOWN:
                ship.steer(DOWN, STOP)
            if event.key == K_LEFT:
                ship.steer(LEFT, STOP)
            if event.key == K_RIGHT:
                ship.steer(RIGHT, STOP)
            if event.key == K_UP:
                ship.steer(UP, STOP)
            if event.key == pygame.K_SPACE:
                ship.shoot(STOP)


def create_starfield(group):
    stars = []
    for i in range(200):
        x, y = random.randrange(X_MAX), random.randrange(Y_MAX)
        s = Star(x, y)
        s.add(group)
        stars.append(s)
    return stars


class BulletSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(BulletSprite, self).__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        for i in range(5, 0, -1):
            color = 255.0 * float(i) / 5
            if bonus == 2:
                pygame.draw.circle(self.image, (color, 0, 0), (5 * 3, 5 * 3), i * 3, 0)
            else:
                pygame.draw.circle(self.image, (0, 0, color), (5, 5), i, 0)

        self.rect = self.image.get_rect()
        self.rect.center = (x + 10, y - 25)
        self.velocity = 10

    def update(self):
        x, y = self.rect.center
        y -= self.velocity
        self.rect.center = x, y
        if y <= 0:
            self.kill()

    def freeze(self):
        self.velocity = 0


class EnemySprite(pygame.sprite.Sprite):
    def __init__(self, x_pos, groups, health):
        super(EnemySprite, self).__init__()
        self.image = pygame.image.load("Assets/Enemy/enemy" + str(stage) + ".png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x_pos, 0)

        self.velocity = random.randint(1, 5)

        self.add(groups)
        self.explosion_sound = pygame.mixer.Sound("Assets/Sound/enemy_explosion.wav")
        self.explosion_sound.set_volume(0.4)
        self.health = health

    def update(self):
        x, y = self.rect.center

        if y > Y_MAX:
            x, y = random.randint(0, X_MAX), 0
            self.velocity = random.randint(3, 10)
        else:
            x, y = x, y + self.velocity

        self.rect.center = x, y

    def freeze(self):
        self.velocity = 0

    def hurt(self):
        global ship
        self.health -= 1
        # if bonus == 2:
        #     self.health -= 1
        if self.health <= 0:
            self.kill()
            ship.score += 10
        else:
            self.image = pygame.image.load("Assets/Enemy/enemy" + str(self.health) + ".png").convert_alpha()

    def kill(self):
        x, y = self.rect.center
        if pygame.mixer.get_init():
            self.explosion_sound.play(maxtime=1000)
            Explosion(x, y)
        super(EnemySprite, self).kill()


class ShipSprite(pygame.sprite.Sprite):
    def __init__(self, groups, weapon_groups):
        super(ShipSprite, self).__init__()
        self.image = pygame.image.load("Assets\Ship\ship1.png")
        self.rect = self.image.get_rect()
        self.rect.center = (X_MAX / 2, Y_MAX - 40)
        self.dx = self.dy = 0
        self.firing = self.shot = False
        self.health = 100
        self.score = 0

        self.groups = [groups, weapon_groups]

        self.mega = 1

        self.autopilot = False
        self.in_position = False
        self.velocity = 2
        self.exploded = False
        self.explosion_sound = pygame.mixer.Sound("Assets/Sound/ship_explosion.wav")
        self.explosion_sound.set_volume(1)

    def update(self):
        x, y = self.rect.center

        if not self.autopilot:
            # Handle movement
            self.rect.center = x + self.dx, y + self.dy

            # Handle firing
            if self.firing:
                global bullet
                bullet += 1
                fire_rate = 5
                if bonus == 2:
                    fire_rate = 7
                if bullet % (10 - fire_rate) == 0:
                    self.shot = BulletSprite(x, y)
                    self.shot.add(self.groups)
                    bullet = 0

            if self.health < 0:
                self.kill()
        else:
            if not self.in_position:

                if x != X_MAX / 2:
                    x += (abs(X_MAX / 2 - x) / (X_MAX / 2 - x)) * 2
                if y != Y_MAX - 100:
                    y += (abs(Y_MAX - 100 - y) / (Y_MAX - 100 - y)) * 2

                if (x == X_MAX / 2 or x - 1 == X_MAX / 2) and (y == Y_MAX - 100 or y + 1 == Y_MAX - 100):
                    self.in_position = True

            else:
                y -= self.velocity
                self.velocity *= 1.5
                if y <= 0:
                    y = -30
            self.rect.center = x, y

    def steer(self, direction, operation):
        v = 5
        if operation == START:
            if direction in (UP, DOWN):
                self.dy = {UP: -v,
                           DOWN: v}[direction]

            if direction in (LEFT, RIGHT):
                self.dx = {LEFT: -v,
                           RIGHT: v}[direction]

        if operation == STOP:
            if direction in (UP, DOWN):
                self.dy = 0
            if direction in (LEFT, RIGHT):
                self.dx = 0

    def shoot(self, operation):
        if operation == START:
            self.firing = True
        else:
            self.firing = False

    def freeze(self):
        self.velocity = 0

    def reset(self):
        self.image = pygame.image.load("Assets\Ship\ship" + str(stage) + ".png")
        self.rect.center = (X_MAX / 2, Y_MAX - 40)
        self.autopilot = False
        self.in_position = False
        self.velocity = 2

    def explode(self):
        if not self.exploded:
            self.exploded = True
            x, y = self.rect.center
            if pygame.mixer.get_init():
                self.explosion_sound.play(maxtime=1000)
                Explosion(x, y)
            super(ShipSprite, self).kill()


class StatusSprite(pygame.sprite.Sprite):
    def __init__(self, ship, groups):
        super(StatusSprite, self).__init__()
        self.image = pygame.Surface((X_MAX, 30))
        self.rect = self.image.get_rect()
        self.rect.bottomleft = 0, Y_MAX

        default_font = pygame.font.get_default_font()
        self.font = pygame.font.Font(default_font, 20)

        self.ship = ship
        self.add(groups)

    def update(self):
        score = self.font.render(
            "Health : {}   Score : {}    Stage : {}".format(self.ship.health, self.ship.score, stage), True,
            (150, 50, 50))
        self.image.fill((0, 0, 0))
        self.image.blit(score, (0, 0))


class Star(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Star, self).__init__()
        self.image = pygame.Surface((2, 2))
        pygame.draw.circle(self.image,
                           (128, 128, 200),
                           (0, 0),
                           2,
                           0)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.velocity = random.randint(1, 3)
        self.size = 1
        self.colour = 128

    def accelerate(self):
        self.image = pygame.Surface((1, self.size))

        if self.size < 200:
            self.size += 4
            self.colour += 20
            if self.colour >= 200:
                self.colour = random.randint(180, 200)
        else:
            self.colour -= 30
            if self.colour <= 20:
                self.colour = random.randrange(20)

        pygame.draw.line(self.image, (self.colour, self.colour, self.colour),
                         (0, 0), (0, self.size))

        if self.velocity < Y_MAX / 3:
            self.velocity += 1

        # x, y = self.rect.center
        # self.rect.center = random.randrange(X_MAX), y

    def update(self):
        x, y = self.rect.center
        if self.rect.center[1] > Y_MAX:
            self.rect.center = (x, 0)
        else:
            self.rect.center = (x, y + self.velocity)

    def freeze(self):
        self.velocity = 0


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Explosion, self).__init__()
        sheet = pygame.image.load("Assets/Explosion/x.png")
        self.images = []
        for i in range(0, 768, 48):
            rect = pygame.Rect((i, 0, 48, 48))
            image = pygame.Surface(rect.size, pygame.SRCALPHA)
            image.blit(sheet, (0, 0), rect)
            self.images.append(image)

        self.image = self.images[0]
        self.mask = pygame.mask.from_surface(self.image)
        self.index = 0
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.add(everything)

    def update(self):
        self.image = self.images[self.index]
        self.mask = pygame.mask.from_surface(self.image)
        self.index += 1
        if self.index >= len(self.images):
            self.kill()


if __name__ == '__main__':
    start_game()
