
try:
    import numba
except ImportError:
    print("Try to install required module: numba")

    import subprocess
    from sys import executable as PYTHON_PATH
    # from bpy.app import binary_path_python as PYTHON_PATH
    subprocess.check_call([PYTHON_PATH, '-m', 'ensurepip', '--upgrade'])
    subprocess.check_call([PYTHON_PATH, '-m', 'pip', 'install', '--upgrade', 'pip'])
    subprocess.check_call([PYTHON_PATH, '-m', 'pip', 'install', '--no-cache-dir', '--pre', 'numba'])

    # from pip._internal import main as pipmain
    # import pip
    # pip.main(['install', '--no-cache-dir', 'numba'])

    try:
        import numba
    except ImportError:
        print("Numba installation failed! Please try to install this package manually..")
