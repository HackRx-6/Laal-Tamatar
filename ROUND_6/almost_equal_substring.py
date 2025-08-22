# Given strings
s = "abcdefg"
pattern = "bcdffg"

# Function to find the smallest starting index of a substring in s that is almost equal to pattern
# A string x is almost equal to y if you can change at most one character in x to make it identical to y.
def find_almost_equal_substring(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    
    for i in range(len_s - len_p + 1):
        # substring of s from i to i + len_p
        substring = s[i:i+len_p]
        
        # count the number of differences
        diff_count = 0
        for j in range(len_p):
            if substring[j] != pattern[j]:
                diff_count += 1
                if diff_count > 1:
                    break
        # if differences are at most one, return the starting index
        if diff_count <= 1:
            return i
    return -1

result = find_almost_equal_substring(s, pattern)
print(result)