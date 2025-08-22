def almost_equal_index(s, pattern):
    m, n = len(s), len(pattern)
    if n > m:
        return -1
    
    for i in range(m - n + 1):
        substring = s[i:i+n]
        diff_count = 0
        for a, b in zip(substring, pattern):
            if a != b:
                diff_count += 1
                if diff_count > 1:
                    break
        if diff_count <= 1:
            return i
    return -1

# Given values
s = "ababbababa"
pattern = "bacaba"

# Get the result
result = almost_equal_index(s, pattern)
print(result)