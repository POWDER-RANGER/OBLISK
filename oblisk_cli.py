#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBLISK CLI - Multi-Agent AI System
Version: 3.0.0
Author: POWDER-RANGER
License: MIT
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, List

__version__ = "3.0.0"
__author__ = "POWDER-RANGER"
__license__ = "MIT"


class CLIConfig:
    """Configuration for CLI application."""
    
    def __init__(self):
        self.app_name = "OBLISK"
        self.version = __version__
        self.description = "Multi-Agent AI System with Encrypted Vaults & Governance"
        self.debug = False
        self.config_file: Optional[str] = None
        self.no_color = False
    
    def get_config_path(self) -> Path:
        """Get configuration file path."""
        if self.config_file:
            return Path(self.config_file)
        
        # Try multiple config locations
        candidates = [
            Path("./config.json"),
            Path("./config.yaml"),
            Path("~/.oblisk/config.json").expanduser(),
            Path("~/.oblisk/config.yaml").expanduser(),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return Path("./config.json")  # Default
    
    def load_config(self) -> dict:
        """Load configuration from file."""
        config_path = self.get_config_path()
        
        if not config_path.exists():
            return {"oblisk": {"version": self.version}}
        
        try:
            with open(config_path, "r") as f:
                if config_path.suffix == ".json":
                    return json.load(f)
                # Add YAML support if needed
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return {"oblisk": {"version": self.version}}


class OBLISKCLI:
    """Main CLI application for OBLISK."""
    
    def __init__(self, config: CLIConfig):
        self.config = config
        self.parser = self._build_parser()
    
    def _build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser."""
        parser = argparse.ArgumentParser(
            prog=self.config.app_name,
            description=self.config.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_epilog(),
        )
        
        # Global options
        parser.add_argument(
            "--version",
            "-v",
            action="version",
            version=f"{self.config.app_name} v{self.config.version}",
            help="Show version information",
        )
        
        parser.add_argument(
            "--config",
            type=str,
            default=None,
            help="Path to configuration file (config.json or config.yaml)",
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug output",
        )
        
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colored output",
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # 'start' command
        start_parser = subparsers.add_parser(
            "start",
            help="Start the OBLISK daemon",
        )
        start_parser.add_argument(
            "--daemon",
            action="store_true",
            help="Run as background daemon (Unix only)",
        )
        start_parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port for daemon to listen on (default: 8000)",
        )
        
        # 'status' command
        status_parser = subparsers.add_parser(
            "status",
            help="Show OBLISK status and agent information",
        )
        status_parser.add_argument(
            "--json",
            action="store_true",
            help="Output status as JSON",
        )
        
        # 'exec' command
        exec_parser = subparsers.add_parser(
            "exec",
            help="Execute a script or command through OBLISK",
        )
        exec_parser.add_argument(
            "script",
            type=str,
            help="Path to script or command to execute",
        )
        exec_parser.add_argument(
            "--timeout",
            type=int,
            default=300,
            help="Execution timeout in seconds (default: 300)",
        )
        
        # 'vault' command
        vault_parser = subparsers.add_parser(
            "vault",
            help="Manage encryption vault",
        )
        vault_subparsers = vault_parser.add_subparsers(dest="vault_action")
        
        vault_subparsers.add_parser("status", help="Show vault status")
        vault_subparsers.add_parser("init", help="Initialize vault")
        vault_subparsers.add_parser("rotate-keys", help="Rotate encryption keys")
        
        # 'memory' command
        memory_parser = subparsers.add_parser(
            "memory",
            help="Manage AI memory systems",
        )
        memory_subparsers = memory_parser.add_subparsers(dest="memory_action")
        
        memory_subparsers.add_parser("list", help="List memory stores")
        memory_subparsers.add_parser("clear", help="Clear memory")
        memory_subparsers.add_parser("export", help="Export memory")
        
        # 'agents' command
        agents_parser = subparsers.add_parser(
            "agents",
            help="Manage agents",
        )
        agents_subparsers = agents_parser.add_subparsers(dest="agents_action")
        
        agents_subparsers.add_parser("list", help="List loaded agents")
        agents_subparsers.add_parser("reload", help="Reload agent configurations")
        
        return parser
    
    @staticmethod
    def _get_epilog() -> str:
        """Get epilog text for help."""
        return """
Examples:
  %(prog)s start                         Start daemon
  %(prog)s start --port 9000             Start on custom port
  %(prog)s status                        Show status
  %(prog)s status --json                 Show status as JSON
  %(prog)s exec ./automation.py          Execute script
  %(prog)s vault init                    Initialize vault
  %(prog)s memory list                   List memory stores
  %(prog)s agents list                   List agents
  %(prog)s --config custom.json start    Use custom config

Documentation:
  https://github.com/POWDER-RANGER/OBLISK
  https://github.com/POWDER-RANGER/OBLISK/docs
"""
    
    def handle_start(self, args: argparse.Namespace) -> int:
        """Handle 'start' command."""
        print(f"[*] Starting {self.config.app_name} daemon...")
        print(f"[*] Version: {self.config.version}")
        
        if self.config.debug:
            print(f"[DEBUG] Config file: {self.config.get_config_path()}")
            config = self.config.load_config()
            print(f"[DEBUG] Config loaded: {json.dumps(config, indent=2)}")
        
        port = args.port
        print(f"[*] Listening on port {port}")
        print(f"[*] Press Ctrl+C to stop")
        
        # TODO: Implement actual daemon logic
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Daemon stopped.")
            return 0
    
    def handle_status(self, args: argparse.Namespace) -> int:
        """Handle 'status' command."""
        status = {
            "name": self.config.app_name,
            "version": self.config.version,
            "status": "online",
            "agents": {
                "loaded": 0,
                "active": 0,
            },
            "vault": {
                "initialized": False,
                "status": "offline",
            },
            "memory": {
                "stores": 0,
                "size_mb": 0,
            },
        }
        
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"OBLISK Status")
            print(f"="*50)
            print(f"Name: {status['name']}")
            print(f"Version: {status['version']}")
            print(f"Status: {status['status']}")
            print(f"Agents: {status['agents']['loaded']} loaded, {status['agents']['active']} active")
            print(f"Vault: {status['vault']['status']} ({status['vault']['initialized']})")
            print(f"Memory: {status['memory']['stores']} stores ({status['memory']['size_mb']} MB)")
        
        return 0
    
    def handle_exec(self, args: argparse.Namespace) -> int:
        """Handle 'exec' command."""
        script_path = args.script
        timeout = args.timeout
        
        print(f"[*] Executing: {script_path}")
        print(f"[*] Timeout: {timeout}s")
        
        # TODO: Implement script execution
        print("[!] Script execution not yet implemented")
        return 1
    
    def handle_vault(self, args: argparse.Namespace) -> int:
        """Handle 'vault' command."""
        action = args.vault_action
        
        if action == "status":
            print("Vault Status")
            print("="*50)
            print("Status: Offline")
            print("Initialized: No")
            print("Keys Loaded: 0")
        elif action == "init":
            print("[*] Initializing vault...")
            print("[!] Vault initialization not yet implemented")
        elif action == "rotate-keys":
            print("[*] Rotating encryption keys...")
            print("[!] Key rotation not yet implemented")
        else:
            self.parser.parse_args(["vault", "--help"])
        
        return 0
    
    def handle_memory(self, args: argparse.Namespace) -> int:
        """Handle 'memory' command."""
        action = args.memory_action
        
        if action == "list":
            print("Memory Stores")
            print("="*50)
            print("No memory stores loaded")
        elif action == "clear":
            print("[*] Clearing memory...")
            print("[!] Memory clearing not yet implemented")
        elif action == "export":
            print("[*] Exporting memory...")
            print("[!] Memory export not yet implemented")
        else:
            self.parser.parse_args(["memory", "--help"])
        
        return 0
    
    def handle_agents(self, args: argparse.Namespace) -> int:
        """Handle 'agents' command."""
        action = args.agents_action
        
        if action == "list":
            print("Loaded Agents")
            print("="*50)
            print("No agents currently loaded")
        elif action == "reload":
            print("[*] Reloading agent configurations...")
            print("[!] Agent reload not yet implemented")
        else:
            self.parser.parse_args(["agents", "--help"])
        
        return 0
    
    def run(self, argv: Optional[List[str]] = None) -> int:
        """Run the CLI application."""
        try:
            args = self.parser.parse_args(argv)
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1
        
        # Update config from args
        if args.config:
            self.config.config_file = args.config
        if args.debug:
            self.config.debug = True
        if args.no_color:
            self.config.no_color = True
        
        # Route to handlers
        if args.command == "start":
            return self.handle_start(args)
        elif args.command == "status":
            return self.handle_status(args)
        elif args.command == "exec":
            return self.handle_exec(args)
        elif args.command == "vault":
            return self.handle_vault(args)
        elif args.command == "memory":
            return self.handle_memory(args)
        elif args.command == "agents":
            return self.handle_agents(args)
        else:
            # No command provided, show help
            self.parser.print_help()
            return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    config = CLIConfig()
    cli = OBLISKCLI(config)
    return cli.run(argv)


if __name__ == "__main__":
    sys.exit(main())
