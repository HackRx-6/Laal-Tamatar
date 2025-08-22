# Given strings
s = "abcdefg"
pattern = "bcdffg"

# Function to check if two strings are almost equal
# almost equal means at most one character difference

def almost_equal(x, y):
    if len(x) != len(y):
        return False
    diff_count = 0
    for i in range(len(x)):
        if x[i] != y[i]:
            diff_count += 1
            if diff_count > 1:
                return False
    return True

# Find smallest starting index of substring in s that is almost equal to pattern

def find_almost_equal_index(s, pattern):
    n, m = len(s), len(pattern)
    for i in range(n - m + 1):
        substring = s[i:i+m]
        if almost_equal(substring, pattern):
            return i
    return -1

# Get the result
result = find_almost_equal_index(s, pattern)

# Print the result
print(result)