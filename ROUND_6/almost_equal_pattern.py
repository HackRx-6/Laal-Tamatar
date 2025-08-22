def almost_equal_index(s, pattern):
    n = len(s)
    m = len(pattern)
    for i in range(n - m + 1):
        substring = s[i:i + m]
        # Count the number of different characters
        differences = sum(1 for a, b in zip(substring, pattern) if a != b)
        if differences <= 1:
            return i
    return -1

s = 'ababbababa'
pattern = 'bacaba'
result = almost_equal_index(s, pattern)
print(result)