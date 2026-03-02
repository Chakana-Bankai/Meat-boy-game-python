.PHONY: server game test

server:
	python -m server.app

game:
	python -m game.main

test:
	pytest -q
