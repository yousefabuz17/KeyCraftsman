from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        packages=find_packages(where='src'),
        package_dir={'': 'src'},
        include_package_data=True,
        package_data={'key_craftsman': ['*.json']},
        )