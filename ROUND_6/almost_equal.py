def smallest_almost_equal_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)

    for i in range(len_s - len_p + 1):
        substring = s[i:i + len_p]
        # Count differences
        diff_count = sum(1 for x, y in zip(substring, pattern) if x != y)
        if diff_count <= 1:
            return i
    return -1

# Example inputs
s1 = 'abcdefg'
pattern1 = 'bcdffg'
result1 = smallest_almost_equal_index(s1, pattern1)

s2 = 'ababbababa'
pattern2 = 'bacaba'
result2 = smallest_almost_equal_index(s2, pattern2)

result1, result2
