from core.agent import chat

if __name__ == "__main__":
    print("Misty AI started (type 'exit' to quit)\n")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Misty.")
            break

        if not user:
            continue

        if user.lower() == "exit":
            break

        response = chat(user, verbose=True)
        print("Misty:", response)
