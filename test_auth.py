"""
Test script to verify authentication is working correctly.

Run this script to test:
1. User registration
2. Password hashing
3. User login
4. Password verification

Usage:
    python test_auth.py
"""

import sys
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import create_user, authenticate_user, get_db, init_db

def test_password_hashing():
    """Test that password hashing and verification work correctly."""
    print("\n=== Testing Password Hashing ===")
    
    test_password = "testpass123"
    
    # Generate hash
    hashed = generate_password_hash(test_password, method='pbkdf2:sha256')
    print(f"Original password: {test_password}")
    print(f"Hashed password: {hashed}")
    
    # Verify correct password
    is_correct = check_password_hash(hashed, test_password)
    print(f"Correct password verification: {is_correct}")
    
    # Verify wrong password
    is_wrong = check_password_hash(hashed, "wrongpassword")
    print(f"Wrong password verification: {is_wrong}")
    
    assert is_correct == True, "Correct password should verify!"
    assert is_wrong == False, "Wrong password should not verify!"
    
    print("✓ Password hashing works correctly!")
    return True


def test_user_registration():
    """Test creating a user in the database."""
    print("\n=== Testing User Registration ===")
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Create test user
    test_username = "test_user_" + str(hash("test"))[-6:]
    test_password = "secure_password_123"
    
    try:
        user_id = create_user(test_username, test_password)
        print(f"✓ User created with ID: {user_id}")
        
        # Verify user exists in database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            print(f"✓ User found in database: {user[1]}")
            print(f"✓ Password is hashed: {user[2][:30]}...")
            
            # Verify the hash is correct
            is_valid = check_password_hash(user[2], test_password)
            print(f"✓ Password hash verification: {is_valid}")
            
            return user_id, test_username, test_password
        else:
            print("✗ User not found in database!")
            return None
            
    except ValueError as e:
        print(f"✗ Registration failed: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def test_user_authentication(username, password):
    """Test authenticating a user."""
    print("\n=== Testing User Authentication ===")
    
    # Test with correct credentials
    user_id = authenticate_user(username, password)
    if user_id:
        print(f"✓ Login successful with user_id: {user_id}")
    else:
        print("✗ Login failed with correct credentials!")
        return False
    
    # Test with wrong password
    wrong_user_id = authenticate_user(username, "wrong_password")
    if wrong_user_id is None:
        print("✓ Login correctly rejected wrong password")
    else:
        print("✗ Login incorrectly accepted wrong password!")
        return False
    
    # Test with non-existent user
    fake_user_id = authenticate_user("nonexistent_user_12345", password)
    if fake_user_id is None:
        print("✓ Login correctly rejected non-existent user")
    else:
        print("✗ Login incorrectly accepted non-existent user!")
        return False
    
    return True


def test_duplicate_registration():
    """Test that duplicate usernames are rejected."""
    print("\n=== Testing Duplicate Registration ===")
    
    username = "duplicate_test_user"
    password = "password123"
    
    try:
        # First registration should succeed
        user_id_1 = create_user(username, password)
        print(f"✓ First registration successful: user_id={user_id_1}")
    except Exception as e:
        print(f"Note: User might already exist from previous test: {e}")
    
    try:
        # Second registration should fail
        user_id_2 = create_user(username, password)
        print(f"✗ Duplicate registration should have failed but didn't!")
        return False
    except ValueError as e:
        print(f"✓ Duplicate registration correctly rejected: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Run all authentication tests."""
    print("=" * 60)
    print("AUTHENTICATION SYSTEM TEST")
    print("=" * 60)
    
    try:
        # Test 1: Password hashing
        if not test_password_hashing():
            print("\n✗ FAILED: Password hashing test")
            return False
        
        # Test 2: User registration
        result = test_user_registration()
        if not result:
            print("\n✗ FAILED: User registration test")
            return False
        
        user_id, username, password = result
        
        # Test 3: User authentication
        if not test_user_authentication(username, password):
            print("\n✗ FAILED: User authentication test")
            return False
        
        # Test 4: Duplicate registration
        if not test_duplicate_registration():
            print("\n✗ FAILED: Duplicate registration test")
            return False
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour authentication system is working correctly.")
        print("\nYou can now:")
        print("1. Start your Flask server: python server.py")
        print("2. Test with Postman or frontend")
        print("\nTo register a new user:")
        print("  POST /register")
        print("  Body: {\"username\": \"yourname\", \"password\": \"yourpass\"}")
        print("\nTo login:")
        print("  POST /login")
        print("  Body: {\"username\": \"yourname\", \"password\": \"yourpass\"}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
