"""Hidden execution harnesses ("drivers") for the seeded function-style problems.

A driver is a complete program with the line {{USER_CODE}} where the student's
`class Solution` is inserted. It parses stdin in the problem's Input Format,
calls the student's method and prints the result in the Output Format. Drivers
are stored in starter_codes.driver_code and are never shown to students.

    function_driver("twoSum", [("nums", "int[]"), ("target", "int")], "int[]")

Input conventions (they match the seeded test data):
  tokens mode  int / long: one token;  int[]: n then n values;
               char[][]: rows cols then one string per row;  ListNode: n then n values
  lines mode   string: one whole line (spaces kept);  TreeNode: one level-order
               line with "null" for missing children (empty line = empty tree)
Output: int/long as-is, bool as true/false, int[] / ListNode as space-separated
values; a void method prints its in-place argument (`print_arg`).
"""

import re

MARKER = "{{USER_CODE}}"


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# ------------------------------------------------------------------ C++
_CPP_NODES = {
    "ListNode": """struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};
""",
    "TreeNode": """struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};
""",
}

_CPP_HELPERS = {
    "int[]": """static vector<int> ca_readIntArray() {
    int n = 0;
    cin >> n;
    vector<int> values(n);
    for (int &x : values) cin >> x;
    return values;
}
""",
    "char[][]": """static vector<vector<char>> ca_readGrid() {
    int rows = 0, cols = 0;
    cin >> rows >> cols;
    vector<vector<char>> grid(rows);
    for (int i = 0; i < rows; i++) {
        string row;
        cin >> row;
        grid[i] = vector<char>(row.begin(), row.end());
    }
    return grid;
}
""",
    "ListNode": """static ListNode* ca_readList() {
    int n = 0;
    cin >> n;
    ListNode dummy;
    ListNode *tail = &dummy;
    for (int i = 0; i < n; i++) {
        int v;
        cin >> v;
        tail->next = new ListNode(v);
        tail = tail->next;
    }
    return dummy.next;
}
""",
    "string": """static string ca_readLine() {
    string line;
    if (!getline(cin, line)) return "";
    if (!line.empty() && line.back() == '\\r') line.pop_back();
    return line;
}
""",
    "TreeNode": """static TreeNode* ca_readTree() {
    string line;
    if (!getline(cin, line)) return nullptr;
    istringstream in(line);
    vector<string> parts;
    string token;
    while (in >> token) parts.push_back(token);
    if (parts.empty() || parts[0] == "null") return nullptr;
    TreeNode *root = new TreeNode(stoi(parts[0]));
    queue<TreeNode*> pending;
    pending.push(root);
    size_t i = 1;
    while (!pending.empty() && i < parts.size()) {
        TreeNode *node = pending.front();
        pending.pop();
        if (i < parts.size() && parts[i] != "null") { node->left = new TreeNode(stoi(parts[i])); pending.push(node->left); }
        i++;
        if (i < parts.size() && parts[i] != "null") { node->right = new TreeNode(stoi(parts[i])); pending.push(node->right); }
        i++;
    }
    return root;
}
""",
    "print_int[]": """static void ca_printArray(const vector<int> &values) {
    for (size_t i = 0; i < values.size(); i++) {
        if (i) cout << ' ';
        cout << values[i];
    }
    cout << '\\n';
}
""",
    "print_ListNode": """static void ca_printList(ListNode *head) {
    bool first = true;
    for (; head; head = head->next) {
        if (!first) cout << ' ';
        cout << head->val;
        first = false;
    }
    cout << '\\n';
}
""",
}

_CPP_READ = {
    "int": "int {p};\n    cin >> {p};",
    "long": "long long {p};\n    cin >> {p};",
    "int[]": "vector<int> {p} = ca_readIntArray();",
    "char[][]": "vector<vector<char>> {p} = ca_readGrid();",
    "ListNode": "ListNode *{p} = ca_readList();",
    "string": "string {p} = ca_readLine();",
    "TreeNode": "TreeNode *{p} = ca_readTree();",
}


