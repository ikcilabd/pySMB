import pygame
import tmx
import spritesheet
from pygame.locals import *


class Enemy(pygame.sprite.Sprite):
	def __init__(self,location,properties, *groups):
		super(Enemy, self).__init__(*groups)
		self.ess = spritesheet.spritesheet('enemy_tileset.png')

							##x,y,w,h,dirydelta
		self.image_list = {'normal':{'goomba':(0,0,16,16,0),
									'turtle':(32,48,16,24,24),
									'beetle':(0,194,16,16,16)},
						'underground':{'goomba':(0,16,16,16,0),
									'turtle':(32,96,16,24,24),
									'beetle':(0,194,16,16,16)},
						'castle':{'goomba':(0,32,16,16,0),
								'turtle':(32,144,16,24,24),
								'beetle':(0,194,16,16,16)}
							}

		ic = self.image_list[properties['style']][properties['type']]

		self.image_anim_left = (self.ess.image_at((ic[0],ic[1],ic[2],ic[3]), colorkey=-1),
								self.ess.image_at((ic[0]+ic[2],ic[1],ic[2],ic[3]), colorkey=-1))
		self.image_anim_right = (self.ess.image_at((ic[0],ic[1]+ic[4],ic[2],ic[3]), colorkey=-1),
								self.ess.image_at((ic[0]+ic[2],ic[1]+ic[4],ic[2],ic[3]), colorkey=-1))
		self.image_anim_stomp = self.ess.image_at((ic[0]+ic[2]+ic[2],ic[1],ic[2],ic[3]), colorkey=-1)

		if properties['type'] == 'turtle':
			self.image_anim_stomp_reanim = self.ess.image_at((ic[0]+ic[2]+ic[2]+ic[2],ic[1],ic[2],ic[3]), colorkey=-1)
		
		self.image_list = (self.image_anim_left,self.image_anim_stomp,self.image_anim_right)

		self.direction = int(properties['direction'])
		
		self.image = self.image_list[1 + self.direction][0]
		
		if self.image.get_size()[1] > 16:
			starting_loc = (location[0],location[1] - (self.image.get_size()[1] - 16))
		else:
			starting_loc = location

		self.rect = pygame.rect.Rect(starting_loc, self.image.get_size())
		self.moving = False
		self.stomped = False
		self.n = 0
		self.anim_phase = 0
		self.dy = 0
		self.properties = properties
		self.stomp_counter = 100
		self.shell_slide = False
		self.move_speed = 35

	def update(self,dt,game):
		enemy_trigger = game.tilemap.viewport.x + game.tilemap.view_w

		if self.rect.x <= enemy_trigger:
			self.moving = True
			
		if self.moving and (self.shell_slide or not self.stomped):
			if self.n % 3 == 0 and not self.shell_slide:
				self.image = self.image_list[1 + self.direction][self.anim_phase]
				if self.anim_phase == 0:
					self.anim_phase = 1
				else:
					self.anim_phase = 0
			elif self.shell_slide:
				self.image = self.image_anim_stomp
				self.move_speed = 200

			last = self.rect.copy()
			self.rect.x += self.direction * self.move_speed * dt
			self.rect.y += self.dy * dt				


			for cell in (game.tilemap.layers['triggers'].collide(self.rect, 'blockers') +
						game.tilemap.layers['changeables'].collide(self.rect, 'blockers')):
				blockers = cell['blockers']
				if 'l' in blockers and last.right <= cell.left and self.rect.right > cell.left:
					self.rect.right = cell.left
					self.direction = -1
				if 'r' in blockers and last.left >= cell.right and self.rect.left < cell.right:
					self.rect.left = cell.right
					self.direction = 1
				if 't' in blockers and last.bottom <= cell.top and self.rect.bottom > cell.top:
					self.rect.bottom = cell.top
					self.dy = 0
				if 'b' in blockers and last.top >= cell.bottom and self.rect.top < cell.bottom:
					self.rect.top = cell.bottom
					self.dy = 0
					break
				if 'x' in blockers:
					if self in game.enemy_list:
						game.enemy_list.remove(self)
					self.kill()

			
			for enemy_sprite in [x.rect for x in game.enemy_list]:
				if last.right <= enemy_sprite.left and self.rect.right > enemy_sprite.left:
					self.rect.right = enemy_sprite.left
					self.direction = -1
				if last.left >= enemy_sprite.right and self.rect.left < enemy_sprite.right:
					self.rect.left = enemy_sprite.right
					self.direction = 1
		

			self.dy = min(800, self.dy+40)

			self.n += 1

		elif self.stomped:

			if self.stomp_counter == 100:
				self.image = self.image_anim_stomp

			if self.properties['type'] == 'goomba':
				if self in game.enemy_list:
					game.enemy_list.remove(self)
				if self.stomp_counter < 85:
					self.kill()
					self.stomp_counter = 0

			elif self.properties['type'] == 'turtle':
				if self.stomp_counter < 30:
					if self.stomp_counter % 6 == 0:
						self.image = self.image_anim_stomp_reanim
					else:
						self.image = self.image_anim_stomp

			self.stomp_counter -= 1
			if self.stomp_counter == 0:
				self.stomped = False
				self.stomp_counter = 100


