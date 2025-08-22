def smallest_almost_equal_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    # Iterate through all possible starting indices
    for start in range(len_s - len_p + 1):
        substring = s[start:start + len_p]
        # Check how many characters differ
        diff_count = sum(1 for a, b in zip(substring, pattern) if a != b)
        if diff_count <= 1:
            return start
    return -1

# Example data
s1 = 'abcdefg'
pattern1 = 'bcdffg'
result1 = smallest_almost_equal_index(s1, pattern1)

s2 = 'ababbababa'
pattern2 = 'bacaba'
result2 = smallest_almost_equal_index(s2, pattern2)

result1, result2
