def smallest_almost_equal_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    
    # Function to check if two strings are almost equal
    def almost_equal(x, y):
        diff_count = 0
        for a, b in zip(x, y):
            if a != b:
                diff_count += 1
            if diff_count > 1:
                return False
        return True
    
    # Iterate through the string s to find the smallest starting index
    for i in range(len_s - len_p + 1):
        if almost_equal(s[i:i+len_p], pattern):
            return i
    return -1

# Given values
s = "abcdefg"
pattern = "bcdffg"

result = smallest_almost_equal_index(s, pattern)
print(result)