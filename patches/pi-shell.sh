pi() {
  case "${1:-}" in
    update) command pi "$@" && ~/.pi/agent/patches/apply.sh; return ;;
    install|remove|uninstall|list|config|auth|mcp) command pi "$@"; return ;;
  esac
  if [ -z "${PI_SUBAGENT_NAME:-}" ]; then command pi --no-sandbox "$@"; else command pi "$@"; fi
}
