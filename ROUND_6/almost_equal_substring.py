def find_almost_equal_substring(s: str, pattern: str) -> int:
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


if __name__ == "__main__":
    s = "abcdefg"
    pattern = "bcdffg"
    result = find_almost_equal_substring(s, pattern)
    print(result)
    
    # For automated response, output in a fixed format
    # so that the handler can parse the output
    # e.g. RESULT: <index>
    print(f"RESULT: {result}")
