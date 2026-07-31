from tools.read_file import write_local_file, read_local_file

# Step 1: Tell the system to write an encrypted file
print("Step 1: Saving the secret file...")
write_message = write_local_file("test_secret.txt", "Hello CRYOUS, this is a top-secret test!")
print(write_message)

# Step 2: Tell the system to read and decrypt that same file
print("\nStep 2: Reading the secret file...")
read_message = read_local_file("test_secret.txt")
print(read_message)