class Flower(pygame.sprite.Sprite):
	
	def __init__(self, location, *groups):
		super(Flower, self).__init__(*groups)
		self.bss = spritesheet.spritesheet('block_tileset.png')
		self.image_list = (self.bss.image_at((48,32,16,16), colorkey=-1),
						self.bss.image_at((64,32,16,16), colorkey=-1),
						self.bss.image_at((80,32,16,16), colorkey=-1),
						self.bss.image_at((96,32,16,16), colorkey=-1))
		self.image = self.image_list[0]
		self.rect = pygame.rect.Rect(location, (self.image.get_size()[0],0))
		self.dy = 0
		self.direction = 1
		self.initial_rise = True
		self.initial_height = self.rect.height
		self.initial_y = self.rect.y
		self.rise_increment = self.image.get_size()[1]/8
		self.blink_increment = 0


	def update(self, dt,game):
		if self.blink_increment < 4:
			blink_tile = self.blink_increment
			self.blink_increment += 1
		elif self.blink_increment == 4:
			blink_tile = 2
			self.blink_increment += 1
		elif self.blink_increment == 5:
			blink_tile = 1
			self.blink_increment += 1
		else:
			blink_tile = 0
			self.blink_increment = 0
		self.image = self.image_list[blink_tile]

		if self.initial_rise:
			if self.rect.height < self.image.get_size()[1]:
				self.rect.height += self.rise_increment
				self.rect.y -= self.rise_increment
			else:
				self.initial_rise = False
		else:
			if self.rect.colliderect(game.player.rect):
				if game.player.player_current_powerup == 1:
					game.player.powerup_anim_phase = 0
				self.kill()

class OneUp(pygame.sprite.Sprite):
	def __init__(self,location, *groups):
		super(OneUp,self).__init__(*groups)
		self.image = pygame.image.load('1up.png')
		self.rect = pygame.rect.Rect(location, (self.image.get_size()[0],0))
		self.dy = 0
		self.direction = 1
		self.initial_rise = True
		self.initial_height = self.rect.height
		self.initial_y = self.rect.y
		self.rise_increment = self.image.get_size()[1]/8
		self.player_dead = False

	def update(self, dt, game):
		if not self.player_dead:
			if self.initial_rise:
				if self.rect.height < self.image.get_size()[1]:
					self.rect.height += self.rise_increment
					self.rect.y -= self.rise_increment
				else:
					self.initial_rise = False
			else:

				last = self.rect.copy()
				self.rect.x += self.direction * 100 * dt
				self.rect.y += self.dy * dt

				for cell in (game.tilemap.layers['triggers'].collide(self.rect, 'blockers') +
							game.tilemap.layers['changeables'].collide(self.rect, 'blockers')):
					blockers = cell['blockers']
					if 'l' in blockers and last.right <= cell.left and self.rect.right > cell.left:
						self.rect.right = cell.left
						self.direction = -1
					if 'r' in blockers and last.left >= cell.right and self.rect.left < cell.right:
						self.rect.left = cell.right
						self.direction = 1
					if 't' in blockers and last.bottom <= cell.top and self.rect.bottom > cell.top:
						self.rect.bottom = cell.top
						self.dy = 0
					if 'b' in blockers and last.top >= cell.bottom and self.rect.top < cell.bottom:
						self.rect.top = cell.bottom
						self.dy = 0
						break
					if 'x' in blockers:
						self.kill()
				if self.rect.colliderect(game.player.rect):
					point_display_x = self.rect.x-game.tilemap.viewport.x
					game.point_list.append([(point_display_x,self.rect.y),'1UP',0])
					game.player_lives += 1
					self.kill()

				self.dy = min(400, self.dy + 40)

