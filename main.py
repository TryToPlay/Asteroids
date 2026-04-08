import helper
import pygame
import sys
import os

pygame.mixer.pre_init(channels=5)
pygame.mixer.init()
pygame.init()

WIDTH = 2097
HEIGHT = 1080
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()
WIDTH, HEIGHT = window.get_size()
FPS = 60
font = pygame.font.SysFont(None, 100)
showHitboxes = False
FILEPATHS = {
				"spaceImg": "assets" + os.sep + "space.jpg",
				"shipImg": "assets" + os.sep + "ship.png",
				"bulletImg": "assets" + os.sep + "bullet.png",
				"asteroidImg": "assets" + os.sep + "asteroid.png",
				"asteroidHitSfx": "assets" + os.sep + "asteroidhit.wav",
				"shootSfx": "assets" + os.sep + "shoot.wav",
				"asteroidExplodeSfx": "assets" + os.sep + "asteroidexplode.wav",
				"shipHitSfx": "assets" + os.sep + "shiphit.wav",
				"shipExplodeSfx": "assets" + os.sep + "shipexplode.wav",
				"music": "assets" + os.sep + "music.mp3"
			}
	
black = (0, 0, 0)
gray = (127, 127, 127)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

background = helper.Background(FILEPATHS["spaceImg"], WIDTH, HEIGHT)

pygame.mixer.music.load(FILEPATHS["music"])
pygame.mixer.music.play(loops=-1)

ship = helper.Ship(FILEPATHS["shipImg"],
					FILEPATHS["shipHitSfx"], FILEPATHS["shipExplodeSfx"],
					helper.Vector(WIDTH // 2, HEIGHT // 2),
					bulletCooldown=0.75, fps=FPS)
shipRotSprites = helper.createRotSprites(ship)					

bulletDamage = 1
bulletSpeed = 20
bullet = helper.Bullet(FILEPATHS["bulletImg"], FILEPATHS["shootSfx"],
						damage=bulletDamage, MaxSpeed=bulletSpeed)
bulletRotSprites = helper.createRotSprites(bullet)

joystick = helper.Joystick(200, 50,
							gray, white,
							WIDTH // 2 - 10, HEIGHT,
							WIDTH // 4, HEIGHT // 2)

button = helper.Button(100, white,
						WIDTH // 2 - 10, HEIGHT,
						WIDTH - WIDTH // 4, HEIGHT // 2)

player = helper.Player(ship, joystick, button,
						shipRotSprites, bulletRotSprites)

asteroidSpeed = 1.5
asteroidHealth = 5
asteroidScore = 100
asteroid = helper.Asteroid(FILEPATHS["asteroidImg"],
							FILEPATHS["asteroidHitSfx"], FILEPATHS["asteroidExplodeSfx"],
							MaxSpeed=asteroidSpeed, health=asteroidHealth, score=asteroidScore)
asteroidRotSprites = helper.createRotSprites(asteroid)
asteroids = []
asteroidTimer = helper.Timer(5, FPS)

difficultyScore = 10
difficultyTimer = helper.Timer(10, FPS)
difficultyTimer.activate()
asteroidCooldownDecrease = 0.90
asteroidSpeedIncrease = 1.10
asteroidScoreIncrease = 1.25
asteroidHealthIncrease = 1.50
bulletCooldownDecrease = 0.90
bulletDamageIncrease = 1.50
bulletSpeedIncrease = 1.05
shipSpeedIncrease = 1.05
difficultyScoreIncrease = 1.25

shipHealthSprite = pygame.transform.scale(pygame.image.load(FILEPATHS["shipImg"]), (50, 50))

while True:
	# Window Control
	
	window.fill(black)
	background.display(window)

	if showHitboxes:
		for bullet in player.bullets:
			pygame.draw.rect(window, red, bullet.hitbox)
		for asteroid in asteroids:
			pygame.draw.rect(window, green, asteroid.hitbox)
		pygame.draw.rect(window, blue, player.ship.hitbox)

	player.display(window, FPS)

	for asteroid in asteroids:
		asteroid.display(window)
	
	score = round(player.score / 10) * 10
	window.blit(font.render(str(score), True, white), (10, 10))
	window.blit(font.render(str(player.ship.health - 1), True, white), (WIDTH - 110, 10))
	window.blit(shipHealthSprite, (WIDTH - 60, 15))

	# Events Handling

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

		if event.type == pygame.FINGERDOWN:
			x = event.x * WIDTH
			y = event.y * HEIGHT
			player.fingerDown(event.finger_id, (x, y))

		if event.type == pygame.FINGERMOTION:
			x = event.x * WIDTH
			y = event.y * HEIGHT
			player.fingerMotion(event.finger_id, (x, y))

		if event.type == pygame.FINGERUP:
			player.fingerUp(event.finger_id)
		
	# Logic Handling
	
	# Background
	background.updatePos(player.ship.speed)
	background.fixPos()

	# Player
	player.update(window, background)

	if player.button.pressed and not player.ship.bulletTimer.active:
		player.shoot(FILEPATHS["bulletImg"], FILEPATHS["shootSfx"],
						damage=bulletDamage, speed=bulletSpeed)

	# Asteroid Spawning
	asteroidTimer.update()
	if not asteroidTimer.active:
		asteroid = helper.spawnAsteroid(FILEPATHS["asteroidImg"], FILEPATHS["asteroidHitSfx"], FILEPATHS["asteroidExplodeSfx"],
										WIDTH, HEIGHT, player, asteroidRotSprites, asteroidSpeed, asteroidHealth, asteroidScore)
		asteroids.append(asteroid)
		asteroidTimer.activate()

	# Asteroid Out Of Bound
	asteroidsToRemove = []
	for asteroid in asteroids:
		if not background.isInsideRenderArea(asteroid.rect):
			asteroidsToRemove.append(asteroid)
		else:	
			asteroid.updatePos(player.ship.speed)
			asteroid.updateRot(asteroidRotSprites)

	# Asteroid-Bullet+Ship Collision
	asteroidsToRemove.extend(player.asteroidInteractions(asteroids))

	# Asteroid Removal
	for asteroid in asteroidsToRemove:
		try:
			asteroids.remove(asteroid)
		except Exception as e:
			pass
	
	# Difficulty Increase
	difficultyTimer.update()
	if not difficultyTimer.active:
		asteroidTimer.cooldown *= asteroidCooldownDecrease
		asteroidSpeed *= asteroidSpeedIncrease
		asteroidScore *= asteroidScoreIncrease
		asteroidHealth *= asteroidHealthIncrease
		player.ship.bulletTimer.cooldown *= bulletCooldownDecrease
		bulletDamage *= bulletDamageIncrease
		bulletSpeed *= bulletSpeedIncrease
		player.ship.MAXSPEED *= shipSpeedIncrease
		player.score += difficultyScore
		difficultyScore *= difficultyScoreIncrease
		difficultyTimer.activate()
		

	pygame.display.update()
	clock.tick(FPS)