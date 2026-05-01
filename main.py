import argparse

from server import app, socketio, configure_demo_mode, configure_node_runtime


def main():
    parser = argparse.ArgumentParser(
        description="Run a PQC blockchain node with peer networking support."
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind")
    parser.add_argument("--difficulty", type=int, default=3, help="Proof-of-work difficulty")
    parser.add_argument("--reward", type=float, default=50.0, help="Mining reward amount")
    parser.add_argument("--demo", action="store_true", help="Enable demo mode presets")
    parser.add_argument(
        "--presentation",
        action="store_true",
        help="Enable presentation mode with verbose logs and simplified demo responses",
    )
    parser.add_argument(
        "--teaching",
        action="store_true",
        help="Enable educational logs that explain cryptographic and blockchain steps",
    )
    args = parser.parse_args()

    if args.presentation:
        configure_demo_mode(
            difficulty=3,
            reward_enabled=True,
            verbose=True,
            mining_reward=50.0,
            presentation_mode=True,
            teaching_mode=args.teaching,
        )
    elif args.demo:
        # Demo mode keeps mining practical on laptops and enables verbose narration.
        configure_demo_mode(
            difficulty=3,
            reward_enabled=True,
            verbose=True,
            mining_reward=50.0,
            presentation_mode=False,
            teaching_mode=args.teaching,
        )
    else:
        configure_demo_mode(
            difficulty=args.difficulty,
            reward_enabled=True,
            verbose=False,
            mining_reward=args.reward,
            presentation_mode=False,
            teaching_mode=args.teaching,
        )

    configure_node_runtime(host=args.host, port=args.port)

    # Each process started on a different port acts as an independent node.
    socketio.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()