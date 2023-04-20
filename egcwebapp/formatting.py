def break_string(string, goal_length, min_length=None, breaking_chars=" ,"):
    """Breaks a string into pieces of a desired length.

    The function tries to break the string into pieces of length
    `goal_length`, where the break can only happen at one of the
    characters contained in the string `breaking_chars`.

    If there is no such character at the desired breaking position,
    it can take one between the position `min_length` and the
    and `goal_length` of the remaining string.

    If also in that region there is none, then take the first available
    breaking point after position `goal_length` (or leave the remaining string
    unbroken if there are no further breaking characters).

    Args:
        string (str):                   The string to be broken into pieces.
        goal_length (int):              The desired length of the pieces.
        min_length (int):               The minimum length of the pieces.
                                        (default: 90% of `goal_length`)
        breaking_chars (str, optional): The characters at which the string
                                        can be broken (default: " ,").

    Returns:
        list: A list of the broken pieces of the original string.
              The breaking character is included in the piece before the break.

    Examples:
        >>> break_string("This is a very long string that needs a break.", 20)
        ['This is a very long ', 'string that needs a ', 'break.']

        >>> break_string("This is a test string", 10, breaking_chars="-")
        ['This is a test string']
    """
    # Check if string is already shorter than goal length
    if len(string) <= goal_length:
        return [string]

    if min_length is None:
      min_length = int(goal_length * 0.9)

    # Find the first breaking character at the goal length
    if string[goal_length] in breaking_chars:
        return [string[:goal_length+1]] + break_string(string[goal_length+1:],
                goal_length, min_length, breaking_chars)

    # Find the last breaking character before the deviation range
    last_break = -1
    for i in range(min_length, goal_length):
        if i >= 0 and string[i] in breaking_chars:
            last_break = i

    # Find the first breaking character after the goal length
    first_break = -1
    for i in range(goal_length+1, len(string)):
        if string[i] in breaking_chars:
            first_break = i
            break

    # Choose the preferred breaking position based on priority
    if last_break >= 0:
        return [string[:last_break+1]] + break_string(string[last_break+1:],
                goal_length, min_length, breaking_chars)
    elif first_break > 0:
        return [string[:first_break+1]] + break_string(string[first_break+1:],
                goal_length, min_length, breaking_chars)
    else:
        return [string]


