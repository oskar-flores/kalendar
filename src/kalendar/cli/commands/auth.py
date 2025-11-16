"""Auth command - OAuth authorization flow."""


def auth_command(args) -> int:
    """Execute auth command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("Kalendar - Calendar Authorization")
    print("=" * 50)

    if args.service == "google":
        return auth_google(args)
    else:
        print(f"Error: Unknown service '{args.service}'")
        return 1


def auth_google(args) -> int:
    """Run Google OAuth authorization flow.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    from pathlib import Path

    credentials_path = Path(args.credentials)

    if not credentials_path.exists():
        print(f"\nError: Credentials file not found: {credentials_path}")
        print("\nTo get credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download credentials JSON")
        print(f"6. Save as: {credentials_path}")
        return 1

    print(f"\nGoogle Calendar Authorization")
    print(f"Credentials: {credentials_path}")
    print()

    try:
        # Import Google auth libraries
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

        # Token file path (save next to credentials)
        token_path = credentials_path.parent / "google_token.json"

        creds = None

        # Check if token already exists
        if token_path.exists():
            print("Existing token found, refreshing...")
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired token...")
                creds.refresh(Request())
            else:
                print("Starting OAuth authorization flow...")
                print("A browser window will open for authorization")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            print(f"Saving token to: {token_path}")
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())

        print("\n✓ Authorization successful!")
        print(f"\nToken saved to: {token_path}")
        print("\nUpdate your config/credentials.json:")
        print("{")
        print('  "google": {')
        print(f'    "token_file": "{token_path}",')
        print(f'    "credentials_file": "{credentials_path}"')
        print("  }")
        print("}")

        return 0

    except ImportError:
        print("\nError: Google Calendar libraries not installed")
        print("Install with: uv add google-auth google-auth-oauthlib google-api-python-client")
        return 1

    except Exception as e:
        print(f"\nError: Authorization failed")
        print(f"  {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1
