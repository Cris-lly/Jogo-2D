import pygame
import sys
import math
import random

# =========================
# CONFIGURAÇÕES
# =========================
WIDTH, HEIGHT = 640, 480
VIEWPORT = pygame.Rect(40, 40, 560, 400)
FPS = 60

pygame.init()

fonte_titulo = pygame.font.SysFont("arial", 42, bold=True)
fonte_instrucao = pygame.font.SysFont("arial", 24)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nave vs Asteroides - CG")
clock = pygame.time.Clock()

# =========================
# MÚSICA E SONS
# =========================

pygame.mixer.music.load("Sounds/The_Astronaut.mp3")   # música de fundo
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)             # loop infinito


# =========================
# Textos
# =========================
def draw_text(text, font, color, x, y, center=True):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)

# =========================
# CORES
# =========================
BLACK = (0,0,0)
WHITE = (255,255,255)
RED   = (255,0,0)
GRAY  = (160,160,160)
BLUE  = (80,160,255)
YELLOW = (255,255,0)

# =========================
# SET PIXEL
# =========================
def set_pixel(x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        screen.set_at((x, y), color)

# =========================
# LINHA - BRESENHAM
# =========================
def draw_line(x0, y0, x1, y1, color):
    dx = abs(x1-x0)
    dy = abs(y1-y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        set_pixel(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

# =========================
# CÍRCULO
# =========================
def draw_circle(cx, cy, r, color):
    x, y = 0, r
    d = 1 - r
    while x <= y:
        for dx, dy in [(x,y),(y,x),(-x,y),(-y,x),
                       (x,-y),(y,-x),(-x,-y),(-y,-x)]:
            set_pixel(cx+dx, cy+dy, color)
        if d < 0:
            d += 2*x + 3
        else:
            d += 2*(x-y) + 5
            y -= 1
        x += 1
# =========================
#ELIPSE
def draw_ellipse(cx, cy, rx, ry, color):
    x, y = 0, ry
    d1 = (ry**2) - (rx**2 * ry) + (0.25 * rx**2)
    dx = 2 * ry**2 * x
    dy = 2 * rx**2 * y

    # Região 1
    while dx < dy:
        for dx_sym, dy_sym in [(x, y), (-x, y), (x, -y), (-x, -y)]:
            set_pixel(cx + dx_sym, cy + dy_sym, color)
        if d1 < 0:
            x += 1
            dx += 2 * ry**2
            d1 += dx + ry**2
        else:
            x += 1
            y -= 1
            dx += 2 * ry**2
            dy -= 2 * rx**2
            d1 += dx - dy + ry**2

    # Região 2
    d2 = ((ry**2) * ((x + 0.5)**2)) + ((rx**2) * ((y - 1)**2)) - (rx**2 * ry**2)
    while y >= 0:
        for dx_sym, dy_sym in [(x, y), (-x, y), (x, -y), (-x, -y)]:
            set_pixel(cx + dx_sym, cy + dy_sym, color)
        if d2 > 0:
            y -= 1
            dy -= 2 * rx**2
            d2 += rx**2 - dy
        else:
            y -= 1
            x += 1
            dx += 2 * ry**2
            dy -= 2 * rx**2
            d2 += dx - dy + rx**2
# =========================
# =========================
# FLOOD FILL
# =========================
def flood_fill(x, y, target, replacement):
    if target == replacement:
        return
    stack = [(x,y)]
    while stack:
        px, py = stack.pop()
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            if screen.get_at((px,py))[:3] == target:
                set_pixel(px,py,replacement)
                stack.extend([
                    (px+1,py),(px-1,py),
                    (px,py+1),(px,py-1)
                ])

# ============================
# BOUNDARY FILL
# ============================
def boundary_fill(x, y, fill_color, boundary_color):
    # Usamos uma pilha (stack) para evitar erro de recursão do Python
    stack = [(x, y)]
    
    while stack:
        px, py = stack.pop()
        
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            current_color = screen.get_at((px, py))[:3]
            
            # Se a cor atual não é a fronteira E ainda não é a cor de preenchimento
            if current_color != boundary_color and current_color != fill_color:
                set_pixel(px, py, fill_color)
                
                # Adiciona vizinhos (4-conectado)
                stack.append((px + 1, py))
                stack.append((px - 1, py))
                stack.append((px, py + 1))
                stack.append((px, py - 1))


# ============================
# SCANLINE
# ============================
def scanline_fill(points, fill_color):
    if len(points) < 3: return

    # 1. Encontrar limites verticais
    ys = [p[1] for p in points]
    min_y, max_y = int(min(ys)), int(max(ys))

    # 2. Iterar por cada linha horizontal
    for y in range(min_y, max_y + 1):
        intersections = []
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            
            # Verifica se a scanline intercepta a aresta
            if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):
                # Cálculo de X da interseção (Interpolação)
                x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                intersections.append(int(x))
        
        # 3. ORDENAR as interseções 
        intersections.sort()
        
        # 4. Preencher entre os pares (A-B, C-D...)
        for i in range(0, len(intersections), 2):
            if i + 1 < len(intersections):
                x_start = intersections[i]
                x_end = intersections[i+1]
                
                # LAÇO DE TEXTURA: Em vez de draw_line, pintamos pixel a pixel
                for x in range(x_start, x_end + 1):

                    if (x // 1 + y // 1) % 2 == 0:
                        set_pixel(x, y, (0, 0, 255))    
                    else:
                        set_pixel(x, y, (0, 0, 180))
# =============================
#INTRO
# ==============================
def intro_logo():
    # Carrega e toca a música da INTRO
    pygame.mixer.music.load("Sounds/capcom.mp3") 
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1) 

    start = pygame.time.get_ticks()

    while True:
        clock.tick(60)
        screen.fill(BLACK)
        draw_logo()
        pygame.display.flip()

        # Verifica se o tempo acabou (6 segundos)
        if pygame.time.get_ticks() - start > 6000:
            # ANTES DE SAIR: Carrega a música principal do JOGO
            pygame.mixer.music.load("Sounds/The_Astronaut.mp3")
            pygame.mixer.music.play(-1)
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
def draw_logo():
    cx, cy = WIDTH // 2, HEIGHT // 2
    rx = 180 
    ry = 100
    
    # 1. Desenha apenas o contorno do círculo (NÃO use flood_fill no círculo)
    draw_ellipse(cx, cy, rx, ry, WHITE)
    tempo_atual = pygame.time.get_ticks()
    
    # A nave aparece após 1 segundo
    if tempo_atual > 1000:
        # Pequena flutuação
        offset_y = int(math.sin(tempo_atual * 0.005) * 7)
        desenhar_nave_detalhada(cx, cy + offset_y)

def desenhar_nave_detalhada(cx, cy):
    # Cores para facilitar
    # Se o flood_fill estiver dando erro, desenhe apenas as linhas primeiro
    
    # --- CORPO CENTRAL (Trapézio/Triângulo) ---
    draw_line(cx, cy - 50, cx + 20, cy + 30, WHITE)   # Lado direito
    draw_line(cx, cy - 50, cx - 20, cy + 30, WHITE)   # Lado esquerdo
    draw_line(cx - 20, cy + 30, cx + 20, cy + 30, WHITE) # Base do corpo

    # --- ASAS ---
    # Asa Esquerda
    draw_line(cx - 20, cy, cx - 50, cy + 40, WHITE)
    draw_line(cx - 50, cy + 40, cx - 20, cy + 30, WHITE)
    
    # Asa Direita
    draw_line(cx + 20, cy, cx + 50, cy + 40, WHITE)
    draw_line(cx + 50, cy + 40, cx + 20, cy + 30, WHITE)

    # --- COCKPIT (Cabine central) ---
    draw_line(cx - 8, cy - 10, cx + 8, cy - 10, WHITE)
    draw_line(cx - 8, cy + 10, cx + 8, cy + 10, WHITE)
    draw_line(cx - 8, cy - 10, cx - 8, cy + 10, WHITE)
    draw_line(cx + 8, cy - 10, cx + 8, cy + 10, WHITE)

    # --- FOGO DO MOTOR (Vermelho/Amarelo) ---
    if (pygame.time.get_ticks() // 200) % 2 == 0:
        draw_line(cx - 10, cy + 30, cx, cy + 60, RED)
        draw_line(cx + 10, cy + 30, cx, cy + 60, RED)

    # --- PREENCHIMENTO OPCIONAL ---
    # Só use se o desenho estiver 100% fechado. 
    # Tente comentar essas linhas se o círculo continuar ficando todo branco.
    # flood_fill(cx, cy + 20, BLACK, GRAY)    # Interior da nave
    # flood_fill(cx, cy, BLACK, BLUE)         # Interior da cabine
# =========================
# ROTAÇÃO (TRANSFORMAÇÃO GEOMÉTRICA)
# =========================
def rotate(p, angle):
    rad = math.radians(angle)
    x = p[0]*math.cos(rad) - p[1]*math.sin(rad)
    y = p[0]*math.sin(rad) + p[1]*math.cos(rad)
    return (int(x), int(y))

def scrolling_story():
    story = [
    "Há muito tempo,",
    "em uma galáxia muito,",
    "muito distante...",
    "",
    "A Rebelião enfrenta",
    "uma nova ameaça",
    "vinda do espaço profundo.",
    "",
    "Asteroides gigantes",
    "avançam rumo às",
    "rotas da Aliança.",
    "",
    "O Capitão Solo,",
    "aos controles da nave,",
    "é a última esperança",
    "para impedir a destruição.",
    "",
    "Que a Força esteja",
    "com você, Capitão."
]


    y = HEIGHT + 20  # começa fora da tela
    speed = 1        # velocidade da subida

    while True:
        clock.tick(60)
        screen.fill(BLACK)

        for i, line in enumerate(story):
            text_surface = fonte_instrucao.render(line, True, YELLOW)
            text_rect = text_surface.get_rect(center=(WIDTH//2, y + i * 35))
            screen.blit(text_surface, text_rect)

        y -= speed  # translação vertical

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return  # pula a história
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()

        # termina quando o texto sai completamente da tela
        if y + len(story) * 35 < 0:
            return

# =========================
# NAVE
# =========================
ship_pos = [VIEWPORT.centerx, VIEWPORT.bottom - 40]
ship_angle = 0
ship_model = [(-10,10),(0,-15),(10,10)]

def draw_ship():
    points = []
    for p in ship_model:
        # Rotaciona e move para a posição da nave
        rp = rotate(p, ship_angle)
        points.append((ship_pos[0] + rp[0], ship_pos[1] + rp[1]))

    # O scanline agora verá 4 interseções em algumas linhas y e 2 em outras
    # Isso fará o desenho "aberto" em cima
    scanline_fill(points, BLUE)

    # Contorno branco para destacar
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        draw_line(p1[0], p1[1], p2[0], p2[1], WHITE)
# =========================
# TIROS
# =========================
shots = []

def shoot():
    shots.append({"x":ship_pos[0], "y":ship_pos[1]-15})

def draw_shots():
    for s in shots:
        draw_line(s["x"], s["y"], s["x"], s["y"]-8, YELLOW)

# =========================
# ASTEROIDES
# =========================
asteroids = []

def spawn_asteroid():
    return {
        "x": random.randint(VIEWPORT.left+20, VIEWPORT.right-20),
        "y": VIEWPORT.top,
        "r": 15
    }

def draw_asteroid(a):
    draw_circle(a["x"], a["y"], a["r"], WHITE)
    flood_fill(a["x"], a["y"], BLACK, GRAY)

# =========================
# COLISÕES
# =========================
def hit_asteroid(s, a):
    return math.hypot(s["x"]-a["x"], s["y"]-a["y"]) < a["r"]

def hit_ship(a):
    return math.hypot(a["x"]-ship_pos[0], a["y"]-ship_pos[1]) < a["r"] + 12

# =========================
# FIM DE JOGO
# =========================
def game_over():
    screen.fill(BLACK)
    pygame.mixer.music.stop()
    draw_text("FIM DE JOGO", fonte_titulo, RED, WIDTH//2, HEIGHT//2)

    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

# =========================
# Menu - instruções
# =========================
def instructions():
    scrolling_story()
    while True:
        screen.fill(BLACK)
        # TÍTULO
        draw_text("INSTRUÇÕES", fonte_titulo, WHITE, WIDTH//2, 80)

        # TEXTO DAS INSTRUÇÕES
        draw_text("Mover a nave:", fonte_instrucao, WHITE, WIDTH//2, 150)
        draw_text("←  Setinha esquerda", fonte_instrucao, WHITE, WIDTH//2, 180)
        draw_text("→  Setinha direita", fonte_instrucao, WHITE, WIDTH//2, 210)

        draw_text("Atirar:", fonte_instrucao, WHITE, WIDTH//2, 260)
        draw_text("Barra de espaço", fonte_instrucao, WHITE, WIDTH//2, 290)

        draw_text("Pressione ENTER para continuar", fonte_instrucao, YELLOW, WIDTH//2, 360)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()


# =========================
# MENU
# =========================
def menu():
    while True:
        # ===== TÍTULO =====
        
        screen.fill(BLACK)
        draw_text("Galactic Impact", fonte_titulo, WHITE, WIDTH//2, 100)
        draw_text("Aperte qualquer tecla para iniciar", fonte_instrucao, WHITE, 320, 200)
        draw_ship()
    
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.flip()


intro_logo()
instructions()
menu()

# =========================
# LOOP PRINCIPAL
# =========================
spawn_timer = 0

while True:
    clock.tick(FPS)
    spawn_timer += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                shoot()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        ship_pos[0] -= 4
    if keys[pygame.K_RIGHT]:
        ship_pos[0] += 4

    ship_pos[0] = max(VIEWPORT.left+20, min(ship_pos[0], VIEWPORT.right-20))

    # Asteroides
    if spawn_timer > 40:
        asteroids.append(spawn_asteroid())
        spawn_timer = 0

    for a in asteroids:
        a["y"] += 3
        if hit_ship(a):
            game_over()

    # Tiros
    for s in shots:
        s["y"] -= 8

    # Colisão tiro-asteroide
    for s in shots[:]:
        for a in asteroids[:]:
            if hit_asteroid(s, a):
                shots.remove(s)
                asteroids.remove(a)
                break

    shots = [s for s in shots if s["y"] > VIEWPORT.top]
    asteroids = [a for a in asteroids if a["y"] < VIEWPORT.bottom]

    # RENDER
    screen.fill(BLACK)

    # Viewport
    for x in range(VIEWPORT.left, VIEWPORT.right):
        set_pixel(x, VIEWPORT.top, WHITE)
        set_pixel(x, VIEWPORT.bottom, WHITE)
    for y in range(VIEWPORT.top, VIEWPORT.bottom):
        set_pixel(VIEWPORT.left, y, WHITE)
        set_pixel(VIEWPORT.right, y, WHITE)

    draw_ship()
    draw_shots()

    for a in asteroids:
        draw_asteroid(a)

    pygame.display.flip()

