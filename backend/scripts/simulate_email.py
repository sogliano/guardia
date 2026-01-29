#!/usr/bin/env python3
"""Guard-IA Email Simulator — send realistic emails to the SMTP gateway.

Simulates the production flow where Google Workspace routes inbound mail
through Guard-IA as an inbound gateway before delivering to Gmail.

Production:
  Internet → MX DNS → Guard-IA:2525 → pipeline → relay to aspmx.l.google.com

Local simulation:
  This script → smtplib → Guard-IA:2525 → pipeline → (relay skipped / fails gracefully)

Usage:
  # Send a single template
  python -m scripts.simulate_email --template phishing

  # Send all templates
  python -m scripts.simulate_email --all

  # Custom recipient and gateway
  python -m scripts.simulate_email --template bec --to ciso@strike.sh

  # List available templates
  python -m scripts.simulate_email --list

  # Send N copies with delay (load simulation)
  python -m scripts.simulate_email --template phishing --count 5 --delay 1.0
"""

import argparse
import smtplib
import sys
import time

from email.policy import SMTP as SMTP_POLICY

from scripts.email_templates import TEMPLATES


def send_email(
    host: str,
    port: int,
    template_name: str,
    recipient: str,
    verbose: bool = False,
) -> bool:
    """Send a single simulated email to the Guard-IA SMTP gateway.

    Returns True on success (250 response), False otherwise.
    """
    factory, description = TEMPLATES[template_name]
    msg = factory(recipient)

    sender = msg["From"]
    to = msg["To"]
    subject = msg["Subject"]

    if verbose:
        print(f"  From:    {sender}")
        print(f"  To:      {to}")
        print(f"  Subject: {subject}")
        print(f"  Auth:    {msg.get('Authentication-Results', 'N/A')[:80]}...")

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo("simulator.guardia.local")
            refused = smtp.sendmail(
                from_addr=msg["From"],
                to_addrs=[to],
                msg=msg.as_bytes(policy=SMTP_POLICY),
            )

            if verbose:
                if refused:
                    print(f"  SMTP: some recipients refused: {refused}")
                else:
                    print("  SMTP: 250 OK — accepted by gateway")

            return len(refused) == 0

    except smtplib.SMTPResponseException as e:
        # Gateway returned an SMTP error (550 blocked, etc.) — this is expected behavior
        error_msg = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        if verbose:
            print(f"  SMTP {e.smtp_code}: {error_msg}")
        return e.smtp_code == 250

    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        print(f"  ERROR: {e}")
        return False


def list_templates() -> None:
    """Print all available email templates."""
    print("\nAvailable email templates:\n")
    for name, (_, desc) in sorted(TEMPLATES.items()):
        print(f"  {name:<12} {desc}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Guard-IA Email Simulator — send realistic emails to the SMTP gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m scripts.simulate_email --template phishing\n"
            "  python -m scripts.simulate_email --all\n"
            "  python -m scripts.simulate_email --template bec --count 3 --delay 2\n"
            "  python -m scripts.simulate_email --list\n"
        ),
    )
    parser.add_argument(
        "--template", "-t",
        choices=list(TEMPLATES.keys()),
        help="Email template to send",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Send all templates (one of each)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available email templates",
    )
    parser.add_argument(
        "--to",
        default="analyst@strike.sh",
        help="Recipient address (default: analyst@strike.sh)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="SMTP gateway host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=2525,
        help="SMTP gateway port (default: 2525)",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of copies to send (default: 1)",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=0.5,
        help="Delay between sends in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Show detailed output (default: on)",
    )

    args = parser.parse_args()

    if args.list:
        list_templates()
        return

    if not args.template and not args.all:
        parser.print_help()
        print("\nError: specify --template NAME or --all")
        sys.exit(1)

    templates_to_send = list(TEMPLATES.keys()) if args.all else [args.template]

    print(f"\n{'='*60}")
    print("  Guard-IA Email Simulator")
    print(f"  Gateway: {args.host}:{args.port}")
    print(f"  Recipient: {args.to}")
    print(f"{'='*60}\n")

    total = 0
    success = 0
    blocked = 0

    for template_name in templates_to_send:
        _, description = TEMPLATES[template_name]

        for i in range(args.count):
            total += 1
            label = f"[{total}]" if args.count > 1 or args.all else ""
            print(f"{label} Sending: {template_name} — {description}")

            ok = send_email(
                host=args.host,
                port=args.port,
                template_name=template_name,
                recipient=args.to,
                verbose=args.verbose,
            )

            if ok:
                success += 1
                print("  Result: ACCEPTED (email entered pipeline)\n")
            else:
                blocked += 1
                print("  Result: BLOCKED/QUARANTINED by pipeline\n")

            if i < args.count - 1 or template_name != templates_to_send[-1]:
                time.sleep(args.delay)

    print(f"{'='*60}")
    print(f"  Summary: {total} sent, {success} accepted, {blocked} blocked/quarantined")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
