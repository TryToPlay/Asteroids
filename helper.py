import pygame
import random
import time
import math
import sys

class Vector:
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y
	
	def magnitude(self):
		return math.sqrt(self.x * self.x + self.y * self.y)
	
	def angle(self):
		return math.atan2(self.y, self.x)
	
	def add(self, vector):
		return Vector(self.x + vector.x, self.y + vector.y)
		
	def sub(self, vector):
		return Vector(self.x - vector.x, self.y - vector.y)
		
	def mul(self, scalar):
		return Vector(self.x * scalar, self.y * scalar)
		
	def dot(self, vector):
		return self.x * vector.x + self.y * vector.y
		
	def projection(self, vector):
		return vector.mul(self.dot(vector) / vector.magnitude() ** 2)
	
	def rot90(self):
		return Vector(self.y, -self.x)
	
	def unit(self):
		if self.magnitude() > 0:
			return self.mul(1 / self.magnitude())
		else:
			return self

class Joystick:
	def __init__(self, outRadius, inRadius, outColor, inColor, boundingRectWidth, boundingRectHeight, boundingRectX, boundingRectY):
		self.outerRadius = outRadius
		self.innerRadius = inRadius
		self.outerColor = outColor
		self.innerColor = inColor
		self.outerPosition = Vector(0, 0)
		self.innerPosition = Vector(0, 0)
		
		self.boundRect = pygame.Rect(0, 0, boundingRectWidth, boundingRectHeight)
		self.boundRect.center = (boundingRectX, boundingRectY)
		self.hidden = True
		self.finger = 0
	
	def display(self, window):
		if not self.hidden:
			pygame.draw.circle(window, self.outerColor, (self.outerPosition.x, self.outerPosition.y), self.outerRadius)
			pygame.draw.circle(window, self.innerColor, (self.innerPosition.x, self.innerPosition.y), self.innerRadius)
	
	def fingerDown(self, fingerID, fingerPos):
		if self.boundRect.collidepoint(fingerPos):
			self.outerPosition = Vector(fingerPos[0], fingerPos[1])
			self.innerPosition = Vector(fingerPos[0], fingerPos[1])
			self.hidden = False
			self.finger = fingerID
	
	def fingerMotion(self, fingerPos):
		if not self.hidden:
			self.innerPosition = Vector(fingerPos[0], fingerPos[1])
			vector = self.outerPosition.sub(self.innerPosition)
			
			if vector.magnitude() > self.outerRadius:
				vector = vector.unit().mul(self.outerRadius)
				self.innerPosition = self.outerPosition.sub(vector)
				
			vector = self.outerPosition.sub(self.innerPosition)
			return vector
		return Vector(0, 0)
	
	def fingerUp(self, fingerID):
		if fingerID == self.finger:
			self.hidden = True

class Button:
	def __init__(self, radius, color, boundingRectWidth, boundingRectHeight, boundingRectX, boundingRectY):
		self.radius = radius
		self.color = color
		self.position = Vector(0, 0)
		self.pressed = False
		
		self.boundRect = pygame.Rect(0, 0, boundingRectWidth, boundingRectHeight)
		self.boundRect.center = (boundingRectX, boundingRectY)
		self.hidden = True
		self.finger = 0
	
	def display(self, window):
		if not self.hidden:
			pygame.draw.circle(window, self.color, (self.position.x, self.position.y), self.radius)
	
	def fingerDown(self, fingerID, fingerPos):
		if self.boundRect.collidepoint(fingerPos):
			self.position = Vector(fingerPos[0], fingerPos[1])
			self.pressed = True
			self.hidden = False
			self.finger = fingerID
	
	def fingerUp(self, fingerID, fingerPos=(0, 0)):
		if fingerID == self.finger:
			self.pressed = False
			self.hidden = True

