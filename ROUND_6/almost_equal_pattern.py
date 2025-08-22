def almost_equal_index(s, pattern):
    pattern_length = len(pattern)
    s_length = len(s)
    for i in range(s_length - pattern_length + 1):
        substring = s[i:i + pattern_length]
        # Count the differences between the substring and the pattern
        differences = sum(1 for a, b in zip(substring, pattern) if a != b)
        # Check if they are almost equal
        if differences <= 1:
            return i
    return -1

s = 'ababbababa'
pattern = 'bacaba'
result = almost_equal_index(s, pattern)
result