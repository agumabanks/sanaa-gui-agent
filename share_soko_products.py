#!/usr/bin/env python3
"""Fetch Soko products and share them via WhatsApp Web or the WhatsApp app."""

from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
import tempfile
import textwrap
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import quote, urlparse

import requests


DEFAULT_BASE_URL = "https://soko.sanaa.ug/api/v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Soko products from the public API and share them to a WhatsApp contact or group."
    )
    selection_mode_default = os.getenv("SOKO_SELECTION_MODE", "random").lower()
    if selection_mode_default not in {"random", "top"}:
        selection_mode_default = "random"
    parser.add_argument(
        "--selection-mode",
        choices=("random", "top"),
        default=selection_mode_default,
        help="Choose whether to pick products randomly or take the top entries (default: %(default)s)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("SOKO_API_BASE_URL", DEFAULT_BASE_URL),
        help="Override the Soko API base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--source",
        choices=("featured", "best_seller", "todays_deal", "search", "category", "custom"),
        default="featured",
        help="Which product collection to fetch (default: %(default)s)",
    )
    parser.add_argument("--page", type=int, default=1, help="Page number for paginated endpoints")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of products to include in the message")
    parser.add_argument("--query", help="Search text used when --source=search or --source=category", default="")
    parser.add_argument(
        "--category-id",
        type=int,
        help="Category id to use when --source=category",
    )
    parser.add_argument(
        "--custom-path",
        help="Custom endpoint path relative to the base URL when --source=custom (e.g. products/featured)",
    )
    parser.add_argument(
        "--destination",
        choices=("contact", "group"),
        required=True,
        help="Where to send the WhatsApp message",
    )
    parser.add_argument(
        "--phone",
        help="Recipient phone number in international format (required when --destination=contact)",
    )
    parser.add_argument(
        "--group-id",
        help="WhatsApp Web group id (required when --destination=group)",
    )
    parser.add_argument(
        "--wait-time",
        type=int,
        default=int(os.getenv("WHATSAPP_WAIT_TIME", 20)),
        help="Seconds pywhatkit waits for WhatsApp Web to load",
    )
    parser.add_argument(
        "--close-time",
        type=int,
        default=int(os.getenv("WHATSAPP_CLOSE_TIME", 5)),
        help="Seconds before pywhatkit closes the browser tab",
    )
    parser.add_argument(
        "--client",
        choices=("web", "app"),
        default=os.getenv("WHATSAPP_CLIENT", "web").lower(),
        help="Choose whether to launch WhatsApp Web or the WhatsApp app (default: %(default)s)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactively pick which product to share",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the payload instead of sending it",
    )
    return parser.parse_args()


def build_request(base_url: str, args: argparse.Namespace) -> Tuple[str, Dict[str, Any]]:
    source = args.source
    params: Dict[str, Any] = {}

    if source == "featured":
        path = "products/featured"
        params["page"] = args.page
    elif source == "best_seller":
        path = "products/best-seller"
    elif source == "todays_deal":
        path = "products/todays-deal"
    elif source == "search":
        path = "products/search"
        params.update({
            "page": args.page,
            "name": args.query or "",
        })
    elif source == "category":
        if args.category_id is None:
            raise ValueError("--category-id is required when --source=category")
        path = f"products/category/{args.category_id}"
        params.update({
            "page": args.page,
            "name": args.query or "",
        })
    elif source == "custom":
        if not args.custom_path:
            raise ValueError("--custom-path is required when --source=custom")
        path = args.custom_path
    else:
        raise ValueError(f"Unsupported source {source}")

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    return url, params


def fetch_products(url: str, params: Dict[str, Any], language: str = "en") -> List[Dict[str, Any]]:
    headers = {"App-Language": language}
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()
    products = payload.get("data") or payload.get("products") or []
    if not isinstance(products, list):
        raise ValueError("Unexpected payload: 'data' is not a list")
    return products


def format_product_message(product: Dict[str, Any], base_url: str, selection_mode: str) -> str:
    name = (product.get("name") or "Unnamed product").strip()
    price = product.get("main_price") or "Price unavailable"
    links = product.get("links") or {}
    details = None
    if isinstance(links, dict):
        details = links.get("details")
    if details and details.startswith("/"):
        details = f"{base_url.rstrip('/')}{details}"
    if not details:
        details = f"{base_url.rstrip('/')}/products/{product.get('id')}"

    header = "Soko product highlight ({} selection):".format(
        "random" if selection_mode == "random" else "top"
    )

    block = textwrap.dedent(
        f"""
        {name}
        Price: {price}
        Link: {details}
        """
    ).strip()

    return f"{header}\n\n{block}"


def pick_candidate_products(
    products: List[Dict[str, Any]], limit: int, selection_mode: str
) -> List[Dict[str, Any]]:
    if not products:
        return []

    limit = max(limit, 1)
    if selection_mode == "random":
        if limit >= len(products):
            return products.copy()
        return random.sample(products, limit)
    return products[:limit]