class Mushroom(pygame.sprite.Sprite):
	
	def __init__(self, location, *groups):
		super(Mushroom, self).__init__(*groups)
		self.image = pygame.image.load('mushroom.png')
		self.rect = pygame.rect.Rect(location, (self.image.get_size()[0],0))
		self.dy = 0
		self.direction = 1
		self.initial_rise = True
		self.initial_height = self.rect.height
		self.initial_y = self.rect.y
		self.rise_increment = self.image.get_size()[1]/8
		self.player_dead = False


	def update(self, dt, game):
		if not self.player_dead:
			if self.initial_rise:
				if self.rect.height < self.image.get_size()[1]:
					self.rect.height += self.rise_increment
					self.rect.y -= self.rise_increment
				else:
					self.initial_rise = False
			else:

				last = self.rect.copy()
				self.rect.x += self.direction * 100 * dt
				self.rect.y += self.dy * dt

				for cell in (game.tilemap.layers['triggers'].collide(self.rect, 'blockers') +
							game.tilemap.layers['changeables'].collide(self.rect, 'blockers')):
					blockers = cell['blockers']
					if 'l' in blockers and last.right <= cell.left and self.rect.right > cell.left:
						self.rect.right = cell.left
						self.direction = -1
					if 'r' in blockers and last.left >= cell.right and self.rect.left < cell.right:
						self.rect.left = cell.right
						self.direction = 1
					if 't' in blockers:
						#if last_bottom == cell.top and self.rect.bottom > cell.top:
						#	self.dy -= 300
						if last.bottom <= cell.top and self.rect.bottom > cell.top:
							self.rect.bottom = cell.top
							self.dy = 0
						
					if 'b' in blockers and last.top >= cell.bottom and self.rect.top < cell.bottom:
						self.rect.top = cell.bottom
						self.dy = 0
						break
					if 'x' in blockers:
						self.kill()
				if self.rect.colliderect(game.player.rect):
					if game.player.player_current_powerup == 0:
						game.player.powerup_anim_phase = 0
					self.kill()

				self.dy = min(400, self.dy + 40)