def _cpp(name, params, returns, print_arg):
    types = {t for _, t in params} | {returns}
    nodes = "".join(_CPP_NODES[n] for n in ("ListNode", "TreeNode") if n in types)
    helper_keys = [t for t in ("int[]", "char[][]", "ListNode", "string", "TreeNode") if t in {t for _, t in params}]
    if returns in ("int[]", "ListNode") or (returns == "void" and print_arg):
        helper_keys.append(f"print_{'int[]' if returns == 'void' else returns}")
    helpers = "".join(_CPP_HELPERS[k] for k in dict.fromkeys(helper_keys))
    reads = "\n    ".join(_CPP_READ[t].format(p=p) for p, t in params)
    call = f"solution.{name}({', '.join(p for p, _ in params)})"
    out = {
        "int": f"cout << {call} << '\\n';",
        "long": f"cout << {call} << '\\n';",
        "bool": f'cout << ({call} ? "true" : "false") << \'\\n\';',
        "int[]": f"ca_printArray({call});",
        "ListNode": f"ca_printList({call});",
        "void": f"{call};\n    ca_printArray({print_arg});",
    }[returns]
    return (
        f"#include <bits/stdc++.h>\nusing namespace std;\n\n{nodes}{MARKER}\n\n{helpers}\n"
        f"int main() {{\n    {reads}\n    Solution solution;\n    {out}\n    return 0;\n}}\n"
    )


# ------------------------------------------------------------------ Java
_JAVA_NODES = {
    "ListNode": """class ListNode {
    int val;
    ListNode next;
    ListNode() {}
    ListNode(int val) { this.val = val; }
    ListNode(int val, ListNode next) { this.val = val; this.next = next; }
}
""",
    "TreeNode": """class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    TreeNode() {}
    TreeNode(int val) { this.val = val; }
    TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
}
""",
}

_JAVA_BASE = r"""    private static final BufferedReader CA_IN = new BufferedReader(new InputStreamReader(System.in));
    private static StringTokenizer caTokens = new StringTokenizer("");

    private static String caNext() throws IOException {
        while (!caTokens.hasMoreTokens()) {
            String line = CA_IN.readLine();
            if (line == null) throw new EOFException("Input ended early");
            caTokens = new StringTokenizer(line);
        }
        return caTokens.nextToken();
    }

    private static String caReadLine() throws IOException {
        String line = CA_IN.readLine();
        return line == null ? "" : line;
    }

    private static String caJoin(int[] values) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < values.length; i++) {
            if (i > 0) out.append(' ');
            out.append(values[i]);
        }
        return out.toString();
    }
"""

_JAVA_HELPERS = {
    "int[]": r"""
    private static int[] caReadIntArray() throws IOException {
        int n = Integer.parseInt(caNext());
        int[] values = new int[n];
        for (int i = 0; i < n; i++) values[i] = Integer.parseInt(caNext());
        return values;
    }
""",
    "char[][]": r"""
    private static char[][] caReadGrid() throws IOException {
        int rows = Integer.parseInt(caNext());
        caNext();
        char[][] grid = new char[rows][];
        for (int i = 0; i < rows; i++) grid[i] = caNext().toCharArray();
        return grid;
    }
""",
    "ListNode": r"""
    private static ListNode caReadList() throws IOException {
        int n = Integer.parseInt(caNext());
        ListNode dummy = new ListNode(0), tail = dummy;
        for (int i = 0; i < n; i++) {
            tail.next = new ListNode(Integer.parseInt(caNext()));
            tail = tail.next;
        }
        return dummy.next;
    }

    private static String caJoin(ListNode head) {
        StringBuilder out = new StringBuilder();
        for (ListNode node = head; node != null; node = node.next) {
            if (out.length() > 0) out.append(' ');
            out.append(node.val);
        }
        return out.toString();
    }
""",
    "TreeNode": r"""
    private static TreeNode caReadTree() throws IOException {
        String line = caReadLine().trim();
        if (line.isEmpty()) return null;
        String[] parts = line.split("\\s+");
        if (parts[0].equals("null")) return null;
        TreeNode root = new TreeNode(Integer.parseInt(parts[0]));
        ArrayDeque<TreeNode> pending = new ArrayDeque<>();
        pending.add(root);
        int i = 1;
        while (!pending.isEmpty() && i < parts.length) {
            TreeNode node = pending.poll();
            if (i < parts.length && !parts[i].equals("null")) { node.left = new TreeNode(Integer.parseInt(parts[i])); pending.add(node.left); }
            i++;
            if (i < parts.length && !parts[i].equals("null")) { node.right = new TreeNode(Integer.parseInt(parts[i])); pending.add(node.right); }
            i++;
        }
        return root;
    }
""",
}

_JAVA_TYPE = {"int": "int", "long": "long", "string": "String", "int[]": "int[]", "char[][]": "char[][]", "ListNode": "ListNode", "TreeNode": "TreeNode"}
_JAVA_READ = {
    "int": "Integer.parseInt(caNext())",
    "long": "Long.parseLong(caNext())",
    "string": "caReadLine()",
    "int[]": "caReadIntArray()",
    "char[][]": "caReadGrid()",
    "ListNode": "caReadList()",
    "TreeNode": "caReadTree()",
}


