"""
Test script for attack detection and auto-suspension system.
Tests the three main scenarios:
1. One attack → Active
2. Two attacks → Suspended
3. Ten attacks → Banned
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "attacker@test.com"
TEST_PASSWORD = "TestPass123!"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_attack_detection():
    print_header("🧪 Attack Detection System Test")
    
    # Step 1: Register test user
    print("📝 Step 1: Registering test user...")
    try:
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "role": "BUYER"
            },
            timeout=5
        )
        if register_response.status_code in [200, 201]:
            print(f"✅ User registered successfully")
        elif register_response.status_code == 400:
            print(f"ℹ️  User already exists (continuing with existing user)")
        else:
            print(f"⚠️  Registration status: {register_response.status_code}")
    except Exception as e:
        print(f"⚠️  Registration error (user may already exist): {e}")
    
    time.sleep(1)
    
    # Step 2: First attack (should stay active)
    print_header("Test Case 1: One Attack → Active")
    print("🎯 Attempting first attack (SQL injection)...")
    try:
        attack1 = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": "' OR 1=1 --"
            },
            timeout=5
        )
        print(f"✅ Attack 1 sent (status: {attack1.status_code})")
        print(f"📊 Expected: attack_count=1, status=active")
    except Exception as e:
        print(f"❌ Attack 1 error: {e}")
    
    time.sleep(2)
    
    # Step 3: Second attack (should trigger suspension)
    print_header("Test Case 2: Two Attacks → Suspended")
    print("🎯 Attempting second attack (should suspend user)...")
    try:
        attack2 = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": "admin' UNION SELECT * FROM users--"
            },
            timeout=5
        )
        print(f"✅ Attack 2 sent (status: {attack2.status_code})")
        print(f"📊 Expected: attack_count=2, status=suspended")
        print(f"⚠️  User should be SUSPENDED now")
    except Exception as e:
        print(f"❌ Attack 2 error: {e}")
    
    time.sleep(2)
    
    # Step 4: Continue to 10 attacks (should trigger ban)
    print_header("Test Case 3: Ten Attacks → Banned")
    print("🎯 Sending attacks 3-10 (should ban user)...")
    for i in range(3, 11):
        try:
            attack = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": f"test{i}' OR 1=1 --"
                },
                timeout=5
            )
            print(f"  ✅ Attack {i} sent")
        except Exception as e:
            print(f"  ❌ Attack {i} error: {e}")
        time.sleep(0.5)
    
    print(f"\n📊 Expected: attack_count=10, status=banned")
    print(f"🚫 User should be BANNED now")
    
    time.sleep(2)
    
    # Step 5: Verify user cannot login
    print_header("Verification: User Cannot Login")
    print("🔒 Attempting to login with correct credentials...")
    try:
        login_attempt = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=5
        )
        print(f"Login status: {login_attempt.status_code}")
        if login_attempt.status_code in [401, 403]:
            print(f"✅ Login blocked (account banned/suspended)")
        else:
            print(f"⚠️  Unexpected status: {login_attempt.status_code}")
            print(f"Response: {login_attempt.text[:200]}")
    except Exception as e:
        print(f"❌ Login verification error: {e}")
    
    # Final summary
    print_header("Test Complete - Verification Steps")
    print("📋 To verify the results:")
    print("1. Open Admin Dashboard: http://localhost:4201/#/secure-admin/login")
    print("2. Go to Users tab")
    print(f"3. Find user: {TEST_EMAIL}")
    print("4. Click to view details")
    print("\n✅ Expected Results:")
    print("   - Attack Attempts: 10")
    print("   - Status: Suspended (Banned)")
    print("   - Security Status: 'User is banned (10+ attacks)'")
    print("   - Ban record in database")
    print("\n💡 Check backend logs:")
    print("   tail -f backend/logs/application.log")
    print("\n" + "="*60)

if __name__ == "__main__":
    print("\n⚠️  Make sure backend is running on http://localhost:8000")
    print("Press Enter to start test...")
    input()
    
    try:
        test_attack_detection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")

