def find_almost_equal_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    
    for i in range(len_s - len_p + 1):
        substring = s[i:i+len_p]
        diff_count = 0
        for j in range(len_p):
            if substring[j] != pattern[j]:
                diff_count += 1
            if diff_count > 1:
                break
        if diff_count <= 1:
            return i
    return -1

# Given values
s = "ababbababa"
pattern = "bacaba"

result = find_almost_equal_index(s, pattern)
print(result)