#include <iostream>
#include <string>
using namespace std;

// Function to compute square
int square(int x) {
    return x * x;
}

int main() {
    int a = 5;
    int arr[3];            // Array declaration
    string msg = "Hello";  // String

    cout << "Enter a number: ";
    int b;
    cin >> b;              // Input

    // Fill array with square of (i + b)
    for (int i = 0; i < 3; i++) {
        arr[i] = square(i + b);
    }

    // Print message while a < 10
    while (a < 10) {
        cout << msg << " " << a << endl;
        a++;
    }

    // Conditional output
    if (b > 10) {
        cout << "Big number!" << endl;
    } else {
        cout << "Small number!" << endl;
    }

    // Print array values for verification
    cout << "Array values: ";
    for (int i = 0; i < 3; i++) {
        cout << arr[i] << " ";
    }
    cout << endl;

    return 0;
}
