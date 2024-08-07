import random
import struct
from time import sleep

from rich import print as rprint


def generate_random_numbers_file(num_integers, filename, max_value=10):
    count = 0
    expected_size = num_integers * 4 / (1024 * 1024)
    rprint(f"About to generate a file of size: {expected_size} MB...")
    sleep(5)

    with open(filename, "wb") as f:
        for _ in range(num_integers):
            number = random.randint(0, max_value)
            if number == 5:
                count = count + 1
            # 'i' is the format character for a 4-byte integer
            f.write(struct.pack("i", number))
        rprint(
            f"Generated {num_integers} random integers in {filename} ({f.tell()/(1024*1024)} MB)"
        )
