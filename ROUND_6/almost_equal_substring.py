def almost_equal_substring_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    
    for i in range(len_s - len_p + 1):
        substring = s[i:i+len_p]
        diff_count = 0
        for a, b in zip(substring, pattern):
            if a != b:
                diff_count += 1
                if diff_count > 1:
                    break
        if diff_count <= 1:
            return i
    return -1

s = "abcdefg"
pattern = "bcdffg"

result = almost_equal_substring_index(s, pattern)
print(result)