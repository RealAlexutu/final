import pygame
import sys
import random
from button import Button
pygame.init()
pygame.mixer.init()
damage_sound = pygame.mixer.Sound("assets/damage_sound.wav")
damage_sound.set_volume(0.5)

game_music = "assets/game_music.mp3"


def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)



WIDTH, HEIGHT = 1920, 1080
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))


pygame.display.set_caption("Cyber Runner")
clock = pygame.time.Clock()
pause_menu_img = pygame.image.load("assets/pause_menu.png").convert_alpha()




class ParallaxBackground:
    def __init__(self, image_paths):
        self.images = [pygame.transform.scale(pygame.image.load(
            path).convert(), (WIDTH * 2, HEIGHT)) for path in image_paths]
        self.index = 0
        self.next_index = 0
        self.scroll_x = 0
        self.scroll_speed = 1
        self.alpha = 255
        self.fading = False
        self.fade_speed = 5
        self.current_img = self.images[self.index].copy()
        self.next_img = self.images[self.index].copy()

    def update(self):
        self.scroll_x -= self.scroll_speed
        if self.scroll_x <= -WIDTH:
            self.scroll_x = 0

        if self.fading:
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                self.alpha = 255
                self.fading = False
                self.index = self.next_index
                self.current_img = self.images[self.index].copy()

    def draw(self, surface):
        bg_img = self.current_img.copy()
        bg_img.set_alpha(255)
        surface.blit(bg_img, (self.scroll_x, 0))
        surface.blit(bg_img, (self.scroll_x + WIDTH * 2, 0))

        if self.fading:
            next_img = self.images[self.next_index].copy()
            next_img.set_alpha(255 - self.alpha)
            surface.blit(next_img, (self.scroll_x, 0))
            surface.blit(next_img, (self.scroll_x + WIDTH * 2, 0))

    def set_background(self, index):
        if 0 <= index < len(self.images) and index != self.index:
            self.next_index = index
            self.fading = True
            self.alpha = 255

    def set_scroll_speed(self, speed):
        self.scroll_speed = speed


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.animations = {
            "idle": [pygame.image.load("assets/p2_walk.png")],
            "run": [pygame.image.load("assets/p2_walk.png")],
            "jump": [pygame.image.load("assets/p2_jump.png")],
            "fly": [pygame.image.load("assets/p2_jump.png")],
        }
        self.state = "idle"
        self.anim_index = 0
        self.image = self.animations[self.state][0]
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT // 2)
        self.velocity_y = 0
        self.gravity = 0.8
        self.jump_strength = -20
        self.grounded = False
        self.double_jump = False
        self.used_double_jump = False
        self.jetpack_enabled = False
        self.jetpack_timer = 0
        self.is_flying = False
        raw_jetpack = pygame.image.load(
            "assets/jetpack_200x200_transparent.png").convert_alpha()
        self.jetpack_img = pygame.transform.scale(raw_jetpack, (150, 150))
        raw_flame = pygame.image.load("assets/flame.png").convert_alpha()
        self.flame_img = pygame.transform.scale(raw_flame, (80, 80))
        self.health = 3
        self.max_health = 3

    def activate_jetpack(self, duration=300):
        self.jetpack_enabled = True
        self.jetpack_timer = duration

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_j] and not self.jetpack_enabled:
            self.activate_jetpack()
        if self.jetpack_enabled and keys[pygame.K_SPACE]:
            self.velocity_y = -5
            self.is_flying = True
        else:
            self.is_flying = False
        if not self.jetpack_enabled and keys[pygame.K_SPACE]:
            if self.grounded:
                self.velocity_y = self.jump_strength
                self.grounded = False
                self.used_double_jump = False
            elif self.double_jump and not self.used_double_jump:
                self.velocity_y = self.jump_strength
                self.used_double_jump = True
        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y
        if self.rect.bottom >= HEIGHT - 20:
            self.rect.bottom = HEIGHT - 20
            self.velocity_y = 1
            self.grounded = True
            self.used_double_jump = False
        if self.rect.top <= 0:
            self.rect.top = 0
            self.velocity_y = 0
        if self.jetpack_enabled:
            self.jetpack_timer -= 1
            if self.jetpack_timer <= 0:
                self.jetpack_enabled = False
        if self.jetpack_enabled and self.is_flying:
            self.state = "fly"
        elif not self.grounded:
            self.state = "jump"
        else:
            self.state = "run" if keys[pygame.K_RIGHT] else "idle"
        self.animate()

    def animate(self):
        frames = self.animations[self.state]
        self.anim_index += 0.1
        if self.anim_index >= len(frames):
            self.anim_index = 0
        self.image = frames[int(self.anim_index)]

    def draw(self, surface):
        jetpack_x = self.rect.left - 30
        jetpack_y = self.rect.top + 15
        surface.blit(self.jetpack_img, (jetpack_x, jetpack_y))
        if self.jetpack_enabled and self.is_flying:
            flame_x = self.rect.left + 7
            flame_y = self.rect.bottom - 70
            surface.blit(self.flame_img, (flame_x, flame_y))
        surface.blit(self.image, self.rect)


