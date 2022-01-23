import multiprocessing as mp
from time import sleep
from random import randint


def rand_sleep(x: int):
    r = randint(1, 4)
    sleep(r)
    print(r)

def test():
    with mp.Pool() as p:
        for res in p.map(rand_sleep, [1, 2, 3, 4]):
            pass
