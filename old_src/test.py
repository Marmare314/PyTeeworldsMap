from strongtyping.strong_typing import match_typing


@match_typing
def func(x: int, y: int):
    return x+y


print(func(1, 2))
