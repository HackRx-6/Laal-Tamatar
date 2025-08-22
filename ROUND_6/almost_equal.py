def find_almost_equal_index(s, pattern):
    m, n = len(s), len(pattern)
    if n > m:
        return -1
    
    for i in range(m - n + 1):
        substring = s[i:i+n]
        diff_count = 0
        for j in range(n):
            if substring[j] != pattern[j]:
                diff_count += 1
            if diff_count > 1:
                break
        if diff_count <= 1:
            return i
    return -1

s = "abcdefg"
pattern = "bcdffg"
result = find_almost_equal_index(s, pattern)
print(result)