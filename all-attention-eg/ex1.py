def exist(board, word):
    rows, cols = len(board), len(board[0])

    def dfs(i, j, index):
        # If all characters are matched, return True.
        if index == len(word):
            return True
        print(f"Now i = {i},j={j}, index={index}, word[index]={word[index]}")
        # Check boundaries and current cell match.
        if i < 0 or i >= rows or j < 0 or j >= cols or board[i][j] != word[index]:
            return False

        # Mark the cell as visited by temporarily modifying it.
        temp = board[i][j]
        board[i][j] = '#'

        # Explore all four directions.
        found = (dfs(i + 1, j, index + 1) or
                 dfs(i - 1, j, index + 1) or
                 dfs(i, j + 1, index + 1) or
                 dfs(i, j - 1, index + 1))

        # Restore the original value (backtracking).
        board[i][j] = temp

        return found

    # Try DFS from each cell in the grid.
    for i in range(rows):
        for j in range(cols):
            if dfs(i, j, 0):
                return True
    return False

# Example usage:
board = [
    ["A", "B", "C", "E"],
    ["S", "F", "C", "S"],
    ["A", "D", "E", "E"]
]
word = "ABCCED"
print(exist(board, word))  # Output: True
