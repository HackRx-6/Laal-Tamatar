def is_almost_equal(x, y):
    differences = 0
    for i in range(len(x)):
        if x[i] != y[i]:
            differences += 1
        if differences > 1:
            return False
    return True

def find_almost_equal_index(s, pattern):
    pattern_length = len(pattern)
    s_length = len(s)
    for i in range(s_length - pattern_length + 1):
        substring = s[i:i + pattern_length]
        if is_almost_equal(substring, pattern):
            return i
    return -1

s = 'abcdefg'
pattern = 'bcdffg'
result = find_almost_equal_index(s, pattern)
result