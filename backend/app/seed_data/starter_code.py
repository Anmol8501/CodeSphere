"""Builds C++ / Java / Python starter code from one compact signature.

    function("twoSum", [("nums", "int[]"), ("target", "int")], "int[]")

Starter code is stored for the future editor only. It is never executed.
"""

import re

# type -> (C++ parameter, C++ return, Java, Python)
_TYPES: dict[str, tuple[str, str, str, str]] = {
    "int": ("int", "int", "int", "int"),
    "long": ("long long", "long long", "long", "int"),
    "bool": ("bool", "bool", "boolean", "bool"),
    "string": ("string", "string", "String", "str"),
    "void": ("void", "void", "void", "None"),
    "int[]": ("vector<int>&", "vector<int>", "int[]", "List[int]"),
    "char[][]": ("vector<vector<char>>&", "vector<vector<char>>", "char[][]", "List[List[str]]"),
    "ListNode": ("ListNode*", "ListNode*", "ListNode", "Optional[ListNode]"),
    "TreeNode": ("TreeNode*", "TreeNode*", "TreeNode", "Optional[TreeNode]"),
}

_CPP_DEFAULT_RETURN = {"int": "0", "long": "0", "bool": "false", "string": '""', "int[]": "{}", "ListNode": "nullptr", "TreeNode": "nullptr"}
_JAVA_DEFAULT_RETURN = {"int": "0", "long": "0", "bool": "false", "string": '""', "int[]": "new int[0]", "ListNode": "null", "TreeNode": "null"}

_NODE_DOCS = {
    "ListNode": (
        "/**\n * struct ListNode {\n *     int val;\n *     ListNode *next;\n *     ListNode(int x) : val(x), next(nullptr) {}\n * };\n */\n",
        "/**\n * class ListNode {\n *     int val;\n *     ListNode next;\n *     ListNode(int val) { this.val = val; }\n * }\n */\n",
        "# class ListNode:\n#     def __init__(self, val=0, next=None):\n#         self.val = val\n#         self.next = next\n\n",
    ),
    "TreeNode": (
        "/**\n * struct TreeNode {\n *     int val;\n *     TreeNode *left;\n *     TreeNode *right;\n *     TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}\n * };\n */\n",
        "/**\n * class TreeNode {\n *     int val;\n *     TreeNode left;\n *     TreeNode right;\n *     TreeNode(int val) { this.val = val; }\n * }\n */\n",
        "# class TreeNode:\n#     def __init__(self, val=0, left=None, right=None):\n#         self.val = val\n#         self.left = left\n#         self.right = right\n\n",
    ),
}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _node_docs(types: list[str]) -> tuple[str, str, str]:
    for node in ("ListNode", "TreeNode"):
        if node in types:
            return _NODE_DOCS[node]
    return ("", "", "")


def function(name: str, params: list[tuple[str, str]], returns: str) -> dict[str, str]:
    """Starter code for a LeetCode-style `class Solution` method."""
    cpp_doc, java_doc, py_doc = _node_docs([t for _, t in params] + [returns])

    cpp_args = ", ".join(f"{_TYPES[t][0]} {p}" for p, t in params)
    cpp_ret = f"\n        return {_CPP_DEFAULT_RETURN[returns]};" if returns != "void" else ""
    cpp = (
        f"{cpp_doc}class Solution {{\npublic:\n    {_TYPES[returns][1]} {name}({cpp_args}) {{\n"
        f"        // Write your solution here{cpp_ret}\n    }}\n}};\n"
    )

    java_args = ", ".join(f"{_TYPES[t][2]} {p}" for p, t in params)
    java_ret = f"\n        return {_JAVA_DEFAULT_RETURN[returns]};" if returns != "void" else ""
    java = (
        f"{java_doc}class Solution {{\n    public {_TYPES[returns][2]} {name}({java_args}) {{\n"
        f"        // Write your solution here{java_ret}\n    }}\n}}\n"
    )

    py_args = "".join(f", {_snake(p)}: {_TYPES[t][3]}" for p, t in params)
    python = (
        f"from typing import List, Optional\n\n{py_doc}class Solution:\n"
        f"    def {_snake(name)}(self{py_args}) -> {_TYPES[returns][3]}:\n"
        f"        # Write your solution here\n        pass\n"
    )
    return {"CPP": cpp, "JAVA": java, "PYTHON": python}


def program() -> dict[str, str]:
    """Starter code for a full program that reads stdin and writes stdout."""
    return {
        "CPP": (
            "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n"
            "    // Read input from stdin and print the answer to stdout\n    return 0;\n}\n"
        ),
        "JAVA": (
            "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n        // Read input and print the answer\n    }\n}\n"
        ),
        "PYTHON": (
            "def main():\n    # Read input with input() and print the answer\n    pass\n\n\n"
            'if __name__ == "__main__":\n    main()\n'
        ),
    }


def queue_design() -> dict[str, str]:
    return {
        "CPP": (
            "class MyQueue {\npublic:\n    MyQueue() {\n    }\n\n    void push(int x) {\n    }\n\n"
            "    int pop() {\n        return 0;\n    }\n\n    int peek() {\n        return 0;\n    }\n\n"
            "    bool empty() {\n        return true;\n    }\n};\n"
        ),
        "JAVA": (
            "class MyQueue {\n    public MyQueue() {\n    }\n\n    public void push(int x) {\n    }\n\n"
            "    public int pop() {\n        return 0;\n    }\n\n    public int peek() {\n        return 0;\n    }\n\n"
            "    public boolean empty() {\n        return true;\n    }\n}\n"
        ),
        "PYTHON": (
            "class MyQueue:\n    def __init__(self):\n        pass\n\n    def push(self, x: int) -> None:\n        pass\n\n"
            "    def pop(self) -> int:\n        pass\n\n    def peek(self) -> int:\n        pass\n\n"
            "    def empty(self) -> bool:\n        pass\n"
        ),
    }
