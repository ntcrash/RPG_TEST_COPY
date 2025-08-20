import random


def roll_dice_old(num_dice=1, num_sides=6):
    """
    Simulates rolling one or more dice with a specified number of sides.

    Args:
        num_dice (int): The number of dice to roll (default is 1).
        num_sides (int): The number of sides on each die (default is 6).

    Returns:
        list: A list containing the results of each die roll.
    """
    if num_dice <= 0 or num_sides <= 0:
        print("Number of dice and number of sides must be positive integers.")
        return []

    results = []
    for _ in range(num_dice):
        roll = random.randint(1, num_sides)
        results.append(roll)
    return results


def roll_dice(num, sides):
    return [random.randint(1, sides) for _ in range(num)]
