# Given strings
s = "ababbababa"
pattern = "bacaba"

pattern_length = len(pattern)

# Function to check if two strings are almost equal
# i.e. they differ by at most one character

def almost_equal(x, y):
    diff_count = 0
    for i in range(len(x)):
        if x[i] != y[i]:
            diff_count += 1
        if diff_count > 1:
            return False
    return True

# Find the smallest starting index of substring in s almost equal to pattern
result = -1
for i in range(len(s) - pattern_length + 1):
    substring = s[i:i + pattern_length]
    if almost_equal(substring, pattern):
        result = i
        break

print(result)