# Translated from C++ (subset) to Python
def square(x):
    return (x * x)
a = 5
arr = [0] * 3
msg = "Hello"
print("Enter a number: ")
b = 0
b = input()
for i in range(0, 3):
    arr[i] = square((i + b))
while (a < 10):
    print(msg, " ", a)
    a = a + 1
if (b > 10):
    print("Big number!")
else:
    print("Small number!")
print("Array values: ")
for i in range(0, 3):
    print(arr[i], " ")
print()