def _java(name, params, returns, print_arg):
    types = {t for _, t in params} | {returns}
    nodes = "".join(_JAVA_NODES[n] for n in ("ListNode", "TreeNode") if n in types)
    helpers = _JAVA_BASE + "".join(_JAVA_HELPERS[t] for t in ("int[]", "char[][]", "ListNode", "TreeNode") if t in types)
    reads = "\n        ".join(f"{_JAVA_TYPE[t]} {p} = {_JAVA_READ[t]};" for p, t in params)
    call = f"solution.{name}({', '.join(p for p, _ in params)})"
    out = {
        "int": f"System.out.println({call});",
        "long": f"System.out.println({call});",
        "bool": f'System.out.println({call} ? "true" : "false");',
        "int[]": f"System.out.println(caJoin({call}));",
        "ListNode": f"System.out.println(caJoin({call}));",
        "void": f"{call};\n        System.out.println(caJoin({print_arg}));",
    }[returns]
    return (
        f"import java.util.*;\nimport java.io.*;\n\n{MARKER}\n\n{nodes}\npublic class Main {{\n{helpers}\n"
        f"    public static void main(String[] args) throws IOException {{\n        {reads}\n"
        f"        Solution solution = new Solution();\n        {out}\n    }}\n}}\n"
    )


# ------------------------------------------------------------------ Python
_PY_NODES = {
    "ListNode": """class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
""",
    "TreeNode": """class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
""",
}

_PY_HELPERS = """def _ca_join(values):
    return " ".join(str(v) for v in values)


def _ca_list_values(head):
    values = []
    while head is not None:
        values.append(head.val)
        head = head.next
    return values


def _ca_build_list(values):
    dummy = tail = ListNode(0)
    for value in values:
        tail.next = ListNode(value)
        tail = tail.next
    return dummy.next


def _ca_build_tree(line):
    parts = line.split()
    if not parts or parts[0] == "null":
        return None
    root = TreeNode(int(parts[0]))
    pending = [root]
    head, i = 0, 1
    while head < len(pending) and i < len(parts):
        node = pending[head]
        head += 1
        if i < len(parts) and parts[i] != "null":
            node.left = TreeNode(int(parts[i]))
            pending.append(node.left)
        i += 1
        if i < len(parts) and parts[i] != "null":
            node.right = TreeNode(int(parts[i]))
            pending.append(node.right)
        i += 1
    return root
"""

_PY_TOKEN_READ = {
    "int": "{p} = int(next(_tokens))",
    "long": "{p} = int(next(_tokens))",
    "int[]": "{p} = [int(next(_tokens)) for _ in range(int(next(_tokens)))]",
    "char[][]": "_rows = int(next(_tokens))\n    next(_tokens)\n    {p} = [list(next(_tokens)) for _ in range(_rows)]",
    "ListNode": "{p} = _ca_build_list([int(next(_tokens)) for _ in range(int(next(_tokens)))])",
}
_PY_LINE_READ = {"string": "{p} = _line({i})", "TreeNode": "{p} = _ca_build_tree(_line({i}))"}


def _python(name, params, returns, print_arg, mode):
    types = {t for _, t in params} | {returns}
    nodes = "".join(_PY_NODES[n] for n in ("ListNode", "TreeNode") if n in types)
    method = _snake(name)
    args = [_snake(p) for p, _ in params]
    if mode == "lines":
        setup = (
            '_lines = [line.rstrip("\\r") for line in sys.stdin.read().split("\\n")]\n'
            '    _line = lambda i: _lines[i] if i < len(_lines) else ""'
        )
        reads = "\n    ".join(_PY_LINE_READ[t].format(p=a, i=i) for i, (a, (_, t)) in enumerate(zip(args, params, strict=False)))
    else:
        setup = "_tokens = iter(sys.stdin.read().split())"
        reads = "\n    ".join(_PY_TOKEN_READ[t].format(p=a) for a, (_, t) in zip(args, params, strict=False))
    call = f"Solution().{method}({', '.join(args)})"
    out = {
        "int": f"print({call})",
        "long": f"print({call})",
        "bool": f'print("true" if {call} else "false")',
        "int[]": f"print(_ca_join({call}))",
        "ListNode": f"print(_ca_join(_ca_list_values({call})))",
        "void": f"{call}\n    print(_ca_join({_snake(print_arg) if print_arg else ''}))",
    }[returns]
    return (
        f"import sys\nfrom typing import List, Optional\n\n{nodes}\n{MARKER}\n\n\n{_PY_HELPERS}\n\n"
        f"def _codearena_main():\n    {setup}\n    {reads}\n    {out}\n\n\n"
        f'if __name__ == "__main__":\n    _codearena_main()\n'
    )


