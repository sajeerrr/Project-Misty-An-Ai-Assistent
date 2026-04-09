from core.agent import chat

if __name__ == "__main__":
    print("🤖 Misty AI Started (type 'exit' to quit)\n")

    while True:
        user = input("You: ")

        if user.lower() == "exit":
            break

        response = chat(user)
        print("Misty:", response)