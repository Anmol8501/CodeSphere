"""Known-correct solutions for every seeded problem, in every language.

Used to verify the hidden harnesses and the seeded test data end to end:
  * tests/test_judge0_live.py submits them to a real Judge0 (opt-in).
Written in the same style a student would write (class Solution for
function-style problems, full programs for stdin/stdout problems).
"""

SOLUTIONS: dict[str, dict[str, str]] = {
    "hello-world": {
        "PYTHON": 'print("Hello, World!")\n',
        "JAVA": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}\n',
        "CPP": '#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}\n',
    },
    "sum-of-two-numbers": {
        "PYTHON": "a, b = map(int, input().split())\nprint(a + b)\n",
        "JAVA": (
            "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n        long a = sc.nextLong(), b = sc.nextLong();\n"
            "        System.out.println(a + b);\n    }\n}\n"
        ),
        "CPP": "#include <iostream>\n\nint main() {\n    long long a, b;\n    std::cin >> a >> b;\n    std::cout << a + b << std::endl;\n    return 0;\n}\n",
    },
    "two-sum": {
        "PYTHON": (
            "class Solution:\n    def two_sum(self, nums, target):\n        seen = {}\n        for i, x in enumerate(nums):\n"
            "            if target - x in seen:\n                return [seen[target - x], i]\n            seen[x] = i\n        return []\n"
        ),
        "JAVA": (
            "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        Map<Integer, Integer> seen = new HashMap<>();\n"
            "        for (int i = 0; i < nums.length; i++) {\n            Integer j = seen.get(target - nums[i]);\n"
            "            if (j != null) return new int[]{j, i};\n            seen.put(nums[i], i);\n        }\n        return new int[0];\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        unordered_map<long long, int> seen;\n"
            "        for (int i = 0; i < (int)nums.size(); i++) {\n            auto it = seen.find((long long)target - nums[i]);\n"
            "            if (it != seen.end()) return {it->second, i};\n            seen[nums[i]] = i;\n        }\n        return {};\n    }\n};\n"
        ),
    },
    "maximum-element-in-array": {
        "PYTHON": "class Solution:\n    def find_max(self, nums):\n        return max(nums)\n",
        "JAVA": "class Solution {\n    public int findMax(int[] nums) {\n        int best = nums[0];\n        for (int x : nums) best = Math.max(best, x);\n        return best;\n    }\n}\n",
        "CPP": "class Solution {\npublic:\n    int findMax(vector<int>& nums) {\n        return *max_element(nums.begin(), nums.end());\n    }\n};\n",
    },
    "best-time-to-buy-and-sell-stock": {
        "PYTHON": (
            "class Solution:\n    def max_profit(self, prices):\n        best, low = 0, float('inf')\n        for p in prices:\n"
            "            low = min(low, p)\n            best = max(best, p - low)\n        return best\n"
        ),
        "JAVA": (
            "class Solution {\n    public int maxProfit(int[] prices) {\n        int best = 0, low = Integer.MAX_VALUE;\n"
            "        for (int p : prices) { low = Math.min(low, p); best = Math.max(best, p - low); }\n        return best;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    int maxProfit(vector<int>& prices) {\n        int best = 0, low = INT_MAX;\n"
            "        for (int p : prices) { low = min(low, p); best = max(best, p - low); }\n        return best;\n    }\n};\n"
        ),
    },
    "maximum-subarray": {
        "PYTHON": (
            "class Solution:\n    def max_sub_array(self, nums):\n        best = cur = nums[0]\n        for x in nums[1:]:\n"
            "            cur = max(x, cur + x)\n            best = max(best, cur)\n        return best\n"
        ),
        "JAVA": (
            "class Solution {\n    public int maxSubArray(int[] nums) {\n        int best = nums[0], cur = nums[0];\n"
            "        for (int i = 1; i < nums.length; i++) { cur = Math.max(nums[i], cur + nums[i]); best = Math.max(best, cur); }\n"
            "        return best;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    int maxSubArray(vector<int>& nums) {\n        int best = nums[0], cur = nums[0];\n"
            "        for (size_t i = 1; i < nums.size(); i++) { cur = max(nums[i], cur + nums[i]); best = max(best, cur); }\n"
            "        return best;\n    }\n};\n"
        ),
    },
    "trapping-rain-water": {
        "PYTHON": (
            "class Solution:\n    def trap(self, height):\n        l, r = 0, len(height) - 1\n        lmax = rmax = water = 0\n"
            "        while l < r:\n            if height[l] < height[r]:\n                lmax = max(lmax, height[l]); water += lmax - height[l]; l += 1\n"
            "            else:\n                rmax = max(rmax, height[r]); water += rmax - height[r]; r -= 1\n        return water\n"
        ),
        "JAVA": (
            "class Solution {\n    public int trap(int[] height) {\n        int l = 0, r = height.length - 1, lmax = 0, rmax = 0, water = 0;\n"
            "        while (l < r) {\n            if (height[l] < height[r]) { lmax = Math.max(lmax, height[l]); water += lmax - height[l]; l++; }\n"
            "            else { rmax = Math.max(rmax, height[r]); water += rmax - height[r]; r--; }\n        }\n        return water;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    int trap(vector<int>& height) {\n        int l = 0, r = (int)height.size() - 1, lmax = 0, rmax = 0, water = 0;\n"
            "        while (l < r) {\n            if (height[l] < height[r]) { lmax = max(lmax, height[l]); water += lmax - height[l]; l++; }\n"
            "            else { rmax = max(rmax, height[r]); water += rmax - height[r]; r--; }\n        }\n        return water;\n    }\n};\n"
        ),
    },
    "valid-palindrome": {
        "PYTHON": (
            "class Solution:\n    def is_palindrome(self, s):\n        t = [c.lower() for c in s if c.isalnum()]\n        return t == t[::-1]\n"
        ),
        "JAVA": (
            "class Solution {\n    public boolean isPalindrome(String s) {\n        int i = 0, j = s.length() - 1;\n        while (i < j) {\n"
            "            char a = s.charAt(i), b = s.charAt(j);\n            if (!Character.isLetterOrDigit(a)) { i++; continue; }\n"
            "            if (!Character.isLetterOrDigit(b)) { j--; continue; }\n"
            "            if (Character.toLowerCase(a) != Character.toLowerCase(b)) return false;\n            i++; j--;\n        }\n        return true;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    bool isPalindrome(string s) {\n        int i = 0, j = (int)s.size() - 1;\n        while (i < j) {\n"
            "            if (!isalnum((unsigned char)s[i])) { i++; continue; }\n            if (!isalnum((unsigned char)s[j])) { j--; continue; }\n"
            "            if (tolower((unsigned char)s[i]) != tolower((unsigned char)s[j])) return false;\n            i++; j--;\n        }\n        return true;\n    }\n};\n"
        ),
    },
    "valid-anagram": {
        "PYTHON": "class Solution:\n    def is_anagram(self, s, t):\n        return sorted(s) == sorted(t)\n",
        "JAVA": (
            "class Solution {\n    public boolean isAnagram(String s, String t) {\n        if (s.length() != t.length()) return false;\n"
            "        int[] count = new int[26];\n        for (int i = 0; i < s.length(); i++) { count[s.charAt(i) - 'a']++; count[t.charAt(i) - 'a']--; }\n"
            "        for (int c : count) if (c != 0) return false;\n        return true;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    bool isAnagram(string s, string t) {\n        sort(s.begin(), s.end());\n        sort(t.begin(), t.end());\n"
            "        return s == t;\n    }\n};\n"
        ),
    },
    "binary-search": {
        "PYTHON": (
            "class Solution:\n    def search(self, nums, target):\n        lo, hi = 0, len(nums) - 1\n        while lo <= hi:\n"
            "            mid = (lo + hi) // 2\n            if nums[mid] == target:\n                return mid\n"
            "            if nums[mid] < target:\n                lo = mid + 1\n            else:\n                hi = mid - 1\n        return -1\n"
        ),
        "JAVA": (
            "class Solution {\n    public int search(int[] nums, int target) {\n        int lo = 0, hi = nums.length - 1;\n        while (lo <= hi) {\n"
            "            int mid = lo + (hi - lo) / 2;\n            if (nums[mid] == target) return mid;\n"
            "            if (nums[mid] < target) lo = mid + 1; else hi = mid - 1;\n        }\n        return -1;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    int search(vector<int>& nums, int target) {\n        int lo = 0, hi = (int)nums.size() - 1;\n"
            "        while (lo <= hi) {\n            int mid = lo + (hi - lo) / 2;\n            if (nums[mid] == target) return mid;\n"
            "            if (nums[mid] < target) lo = mid + 1; else hi = mid - 1;\n        }\n        return -1;\n    }\n};\n"
        ),
    },
    "first-and-last-position": {
        "PYTHON": (
            "from bisect import bisect_left, bisect_right\n\n\nclass Solution:\n    def search_range(self, nums, target):\n"
            "        lo, hi = bisect_left(nums, target), bisect_right(nums, target) - 1\n        return [lo, hi] if lo <= hi else [-1, -1]\n"
        ),
        "JAVA": (
            "class Solution {\n    private int bound(int[] nums, long target) {\n        int lo = 0, hi = nums.length;\n"
            "        while (lo < hi) { int mid = (lo + hi) >>> 1; if (nums[mid] < target) lo = mid + 1; else hi = mid; }\n        return lo;\n    }\n\n"
            "    public int[] searchRange(int[] nums, int target) {\n        int lo = bound(nums, target), hi = bound(nums, (long) target + 1) - 1;\n"
            "        return lo <= hi ? new int[]{lo, hi} : new int[]{-1, -1};\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    vector<int> searchRange(vector<int>& nums, int target) {\n"
            "        auto lo = lower_bound(nums.begin(), nums.end(), target);\n        auto hi = upper_bound(nums.begin(), nums.end(), target);\n"
            "        if (lo == hi) return {-1, -1};\n        return {(int)(lo - nums.begin()), (int)(hi - nums.begin()) - 1};\n    }\n};\n"
        ),
    },
    "sort-colors": {
        "PYTHON": (
            "class Solution:\n    def sort_colors(self, nums):\n        lo, mid, hi = 0, 0, len(nums) - 1\n        while mid <= hi:\n"
            "            if nums[mid] == 0:\n                nums[lo], nums[mid] = nums[mid], nums[lo]; lo += 1; mid += 1\n"
            "            elif nums[mid] == 1:\n                mid += 1\n            else:\n                nums[mid], nums[hi] = nums[hi], nums[mid]; hi -= 1\n"
        ),
        "JAVA": (
            "class Solution {\n    public void sortColors(int[] nums) {\n        int lo = 0, mid = 0, hi = nums.length - 1;\n        while (mid <= hi) {\n"
            "            if (nums[mid] == 0) { int t = nums[lo]; nums[lo++] = nums[mid]; nums[mid++] = t; }\n"
            "            else if (nums[mid] == 1) mid++;\n            else { int t = nums[hi]; nums[hi--] = nums[mid]; nums[mid] = t; }\n        }\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    void sortColors(vector<int>& nums) {\n        int lo = 0, mid = 0, hi = (int)nums.size() - 1;\n"
            "        while (mid <= hi) {\n            if (nums[mid] == 0) swap(nums[lo++], nums[mid++]);\n            else if (nums[mid] == 1) mid++;\n"
            "            else swap(nums[mid], nums[hi--]);\n        }\n    }\n};\n"
        ),
    },
    "merge-sorted-array": {
        "PYTHON": (
            "class Solution:\n    def merge(self, nums1, m, nums2, n):\n        i, j, k = m - 1, n - 1, m + n - 1\n        while j >= 0:\n"
            "            if i >= 0 and nums1[i] > nums2[j]:\n                nums1[k] = nums1[i]; i -= 1\n            else:\n"
            "                nums1[k] = nums2[j]; j -= 1\n            k -= 1\n"
        ),
        "JAVA": (
            "class Solution {\n    public void merge(int[] nums1, int m, int[] nums2, int n) {\n        int i = m - 1, j = n - 1, k = m + n - 1;\n"
            "        while (j >= 0) nums1[k--] = (i >= 0 && nums1[i] > nums2[j]) ? nums1[i--] : nums2[j--];\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    void merge(vector<int>& nums1, int m, vector<int>& nums2, int n) {\n        int i = m - 1, j = n - 1, k = m + n - 1;\n"
            "        while (j >= 0) nums1[k--] = (i >= 0 && nums1[i] > nums2[j]) ? nums1[i--] : nums2[j--];\n    }\n};\n"
        ),
    },
    "reverse-linked-list": {
        "PYTHON": (
            "class Solution:\n    def reverse_list(self, head):\n        prev = None\n        while head:\n"
            "            head.next, prev, head = prev, head, head.next\n        return prev\n"
        ),
        "JAVA": (
            "class Solution {\n    public ListNode reverseList(ListNode head) {\n        ListNode prev = null;\n"
            "        while (head != null) { ListNode next = head.next; head.next = prev; prev = head; head = next; }\n        return prev;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    ListNode* reverseList(ListNode* head) {\n        ListNode* prev = nullptr;\n"
            "        while (head) { ListNode* next = head->next; head->next = prev; prev = head; head = next; }\n        return prev;\n    }\n};\n"
        ),
    },
    "middle-of-linked-list": {
        "PYTHON": (
            "class Solution:\n    def middle_node(self, head):\n        slow = fast = head\n        while fast and fast.next:\n"
            "            slow, fast = slow.next, fast.next.next\n        return slow\n"
        ),
        "JAVA": (
            "class Solution {\n    public ListNode middleNode(ListNode head) {\n        ListNode slow = head, fast = head;\n"
            "        while (fast != null && fast.next != null) { slow = slow.next; fast = fast.next.next; }\n        return slow;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    ListNode* middleNode(ListNode* head) {\n        ListNode *slow = head, *fast = head;\n"
            "        while (fast && fast->next) { slow = slow->next; fast = fast->next->next; }\n        return slow;\n    }\n};\n"
        ),
    },
    "valid-parentheses": {
        "PYTHON": (
            "class Solution:\n    def is_valid(self, s):\n        pairs = {')': '(', ']': '[', '}': '{'}\n        stack = []\n        for c in s:\n"
            "            if c in pairs:\n                if not stack or stack.pop() != pairs[c]:\n                    return False\n"
            "            else:\n                stack.append(c)\n        return not stack\n"
        ),
        "JAVA": (
            "class Solution {\n    public boolean isValid(String s) {\n        Deque<Character> stack = new ArrayDeque<>();\n"
            "        for (char c : s.toCharArray()) {\n            if (c == '(' || c == '[' || c == '{') { stack.push(c); continue; }\n"
            "            if (stack.isEmpty()) return false;\n            char open = stack.pop();\n"
            "            if ((c == ')' && open != '(') || (c == ']' && open != '[') || (c == '}' && open != '{')) return false;\n"
            "        }\n        return stack.isEmpty();\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    bool isValid(string s) {\n        string stack;\n        for (char c : s) {\n"
            "            if (c == '(' || c == '[' || c == '{') { stack.push_back(c); continue; }\n            if (stack.empty()) return false;\n"
            "            char open = stack.back();\n            stack.pop_back();\n"
            "            if ((c == ')' && open != '(') || (c == ']' && open != '[') || (c == '}' && open != '{')) return false;\n"
            "        }\n        return stack.empty();\n    }\n};\n"
        ),
    },
    "implement-queue-using-stacks": {
        "PYTHON": (
            "class MyQueue:\n    def __init__(self):\n        self.inbox, self.outbox = [], []\n\n    def push(self, x: int) -> None:\n"
            "        self.inbox.append(x)\n\n    def _move(self):\n        if not self.outbox:\n            while self.inbox:\n"
            "                self.outbox.append(self.inbox.pop())\n\n    def pop(self) -> int:\n        self._move()\n        return self.outbox.pop()\n\n"
            "    def peek(self) -> int:\n        self._move()\n        return self.outbox[-1]\n\n    def empty(self) -> bool:\n"
            "        return not self.inbox and not self.outbox\n"
        ),
        "JAVA": (
            "class MyQueue {\n    private final Deque<Integer> inbox = new ArrayDeque<>(), outbox = new ArrayDeque<>();\n\n"
            "    public MyQueue() {}\n\n    public void push(int x) { inbox.push(x); }\n\n"
            "    private void move() { if (outbox.isEmpty()) while (!inbox.isEmpty()) outbox.push(inbox.pop()); }\n\n"
            "    public int pop() { move(); return outbox.pop(); }\n\n    public int peek() { move(); return outbox.peek(); }\n\n"
            "    public boolean empty() { return inbox.isEmpty() && outbox.isEmpty(); }\n}\n"
        ),
        "CPP": (
            "class MyQueue {\n    stack<int> inbox, outbox;\n    void move() { if (outbox.empty()) while (!inbox.empty()) { outbox.push(inbox.top()); inbox.pop(); } }\n"
            "public:\n    MyQueue() {}\n    void push(int x) { inbox.push(x); }\n    int pop() { move(); int v = outbox.top(); outbox.pop(); return v; }\n"
            "    int peek() { move(); return outbox.top(); }\n    bool empty() { return inbox.empty() && outbox.empty(); }\n};\n"
        ),
    },
    "maximum-depth-of-binary-tree": {
        "PYTHON": (
            "class Solution:\n    def max_depth(self, root):\n        if root is None:\n            return 0\n"
            "        return 1 + max(self.max_depth(root.left), self.max_depth(root.right))\n"
        ),
        "JAVA": (
            "class Solution {\n    public int maxDepth(TreeNode root) {\n        if (root == null) return 0;\n"
            "        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    int maxDepth(TreeNode* root) {\n        if (!root) return 0;\n"
            "        return 1 + max(maxDepth(root->left), maxDepth(root->right));\n    }\n};\n"
        ),
    },
    "binary-tree-inorder-traversal": {
        "PYTHON": (
            "class Solution:\n    def inorder_traversal(self, root):\n        out, stack, node = [], [], root\n        while stack or node:\n"
            "            while node:\n                stack.append(node)\n                node = node.left\n            node = stack.pop()\n"
            "            out.append(node.val)\n            node = node.right\n        return out\n"
        ),
        "JAVA": (
            "class Solution {\n    public int[] inorderTraversal(TreeNode root) {\n        List<Integer> out = new ArrayList<>();\n"
            "        Deque<TreeNode> stack = new ArrayDeque<>();\n        TreeNode node = root;\n        while (node != null || !stack.isEmpty()) {\n"
            "            while (node != null) { stack.push(node); node = node.left; }\n            node = stack.pop();\n"
            "            out.add(node.val);\n            node = node.right;\n        }\n"
            "        int[] result = new int[out.size()];\n        for (int i = 0; i < result.length; i++) result[i] = out.get(i);\n        return result;\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    vector<int> inorderTraversal(TreeNode* root) {\n        vector<int> out;\n        stack<TreeNode*> st;\n"
            "        TreeNode* node = root;\n        while (node || !st.empty()) {\n            while (node) { st.push(node); node = node->left; }\n"
            "            node = st.top(); st.pop();\n            out.push_back(node->val);\n            node = node->right;\n        }\n        return out;\n    }\n};\n"
        ),
    },
    "number-of-islands": {
        "PYTHON": (
            "class Solution:\n    def num_islands(self, grid):\n        rows, cols, count = len(grid), len(grid[0]), 0\n"
            "        for r in range(rows):\n            for c in range(cols):\n                if grid[r][c] != '1':\n                    continue\n"
            "                count += 1\n                stack = [(r, c)]\n                grid[r][c] = '0'\n                while stack:\n"
            "                    y, x = stack.pop()\n                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):\n"
            "                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == '1':\n"
            "                            grid[ny][nx] = '0'\n                            stack.append((ny, nx))\n        return count\n"
        ),
        "JAVA": (
            "class Solution {\n    public int numIslands(char[][] grid) {\n        int count = 0;\n"
            "        for (int r = 0; r < grid.length; r++)\n            for (int c = 0; c < grid[r].length; c++)\n"
            "                if (grid[r][c] == '1') { count++; sink(grid, r, c); }\n        return count;\n    }\n\n"
            "    private void sink(char[][] grid, int r, int c) {\n        Deque<int[]> stack = new ArrayDeque<>();\n"
            "        stack.push(new int[]{r, c});\n        grid[r][c] = '0';\n        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};\n"
            "        while (!stack.isEmpty()) {\n            int[] cell = stack.pop();\n            for (int[] d : dirs) {\n"
            "                int y = cell[0] + d[0], x = cell[1] + d[1];\n"
            "                if (y >= 0 && y < grid.length && x >= 0 && x < grid[y].length && grid[y][x] == '1') { grid[y][x] = '0'; stack.push(new int[]{y, x}); }\n"
            "            }\n        }\n    }\n}\n"
        ),
        "CPP": (
            "class Solution {\npublic:\n    int numIslands(vector<vector<char>>& grid) {\n        int count = 0;\n"
            "        for (int r = 0; r < (int)grid.size(); r++)\n            for (int c = 0; c < (int)grid[r].size(); c++)\n"
            "                if (grid[r][c] == '1') { count++; sink(grid, r, c); }\n        return count;\n    }\n\nprivate:\n"
            "    void sink(vector<vector<char>>& grid, int r, int c) {\n        vector<pair<int, int>> st{{r, c}};\n        grid[r][c] = '0';\n"
            "        int dy[] = {1, -1, 0, 0}, dx[] = {0, 0, 1, -1};\n        while (!st.empty()) {\n            int y = st.back().first, x = st.back().second;\n            st.pop_back();\n"
            "            for (int k = 0; k < 4; k++) {\n                int ny = y + dy[k], nx = x + dx[k];\n"
            "                if (ny >= 0 && ny < (int)grid.size() && nx >= 0 && nx < (int)grid[ny].size() && grid[ny][nx] == '1') { grid[ny][nx] = '0'; st.push_back({ny, nx}); }\n"
            "            }\n        }\n    }\n};\n"
        ),
    },
    "climbing-stairs": {
        "PYTHON": "class Solution:\n    def climb_stairs(self, n):\n        a, b = 1, 1\n        for _ in range(n):\n            a, b = b, a + b\n        return a\n",
        "JAVA": "class Solution {\n    public int climbStairs(int n) {\n        int a = 1, b = 1;\n        for (int i = 0; i < n; i++) { int t = a + b; a = b; b = t; }\n        return a;\n    }\n}\n",
        "CPP": "class Solution {\npublic:\n    int climbStairs(int n) {\n        long long a = 1, b = 1;\n        for (int i = 0; i < n; i++) { long long t = a + b; a = b; b = t; }\n        return (int)a;\n    }\n};\n",
    },
}