def function_driver(name: str, params: list[tuple[str, str]], returns: str, *, mode: str = "tokens", print_arg: str | None = None) -> dict[str, str]:
    """Drivers for a `class Solution` method, for C++ / Java / Python."""
    return {
        "CPP": _cpp(name, params, returns, print_arg),
        "JAVA": _java(name, params, returns, print_arg),
        "PYTHON": _python(name, params, returns, print_arg, mode),
    }


# ------------------------------------------------------------------ special I/O shapes
def merge_sorted_array_driver() -> dict[str, str]:
    """Input: "m n", then m values of nums1, then n values of nums2."""
    return {
        "CPP": f"""#include <bits/stdc++.h>
using namespace std;

{MARKER}

int main() {{
    int m = 0, n = 0;
    cin >> m >> n;
    vector<int> nums1(m + n, 0), nums2(n);
    for (int i = 0; i < m; i++) cin >> nums1[i];
    for (int &x : nums2) cin >> x;
    Solution solution;
    solution.merge(nums1, m, nums2, n);
    for (size_t i = 0; i < nums1.size(); i++) cout << (i ? " " : "") << nums1[i];
    cout << '\\n';
    return 0;
}}
""",
        "JAVA": f"""import java.util.*;
import java.io.*;

{MARKER}

public class Main {{
    public static void main(String[] args) throws IOException {{
        StreamTokenizer in = new StreamTokenizer(new BufferedReader(new InputStreamReader(System.in)));
        in.nextToken(); int m = (int) in.nval;
        in.nextToken(); int n = (int) in.nval;
        int[] nums1 = new int[m + n];
        int[] nums2 = new int[n];
        for (int i = 0; i < m; i++) {{ in.nextToken(); nums1[i] = (int) in.nval; }}
        for (int i = 0; i < n; i++) {{ in.nextToken(); nums2[i] = (int) in.nval; }}
        new Solution().merge(nums1, m, nums2, n);
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < nums1.length; i++) {{ if (i > 0) out.append(' '); out.append(nums1[i]); }}
        System.out.println(out);
    }}
}}
""",
        "PYTHON": f"""import sys
from typing import List, Optional

{MARKER}


def _codearena_main():
    tokens = iter(sys.stdin.read().split())
    m, n = int(next(tokens)), int(next(tokens))
    nums1 = [int(next(tokens)) for _ in range(m)] + [0] * n
    nums2 = [int(next(tokens)) for _ in range(n)]
    Solution().merge(nums1, m, nums2, n)
    print(" ".join(str(v) for v in nums1))


if __name__ == "__main__":
    _codearena_main()
""",
    }


def queue_design_driver() -> dict[str, str]:
    """Input: q, then q operations ("push x", "pop", "peek", "empty")."""
    return {
        "CPP": f"""#include <bits/stdc++.h>
using namespace std;

{MARKER}

int main() {{
    int q = 0;
    cin >> q;
    MyQueue obj;
    for (int i = 0; i < q; i++) {{
        string op;
        cin >> op;
        if (op == "push") {{ int x; cin >> x; obj.push(x); }}
        else if (op == "pop") cout << obj.pop() << '\\n';
        else if (op == "peek") cout << obj.peek() << '\\n';
        else if (op == "empty") cout << (obj.empty() ? "true" : "false") << '\\n';
    }}
    return 0;
}}
""",
        "JAVA": f"""import java.util.*;
import java.io.*;

{MARKER}

public class Main {{
    public static void main(String[] args) throws IOException {{
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        int q = Integer.parseInt(in.readLine().trim());
        MyQueue obj = new MyQueue();
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < q; i++) {{
            String[] parts = in.readLine().trim().split("\\\\s+");
            // Classic if/else: Judge0's OpenJDK 13 has no arrow-style switch.
            if (parts[0].equals("push")) obj.push(Integer.parseInt(parts[1]));
            else if (parts[0].equals("pop")) out.append(obj.pop()).append('\\n');
            else if (parts[0].equals("peek")) out.append(obj.peek()).append('\\n');
            else if (parts[0].equals("empty")) out.append(obj.empty() ? "true" : "false").append('\\n');
        }}
        System.out.print(out);
    }}
}}
""",
        "PYTHON": f"""import sys
from typing import List, Optional

{MARKER}


def _codearena_main():
    lines = sys.stdin.read().split("\\n")
    q = int(lines[0])
    obj = MyQueue()
    out = []
    for line in lines[1:q + 1]:
        parts = line.split()
        if parts[0] == "push":
            obj.push(int(parts[1]))
        elif parts[0] == "pop":
            out.append(str(obj.pop()))
        elif parts[0] == "peek":
            out.append(str(obj.peek()))
        elif parts[0] == "empty":
            out.append("true" if obj.empty() else "false")
    print("\\n".join(out))


if __name__ == "__main__":
    _codearena_main()
""",
    }
