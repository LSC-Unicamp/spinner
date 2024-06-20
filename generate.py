import random
import struct


def generate_random_numbers_file(filename, num_integers, max_value=100):
    count = 0
    with open(filename, "wb") as f:
        for _ in range(num_integers):
            number = random.randint(0, max_value)
            if number == 5:
                count = count + 1
            # 'i' is the format character for a 4-byte integer
            f.write(struct.pack("i", number))
    print(f"Number of 5s generated: {count}")


if __name__ == "__main__":
    filename = "random_numbers.bin"
    num_integers = 1000000000
    max_value = 10
    generate_random_numbers_file(filename, num_integers, max_value)

    print(f"File '{filename}' generated with {num_integers} random integers.")
