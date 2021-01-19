import os
import sys
import site


def ensure_user_sitepackages():
    user_site_packages_path = site.getusersitepackages()

    if not os.path.exists(user_site_packages_path):
        print("Create user site packages folder..")
        os.makedirs(user_site_packages_path)
        user_site_packages_path = site.getusersitepackages()

    if os.path.exists(user_site_packages_path) and user_site_packages_path not in sys.path:
        sys.path.append(user_site_packages_path)


def setup_numba():
    try:
        import numba
    except ImportError:
        print("Try to install required module: numba")

        import subprocess
        from sys import executable as PYTHON_PATH
        # from bpy.app import binary_path_python as PYTHON_PATH
        subprocess.check_call([PYTHON_PATH, '-m', 'ensurepip', '--upgrade', '--user'])
        subprocess.check_call([PYTHON_PATH, '-m', 'pip', 'install', '--upgrade', '--user', 'pip'])
        subprocess.check_call([PYTHON_PATH, '-m', 'pip', 'install', '--user', '--no-cache-dir', '--pre', 'numba'])
        subprocess.check_call([PYTHON_PATH, '-m', 'pip', 'install', '--user', '--no-cache-dir', '--upgrade', 'numba'])

        # from pip._internal import main as pipmain
        # import pip
        # pip.main(['install', '--no-cache-dir', 'numba'])

        try:
            import numba
        except ImportError:
            print("Numba installation failed! Please try to install this package manually..")


def find_cuda():
    def print_error(env_path):
        print("[%s] is not a valid CUDA file path. Please specify NUMBA_CUDA_DRIVER env variable. \
                It must be a filepath for the .so/.dll/.dylib file" % env_path)

    is_available = False

    env_path = os.environ.get('NUMBA_CUDA_DRIVER')

    if sys.platform == 'win32':
        dll_paths = ['\\windows\\system32\\nvcuda.dll']
    elif sys.platform == 'darwin':
        dll_paths = ['/usr/local/cuda/lib/libcuda.dylib']
    else:
        dll_paths = ['/usr/lib/libcuda.so', '/usr/lib64/libcuda.so', '/usr/lib/libcuda.so.1', '/usr/lib64/libcuda.so.1']

    path_candidates = dll_paths

    lib_matches = ['nvcuda.dll', 'libcuda.dylib', 'libcuda.so', 'libcuda.so.1']
    if env_path and env_path != '0':
        if any(name in env_path for name in lib_matches):
            path_candidates += [env_path]
        else:
            print_error(env_path)

    for cuda_path in path_candidates:
        if cuda_path is not None:
            try:
                cuda_path = os.path.abspath(cuda_path)
                if os.path.isfile(cuda_path):
                    is_available = True
                    break
            except Exception:
                pass

    if not is_available:
        paths = ', '.join(path_candidates)
        print_error(paths)

    return is_available


def detect_cuda():
    if not find_cuda():
        print('CUDA not found. Enable CUDASIM in numba.')
        os.environ["NUMBA_ENABLE_CUDASIM"] = "1"
    else:
        print('CUDA found..')
