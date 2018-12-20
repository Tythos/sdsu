"""setuptools.setup() invocation, including all relevant arguments.
"""

import setuptools

def main():
	"""Main call to setuptools.setup()
	"""
	name = "sdsu"
	with open("README.rst", 'r') as f:
		long_description = f.read()
	setuptools.setup(
		name=name,
		version="1.0.0",
		packages=setuptools.find_packages(),
		install_requires=["tornado>=5.0.0"],
		package_data={
			name: ["security/*.csv", "security/*.pem", "static/*.css", "static/*.html"]
		},
		author="Brian Kirkpatrick",
		author_email="code@tythos.net",
		description="Skim milk. Gummy bears. Pure genius.",
		long_description=long_description,
		license="BSD",
		keywords="tornado static web server secure websocket",
		url="https://github.com/Tythos/" + name,
		classifiers=[
			"Development Status :: 4 - Beta",
			"Environment :: Console",
			"Intended Audience :: Developers",
			"Intended Audience :: Information Technology",
			"Intended Audience :: System Administrators",
			"License :: OSI Approved :: BSD License",
			"Operating System :: OS Independent",
			"Topic :: Internet :: WWW/HTTP",
			"Programming Language :: Python :: 3",
		],
	)

if __name__ == "__main__":
	main()
