# Given strings
s = "ababbababa"
pattern = "bacaba"

# Function to check if two strings are almost equal
# i.e., differ in at most one character

def is_almost_equal(x, y):
    diff_count = 0
    for i in range(len(x)):
        if x[i] != y[i]:
            diff_count += 1
            if diff_count > 1:
                return False
    return True

# Function to find smallest start index of a substring in s almost equal to pattern

def smallest_almost_equal_index(s, pattern):
    n = len(s)
    m = len(pattern)
    for i in range(n - m + 1):
        substring = s[i:i+m]
        if is_almost_equal(substring, pattern):
            return i
    return -1

# Call the function and print result
result = smallest_almost_equal_index(s, pattern)
print(result)