class Object:
	def __init__(self, sprite, hitboxScale=1.0, posVector=Vector(0, 0), MaxSpeed=1.0, sizeX=100, sizeY=100, channel_no=0, rotSpeed=1):
		self.sprite = pygame.transform.scale(pygame.image.load(sprite), (sizeX, sizeY))
		
		self.hitboxScale = hitboxScale
		self.rect = self.sprite.get_rect()
		self.hitbox = pygame.transform.scale(self.sprite, (sizeX * self.hitboxScale, sizeY * self.hitboxScale)).get_rect()
		
		self.position = posVector
		self.hitbox.centerx = self.position.x
		self.hitbox.centery = self.position.y
		self.rect.centerx = self.position.x
		self.rect.centery = self.position.y
		self.angle = 0
		self.rotSpeed = rotSpeed
		
		self.MAXSPEED = MaxSpeed
		self.speed = Vector(0, 0)
		self.channel = pygame.mixer.Channel(channel_no)
	
	def setRectAndHitbox(self):
		self.rect = self.sprite.get_rect()
		self.hitbox = pygame.transform.scale(self.sprite, (self.sprite.get_width() * self.hitboxScale, self.sprite.get_height() * self.hitboxScale)).get_rect()
		
	def setPos(self):
		self.hitbox.centerx = self.position.x
		self.hitbox.centery = self.position.y
		self.rect.centerx = self.position.x
		self.rect.centery = self.position.y
		
	def updatePos(self, extraSpeed=Vector(0, 0)):
		self.position = self.position.sub(self.speed.sub(extraSpeed))
		self.setPos()
	
	def setSpeedZero(self):
		self.speed.x = 0
		self.speed.y = 0
	
	def display(self, window):
		window.blit(self.sprite, self.rect)
	
	def rotate(self, angle, rotSprites):
		self.sprite = rotSprites[angle]
		self.angle = angle
		self.setRectAndHitbox()
		self.setPos()
	
	def updateRot(self, rotSprites):
		angle = int(self.angle + self.rotSpeed)
		if angle > 360:
			angle = angle - 360 + self.rotSpeed
		elif angle < -360:
			angle = angle + 360 - self.rotSpeed
		self.rotate(angle, rotSprites)
	
	def setPosRotVel(self, position, angle, rotSprites):
		self.position = position
		self.setPos()
		self.rotate(angle, rotSprites)
		self.speed = Vector(math.sin(math.radians(angle)) * self.MAXSPEED,
							math.cos(math.radians(angle)) * self.MAXSPEED)
	
def getAngle_fromVector(vector):
	angle = -round(math.degrees(vector.rot90().angle()))
	return angle

def createRotSprites(object):
	objectRotSprites = {}
	for theta in range(-360, 361):
		objectRotSprites[theta] = pygame.transform.rotate(object.sprite, theta)
	return objectRotSprites

class Timer:
	def __init__(self, cooldown, fps=60):
		self.cooldown = cooldown * fps
		self.active = False
		self.timer = 0
	
	def update(self):
		if self.active:
			if self.timer >= self.cooldown:
				self.timer = 0
				self.active = False
			else:
				self.timer += 1
	
	def activate(self):
		self.active = True
	
class Ship(Object):
	def __init__(self, sprite, hitSfx, explodeSfx, posVector=Vector(0, 0), MaxSpeed=0.025, sizeX=75, sizeY=75, channel_no=1, bulletCooldown=1.0, fps=60):
		super().__init__(sprite, 0.6, posVector, MaxSpeed, sizeX, sizeY, channel_no)
		
		self.health = 3
		invincibilityCooldown = 3
		self.invincibilityTimer = Timer(invincibilityCooldown, fps)
		self.bulletTimer = Timer(bulletCooldown, fps)
		self.spriteOn = True
		
		self.hitSound = pygame.mixer.Sound(hitSfx)
		self.explodeSound = pygame.mixer.Sound(explodeSfx)
	
	def invincibilityDisplay(self, window, fps):
		flickerRate = 0.5
		if (self.invincibilityTimer.timer % (flickerRate / 2 * fps)) == 0:
			self.spriteOn = False
		if (self.invincibilityTimer.timer % (flickerRate / 1 * fps)) == 0:
			self.spriteOn = True
		if self.spriteOn:
			self.display(window)

