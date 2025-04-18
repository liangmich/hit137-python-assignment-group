def shift_char(c, shift_amount):
    """
    Shifts an alphabetic character 'c' by 'shift_amount' with wrap-around.
    Non-alphabetic characters remain unchanged.
    """
    if c.islower():
        base = ord('a')
        return chr((ord(c) - base + shift_amount) % 26 + base)
    elif c.isupper():
        base = ord('A')
        return chr((ord(c) - base + shift_amount) % 26 + base)
    else:
        return c

def classify_char(c):
    """
    Determines the classification of a character and returns one of:
      - 'lower_first': lowercase letter in the range a-m
      - 'lower_second': lowercase letter in the range n-z
      - 'upper_first': uppercase letter in the range A-M
      - 'upper_second': uppercase letter in the range N-Z
      - 'other': other characters (digits, punctuation, spaces, etc.)
    """
    if c.islower():
        if 'a' <= c <= 'm':
            return 'lower_first'
        elif 'n' <= c <= 'z':
            return 'lower_second'
        else:
            return 'other'
    elif c.isupper():
        if 'A' <= c <= 'M':
            return 'upper_first'
        elif 'N' <= c <= 'Z':
            return 'upper_second'
        else:
            return 'other'
    else:
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
    encrypted = []
    for c in text:
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
    decrypted = []
    for item in encrypted_data:
        # Do not strip the line to preserve internal spaces
        if "|" not in item:
            decrypted.append(item)
            continue
        encrypted_char, ctype = item.split("|", 1)
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
        decrypted.append(original_char)
    return "".join(decrypted)

def verify(original, decrypted):
    """
    Checks if the decrypted text is exactly the same as the original text.
    """
    return original == decrypted

def main():
    # Get user input parameters
    n = int(input("Enter value for n: "))
    m = int(input("Enter value for m: "))

    # Set file paths to C:\Users\ingram\Desktop\assignment
    input_path = r"C:\Users\ingram\Desktop\assignment\raw_text.txt"
    encrypted_path = r"C:\Users\ingram\Desktop\assignment\encrypted_text.txt"

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
