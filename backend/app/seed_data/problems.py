"""Starter problem set (original statements written for CodeArena).

Test case `input_data` follows each problem's Input Format (stdin text), so the
future judge can feed it directly. The first test case of each problem is a
visible sample; the rest are hidden.
"""

from app.seed_data.harness import function_driver, merge_sorted_array_driver, queue_design_driver
from app.seed_data.starter_code import function, program, queue_design


def solve(name: str, params: list[tuple[str, str]], returns: str, **driver_options) -> dict:
    """Visible starter code + hidden harness generated from one signature."""
    return {
        "starter": function(name, params, returns),
        "driver": function_driver(name, params, returns, **driver_options),
    }


def _cases(*pairs: tuple[str, str]) -> list[dict]:
    return [
        {"input_data": inp, "expected_output": out, "is_hidden": i > 0}
        for i, (inp, out) in enumerate(pairs)
    ]


ARRAY_INPUT = "The first line contains an integer `n`.\nThe second line contains `n` space-separated integers."
LIST_INPUT = "The first line contains `n`, the number of nodes.\nThe second line contains `n` space-separated node values from head to tail."
TREE_INPUT = "A single line with the tree in level order, using `null` for a missing child. An empty line means an empty tree."

PROBLEMS: list[dict] = [
    # ---------------------------------------------------------------- basics
    {
        "slug": "hello-world",
        "title": "Hello World",
        "topic": "programming-basics",
        "difficulty": "EASY",
        "tags": ["Implementation"],
        "description": (
            "Every programming journey starts with a single line of output.\n\n"
            "Write a program that prints exactly `Hello, World!` to standard output.\n\n"
            "Pay attention to the capital letters, the comma and the exclamation mark: the output must match character for character."
        ),
        "constraints": "There is no input.",
        "input_format": "No input is given.",
        "output_format": "Print `Hello, World!` on a single line.",
        "examples": [{"input": "(no input)", "output": "Hello, World!", "explanation": "The program ignores input and prints the greeting."}],
        "starter": program(),
        "test_cases": _cases(("", "Hello, World!")),
    },
    {
        "slug": "sum-of-two-numbers",
        "title": "Sum of Two Numbers",
        "topic": "programming-basics",
        "difficulty": "EASY",
        "tags": ["Math", "Implementation"],
        "description": (
            "Read two integers `a` and `b` and print their sum.\n\n"
            "The values can be large, so think about which data type can hold the result without overflowing."
        ),
        "constraints": "-10^9 ≤ a, b ≤ 10^9",
        "input_format": "A single line containing two space-separated integers `a` and `b`.",
        "output_format": "Print the value of `a + b`.",
        "examples": [
            {"input": "3 5", "output": "8", "explanation": "3 + 5 = 8."},
            {"input": "-4 10", "output": "6", "explanation": None},
        ],
        "starter": program(),
        "test_cases": _cases(("3 5", "8"), ("-4 10", "6"), ("1000000000 1000000000", "2000000000"), ("0 0", "0")),
    },
    # ---------------------------------------------------------------- arrays
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "topic": "arrays",
        "difficulty": "EASY",
        "tags": ["Array", "HashMap"],
        "description": (
            "You are given an array of integers `nums` and an integer `target`.\n\n"
            "Find two **different** positions `i` and `j` such that `nums[i] + nums[j] == target`, "
            "and return them as `[i, j]` with `i < j`.\n\n"
            "Every input has exactly one valid pair, and the same element cannot be used twice.\n\n"
            "A double loop works, but can you do it in a single pass by remembering the values you have already seen?"
        ),
        "constraints": "2 ≤ n ≤ 10^4\n-10^9 ≤ nums[i] ≤ 10^9\n-10^9 ≤ target ≤ 10^9\nExactly one valid answer exists.",
        "input_format": ARRAY_INPUT + "\nThe third line contains the integer `target`.",
        "output_format": "Print the two indices `i j` (with `i < j`) separated by a space.",
        "examples": [
            {"input": "nums = [2, 7, 11, 15]\ntarget = 9", "output": "[0, 1]", "explanation": "nums[0] + nums[1] = 2 + 7 = 9."},
            {"input": "nums = [3, 2, 4]\ntarget = 6", "output": "[1, 2]", "explanation": "nums[1] + nums[2] = 2 + 4 = 6."},
        ],
        **solve("twoSum", [("nums", "int[]"), ("target", "int")], "int[]"),
        "test_cases": _cases(
            ("4\n2 7 11 15\n9", "0 1"),
            ("3\n3 2 4\n6", "1 2"),
            ("2\n3 3\n6", "0 1"),
            ("5\n-1 -2 -3 -4 -5\n-8", "2 4"),
        ),
    },
    {
        "slug": "maximum-element-in-array",
        "title": "Maximum Element in Array",
        "topic": "arrays",
        "difficulty": "EASY",
        "tags": ["Array"],
        "description": (
            "Given an array of integers `nums`, return the largest value it contains.\n\n"
            "Solve it with a single pass over the array, without sorting."
        ),
        "constraints": "1 ≤ n ≤ 10^5\n-10^9 ≤ nums[i] ≤ 10^9",
        "input_format": ARRAY_INPUT,
        "output_format": "Print the maximum element.",
        "examples": [
            {"input": "nums = [3, 9, 2, 7, 4]", "output": "9", "explanation": "9 is larger than every other element."},
            {"input": "nums = [-5, -1, -9]", "output": "-1", "explanation": "All values are negative; -1 is the largest."},
        ],
        **solve("findMax", [("nums", "int[]")], "int"),
        "test_cases": _cases(("5\n3 9 2 7 4", "9"), ("3\n-5 -1 -9", "-1"), ("1\n42", "42"), ("4\n6 6 6 6", "6")),
    },
    {
        "slug": "best-time-to-buy-and-sell-stock",
        "title": "Best Time to Buy and Sell Stock",
        "topic": "arrays",
        "difficulty": "EASY",
        "tags": ["Array", "Greedy"],
        "description": (
            "`prices[i]` is the price of a stock on day `i`.\n\n"
            "You may buy one share on some day and sell it on a **later** day. "
            "Return the maximum profit you can make. If no profitable trade exists, return `0`.\n\n"
            "Hint: while scanning the days, keep track of the cheapest price seen so far."
        ),
        "constraints": "1 ≤ n ≤ 10^5\n0 ≤ prices[i] ≤ 10^4",
        "input_format": ARRAY_INPUT,
        "output_format": "Print the maximum profit.",
        "examples": [
            {"input": "prices = [7, 1, 5, 3, 6, 4]", "output": "5", "explanation": "Buy on day 1 (price 1) and sell on day 4 (price 6): 6 - 1 = 5."},
            {"input": "prices = [7, 6, 4, 3, 1]", "output": "0", "explanation": "Prices only fall, so the best choice is not to trade."},
        ],
        **solve("maxProfit", [("prices", "int[]")], "int"),
        "test_cases": _cases(("6\n7 1 5 3 6 4", "5"), ("5\n7 6 4 3 1", "0"), ("2\n1 2", "1"), ("7\n3 3 5 0 0 3 1", "3")),
    },
    {
        "slug": "maximum-subarray",
        "title": "Maximum Subarray",
        "topic": "arrays",
        "difficulty": "MEDIUM",
        "tags": ["Array", "DP"],
        "description": (
            "Given an integer array `nums`, find the contiguous, non-empty subarray with the largest sum and return that sum.\n\n"
            "Think about this question at every index: is it better to extend the previous subarray, or to start fresh here?"
        ),
        "constraints": "1 ≤ n ≤ 10^5\n-10^4 ≤ nums[i] ≤ 10^4",
        "input_format": ARRAY_INPUT,
        "output_format": "Print the largest subarray sum.",
        "examples": [
            {"input": "nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]", "output": "6", "explanation": "The subarray [4, -1, 2, 1] has the largest sum, 6."},
            {"input": "nums = [-3, -1, -2]", "output": "-1", "explanation": "The subarray must be non-empty, so the answer is the single element -1."},
        ],
        **solve("maxSubArray", [("nums", "int[]")], "int"),
        "test_cases": _cases(
            ("9\n-2 1 -3 4 -1 2 1 -5 4", "6"),
            ("1\n1", "1"),
            ("5\n5 4 -1 7 8", "23"),
            ("3\n-3 -1 -2", "-1"),
        ),
    },
    {
        "slug": "trapping-rain-water",
        "title": "Trapping Rain Water",
        "topic": "arrays",
        "difficulty": "HARD",
        "tags": ["Array", "Two Pointer", "Stack"],
        "description": (
            "`height[i]` is the height of a bar of width 1 in an elevation map.\n\n"
            "After it rains, water collects in the dips between bars. Compute how many units of water are trapped.\n\n"
            "The water above a bar is limited by the **shorter** of the tallest bars to its left and to its right."
        ),
        "constraints": "1 ≤ n ≤ 2 × 10^4\n0 ≤ height[i] ≤ 10^5",
        "input_format": ARRAY_INPUT,
        "output_format": "Print the total units of trapped water.",
        "examples": [
            {"input": "height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]", "output": "6", "explanation": "Six units of water fit in the gaps between the bars."},
            {"input": "height = [4, 2, 0, 3, 2, 5]", "output": "9", "explanation": None},
        ],
        **solve("trap", [("height", "int[]")], "int"),
        "test_cases": _cases(
            ("12\n0 1 0 2 1 0 1 3 2 1 2 1", "6"),
            ("6\n4 2 0 3 2 5", "9"),
            ("3\n1 2 3", "0"),
            ("5\n5 0 0 0 5", "15"),
        ),
    },
    # ---------------------------------------------------------------- strings
    {
        "slug": "valid-palindrome",
        "title": "Valid Palindrome",
        "topic": "strings",
        "difficulty": "EASY",
        "tags": ["String", "Two Pointer"],
        "description": (
            "A phrase is a palindrome if it reads the same forwards and backwards after you:\n\n"
            "- convert all uppercase letters to lowercase, and\n"
            "- remove every character that is not a letter or a digit.\n\n"
            "Given a string `s`, return `true` if it is a palindrome and `false` otherwise. "
            "An empty string (after cleaning) counts as a palindrome."
        ),
        "constraints": "1 ≤ length of s ≤ 2 × 10^5\n`s` contains printable ASCII characters.",
        "input_format": "A single line containing the string `s`.",
        "output_format": "Print `true` or `false`.",
        "examples": [
            {"input": 's = "A man, a plan, a canal: Panama"', "output": "true", "explanation": 'After cleaning it becomes "amanaplanacanalpanama", which is a palindrome.'},
            {"input": 's = "race a car"', "output": "false", "explanation": '"raceacar" is not the same reversed.'},
        ],
        **solve("isPalindrome", [("s", "string")], "bool", mode="lines"),
        "test_cases": _cases(("A man, a plan, a canal: Panama", "true"), ("race a car", "false"), (" ", "true"), ("0P", "false")),
    },
    {
        "slug": "valid-anagram",
        "title": "Valid Anagram",
        "topic": "strings",
        "difficulty": "EASY",
        "tags": ["String", "HashMap", "Sorting"],
        "description": (
            "Two strings are anagrams if one can be formed by rearranging all the letters of the other, using each letter exactly once.\n\n"
            "Given strings `s` and `t`, return `true` if `t` is an anagram of `s`, otherwise `false`."
        ),
        "constraints": "1 ≤ length of s, t ≤ 5 × 10^4\n`s` and `t` contain lowercase English letters only.",
        "input_format": "The first line contains `s`.\nThe second line contains `t`.",
        "output_format": "Print `true` or `false`.",
        "examples": [
            {"input": 's = "listen"\nt = "silent"', "output": "true", "explanation": "Both words use the same letters with the same counts."},
            {"input": 's = "rat"\nt = "car"', "output": "false", "explanation": None},
        ],
        **solve("isAnagram", [("s", "string"), ("t", "string")], "bool", mode="lines"),
        "test_cases": _cases(("anagram\nnagaram", "true"), ("rat\ncar", "false"), ("a\nab", "false"), ("listen\nsilent", "true")),
    },
    # ---------------------------------------------------------------- searching
    {
        "slug": "binary-search",
        "title": "Binary Search",
        "topic": "searching",
        "difficulty": "EASY",
        "tags": ["Array", "Binary Search"],
        "description": (
            "You are given an array `nums` of **distinct** integers sorted in increasing order, and a value `target`.\n\n"
            "Return the index of `target` in `nums`, or `-1` if it is not present.\n\n"
            "Your solution should run in O(log n) time by halving the search range at every step."
        ),
        "constraints": "1 ≤ n ≤ 10^4\n-10^4 ≤ nums[i], target ≤ 10^4\nAll values in `nums` are distinct and sorted ascending.",
        "input_format": ARRAY_INPUT + "\nThe third line contains `target`.",
        "output_format": "Print the index of `target`, or `-1`.",
        "examples": [
            {"input": "nums = [-1, 0, 3, 5, 9, 12]\ntarget = 9", "output": "4", "explanation": "9 is at index 4."},
            {"input": "nums = [-1, 0, 3, 5, 9, 12]\ntarget = 2", "output": "-1", "explanation": "2 does not appear in the array."},
        ],
        **solve("search", [("nums", "int[]"), ("target", "int")], "int"),
        "test_cases": _cases(
            ("6\n-1 0 3 5 9 12\n9", "4"),
            ("6\n-1 0 3 5 9 12\n2", "-1"),
            ("1\n5\n5", "0"),
            ("5\n1 3 5 7 9\n1", "0"),
        ),
    },
    {
        "slug": "first-and-last-position",
        "title": "First and Last Position",
        "topic": "searching",
        "difficulty": "MEDIUM",
        "tags": ["Array", "Binary Search"],
        "description": (
            "Given an array `nums` sorted in non-decreasing order (values may repeat) and a `target`, "
            "find the first and last index where `target` appears.\n\n"
            "Return `[-1, -1]` if `target` is not in the array.\n\n"
            "Aim for O(log n): run binary search twice, once for the left boundary and once for the right."
        ),
        "constraints": "0 ≤ n ≤ 10^5\n-10^9 ≤ nums[i], target ≤ 10^9\n`nums` is sorted in non-decreasing order.",
        "input_format": ARRAY_INPUT + " (empty when `n` is 0)\nThe third line contains `target`.",
        "output_format": "Print the first and last index separated by a space, or `-1 -1`.",
        "examples": [
            {"input": "nums = [5, 7, 7, 8, 8, 10]\ntarget = 8", "output": "[3, 4]", "explanation": "8 first appears at index 3 and last at index 4."},
            {"input": "nums = [5, 7, 7, 8, 8, 10]\ntarget = 6", "output": "[-1, -1]", "explanation": None},
        ],
        **solve("searchRange", [("nums", "int[]"), ("target", "int")], "int[]"),
        "test_cases": _cases(
            ("6\n5 7 7 8 8 10\n8", "3 4"),
            ("6\n5 7 7 8 8 10\n6", "-1 -1"),
            ("0\n\n0", "-1 -1"),
            ("5\n2 2 2 2 2\n2", "0 4"),
        ),
    },
    # ---------------------------------------------------------------- sorting
    {
        "slug": "sort-colors",
        "title": "Sort Colors",
        "topic": "sorting",
        "difficulty": "MEDIUM",
        "tags": ["Array", "Two Pointer", "Sorting"],
        "description": (
            "An array `nums` contains only the values `0`, `1` and `2`, representing three colors.\n\n"
            "Sort the array **in place** so that all `0`s come first, then all `1`s, then all `2`s. "
            "Do not use a library sort.\n\n"
            "Challenge: can you do it in one pass using three pointers?"
        ),
        "constraints": "1 ≤ n ≤ 300\n`nums[i]` is 0, 1 or 2.",
        "input_format": ARRAY_INPUT,
        "output_format": "Print the sorted array as space-separated integers.",
        "examples": [
            {"input": "nums = [2, 0, 2, 1, 1, 0]", "output": "[0, 0, 1, 1, 2, 2]", "explanation": None},
            {"input": "nums = [2, 0, 1]", "output": "[0, 1, 2]", "explanation": None},
        ],
        **solve("sortColors", [("nums", "int[]")], "void", print_arg="nums"),
        "test_cases": _cases(("6\n2 0 2 1 1 0", "0 0 1 1 2 2"), ("3\n2 0 1", "0 1 2"), ("1\n0", "0"), ("5\n1 1 1 0 2", "0 1 1 1 2")),
    },
    {
        "slug": "merge-sorted-array",
        "title": "Merge Sorted Array",
        "topic": "sorting",
        "difficulty": "EASY",
        "tags": ["Array", "Two Pointer", "Sorting"],
        "description": (
            "You have two sorted arrays. `nums1` holds `m` sorted values followed by `n` empty slots, "
            "and `nums2` holds `n` sorted values.\n\n"
            "Merge `nums2` into `nums1` so that `nums1` becomes one sorted array of length `m + n`.\n\n"
            "Tip: filling `nums1` from the back avoids overwriting values you still need."
        ),
        "constraints": "0 ≤ m, n ≤ 200\n1 ≤ m + n ≤ 200\n-10^9 ≤ values ≤ 10^9",
        "input_format": "The first line contains `m` and `n`.\nThe second line contains the `m` values of `nums1`.\nThe third line contains the `n` values of `nums2`.",
        "output_format": "Print the merged array as space-separated integers.",
        "examples": [
            {"input": "nums1 = [1, 2, 3, _, _, _], m = 3\nnums2 = [2, 5, 6], n = 3", "output": "[1, 2, 2, 3, 5, 6]", "explanation": None},
        ],
        "starter": function("merge", [("nums1", "int[]"), ("m", "int"), ("nums2", "int[]"), ("n", "int")], "void"),
        "driver": merge_sorted_array_driver(),
        "test_cases": _cases(
            ("3 3\n1 2 3\n2 5 6", "1 2 2 3 5 6"),
            ("1 0\n1\n", "1"),
            ("0 1\n\n1", "1"),
            ("4 2\n-3 0 0 7\n-5 8", "-5 -3 0 0 7 8"),
        ),
    },
    # ---------------------------------------------------------------- linked list
    {
        "slug": "reverse-linked-list",
        "title": "Reverse Linked List",
        "topic": "linked-list",
        "difficulty": "EASY",
        "tags": ["Linked List", "Recursion"],
        "description": (
            "Given the `head` of a singly linked list, reverse the direction of every link and return the new head.\n\n"
            "Try it both ways: iteratively with three pointers (`prev`, `current`, `next`) and recursively."
        ),
        "constraints": "1 ≤ number of nodes ≤ 5000\n-5000 ≤ node value ≤ 5000",
        "input_format": LIST_INPUT,
        "output_format": "Print the reversed list's values from head to tail.",
        "examples": [
            {"input": "head = 1 → 2 → 3 → 4 → 5", "output": "5 → 4 → 3 → 2 → 1", "explanation": None},
            {"input": "head = 1 → 2", "output": "2 → 1", "explanation": None},
        ],
        **solve("reverseList", [("head", "ListNode")], "ListNode"),
        "test_cases": _cases(("5\n1 2 3 4 5", "5 4 3 2 1"), ("2\n1 2", "2 1"), ("1\n7", "7")),
    },
    {
        "slug": "middle-of-linked-list",
        "title": "Middle of Linked List",
        "topic": "linked-list",
        "difficulty": "EASY",
        "tags": ["Linked List", "Two Pointer"],
        "description": (
            "Given the `head` of a singly linked list, return its middle node. "
            "If the list has two middle nodes, return the **second** one.\n\n"
            "Can you find it in one pass? Move one pointer one step at a time and another two steps at a time."
        ),
        "constraints": "1 ≤ number of nodes ≤ 100\n1 ≤ node value ≤ 100",
        "input_format": LIST_INPUT,
        "output_format": "Print the values from the middle node to the tail.",
        "examples": [
            {"input": "head = 1 → 2 → 3 → 4 → 5", "output": "3 → 4 → 5", "explanation": "The middle node is 3."},
            {"input": "head = 1 → 2 → 3 → 4 → 5 → 6", "output": "4 → 5 → 6", "explanation": "There are two middle nodes (3 and 4); return the second."},
        ],
        **solve("middleNode", [("head", "ListNode")], "ListNode"),
        "test_cases": _cases(("5\n1 2 3 4 5", "3 4 5"), ("6\n1 2 3 4 5 6", "4 5 6"), ("1\n1", "1")),
    },
    # ---------------------------------------------------------------- stack
    {
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "topic": "stack",
        "difficulty": "EASY",
        "tags": ["String", "Stack"],
        "description": (
            "A string `s` contains only the bracket characters `(`, `)`, `[`, `]`, `{` and `}`.\n\n"
            "It is **valid** when every opening bracket is closed by the same type of bracket, "
            "and brackets are closed in the correct order.\n\n"
            "Return `true` if `s` is valid, otherwise `false`."
        ),
        "constraints": "1 ≤ length of s ≤ 10^4\n`s` contains only `()[]{}`.",
        "input_format": "A single line containing `s`.",
        "output_format": "Print `true` or `false`.",
        "examples": [
            {"input": 's = "{[]}"', "output": "true", "explanation": "Each opening bracket is closed in the right order."},
            {"input": 's = "([)]"', "output": "false", "explanation": "The `[` is closed by `)` before its own `]`."},
        ],
        **solve("isValid", [("s", "string")], "bool", mode="lines"),
        "test_cases": _cases(("()", "true"), ("()[]{}", "true"), ("(]", "false"), ("([)]", "false"), ("{[]}", "true")),
    },
    # ---------------------------------------------------------------- queue
    {
        "slug": "implement-queue-using-stacks",
        "title": "Implement Queue using Stacks",
        "topic": "queue",
        "difficulty": "EASY",
        "tags": ["Stack", "Queue", "Design"],
        "description": (
            "Build a first-in, first-out queue using **only two stacks** and their standard operations "
            "(push to top, pop from top, peek at top, size, is empty).\n\n"
            "Implement the `MyQueue` class:\n\n"
            "- `push(x)`: add `x` to the back of the queue\n"
            "- `pop()`: remove and return the front element\n"
            "- `peek()`: return the front element without removing it\n"
            "- `empty()`: return whether the queue is empty\n\n"
            "Every `pop` and `peek` call is made on a non-empty queue. Can each operation be O(1) amortized?"
        ),
        "constraints": "1 ≤ x ≤ 9\nAt most 100 operations are performed.",
        "input_format": "The first line contains `q`, the number of operations.\nEach of the next `q` lines is `push x`, `pop`, `peek` or `empty`.",
        "output_format": "For every `pop`, `peek` and `empty` operation, print its result on its own line.",
        "examples": [
            {"input": "push 1\npush 2\npeek\npop\nempty", "output": "1\n1\nfalse", "explanation": "peek returns 1, pop removes 1, and the queue still holds 2."},
        ],
        "starter": queue_design(),
        "driver": queue_design_driver(),
        "test_cases": _cases(
            ("5\npush 1\npush 2\npeek\npop\nempty", "1\n1\nfalse"),
            ("6\npush 5\npop\nempty\npush 3\npush 4\npeek", "5\ntrue\n3"),
        ),
    },
    # ---------------------------------------------------------------- trees
    {
        "slug": "maximum-depth-of-binary-tree",
        "title": "Maximum Depth of Binary Tree",
        "topic": "trees",
        "difficulty": "EASY",
        "tags": ["Tree", "DFS", "BFS", "Recursion"],
        "description": (
            "The depth of a binary tree is the number of nodes on the longest path from the root down to a leaf.\n\n"
            "Given the `root` of a binary tree, return its depth. An empty tree has depth `0`.\n\n"
            "Solve it recursively (depth = 1 + the deeper subtree), then try a level-by-level BFS."
        ),
        "constraints": "0 ≤ number of nodes ≤ 10^4\n-100 ≤ node value ≤ 100",
        "input_format": TREE_INPUT,
        "output_format": "Print the maximum depth.",
        "examples": [
            {"input": "root = [3, 9, 20, null, null, 15, 7]", "output": "3", "explanation": "The longest path is 3 → 20 → 15 (or 3 → 20 → 7)."},
            {"input": "root = [1, null, 2]", "output": "2", "explanation": None},
        ],
        **solve("maxDepth", [("root", "TreeNode")], "int", mode="lines"),
        "test_cases": _cases(
            ("3 9 20 null null 15 7", "3"),
            ("1 null 2", "2"),
            ("", "0"),
            ("1 2 null 3 null 4", "4"),
        ),
    },
    {
        "slug": "binary-tree-inorder-traversal",
        "title": "Inorder Traversal",
        "topic": "trees",
        "difficulty": "EASY",
        "tags": ["Tree", "DFS", "Stack"],
        "description": (
            "Inorder traversal visits a binary tree in this order: the left subtree, then the node itself, then the right subtree.\n\n"
            "Given the `root` of a binary tree, return the values in inorder.\n\n"
            "The recursive solution is short. Can you also do it iteratively with an explicit stack?"
        ),
        "constraints": "1 ≤ number of nodes ≤ 100\n-100 ≤ node value ≤ 100",
        "input_format": TREE_INPUT,
        "output_format": "Print the inorder values separated by spaces.",
        "examples": [
            {"input": "root = [1, null, 2, 3]", "output": "[1, 3, 2]", "explanation": "Node 1 has no left child, so 1 is visited first; then the subtree rooted at 2 gives 3, 2."},
            {"input": "root = [4, 2, 6, 1, 3, 5, 7]", "output": "[1, 2, 3, 4, 5, 6, 7]", "explanation": None},
        ],
        **solve("inorderTraversal", [("root", "TreeNode")], "int[]", mode="lines"),
        "test_cases": _cases(("1 null 2 3", "1 3 2"), ("1", "1"), ("4 2 6 1 3 5 7", "1 2 3 4 5 6 7")),
    },
    # ---------------------------------------------------------------- graphs
    {
        "slug": "number-of-islands",
        "title": "Number of Islands",
        "topic": "graphs",
        "difficulty": "MEDIUM",
        "tags": ["Graph", "DFS", "BFS", "Matrix"],
        "description": (
            "You are given a 2D grid of `'1'` (land) and `'0'` (water).\n\n"
            "An **island** is a group of land cells connected horizontally or vertically (not diagonally). "
            "Everything outside the grid is water.\n\n"
            "Return the number of islands. Each time you find unvisited land, explore its whole island with DFS or BFS and count it once."
        ),
        "constraints": "1 ≤ rows, cols ≤ 300\n`grid[i][j]` is `'0'` or `'1'`.",
        "input_format": "The first line contains `rows` and `cols`.\nEach of the next `rows` lines contains a string of `cols` characters (`0` or `1`).",
        "output_format": "Print the number of islands.",
        "examples": [
            {"input": "grid =\n11110\n11010\n11000\n00000", "output": "1", "explanation": "All land cells are connected into one island."},
            {"input": "grid =\n11000\n11000\n00100\n00011", "output": "3", "explanation": None},
        ],
        **solve("numIslands", [("grid", "char[][]")], "int"),
        "test_cases": _cases(
            ("4 5\n11110\n11010\n11000\n00000", "1"),
            ("4 5\n11000\n11000\n00100\n00011", "3"),
            ("1 1\n0", "0"),
            ("3 3\n101\n010\n101", "5"),
        ),
    },
    # ---------------------------------------------------------------- dp
    {
        "slug": "climbing-stairs",
        "title": "Climbing Stairs",
        "topic": "dynamic-programming",
        "difficulty": "EASY",
        "tags": ["DP", "Math", "Recursion"],
        "description": (
            "A staircase has `n` steps. Each move, you climb either **1** or **2** steps.\n\n"
            "In how many distinct ways can you reach the top?\n\n"
            "Notice that the last move is either a 1-step or a 2-step, so `ways(n) = ways(n - 1) + ways(n - 2)`. "
            "Avoid recomputing the same values."
        ),
        "constraints": "1 ≤ n ≤ 45",
        "input_format": "A single integer `n`.",
        "output_format": "Print the number of distinct ways.",
        "examples": [
            {"input": "n = 2", "output": "2", "explanation": "1 + 1, or 2."},
            {"input": "n = 3", "output": "3", "explanation": "1 + 1 + 1, 1 + 2, or 2 + 1."},
        ],
        **solve("climbStairs", [("n", "int")], "int"),
        "test_cases": _cases(("2", "2"), ("3", "3"), ("1", "1"), ("10", "89"), ("45", "1836311903")),
    },
]
