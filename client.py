#!/usr/bin/python

import random
import socket
import json
import math
import traceback
import curses

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(1)

SERVER = "141.3.235.98"
PORT = 2014

connection = socket.socket()

CLIENT = "[#kitinfo] klaxa"
PASS = "XOmBg/gQZHhrGuMv8lc7QVVYOGw="

init_json = dict()
init_json["accelerate"] = 1
init_json["shoot"] = "LEL"
init_json["name"] = CLIENT
init_json["pw"] = PASS

print("connecting")
connection.connect((SERVER,PORT))
connection_file = connection.makefile("r")
print("connected!")

print(str(init_json))
print("sending")
prepared_json = str(init_json) + "\n"
connection.sendall(bytes(prepared_json, 'utf-8'))
print("sent")

def wrap_coord(number):
	if number > 50:
		number -= 100
	if number < -50:
		number += 100
	return number
def wrap_dir(direction):
	if direction < 0:
		return direction + 2 * math.pi
	return direction
def find_best_point(input_json, my_tank):
	my_id = my_tank["tank"]
	center_x = my_tank["x"]
	center_y = my_tank["y"]
	tanks = []
	high_score = 0
	target_tank = (0, 0, 0, 0)
	for obj in input_json["msg"]:
		try:
			tanks.append((obj["tank"], wrap_coord(obj["x"] - center_x), wrap_coord(obj["y"] - center_y), obj["score"]))
		except KeyError:
			pass
	for target in tanks:
		(tank_id, x, y, score) = target
		if (tank_id != my_id):
			if (score > high_score):
				target_tank = target
	
	return target_tank

def find_closest_point(input_json, my_tank):
	my_id = my_tank["tank"]
	center_x = my_tank["x"]
	center_y = my_tank["y"]
	tanks = []
	target_tank = (0, 0, 0, 0)
	low_dist = 100
	for obj in input_json["msg"]:
		try:
			x = wrap_coord(obj["x"] - center_x)
			y = wrap_coord(obj["y"] - center_y)
			dist = math.sqrt(x * x + y * y)
			tanks.append((obj["tank"], x, y, dist))
		except KeyError:
			pass
	
	for target in tanks:
		(tank_id, x, y, dist) = target
		if (tank_id != my_id):
			if (dist < low_dist):
				target_tank = target
	return target_tank
def get_direction(tank):
	(tank_id, x, y, score) = tank
	return (wrap_dir(math.atan2(y,x)))
def calculate_response(input_json):
	response = dict()
	response["accelerate"] = 1
	response["turn"] = (random.random() - 0.5) * 2
	response["pw"] = PASS
	my_tank = dict()
	for obj in input_json["msg"]:
		try:
			if (obj["tank"] == input_json["id"]):
				my_tank = obj
				print(str(my_tank))
				break
		except KeyError:
			pass
	
	try:
		target_tank = find_best_point(input_json, my_tank)
		target_direction = get_direction(target_tank)
		my_direction = my_tank["direction"]
		
		if (my_tank["direction"] < target_direction):
			response["turn"] = min(abs(my_tank["direction"] - target_direction) * 2, 1)
		else:
			response["turn"] = max(-1 * abs(my_tank["direction"] - target_direction) * 2, -1)
		if (abs(my_tank["direction"] - target_direction) < 0.3):
			response["shoot"] = "LEL"
			pass
		(tank_id, x, y, score) = target_tank
		
		print("target direction: %.2f, my x: %d, my y: %d, their x: %d, their y: %d" % (target_direction, my_tank["x"], my_tank["y"], x, y))
	except KeyError:
		print("No own tank present")
	
	# check for threat
	missiles = []
	safe_radius = 1
	for obj in input_json["msg"]:
		try:
			if (obj["missile"]):
				missiles.append((wrap_coord(obj["x"] - my_tank["x"]), wrap_coord(obj["y"] - my_tank["y"]), obj["direction"]))
		except KeyError:
			pass
	for missile in missiles:
		(x, y, direction) = missile
		x2 = x + math.sin(direction)
		y2 = y + math.cos(direction)
		d_x = x2 - x
		d_y = y2 - y
		d_r = math.sqrt(d_x * d_x + d_y * d_y)
		determinant = x * y2 - x2 * y
		discriminant = safe_radius * safe_radius * d_r * d_r - determinant * determinant
		if discriminant > 0:
			print("threat detected, initiating stop")
			response["accelerate"] = 0 #-0.25
	return response

def reconnect():
	global connection
	global connection_file
	connection.close()
	connection = socket.socket()
	connection.connect((SERVER,PORT))
	connection_file = connection.makefile("r")

while(True):

	try: 
		response = connection_file.readline()
		try:
			#print(response)
			response = json.loads(response)
			my_response = calculate_response(response)
			#print(my_response)
			connection.sendall(bytes(str(my_response) + "\n", 'utf-8'))
		except BaseException as e:
			print("Oops")
			print(traceback.format_exc())
			print(response)
			curses.endwin()
			exit(1)
		
	except KeyboardInterrupt:
		connection.sendall(bytes("asd", 'utf-8'))
		connection.shutdown(socket.SHUT_RDWR)
		connection.close()
		curses.endwin()
