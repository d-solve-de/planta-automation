# =============================================================================
# __main__.py - Package Entry Point
# =============================================================================
# This module enables running the package as a module:
#   python3 -m planta_filler
#
# It simply delegates to the CLI main function.
# =============================================================================

from .cli import main

if __name__ == '__main__':
    main()
