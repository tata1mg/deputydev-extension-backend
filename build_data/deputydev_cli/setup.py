from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel


# Subclassing bdist_wheel to mark as non-pure
class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False  # Force the wheel to be platform-specific


setup(
    package_data={"your_package_name": ["pyarmor_runtime_000000/pyarmor_runtime.so"]},
    include_package_data=True,
    cmdclass={"bdist_wheel": bdist_wheel},
)