class Player(pygame.sprite.Sprite):
	def __init__(self, location, *groups):
		super(Player,self).__init__(*groups)


		self.player_current_powerup = 0
		self.player_current_direction = 1


		self.player_anim_phase = 0
		self.set_player_images()
		
		self.image = self.player_image_still
		##set hit detection rectange
		self.rect = pygame.rect.Rect(location,self.image.get_size())



		self.resting = False
		self.dy = 0
		self.key_press_direction = self.player_current_direction

		self.n = 0
		self.blink_level = 0
		self.moving_cell_list = []
		self.moving_coins_list = []
		self.moving_mushroom_list = []
		self.jump_pressed = False
		self.jump_active = False
		self.powerup_anim_phase = 11
		self.powerdown_counter = 16
		self.powerdown_anim_phase = self.powerdown_counter
		self.player_dead = False
		self.player_death_max_y_hit = False
		self.player_death_anim = 0
		self.combo_multiplier = 1
		self.player_speed_start = 75
		self.player_speed = self.player_speed_start
		self.player_speed_max = 160
		self.player_jump_height = -405


		print("PLAYER START")


	def set_player_images(self):
		self.pss = spritesheet.spritesheet('mario_tileset.png')
		if self.player_current_powerup == 0:
			x_line = 0
			if self.player_current_direction == 1:
				y_line = 80
			else:
				y_line = 64
			x_size = 16
			y_size = 16
		elif self.player_current_powerup == 1:
			x_line = 0
			if self.player_current_direction == 1:
				y_line = 32
			else:
				y_line = 0
			x_size = 16
			y_size = 32
		else:
			x_line = 0
			if self.player_current_direction == 1:
				y_line = 128

			else:
				y_line = 96
			x_size = 16
			y_size = 32								

		self.player_image_still = self.pss.image_at((0 + x_line,y_line,x_size,y_size), colorkey=-1)
		self.player_image_1 = self.pss.image_at((16 + x_line,y_line,x_size,y_size), colorkey=-1)
		self.player_image_2 = self.pss.image_at((32 + x_line,y_line,x_size,y_size), colorkey=-1)
		self.player_image_3 = self.pss.image_at((48 + x_line,y_line,x_size,y_size), colorkey=-1)
		self.player_image_list = [self.player_image_1,
								self.player_image_2,
								self.player_image_3
								]
		self.player_image_change_dir = self.pss.image_at((64 + x_line,y_line,x_size,y_size), colorkey=-1)
		self.player_image_jump = self.pss.image_at((80 + x_line,y_line,x_size,y_size), colorkey=-1)
		self.player_mid_powerup = self.pss.image_at((112 + x_line,y_line,x_size,23), colorkey=-1)
		self.player_blink_list = [self.pss.image_at(((self.player_anim_phase*16),y_line+96,x_size,y_size), colorkey=-1),
								self.pss.image_at(((self.player_anim_phase*16),y_line+160,x_size,y_size), colorkey=-1),
								self.pss.image_at(((self.player_anim_phase*16),y_line+224,x_size,y_size), colorkey=-1),
								self.pss.image_at(((self.player_anim_phase*16),y_line+288,x_size,y_size), colorkey=-1)
								]
		self.player_image_big_powerdown = self.pss.image_at(((96 + x_line),self.player_current_direction * 32,16,32), colorkey=-1)
		self.player_image_small_powerdown = self.pss.image_at(((96 + x_line),(self.player_current_direction * 16)+64,16,16), colorkey=-1)
		self.player_image_dead = self.pss.image_at((112,64,16,16),colorkey=-1)

	def update(self, dt, game):
		if not self.player_dead:
			last = self.rect.copy() ##Current rect used to compare where you are vs where you're going
			key = pygame.key.get_pressed()
			if key[pygame.K_LSHIFT]: ##player speed
				if self.player_speed == self.player_speed_max:
					dt *= 1.5

			############LEFT/RIGHT MOVEMENT#################
			if key[pygame.K_LEFT] or key[pygame.K_RIGHT]:
				if key[pygame.K_LEFT]:
					self.key_press_direction = -1   #Left
				else:
					self.key_press_direction = 1   #Right

				if self.key_press_direction != self.player_current_direction:   #First anim after a direction change
					self.player_speed = self.player_speed_start
					self.player_current_direction = self.key_press_direction
					if not self.jump_active:
						self.image = self.player_image_change_dir
					self.player_anim_phase = 0
				elif self.resting and not self.jump_active:
					self.set_player_images()
					self.image = self.player_image_list[self.player_anim_phase]   #Normal animation
					if self.player_speed < self.player_speed_max:
						self.player_speed += 10
					if self.n % 2 == 0:
						if self.player_anim_phase == 2:
							self.player_anim_phase = 0
						else:
							self.player_anim_phase += 1

				self.rect.x += self.player_speed * dt * self.player_current_direction	#Horizontal movement
				#self.rect.x += 7 * self.player_current_direction
			elif self.resting:
			#	if self.player_speed > self.player_speed_start:
			#		self.set_player_images()
			#		self.image = self.player_image_list[self.player_anim_phase]
			#		self.player_speed -= 15
			#		self.rect.x += self.player_speed * dt * self.player_current_direction
			#		if self.player_anim_phase == 2:
			#			self.player_anim_phase = 0
			#		else:
			#			self.player_anim_phase += 1
			#	else:
				self.image = self.player_image_still 
				self.player_anim_phase = 0
				self.player_speed = self.player_speed_start

			###########JUMPING################################
			if self.resting and key[pygame.K_SPACE] and not self.jump_pressed:
				self.jump_pressed = True
				self.jump_active = True
				self.image = self.player_image_jump
				self.dy = self.player_jump_height

				if key[pygame.K_LSHIFT]:
					self.dy -= 10


			if not key[pygame.K_SPACE]:
				self.jump_pressed = False



			self.dy = min(400, self.dy + 40)

			self.rect.y += self.dy * dt

			new = self.rect

			self.resting = False

			for cell in (game.tilemap.layers['triggers'].collide(new, 'blockers') + game.tilemap.layers['changeables'].collide(new, 'blockers')):
				blockers = cell['blockers']

				if 'l' in blockers and last.right <= cell.left and new.right > cell.left:
					new.right = cell.left
				if 'r' in blockers and last.left >= cell.right and new.left < cell.right:
					new.left = cell.right
				if 't' in blockers and last.bottom <= cell.top and new.bottom > cell.top:
					self.resting = True
					self.jump_active = False
					new.bottom = cell.top
					self.dy = 0
					self.combo_multiplier = 1
				if 'b' in blockers and last.top >= cell.bottom and new.top < cell.bottom:
					new.top = cell.bottom
					self.dy = 0
					if cell.name != 'empty_block':
						self.process_changed_block(cell, game)
						self.moving_cell_list.append([cell,0,cell.py])
			#if self.resting:
			#	if self.player_speed > self.player_speed_start:
			#		self.set_player_images()
			#		self.image = self.player_image_list[self.player_anim_phase]
			#		self.player_speed -= 15
			#		self.rect.x += self.player_speed * dt * self.player_current_direction
			#		if self.player_anim_phase == 2:
			#			self.player_anim_phase = 0
			#		else:
			#			self.player_anim_phase += 1
			#	else:
			#		self.image = self.player_image_still 
			#		self.player_anim_phase = 0
			#		self.player_speed = self.player_speed_start					

			self.bump_up_block(game)
			

			enemy_col = new.collidelist(game.enemy_list)
			if enemy_col > -1 and self.powerdown_anim_phase == self.powerdown_counter:
				enemy_sprite = game.enemy_list[enemy_col]
				if self.rect.bottom < enemy_sprite.rect.bottom - (enemy_sprite.rect.height / 2) and not enemy_sprite.stomped:
					##stomped
					print("STOMPED")
					enemy_sprite.stomped = True
					self.dy = -160
					#enemy_sprite.shell_slide = True
					#enemy_sprite.stomp_counter = 160
				elif enemy_sprite.stomped:
					enemy_sprite.shell_slide = True
					enemy_sprite.stomp_counter = 100					
				elif self.powerdown_anim_phase == self.powerdown_counter:
					self.powerdown_anim_phase = 0


			#	#for enemy_sprite in game.enemy_list:
			#	#if last.right <= enemy_sprite.rect.left and self.rect.right > enemy_sprite.rect.left:
			#	print("player",self.rect.right,self.rect.left,self.rect.top,self.rect.bottom)
			#	print("enemy",enemy_sprite.rect.right,enemy_sprite.rect.left,enemy_sprite.rect.top,enemy_sprite.rect.bottom)
			#	if self.rect.right > enemy_sprite.rect.left:
			#		if enemy_sprite.stomped and not enemy_sprite.shell_slide:
			#			enemy_sprite.shell_slide = True
			#			enemy_sprite.stomp_counter = 100
			#			enemy_sprite.direction = 1				
			#		#else:
			#			#self.powerdown_anim_phase = 0
			#	#if last.left >= enemy_sprite.rect.right and self.rect.left < enemy_sprite.rect.right:
			#	if self.rect.left < enemy_sprite.rect.right:
			#		if enemy_sprite.stomped and not enemy_sprite.shell_slide:
			#			enemy_sprite.shell_slide = True
			#			enemy_sprite.stomp_counter = 100
			#			enemy_sprite.direction = -1
			#		#else:		
			#			#self.powerdown_anim_phase = 0
			#	if last.bottom <= enemy_sprite.rect.top and new.bottom > enemy_sprite.rect.top:
			#		self.powerdown_anim_phase = 11
			#		if enemy_sprite.stomped and not enemy_sprite.shell_slide:
			#			enemy_sprite.shell_slide = True
			#			enemy_sprite.stomp_counter = 100
			#			if self.rect.left >= enemy_sprite.rect.left + (enemy_sprite.rect.width / 2):
			#				enemy_sprite.direction = -1
			#			else:
			#				enemy_sprite.direction = 1
			#		else:
			#			enemy_sprite.stomped = True
			#			enemy_sprite.shell_slide = False
			#		self.dy = -150
			#		stomp_score = 100*self.combo_multiplier
			#		point_display_x = self.rect.x-game.tilemap.viewport.x
			#		if stomp_score > 8000:
			#			stomp_score = '1UP'
			#		else:
			#			game.player_score += stomp_score
			#		game.point_list.append([(point_display_x,self.rect.y),stomp_score,0])
			#		
			#		if self.combo_multiplier == 8:
			#			self.combo_multiplier = 10
			#		else:
			#			self.combo_multiplier *= 2

			if self.powerup_anim_phase < 11:
				if self.powerup_anim_phase == 0:
					point_display_x = self.rect.x-game.tilemap.viewport.x
					game.point_list.append([(point_display_x,self.rect.y),1000,0])
					game.player_score += 1000
				pre_powerup_height = self.image.get_size()[1] ##get the old height
				self.powerup_anim()
				self.rect.y  = self.rect.y + pre_powerup_height - self.image.get_size()[1] ##set the correct location based on height
				self.rect.height = self.image.get_size()[1] ##set rect size based on new height
				self.rect.width = self.image.get_size()[0] ##set rect size based on new width

			if self.powerdown_anim_phase < self.powerdown_counter:
				pre_powerdown_height = self.image.get_size()[1]
				self.powerdown_anim(pre_powerdown_height)
				#self.rect.y = self.rect.y + pre_powerdown_height - self.image.get_size()[1]
				#self.rect.height = self.image.get_size()[1]
				#self.rect.width = self.image.get_size()[0]

			self.n += 1
			game.tilemap.set_focus(new.x, new.y)
		else:
			self.death_sequence()


	def powerdown_anim(self,pre_powerdown_height):
		if self.player_current_powerup > 0:
			if self.powerdown_anim_phase % 2 == 0 and self.powerdown_anim_phase < 7:
				if self.powerdown_anim_phase == 0:
					next_image = self.player_image_jump

				elif self.powerdown_anim_phase in [2,4]:
					next_image = self.player_image_big_powerdown
					#next_image.set_alpha(255)
				elif self.powerdown_anim_phase == 6:
					next_image = self.player_image_small_powerdown
					#next_image.set_alpha(255)
			else:
				self.powerdown_current_powerup = 0
				self.set_player_images()
				next_image = self.player_image_list[self.player_anim_phase]
				self.powerdown_current_powerup = 1
				#next_image.set_alpha(255)
				
			if self.powerdown_anim_phase == self.powerdown_counter - 1:
				self.player_current_powerup = 0
				self.set_player_images()
				next_image = self.player_image_list[self.player_anim_phase]
				#next_image.set_alpha(255)
			print(self.powerdown_anim_phase)
			self.rect.height = next_image.get_size()[1]
			self.rect.y = self.rect.y + pre_powerdown_height - next_image.get_size()[1]

			#self.rect.width = next_image.get_size()[0]
			self.image = next_image
			print(self.rect.y)
			print(pre_powerdown_height)
			print(self.image.get_size())
			print("-"*20)
		else:
			print(self.powerdown_anim_phase,"DEATH")
			self.image = self.player_image_dead
			self.player_dead_y = self.rect.y
			self.player_dead = True

		self.powerdown_anim_phase += 1

	def death_sequence(self):
		if self.player_death_anim > 10:
			if not self.player_death_max_y_hit:
				if self.rect.y > (self.player_dead_y - 60):
					self.rect.y -= 6
				else:
					self.player_death_max_y_hit = True
			else:
				self.rect.y += 6

		self.player_death_anim += 1
	def powerup_anim(self):
		if self.player_current_powerup == 0:
			if self.powerup_anim_phase < 10:
				if self.powerup_anim_phase % 2 == 0:
					if self.powerup_anim_phase <= 6:
						self.player_current_powerup = 0
					else:
						self.player_current_powerup = 1
					self.set_player_images()
					self.image = self.player_image_still
					self.player_current_powerup = 0
				else:
					self.player_current_powerup = 1
					self.set_player_images()
					self.image = self.player_mid_powerup
					self.player_current_powerup = 0
					self.set_player_images()
			else:
				self.player_current_powerup = 1
				self.set_player_images()
				self.image = self.player_image_still
				
		elif self.player_current_powerup == 1:
			if self.powerup_anim_phase < 10:
				self.set_player_images()
				if self.powerup_anim_phase in [2,6]:
					self.image = self.player_blink_list[0]
				elif self.powerup_anim_phase in [3,7]:
					self.image = self.player_blink_list[1]
				elif self.powerup_anim_phase in [0,4,8]:
					self.image = self.player_blink_list[2]
				elif self.powerup_anim_phase in [1,5,9]:
					self.image = self.player_blink_list[3]
			elif self.powerup_anim_phase == 10:
				self.player_current_powerup = 2
				self.set_player_images()
				self.image = self.player_blink_list[0]
		
		self.rect.width = self.image.get_size()[0]
		self.rect.height = self.image.get_size()[1]
		self.powerup_anim_phase += 1


	def bump_up_block(self, game):
		increments = (2,4,2,0)
		for moving_cell in self.moving_cell_list:
			if moving_cell[1] < 4:
				moving_cell[0].py = moving_cell[2] - increments[moving_cell[1]]
				moving_cell[1] += 1
			if moving_cell[1] == 2:
				bumpable_col = pygame.Rect(moving_cell[0].px,moving_cell[0].py,moving_cell[0].width,moving_cell[0].height).collidelist(game.bumpable_list)
				if bumpable_col > -1 and moving_cell[0].properties['status'] == 'breakable':
					game.bumpable_list[bumpable_col].dy -= 300


	def process_changed_block(self,cell, game):
		if 'status' in cell.properties:
			if cell.properties['status'] == 'coin' and 'coin' in cell.properties:
				if cell.properties['coin'] > 0:
					Coin((cell.px,cell.py), game.sprites)
					cell.properties['coin'] = int(cell.properties['coin']) - 1
					game.player_coins += 1
					game.player_score += 200
					if cell.properties['coin'] == 0:
						cell.properties['status'] = 'empty'
						cell.name = 'empty_block'
						cell.tile = game.tilemap.tilesets[7]
			if cell.properties['status'] == 'powerup':
				if self.player_current_powerup == 0:
					game.bumpable_list.append(Mushroom((cell.px,cell.py), game.sprites))
					cell.properties['status'] = 'empty'
					cell.name = 'empty_block'
					cell.tile = game.tilemap.tilesets[7]
				elif self.player_current_powerup > 0:
					Flower((cell.px,cell.py), game.sprites)
					cell.properties['status'] = 'empty'
					cell.name = 'empty_block'
					cell.tile = game.tilemap.tilesets[7]
			if cell.properties['status'] == '1up':
				game.bumpable_list.append(OneUp((cell.px,cell.py), game.sprites))
				cell.properties['status'] = 'empty'
				if cell.name == 'hidden_1up':
					cell.properties['blockers'] = 'tlrb'
				cell.name = 'empty_block'
				cell.tile = game.tilemap.tilesets[7]
			if cell.properties['status'] == 'breakable':
				if self.player_current_powerup > 0:
					BrokenBlock((cell.px,cell.py),0, game.sprites)
					BrokenBlock((cell.px,cell.py),1, game.sprites)
					BrokenBlock((cell.px,cell.py),2, game.sprites)
					BrokenBlock((cell.px,cell.py),3, game.sprites)
					game.tilemap.layers['changeables'].objects.remove(cell)
					game.player_score += 50

