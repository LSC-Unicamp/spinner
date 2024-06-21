import random
import struct
from rich import print as rprint


def generate_random_numbers_file(num_integers, filename, max_value=10):
    count = 0
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
