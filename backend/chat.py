from agent import llm, provider


def main() -> None:
    print(f"Using {provider.name} ({provider.model}). Type quit or exit to stop.")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() in {"quit", "exit"}:
            break

        response = llm.invoke(user_input)
        print(response.content)


if __name__ == "__main__":
    main()
