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
def find_almost_equal(s, pattern):
    n = len(s)
    m = len(pattern)
    for i in range(n - m + 1):
        substring = s[i:i+m]
        # Count differences
        diff_count = sum(1 for x, y in zip(substring, pattern) if x != y)
        if diff_count <= 1:
            return i
    return -1

# Given values
s = "abcdefg"
pattern = "bcdffg"

result = smallest_almost_equal_index(s, pattern)
print(result)
if __name__ == "__main__":
    s = "ababbababa"
    pattern = "bacaba"
    result = find_almost_equal(s, pattern)
    print(result)