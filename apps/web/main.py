from datetime import datetime


def main() -> None:
    print("[apps/web] skeleton runner")
    print(f"timestamp={datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()
