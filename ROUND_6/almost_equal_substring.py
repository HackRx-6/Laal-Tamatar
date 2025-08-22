# Code to find the smallest starting index of a substring in s that is almost equal to pattern

s = "abcdefg"
pattern = "bcdffg"


def is_almost_equal(x, y):
    count_diff = 0
    for i in range(len(x)):
        if x[i] != y[i]:
            count_diff += 1
            if count_diff > 1:
                return False
    return True


def smallest_almost_equal_index(s, pattern):
    m, n = len(s), len(pattern)
    for i in range(m - n + 1):
        if is_almost_equal(s[i:i + n], pattern):
            return i
    return -1


result = smallest_almost_equal_index(s, pattern)
print(result)