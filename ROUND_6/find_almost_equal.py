def find_almost_equal_index(s, pattern):
    n, m = len(s), len(pattern)
    for i in range(n - m + 1):
        substring = s[i:i+m]
        diff_count = 0
        for j in range(m):
            if substring[j] != pattern[j]:
                diff_count += 1
                if diff_count > 1:
                    break
        if diff_count <= 1:
            return i
    return -1

s = "ababbababa"
pattern = "bacaba"
result = find_almost_equal_index(s, pattern)
print(result)