from setuptools import find_packages, setup

package_name = 'panda_control1'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pick_demo_node=panda_control1.pick_demo_node:main',
            'act_eval_node=panda_control1.act_eval_node:main',
            'pick_demo2_node=panda_control1.pick_demo2_node:main',
            'pick_smooth_node=panda_control1.pick_smooth_node:main'
        ],
    },
)
