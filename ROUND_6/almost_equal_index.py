def smallest_almost_equal_index(s, pattern):
    pattern_len = len(pattern)
    s_len = len(s)

    for i in range(s_len - pattern_len + 1):
        substring = s[i:i + pattern_len]
        # Count the differences between substring and pattern
        diff_count = sum(1 for j in range(pattern_len) if substring[j] != pattern[j])
        if diff_count <= 1:
            return i  # Return the starting index if almost equal
    return -1  # Return -1 if no suitable index is found

# Values based on the question
s = "abcdefg"
pattern = "bcdffg"
result = smallest_almost_equal_index(s, pattern)
result