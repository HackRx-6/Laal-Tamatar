def smallest_almost_equal_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    
    for i in range(len_s - len_p + 1):
        substring = s[i:i+len_p]
        # Count the differences
        diff_count = sum(1 for x, y in zip(substring, pattern) if x != y)
        if diff_count <= 1:
            return i
    return -1

s = "ababbababa"
pattern = "bacaba"

result = smallest_almost_equal_index(s, pattern)
print(result)  # This will print the output to be captured
