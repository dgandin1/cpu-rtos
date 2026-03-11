A simple script to practice vi!

def do_stuff(stuff, i):
	
	for elem in range(i):
		print(stuff)

do_stuff("hello world", 10)

def do_some_more_stuff(stuff, i, j):
	
	for elem in range(i):
		for elem in range(j):
			print(stuff)

do_some_more_stuff("bye", 20, 10)
