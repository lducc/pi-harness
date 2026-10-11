# Security policy

Please report security issues privately through GitHub's security advisory
feature when available, or contact the repository owner through the profile at
https://github.com/qhy991.

Do not open a public issue for a vulnerability involving unsafe SVG/XML
processing, path traversal, command execution, or untrusted downloaded paper
content.

This project processes external HTML, SVG, XML, and image files. Treat inputs
from unknown sources as untrusted, use an isolated workspace, and review
embedded content before opening it in desktop applications.
