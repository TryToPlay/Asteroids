import helper
import pygame
import asyncio
import sys

async def main():

	pygame.mixer.pre_init(channels=5)
	pygame.mixer.init()
	pygame.init()

	WIDTH = 2097
	HEIGHT = 1080
	window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
	WIDTH, HEIGHT = window.get_size()
	FPS = 60
	shipSize = 50
	bulletSize = 12
	asteroidSize = 100
	fontSize = 50
	font = pygame.font.SysFont(None, fontSize)
	showHitboxes = False
	FILEPATHS = {
					"spaceImg": "space.jpg",
					"shipImg": "ship.png",
					"bulletImg": "bullet.png",
					"asteroidImg": "asteroid.png",
					"asteroidHitSfx": "asteroidhit.wav",
					"shootSfx": "shoot.wav",
					"asteroidExplodeSfx": "asteroidexplode.wav",
					"shipHitSfx": "shiphit.wav",
					"shipExplodeSfx": "shipexplode.wav",
					"music": "music.mp3"
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
						bulletCooldown=0.75, fps=FPS,
						sizeX=shipSize, sizeY=shipSize)
	shipRotSprites = helper.createRotSprites(ship)					

	bulletDamage = 1
	bulletSpeed = 20
	bullet = helper.Bullet(FILEPATHS["bulletImg"], FILEPATHS["shootSfx"],
							damage=bulletDamage, MaxSpeed=bulletSpeed,
							sizeX=bulletSize, sizeY=bulletSize)
	bulletRotSprites = helper.createRotSprites(bullet)

	joystick = helper.Joystick(100, 25,
							gray, white,
							WIDTH // 2 - 10, HEIGHT,
							WIDTH // 4, HEIGHT // 2)

	button = helper.Button(50, white,
							WIDTH // 2 - 10, HEIGHT,
							WIDTH - WIDTH // 4, HEIGHT // 2)



	player = helper.Player(ship, joystick, button,
							shipRotSprites, bulletRotSprites)

	asteroidSpeed = 1.5
	asteroidHealth = 5
	asteroidScore = 100
	asteroid = helper.Asteroid(FILEPATHS["asteroidImg"],
								FILEPATHS["asteroidHitSfx"], FILEPATHS["asteroidExplodeSfx"],
								MaxSpeed=asteroidSpeed, health=asteroidHealth, score=asteroidScore,
								sizeX=asteroidSize, sizeY=asteroidSize)
	asteroidRotSprites = helper.createRotSprites(asteroid)
	asteroids = []
	asteroidTimer = helper.Timer(5, FPS)

	difficultyScore = 10
	difficultyTimer = helper.Timer(2, FPS)
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

	shipHealthSprite = pygame.transform.scale(pygame.image.load(FILEPATHS["shipImg"]), (fontSize // 2, fontSize // 2))

	while True:
		# Window Control
		
		window.fill(black)
		background.display(window)

		if showHitboxes:
			pygame.draw.rect(window, blue, player.joystick.boundRect)
			pygame.draw.rect(window, red, player.button.boundRect)
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
		window.blit(font.render(str(player.ship.health - 1), True, white), (WIDTH - 2 * fontSize - 10, 10))
		window.blit(shipHealthSprite, (WIDTH - fontSize - 10, 15))

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
											WIDTH, HEIGHT, player, asteroidRotSprites, asteroidSpeed, asteroidHealth, asteroidScore,
											sizeX=asteroidSize, sizeY=asteroidSize)
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
		await asyncio.sleep(1 / FPS)

try:
	asyncio.get_running_loop()
	asyncio.create_task(main())
except RuntimeError:
	asyncio.run(main())