class BrokenBlock(pygame.sprite.Sprite):
	def __init__(self,location,quad,*groups):
		super(BrokenBlock,self).__init__(*groups)
		self.bss = spritesheet.spritesheet('block_tileset.png')
		self.image_topleft = self.bss.image_at((16,16,8,8),colorkey=-1)
		self.image_topright = self.bss.image_at((24,16,8,8),colorkey=-1)
		self.image_bottomleft = self.bss.image_at((16,24,8,8),colorkey=-1)
		self.image_bottomright = self.bss.image_at((24,24,8,8),colorkey=-1)
		
		self.brokenblock_group = [[self.image_topleft,0,0],
								[self.image_topright,8,0],
								[self.image_bottomleft,0,8],
								[self.image_bottomright,8,8]
								]
		self.initial_location = (location[0]+self.brokenblock_group[quad][1],location[1]+self.brokenblock_group[quad][2])
		self.image_nwse = self.bss.image_at((20,36,8,8),colorkey=-1)
		self.image_nesw = self.bss.image_at((20,52,8,8),colorkey=-1)
		self.image = self.brokenblock_group[quad][0]
		self.rect = pygame.rect.Rect(self.initial_location, self.image.get_size())
		self.n = 0
		self.initial_location = location
		self.quad = quad

	def update(self, dt, game):
		x_interval = 4
		y_interval = 12
		if self.n > 0:
			self.image = self.brokenblock_group[self.n % 2][0]
			if self.quad == 0:
				self.rect.x -= x_interval
				if self.rect.x > self.initial_location[0] - 24:
					self.rect.y -=  y_interval
				else:
					self.rect.y += y_interval

			elif self.quad == 2:
				self.rect.x -= x_interval
				if self.rect.x > self.initial_location[0] - 16:
					self.rect.y -=  y_interval
				else:
					self.rect.y += y_interval				
			elif self.quad == 1:
				self.rect.x += x_interval
				if self.rect.x < self.initial_location[0] + 32:
					self.rect.y -=  y_interval
				else:
					self.rect.y += y_interval
			elif self.quad == 3:
				self.rect.x += x_interval
				if self.rect.x < self.initial_location[0] + 24:
					self.rect.y -=  y_interval
				else:
					self.rect.y += y_interval	

			if self.rect.y > 300:
				self.kill() 

		self.n += 1
		


