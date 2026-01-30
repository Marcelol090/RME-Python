from setuptools import find_packages, setup

# Create py_rme_canary namespace by specifying packages explicitly
packages = []
for pkg in find_packages():
    if pkg in ["core", "logic_layer", "vis_layer", "tools"]:
        # Add as py_rme_canary.XXX
        packages.append(f"py_rme_canary.{pkg}")
        # Also add subpackages
        for subpkg in find_packages(pkg):
            packages.append(f"py_rme_canary.{pkg}.{subpkg}")
    else:
        packages.append(pkg)

setup(
    name="py_rme_canary",
    version="0.1.0",
    packages=packages,
    package_dir={
        "py_rme_canary.core": "core",
        "py_rme_canary.logic_layer": "logic_layer",
        "py_rme_canary.vis_layer": "vis_layer",
        "py_rme_canary.tools": "tools",
    },
    install_requires=[
        "PyQt6>=6.10.0",
        "Pillow>=10.0.0",
        "pygame>=2.1.3",
        "defusedxml>=0.7.1",
        "pytest>=9.0.0",
        "pytest-qt>=4.5.0",
        "ruff>=0.14.0",
        "mypy>=1.19.0",
    ],
    python_requires=">=3.12",
)