def prompt_for_product(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("Select a product to share:")
    for idx, product in enumerate(candidates, start=1):
        name = (product.get("name") or "Unnamed product").strip()
        price = product.get("main_price") or "Price unavailable"
        print(f"  {idx}. {name} — {price}")

    while True:
        choice = input("Enter product number (default 1): ").strip()
        if not choice:
            return candidates[0]
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(candidates):
                return candidates[index - 1]
        print("Invalid selection. Please try again.")


def select_product(
    products: List[Dict[str, Any]],
    limit: int,
    selection_mode: str,
    interactive: bool,
) -> Dict[str, Any] | None:
    candidates = pick_candidate_products(products, limit, selection_mode)
    if not candidates:
        return None

    if interactive and sys.stdin.isatty():
        try:
            return prompt_for_product(candidates)
        except (KeyboardInterrupt, EOFError):
            print()
            return None

    if selection_mode == "random":
        return random.choice(candidates)
    return candidates[0]


def open_url(url: str) -> bool:
    try:
        opened = webbrowser.open(url, new=2)
    except webbrowser.Error:
        opened = False
    if opened:
        return True

    if sys.platform.startswith("darwin"):
        result = subprocess.run(["open", url], check=False)
        return result.returncode == 0
    if os.name == "nt":
        result = subprocess.run(["start", "", url], shell=True, check=False)
        return result.returncode == 0

    result = subprocess.run(["xdg-open", url], check=False)
    return result.returncode == 0


def extract_image_url(product: Dict[str, Any], base_url: str) -> str | None:
    image_url = product.get("thumbnail_image")
    if not isinstance(image_url, str) or not image_url.strip():
        return None

    image_url = image_url.strip()
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url

    return f"{base_url.rstrip('/')}/{image_url.lstrip('/')}"


def download_image(image_url: str) -> Path | None:
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to download image: {exc}", file=sys.stderr)
        return None

    suffix = Path(urlparse(image_url).path).suffix or ".jpg"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
        return Path(temp_file.name)
    except OSError as exc:
        print(f"Failed to store image: {exc}", file=sys.stderr)
        return None


def load_pywhatkit():
    try:
        import pywhatkit as kit  # type: ignore
    except ImportError as exc:  # pragma: no cover - import guard
        raise SystemExit(
            "pywhatkit is required for WhatsApp automation. Install it with 'pip install pywhatkit'."
        ) from exc
    return kit


def send_whatsapp_message(
    message: str,
    destination: str,
    phone: str | None,
    group_id: str | None,
    wait_time: int,
    close_time: int,
    client: str,
    image_path: Path | None,
) -> None:
    if client != "web":
        raise SystemExit("Automatic sending with images is only supported when --client=web.")

    kit = load_pywhatkit()

    if destination == "contact":
        if not phone:
            raise SystemExit("--phone is required when --destination=contact")
        if image_path:
            kit.sendwhats_image(
                receiver=phone,
                img_path=str(image_path),
                caption=message,
                wait_time=wait_time,
                tab_close=True,
                close_time=close_time,
            )
        else:
            kit.sendwhatmsg_instantly(
                phone, message, wait_time=wait_time, tab_close=True, close_time=close_time
            )
        return

    if not group_id:
        raise SystemExit("--group-id is required when --destination=group")

    if image_path:
        kit.sendwhats_image(
            receiver=group_id,
            img_path=str(image_path),
            caption=message,
            wait_time=wait_time,
            tab_close=True,
            close_time=close_time,
        )
    else:
        kit.sendwhatmsg_to_group_instantly(
            group_id, message, wait_time=wait_time, tab_close=True, close_time=close_time
        )


def main() -> None:
    args = parse_args()

    try:
        url, params = build_request(args.base_url, args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    try:
        products = fetch_products(url, params)
    except requests.HTTPError as exc:
        raise SystemExit(f"API request failed: {exc}") from exc
    except requests.RequestException as exc:
        raise SystemExit(f"Network error: {exc}") from exc
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    product = select_product(products, args.limit, args.selection_mode, args.interactive)
    if not product:
        print("No products found for the requested source.")
        return

    resolved_base = DEFAULT_BASE_URL if args.base_url == DEFAULT_BASE_URL else args.base_url
    message = format_product_message(product, resolved_base, args.selection_mode)
    image_url = extract_image_url(product, resolved_base)

    if args.dry_run:
        print(message)
        if image_url:
            print(f"Image: {image_url}")
        return

    image_path: Path | None = None
    try:
        if image_url:
            image_path = download_image(image_url)

        send_whatsapp_message(
            message=message,
            destination=args.destination,
            phone=args.phone,
            group_id=args.group_id,
            wait_time=args.wait_time,
            close_time=args.close_time,
            client=args.client,
            image_path=image_path,
        )
    except SystemExit as exc:
        raise
    except Exception as exc:  # pragma: no cover - pywhatkit may raise assorted exceptions
        raise SystemExit(f"Failed to send WhatsApp message: {exc}") from exc
    finally:
        if image_path is not None:
            try:
                image_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code:
            print(exc, file=sys.stderr)
        sys.exit(exc.code if isinstance(exc.code, int) else 1)
