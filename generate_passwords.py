#!/usr/bin/env python3
"""
Generate random passwords for jukebox users
"""
import secrets
import string
from werkzeug.security import generate_password_hash

# User list
users = ['catherine', 'tim', 'alex', 'libby']

def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def main():
    print("Generating passwords for jukebox users...")
    print("=" * 50)
    
    passwords = {}
    hashed_passwords = {}
    
    # Generate passwords for each user
    for user in users:
        password = generate_password()
        passwords[user] = password
        hashed_passwords[user] = generate_password_hash(password)
        print(f"{user:<10}: {password}")
    
    # Save plain text passwords for reference
    with open('user_passwords.txt', 'w') as f:
        f.write("Jukebox User Passwords\n")
        f.write("=" * 30 + "\n\n")
        f.write("KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT\n\n")
        for user in users:
            f.write(f"{user:<10}: {passwords[user]}\n")
    
    # Save hashed passwords for the application
    with open('hashed_passwords.py', 'w') as f:
        f.write("# Hashed passwords for jukebox users\n")
        f.write("# Generated automatically - do not edit manually\n\n")
        f.write("USERS = {\n")
        for user in users:
            f.write(f'    "{user}": "{hashed_passwords[user]}",\n')
        f.write("}\n")
    
    print("\n" + "=" * 50)
    print("Files created:")
    print("- user_passwords.txt (plain text passwords - for your reference)")
    print("- hashed_passwords.py (hashed passwords - for the app)")
    print("\nIMPORTANT: Add user_passwords.txt to .gitignore!")

if __name__ == "__main__":
    main()