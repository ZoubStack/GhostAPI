"""CLI for ghostapi."""

import sys
import argparse
from typing import Optional

from ghostapi import create_api, get_app


def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    debug: bool = False
) -> None:
    """
    Run the ghostapi server.
    
    Args:
        host: Server host.
        port: Server port.
        reload: Enable auto-reload.
        debug: Enable debug mode.
    """
    import uvicorn
    from ghostapi import get_app
    
    app = get_app()
    
    if app is None:
        print("Error: No app created. Call expose() or create_api() first.")
        sys.exit(1)
    
    print(f"\n🚀 Starting GhostAPI server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"\n📚 API Documentation: http://{host}:{port}/docs")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info" if debug else "warning"
    )


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GhostAPI - Transform Python functions into REST APIs"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the API server")
    run_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    run_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload"
    )
    run_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    # New function command
    new_parser = subparsers.add_parser("new", help="Create a new API function")
    new_parser.add_argument(
        "--name",
        type=str,
        help="Function name"
    )
    new_parser.add_argument(
        "--route",
        type=str,
        help="Route path (e.g., /users/create)"
    )
    new_parser.add_argument(
        "--method",
        type=str,
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP method"
    )
    new_parser.add_argument(
        "--auth",
        type=str,
        help="Authentication level (user, admin, or custom role)"
    )
    new_parser.add_argument(
        "--rate-limit",
        type=str,
        help="Rate limit in requests per minute"
    )
    new_parser.add_argument(
        "--cache",
        type=str,
        help="Cache TTL in seconds"
    )
    new_parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Launch interactive mode"
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        run(
            host=args.host,
            port=args.port,
            reload=args.reload,
            debug=args.debug
        )
    elif args.command == "new":
        new_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


def interactive_new() -> None:
    """
    Interactive CLI for creating new ghostapi functions.
    
    Example:
        ghostapi new function create_user --auth=user --rate-limit=10
    """
    print("\n🧙‍♂️ GhostAPI - New Function Generator\n")
    print("=" * 50)
    
    # Get function name
    print("\n📝 Creating a new API function...\n")
    
    # Function type selection
    print("Select function type:")
    print("  1. Simple function (GET)")
    print("  2. Data processing (POST)")
    print("  3. CRUD operation")
    print("  4. Custom")
    
    type_choice = input("\nType [1-4]: ").strip() or "1"
    
    # Get function name
    func_name = input("\n📌 Function name (e.g., create_user): ").strip()
    if not func_name:
        print("❌ Error: Function name is required")
        return
    
    # Get route path
    route_path = input("📍 Route path (e.g., /users/create): ").strip() or f"/{func_name.replace('_', '-')}"
    
    # HTTP method
    http_methods = {"1": "GET", "2": "POST", "3": "PUT", "4": "DELETE"}
    print("\n🌐 HTTP Method:")
    print("  1. GET (read)")
    print("  2. POST (create)")
    print("  3. PUT (update)")
    print("  4. DELETE (delete)")
    
    method_choice = input("Method [1-4]: ").strip() or "1"
    http_method = http_methods.get(method_choice, "GET")
    
    # Authentication
    print("\n🔐 Authentication:")
    print("  1. None (public)")
    print("  2. User (requires login)")
    print("  3. Admin (requires admin role)")
    print("  4. Custom role")
    
    auth_choice = input("Auth level [1-4]: ").strip() or "1"
    auth_map = {"1": None, "2": "user", "3": "admin"}
    
    auth = auth_map.get(auth_choice)
    if auth_choice == "4":
        auth = input("   Enter custom role: ").strip()
    
    # Rate limiting
    print("\n⚡ Rate Limiting:")
    print("  1. None (unlimited)")
    print("  2. Low (10 req/min)")
    print("  3. Medium (60 req/min)")
    print("  4. High (100 req/min)")
    print("  5. Custom")
    
    rate_choice = input("Rate limit [1-5]: ").strip() or "1"
    rate_map = {"1": None, "2": "10", "3": "60", "4": "100"}
    
    rate_limit = rate_map.get(rate_choice)
    if rate_choice == "5":
        rate_limit = input("   Enter custom limit (req/min): ").strip()
    
    # Caching
    print("\n💾 Caching:")
    print("  1. None")
    print("  2. 5 minutes")
    print("  3. 15 minutes")
    print("  4. 1 hour")
    print("  5. Custom")
    
    cache_choice = input("Cache [1-5]: ").strip() or "1"
    cache_map = {"1": None, "2": "300", "3": "900", "4": "3600"}
    
    cache_ttl = cache_map.get(cache_choice)
    if cache_choice == "5":
        cache_ttl = input("   Enter custom TTL (seconds): ").strip()
    
    # Generate the function code
    print("\n" + "=" * 50)
    print("\n✅ Generating function...\n")
    
    # Build decorators
    decorators = []
    if auth:
        decorators.append(f'@require_auth("{auth}")')
    if rate_limit:
        decorators.append(f'@rate_limit({rate_limit})')
    if cache_ttl:
        decorators.append(f'@cache(ttl={cache_ttl})')
    
    decorator_str = "\n".join(decorators)
    if decorator_str:
        decorator_str += "\n"
    
    # Determine parameters based on method
    params = ""
    if http_method in ["POST", "PUT"]:
        params = "    data: dict = {}\n"
    else:
        params = "    id: str = None\n"
    
    # Generate code
    code = f'''from ghostapi import expose, require_auth, rate_limit, cache

{decorator_str}def {func_name}({params}) -> dict:
    """
    {http_method} {route_path}
    
    Autogenerated by GhostAPI CLI.
    """
    # TODO: Implement your logic here
    return {{
        "success": True,
        "message": "{func_name} executed successfully"
    }}

# Expose the function as an API endpoint
@expose("{route_path}", method="{http_method}")
def {func_name}_endpoint({params}):
    """API endpoint wrapper."""
    return {func_name}({params.strip()})
'''
    
    # Write to file
    output_file = f"{func_name}_api.py"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"📄 Created: {output_file}")
    print(f"\n📍 Route: {http_method} {route_path}")
    
    if auth:
        print(f"🔐 Auth: Required ({auth})")
    if rate_limit:
        print(f"⚡ Rate limit: {rate_limit} req/min")
    if cache_ttl:
        print(f"💾 Cache: {cache_ttl}s TTL")
    
    print("\n✨ Run with: ghostapi run")
    print("=" * 50)


