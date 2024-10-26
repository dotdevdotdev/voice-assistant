import sys
from application import Application


def main():
    try:
        app = Application()
        return app.run()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
