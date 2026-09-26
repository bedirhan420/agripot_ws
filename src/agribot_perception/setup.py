from setuptools import find_packages, setup

package_name = 'agribot_perception'

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
    description='YOLOv8 tabanli meyve tespiti ve olgunluk siniflandirma.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'perception_node = agribot_perception.nodes.perception_node:main',
        ],
    },
)
