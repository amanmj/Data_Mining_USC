import re
import random
def isprime(num):
    # If given number is greater than 1
    if num > 1:
        # Iterate from 2 to n / 2
        for i in range(2, num // 2):

            # If num is divisible by any number between
            # 2 and n / 2, it is not prime
            if (num % i) == 0:
                return False
        else:
            return True
    else:
        return False


def isPrime2(n):
    # Corner cases
    if (n <= 1):
        return False
    if (n <= 3):
        return True

    # This is checked so that we can skip
    # middle five numbers in below loop
    if (n % 2 == 0 or n % 3 == 0):
        return False

    i = 5
    while (i * i <= n):
        if (n % i == 0 or n % (i + 2) == 0):
            return False
        i = i + 6

    return True

print(isprime(21))
print(isPrime2(1398318269))
random.seed(7)
random_prime_a = random.choices([x for x in range(1000, 2000) if isprime(x)], k=23)
random_prime_b = random.choices([x for x in range(1000, 2000) if isprime(x)], k=23)


print(random_prime_a)
print(random_prime_b)

PRIME = random.choices([x for x in range(1000000, 1000100) if isPrime2(x)])
print(PRIME)