from setuptools import find_packages, setup

package_name = 'agribot_navigation'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AgriBot Dev Team',
    maintainer_email='dev@example.com',
    description='Sira takibi, EKF fuzyon ve Nav2 tabanli dinamik engel kacinma.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'navigation_manager_node = agribot_navigation.nodes.navigation_manager_node:main',
        ],
    },
)