class Bullet(Object):
	def __init__(self, sprite, shootSfx, posVector=Vector(0, 0), MaxSpeed=20.0, damage=1, sizeX=25, sizeY=25, channel_no=2):
		super().__init__(sprite, 0.7, posVector, MaxSpeed, sizeX, sizeY, channel_no)
		
		self.damage = damage
		
		self.shootSound = pygame.mixer.Sound(shootSfx)
		self.shootSound.set_volume(0.3)
		
class Asteroid(Object):
	def __init__(self, sprite, hitSfx, explodeSfx, posVector=Vector(0, 0), MaxSpeed=1.5, health=5, score=100, sizeX=200, sizeY=200, channel_no=3):
		super().__init__(sprite, 0.6, posVector, MaxSpeed, sizeX, sizeY, channel_no)
		
		self.health = health
		self.score = score
		self.rotSpeed = 1 if random.random() >= 0.5 else -1
		
		self.hitSound = pygame.mixer.Sound(hitSfx)
		self.hitSound.set_volume(0.5)
		self.explodeSound = pygame.mixer.Sound(explodeSfx)

def spawnAsteroid(asteroidImg, asteroidHitSfx, asteroidExplodeSfx, width, height, player, asteroidRotSprites, asteroidSpeed, asteroidHealth, asteroidScore):
	asteroid = Asteroid(asteroidImg, asteroidHitSfx, asteroidExplodeSfx,
						MaxSpeed=asteroidSpeed, health=asteroidHealth, score=asteroidScore)
	position = randBoundaryPosition(width, height,
									asteroid.hitbox.width / 2,
									asteroid.hitbox.height / 2)
	vector = position.sub(player.ship.position)
	angle = getAngle_fromVector(vector)
	asteroid.setPosRotVel(position, angle, asteroidRotSprites)
	return asteroid

def randBoundaryPosition(width, height, offsetX, offsetY):
	val = random.randint(0, 3)
	if val == 0:
		return Vector(-offsetX, random.randint(0, height))
	elif val == 1:
		return Vector(width + offsetX, random.randint(0, height))
	elif val == 2:
		return Vector(random.randint(0, width), -offsetY)
	elif val == 3:
		return Vector(random.randint(0, width), height + offsetY)

class Player:
	def __init__(self, ship, joystick, button, shipRotSprites, bulletRotSprites):
		self.ship = ship
		self.joystick = joystick
		self.button = button
		self.shipRotSprites = shipRotSprites
		self.bullets = []
		self.bulletsToRemove = []
		self.bulletRotSprites = bulletRotSprites
		self.score = 0
	
	def display(self, window, fps):
		self.joystick.display(window)
		self.button.display(window)
		if self.ship.invincibilityTimer.active:
			self.ship.invincibilityDisplay(window, fps)
		else:
			self.ship.display(window)
		for bullet in self.bullets:
			bullet.display(window)
	
	def fingerDown(self, fingerID, fingerPos):
		self.joystick.fingerDown(fingerID, fingerPos)
		self.ship.setSpeedZero()
		self.button.fingerDown(fingerID, fingerPos)
	
	def fingerMotion(self, fingerID, fingerPos):
		if fingerID == self.joystick.finger:
			vector = self.joystick.fingerMotion(fingerPos)
			self.ship.speed = vector.mul(self.ship.MAXSPEED)
			angle = getAngle_fromVector(vector)
			self.ship.rotate(angle, self.shipRotSprites)
	
	def fingerUp(self, fingerID):
		self.joystick.fingerUp(fingerID)
		self.ship.setSpeedZero()
		self.button.fingerUp(fingerID)
	
	def shoot(self, bulletImg, shootSfx, damage, speed):
		bullet = Bullet(bulletImg, shootSfx, damage=damage, MaxSpeed=speed)
		bullet.setPosRotVel(self.ship.position, self.ship.angle, self.bulletRotSprites)
		self.bullets.append(bullet)
		self.ship.bulletTimer.activate()
		bullet.channel.play(bullet.shootSound)
	
	def update(self, window, background):
