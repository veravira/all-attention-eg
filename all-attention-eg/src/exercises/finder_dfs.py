matrix = [
    ['A', 'B', 'Z', 'I'],
    ['E', 'Z', 'D', 'N'],
    ['P', 'B', 'O', 'C'],
    ['A', 'C', 'K', 'D']
]

word = "DOK"
def exist(matrix, word):
    index = 0
    found = False

    def dfs(i,j, index):
        if index == len(word):
            return True
        if i < 0 or i >= len(matrix) or j < 0 or j >= len(matrix[0]) or matrix[i][j] != word[index]:
            return False
        temp = matrix[i][j]
        matrix[i][j] = '%'
        print(f'(i,j)={i,j} and index ={index}')
        found = (dfs(i + 1, j, index + 1) or
                 dfs(i - 1, j, index + 1) or
                 dfs(i, j + 1, index + 1) or
                 dfs(i, j - 1, index + 1))
        matrix[i][j] = temp
        return found

    if len(word)==0:
        return True
    else:
        for i in range(len(matrix)):
            for j in range(len(matrix[0])):
                if matrix[i][j] == word[index]:
                    if dfs(i,j, index):
                        return True
        return False


print(exist(matrix, word))  # Output: True