class Coin(pygame.sprite.Sprite):
	
	def __init__(self, location, *groups):
		super(Coin, self).__init__(*groups)
		self.bss = spritesheet.spritesheet('block_tileset.png')
		self.image_list = (self.bss.image_at((48,16,16,16), colorkey=-1),
						self.bss.image_at((64,16,16,16), colorkey=-1),
						self.bss.image_at((80,16,16,16), colorkey=-1),
						self.bss.image_at((96,16,16,16), colorkey=-1))
		self.image = self.image_list[0]
		self.rect = pygame.rect.Rect(location, self.image.get_size())
		self.initial_py = location[1]
		self.initial_px = location[0]
		self.n = 0
		self.point_n = 0

	def update(self, dt, game):
		increments = (20,25,30,35,40,45,50,55,50,45,35,30,25,20)
		show_list = (0,1,2,3,0,1,2,3,0,1,2,3,0,1)
		last = self.rect.copy()
		
		if self.n < 14:
			self.image = self.image_list[show_list[self.n]]
			self.rect.y = (self.initial_py - increments[self.n])
			self.n += 1
		else:
			point_display_x = self.rect.x-game.tilemap.viewport.x
			game.point_list.append([(point_display_x,self.rect.y),200,0])
			self.kill()


class Game(object):
	def main(self, screen):
		clock = pygame.time.Clock()

		players_name = 'mario'

		dt = clock.tick(30)
		
		self.tilemap = tmx.load('11.tmx', screen.get_size())
		#self.tilemap = tmx.load('11.tmx', (360,240))
		self.sprites = tmx.SpriteLayer()

		start_cell = self.tilemap.layers['triggers'].find('player')[0]
		self.player = Player((start_cell.px, start_cell.py), self.sprites)
		self.tilemap.layers.append(self.sprites)

		initial_blink_surface = self.tilemap.tilesets[4].surface.copy()
		blink_level = 0
		coin_blink = 0

		self.player_lives = 3
		self.player_coins = 0
		self.player_score = 0
		self.game_time = 400
		self.game_world = 1
		self.game_level = 1


		self.enemy_list = []
		for cell in self.tilemap.layers['enemies'].objects:
			self.enemy_list.append(Enemy((cell.px,cell.py),cell.properties, self.sprites))
		
		font_size = 8
		self.set_font_images(font_size)

		self.css = spritesheet.spritesheet('coin_tileset.png')
		coin_image_list = [self.css.image_at((64,0,8,8), colorkey=-1),
						self.css.image_at((72,0,8,8), colorkey=-1),
						self.css.image_at((80,0,8,8), colorkey=-1)
						]

		self.point_list = []
		self.point_float = 40


		self.bumpable_list = []

		n=0
		while 1:
			
			clock.tick(30)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return
				if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					return

			################Blinking Question Blocks################		
			if n % 3 == 0:

				if blink_level < 6:
					if blink_level < 3:
						blink_tile = 4 + blink_level
						coin_blink = blink_level
					elif blink_level == 3:
						blink_tile = 5
						coin_blink = 1
					else:
						blink_tile = 4
						self.tilemap.tilesets[4].surface = initial_blink_surface  ##gotta do this for some reason
						coin_blink = 0

					for cell in self.tilemap.layers['changeables'].find('question_block'):
						cell.tile.surface = self.tilemap.tilesets[blink_tile].surface
					
					blink_level += 1
				else:
					blink_level = 0
					coin_blink = 0

			########################################################
			if n % 10 == 0 and not self.player.player_dead:
				self.game_time -=1
			




			self.tilemap.update(dt / 1000.,self)
			screen.fill((92,148,252))
			
			name_start_x = 8
			score_start_x = name_start_x
			time_title_start_x = 184
			time_count_start_x = 192
			lives_count_start_x = 88
			world_title_start_x = 128
			world_count_start_x = 144
			for letter in players_name:
				name_start_x += font_size
				screen.blit(self.letter_image_dict[letter],(name_start_x,font_size))
			for number in str(self.player_score).zfill(6):
				score_start_x += font_size
				screen.blit(self.number_image_list[int(number)],(score_start_x,font_size*2))
			for letter in 'time':
				time_title_start_x += font_size
				screen.blit(self.letter_image_dict[letter],(time_title_start_x,font_size))
			for number in str(self.game_time).zfill(3):
				time_count_start_x += font_size
				screen.blit(self.number_image_list[int(number)],(time_count_start_x,font_size*2))

			screen.blit(coin_image_list[coin_blink],(80,16))
			screen.blit(self.letter_image_dict['by'],(lives_count_start_x,16))
			for number in str(self.player_coins).zfill(2):
				lives_count_start_x += font_size
				screen.blit(self.number_image_list[int(number)],(lives_count_start_x,font_size*2))
			for letter in 'world':
				world_title_start_x += font_size
				screen.blit(self.letter_image_dict[letter],(world_title_start_x,font_size))
			screen.blit(self.number_image_list[self.game_world],(world_count_start_x,font_size*2))
			screen.blit(self.letter_image_dict['dash'],(world_count_start_x+font_size,font_size*2))
			screen.blit(self.number_image_list[self.game_level],(world_count_start_x+(font_size*2),font_size*2))

			for point in self.point_list:
				if point[2] < self.point_float:
					n = 0
					if point[1] == '1UP':
						screen.blit(self.point_image_dict['1UP'],(point[0][0]+(n*4),point[0][1]-point[2]))
						n += 1
					else:
						for number in str(point[1]):
							screen.blit(self.point_image_dict[int(number)],(point[0][0]+(n*4),point[0][1]-point[2]))
							n += 1	
					point[2] += 1			

			self.tilemap.draw(screen)
			pygame.display.flip()			

			n+= 1




	def set_font_images(self,xy):
		
		self.tss = spritesheet.spritesheet('text_med_tileset.png')
		self.sss = spritesheet.spritesheet('score_tileset.png')

		self.number_image_list = []
		self.letter_image_dict = {}
		self.point_image_dict = {}

		for number in range(10):
			self.number_image_list.append(self.tss.image_at((number*xy,0,xy,xy), colorkey=(0,0,0)))
		
		letter_row = 1
		letter_count=0
		for letter in [chr(x) for x in range(ord('a'),ord('z')+1)]:
			if letter_count == 10:
				letter_row += 1
				letter_count = 0
			self.letter_image_dict[letter] = self.tss.image_at((letter_count*xy,letter_row*xy,xy,xy),colorkey=(0,0,0))
			letter_count += 1
		self.letter_image_dict['dash'] = self.tss.image_at((6*xy,3*xy,xy,xy), colorkey=(0,0,0))
		self.letter_image_dict['by'] = self.tss.image_at((7*xy,3*xy,xy,xy), colorkey=(0,0,0))
		self.letter_image_dict['cop'] = self.tss.image_at((8*xy,3*xy,xy,xy), colorkey=(0,0,0))
		self.letter_image_dict['exc'] = self.tss.image_at((9*xy,3*xy,xy,xy), colorkey=(0,0,0))

		score_count = 0
		for number in [0,1,2,4,5,8]:
			self.point_image_dict[number] = self.sss.image_at((score_count*4,0,4,8), colorkey=(0,0,0))
			score_count += 1
		self.point_image_dict['1UP'] = self.sss.image_at((score_count*4,0,16,8), colorkey=(0,0,0))

if __name__ == '__main__':	
	pygame.init()
	screen = pygame.display.set_mode((250,240))

	#screen = pygame.display.set_mode((720,480),0,32)

	Game().main(screen)