def new_command(args) -> None:
    """Handle 'ghostapi new' command."""
    if args.interactive:
        interactive_new()
        return
    
    # Non-interactive mode (from args)
    func_name = args.name
    route_path = args.route or f"/{func_name.replace('_', '-')}"
    http_method = args.method.upper()
    auth = args.auth
    rate_limit_val = args.rate_limit
    cache_ttl = args.cache
    
    # Build decorators
    decorators = []
    if auth:
        decorators.append(f'@require_auth("{auth}")')
    if rate_limit_val:
        decorators.append(f'@rate_limit({rate_limit_val})')
    if cache_ttl:
        decorators.append(f'@cache(ttl={cache_ttl})')
    
    decorator_str = "\n".join(decorators)
    if decorator_str:
        decorator_str += "\n"
    
    # Parameters
    params = ""
    if http_method in ["POST", "PUT"]:
        params = "    data: dict = {}\n"
    else:
        params = "    id: str = None\n"
    
    # Generate code
    code = f'''from ghostapi import expose, require_auth, rate_limit, cache

{decorator_str}def {func_name}({params}) -> dict:
    """
    {http_method} {route_path}
    
    Autogenerated by GhostAPI CLI.
    """
    # TODO: Implement your logic here
    return {{
        "success": True,
        "message": "{func_name} executed successfully"
    }}

# Expose the function as an API endpoint
@expose("{route_path}", method="{http_method}")
def {func_name}_endpoint({params}):
    """API endpoint wrapper."""
    return {func_name}({params.strip()})
'''
    
    output_file = f"{func_name}_api.py"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"✅ Created: {output_file}")
    print(f"📍 Route: {http_method} {route_path}")
    if auth:
        print(f"🔐 Auth: {auth}")
    if rate_limit_val:
        print(f"⚡ Rate limit: {rate_limit_val} req/min")
    if cache_ttl:
        print(f"💾 Cache: {cache_ttl}s TTL")
    print()
