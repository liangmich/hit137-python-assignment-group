def shift_char(c, shift_amount):
    """
    Shifts an alphabetic character 'c' by 'shift_amount', using modulo to wrap around the alphabet.
     - For lowercase letters, it wraps around 'a' to 'z' and vice versa.
     - For uppercase letters, it wraps around 'A' to 'Z' and vice versa.
     - Non-alphabetic characters remain unchanged.
    """
    if 'a' <= c <= 'z':  # If the input letter is lowercase (only shift standard ASCII letters)
        base = ord('a')  # Base ASCII value for lowercase letters
        return chr((ord(c) - base + shift_amount) % 26 + base)
        # ord(c) - base gives the position of the letter in the alphabet(0-25)
        # Adding the shift amount and using modulo 26 to wrap around the alphabet

    # If the input letter is uppercase (only shift standard ASCII letters)
    elif 'A' <= c <= 'Z':
        base = ord('A')
        return chr((ord(c) - base + shift_amount) % 26 + base)
    else:
        return c  # Non-alphabetic characters remain unchanged


def classify_char(c):
    """
    Determines the classification of a character and returns one of:
      - 'lower_first': lowercase letter in the range a-m
      - 'lower_second': lowercase letter in the range n-z
      - 'upper_first': uppercase letter in the range A-M
      - 'upper_second': uppercase letter in the range N-Z
      - 'other': non-alphabetic character
        (e.g. digits, punctuation, spaces, or non-ASCII letters like é, ñ, etc.)
      - Only standard ASCII letters (a-z, A-Z) are considered alphabetic characters.
    """
    if c.islower():
        if 'a' <= c <= 'm':
            return 'lower_first'  # If the letter is in the range a-m, return 'lower_first'
        elif 'n' <= c <= 'z':
            return 'lower_second'  # If the letter is in the range n-z, return 'lower_second'
        else:
            # If the letter is not in the range a-z (e.g. non-ASCII letter like é,ñ),return 'other'
            return 'other'
    elif c.isupper():
        if 'A' <= c <= 'M':
            return 'upper_first'  # If the letter is in the range A-M, return 'upper_first'
        elif 'N' <= c <= 'Z':
            return 'upper_second'  # If the letter is in the range N-Z, return 'upper_second'
        else:
            # If the letter is not in the range A-Z (e.g. non-ASCII letter like Ñ,Ü), return 'other'
            return 'other'

    else:
        # If the character is not a standard letter (e.g. digit, punctuation, space), return 'other'
        return 'other'


def encrypt_with_meta(text, n, m):
    """
    Encrypts the text according to the assignment rules and records the original classification for each character.
      - For lowercase letters:
           If in a-m: shift forward by n*m positions.
           If in n-z: shift backward by (n+m) positions (using a negative shift).
      - For uppercase letters:
           If in A-M: shift backward by n positions (negative shift).
           If in N-Z: shift forward by m^2 positions.
      - Non-alphabetic characters remain unchanged.
    Returns a list where each element is formatted as "encrypted_character|classification".
    """
    encrypted = []  # List to store the encrypted characters and their classifications
    for c in text:  # Iterate through each character in the input text
        ctype = classify_char(c)
        if ctype == 'lower_first':
            new_c = shift_char(c, n * m)
        elif ctype == 'lower_second':
            new_c = shift_char(c, -(n + m))
        elif ctype == 'upper_first':
            new_c = shift_char(c, -n)
        elif ctype == 'upper_second':
            new_c = shift_char(c, m ** 2)
        else:
            new_c = c
        encrypted.append(f"{new_c}|{ctype}")
    return encrypted


def decrypt_with_meta(encrypted_data, n, m):
    """
    Restores the original characters using the encrypted data and the recorded classification.
      - For 'lower_first': use a reverse shift of -(n*m)
      - For 'lower_second': use a reverse shift of +(n+m)
      - For 'upper_first': use a reverse shift of +n
      - For 'upper_second': use a reverse shift of -(m^2)
    """
    decrypted = []  # List to store the decrypted characters
    for item in encrypted_data:
        # Do not strip the line to preserve internal spaces
        if "|" not in item:
            decrypted.append(item)
            continue

        encrypted_char, ctype = item.split("|", 1)

        # Depending on the classification, apply the appropriate reverse shift
        if ctype == 'lower_first':
            original_char = shift_char(encrypted_char, -(n * m))
        elif ctype == 'lower_second':
            original_char = shift_char(encrypted_char, n + m)
        elif ctype == 'upper_first':
            original_char = shift_char(encrypted_char, n)
        elif ctype == 'upper_second':
            original_char = shift_char(encrypted_char, -(m ** 2))
        else:
            original_char = encrypted_char
        # Append the decrypted character to the list
        decrypted.append(original_char)
    # Join the decrypted characters into a single string
    return "".join(decrypted)


def verify(original, decrypted):
    """
    Checks if the decrypted text is exactly the same as the original text.
    """
    return original == decrypted


def main():
    # Get user input for n and m
    # n = int(input("Enter value for n: "))
    # m = int(input("Enter value for m: "))
    # Set fixed values for assignment output
    n = 3  # Example value for n
    m = 4  # Example value for m

    # Set file paths — please modify according to your system:
    # For Windows, use raw string literals (r"") to avoid escape sequences(r"\path\to\file.txt")
    # For Mac/Linux, use normal string literals ("/path/to/file.txt")
    # Path to the input file fit for Mac
    input_path = "/Users/iammin/Documents/IT/HIT137 Python/HIT137 Assignment 2 S1 2025/raw_text.txt"
    # Path to the output file fit for Mac
    encrypted_path = "/Users/iammin/Documents/IT/HIT137 Python/HIT137 Assignment 2 S1 2025/encrypted_text.txt"

    # Read the original file content
    with open(input_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # Encrypt the text and record metadata (classification)
    encrypted_data = encrypt_with_meta(original_text, n, m)

    # Write the encrypted data to file (each record on a new line)
    with open(encrypted_path, 'w', encoding='utf-8') as f:
        for item in encrypted_data:
            f.write(item + "\n")
    print(f"Encrypted text saved to {encrypted_path}")

    # Read the encrypted data using splitlines() to preserve internal spaces
    with open(encrypted_path, 'r', encoding='utf-8') as f:
        encrypted_lines = f.read().splitlines()

    # Decrypt the file content
    decrypted_text = decrypt_with_meta(encrypted_lines, n, m)

    # Verify if decryption was successful
    if verify(original_text, decrypted_text):
        print("✅ Decryption successful: The decrypted text matches the original.")
    else:
        print("❌ Decryption failed: The decrypted text does NOT match the original.")


if __name__ == "__main__":
    main()