#		self.ship.updatePos()
		self.ship.bulletTimer.update()
		self.ship.invincibilityTimer.update()
		
		bulletsToRemove = []
		for bullet in self.bullets:
			if not background.isInsideRenderArea(bullet.rect):
				bulletsToRemove.append(bullet)
			else:	
				bullet.updatePos(self.ship.speed)
		
		for bullet in bulletsToRemove:
			try:
				self.bullets.remove(bullet)
			except Exception as e:
				pass
	
	def asteroidInteractions(self, asteroids):
		bulletsToRemove = []
		asteroidsToRemove = []
		
		for asteroid in asteroids:
			for bullet in self.bullets:
				if asteroid.hitbox.colliderect(bullet.hitbox) and asteroid.health > 0:
					asteroid.health -= bullet.damage
					bulletsToRemove.append(bullet)
					if asteroid.health <= 0:
						asteroidsToRemove.append(asteroid)
						self.score += asteroid.score
						asteroid.channel.play(asteroid.explodeSound)
					else:
						asteroid.channel.play(asteroid.hitSound)
			if not self.ship.invincibilityTimer.active and asteroid.hitbox.colliderect(self.ship.hitbox) and asteroid.health > 0:
				self.ship.health -= 1
				if self.ship.health > 0:
					self.ship.channel.play(self.ship.hitSound)
					self.ship.invincibilityTimer.activate()
				else:
					self.ship.channel.play(self.ship.explodeSound)
					pygame.mixer.music.stop()
					time.sleep(2)
					print("Score:", self.score)
					pygame.quit()
					sys.exit()
		
		for bullet in bulletsToRemove:
			try:
				self.bullets.remove(bullet)
			except Exception as e:
				pass
		return asteroidsToRemove

class Background:
	def __init__(self, sprite, width=2097, height=1080):
		self.sprite = pygame.transform.scale(pygame.image.load(sprite), (width, height))
		self.width = width
		self.height = height
		self.layout = []
		
		for i in range(-1, 2):
			tempRow = []
			for j in range(-1, 2):
				rect = self.sprite.get_rect()
				rect.centerx = (i + 1 / 2) * width
				rect.centery = (j + 1 / 2) * height
				tempRow.append(rect)
			self.layout.append(tempRow)
		
	def display(self, window):
		for i in range(-1, 2):
			for j in range(-1, 2):
				window.blit(self.sprite, self.layout[i][j])
		
	def updatePos(self, speed):
		for i in range(-1, 2):
			for j in range(-1, 2):
				self.layout[i][j].centerx += int(speed.x)
				self.layout[i][j].centery += int(speed.y)
	
	def fixPos(self):
		for i in range(-1, 2):
			for j in range(-1, 2):
				if self.layout[i][j].centerx < ((-1 + 1 / 2) * self.width):
					self.layout[i][j].centerx = (1 + 1 / 2) * self.width
					
				elif self.layout[i][j].centerx > ((1 + 1 / 2) * self.width):
					self.layout[i][j].centerx = (-1 + 1 / 2) * self.width
					
				if self.layout[i][j].centery < ((-1 + 1 / 2) * self.height):
					self.layout[i][j].centery = (1 + 1 / 2) * self.height
					
				elif self.layout[i][j].centery > ((1 + 1 / 2) * self.height):
					self.layout[i][j].centery = (-1 + 1 / 2) * self.height
	
	def isInsideRenderArea(self, rect):
		if rect.x > -self.width and rect.x < (2 * self.width) and rect.y > -self.height and rect.y < (2 * self.height):
			return True
		return False