class ToxicBarrel(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.image.load(
            "assets/toxic_barrel.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (64, 64))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = HEIGHT - self.rect.height + 10

    def update(self, speed):
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()


class CeilingLaser(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.image.load(
            "assets/laser_vertical.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (32, 200))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y -= 60

    def update(self, speed):
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()


class FloorLaser(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.image.load(
            "assets/laser_vertical.png").convert_alpha()
        self.image = pygame.transform.flip(self.image, False, True)
        self.image = pygame.transform.scale(self.image, (32, 200))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = HEIGHT + 38

    def update(self, speed):
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()

def pause_menu():
    

    pygame.mixer.music.pause()
    paused = True
     

    pause_menu_img = pygame.image.load("assets/pause_menu.png").convert_alpha()
    pause_menu_img = pygame.transform.scale(pause_menu_img, (800, 600))  # dimensiune finală

    # Poziționează imaginea pe centru
    pause_menu_rect = pause_menu_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    while paused:
        screen.blit(pause_menu_img, pause_menu_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                paused = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Coordonate empirice în funcție de imagine – ajustează dacă nu e perfect:
                resume_area = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 30, 300, 70)
                quit_area = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 120, 300, 70)

                if resume_area.collidepoint(mouse_pos):
                    paused = False
                elif quit_area.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()

    pygame.mixer.music.unpause()




def main_menu():
    # Pornește muzica de meniu
    pygame.mixer.music.load("assets/menu_music.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    # Sunet de hover
    hover_sound = pygame.mixer.Sound("assets/hover_sound.wav")
    hover_sound.set_volume(0.5)
    hovered_button = None

    # Fundal imagine
    background_img = pygame.image.load("assets/background.png").convert()
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

    # Butoane
    play_button = Button(
        image=pygame.image.load("assets/Play Rect.png"),
        pos=(WIDTH // 2, 300),
        text_input="PLAY",
        font=get_font(50),
        base_color=WHITE,
        hovering_color=RED
    )
    quit_button = Button(
        image=pygame.image.load("assets/Quit Rect.png"),
        pos=(WIDTH // 2, 400),
        text_input="QUIT",
        font=get_font(50),
        base_color=WHITE,
        hovering_color=RED
    )

    while True:
        screen.blit(background_img, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        # Titlu
        title_text = get_font(100).render("JURASSIC JUMPERS", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_text, title_rect)

        # Actualizare butoane
        for button in [play_button, quit_button]:
            button.changeColor(mouse_pos)
            button.update(screen)

            if button.rect.collidepoint(mouse_pos):
                if hovered_button != button:
                    hover_sound.play()
                    hovered_button = button
            else:
                if hovered_button == button:
                    hovered_button = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.checkForInput(mouse_pos):
                    pygame.mixer.music.stop()
                    return  # Intră în joc
                if quit_button.checkForInput(mouse_pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()





def main():
    pygame.mixer.music.load("assets/game_music.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    player = Player()
    obstacle_group = pygame.sprite.Group()
    background = ParallaxBackground([
        "assets/bg0.png",  # City
        "assets/bg1.png",  # Dark Oak
        "assets/bg2.png",  # Dry
        "assets/bg3.png",   # Nuclear
        "assets/bg4.png",  # Moon
    ])

   

    obstacle_timer = 0
    score = 0
    game_speed = 5
    font = pygame.font.SysFont("Arial", 30)
    next_obstacle_type = "barrel"
    current_bg_index = -1

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
              running = False
          elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
              pause_menu()


        player.update()

        for obstacle in obstacle_group:
            obstacle.update(game_speed)

        obstacle_timer += 1
        if obstacle_timer > 120:
            x = WIDTH + random.randint(0, 200)
            if next_obstacle_type == "barrel":
                obstacle = ToxicBarrel(x)
                next_obstacle_type = "laser"
            else:
                obstacle = random.choice([CeilingLaser(x), FloorLaser(x)])
                next_obstacle_type = "barrel"
            obstacle_group.add(obstacle)
            obstacle_timer = 0

        score += 1

        # Dinamic speed increase
        if score % 500 == 0:
            game_speed += 0.5
        background.set_scroll_speed(game_speed * 0.2)

        # Background transition
        if score < 1000:
            bg_index = 0
        elif score < 2000:
            bg_index = 1
        elif score < 3000:
            bg_index = 2
        elif score < 4000:
            bg_index = 3
        else:
            bg_index = 4

        if bg_index != current_bg_index:
            background.set_background(bg_index)
            current_bg_index = bg_index

        background.update()

        if pygame.sprite.spritecollide(player, obstacle_group, False):
            damage_sound.play()
            player.health -= 1
            obstacle_group.empty()
            if player.health <= 0:
                running = False

        screen.fill(BLACK)
        background.draw(screen)
        player.draw(screen)
        obstacle_group.draw(screen)

        score_text = font.render(f"Score: {score}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(health_text, (10, 40))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main_menu()
    main()

