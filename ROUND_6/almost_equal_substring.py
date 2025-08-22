def almost_equal_substring(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    
    for i in range(len_s - len_p + 1):
        substring = s[i:i+len_p]
        # Count the differences
        diff = sum(1 for x, y in zip(substring, pattern) if x != y)
        if diff <= 1:
            return i
    return -1

s = "abcdefg"
pattern = "bcdffg"

result = almost_equal_substring(s, pattern)
print(result)