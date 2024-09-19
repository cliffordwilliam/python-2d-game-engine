# Python 2D Game Engine

This is my python 2D game engine project. I will work on it while making a game along side of it as a proof of concept. It comes with json editor, level editor and the game engine itself. There is no GUI but there are helpful classes out of the box you can use for common things like animation, saving, key binding, collision, camera and so much more. Think of it like a wrapper for pygame.

## Motivation

This project is the only thing right now that motivates me to keep going in life, my long term goal is to make a series out of this game. I will share more as I am also working on a blog to showcase my development, aka devlog.

## Python Version

This project is developed and tested with Python 3.12.3.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

Note: If you use VSCode do not forget to set interpreter to the venv python for import dependencies detection.

Steps to install and run the project:

1. Clone the repository:

   ```bash
   git clone https://github.com/cliffordwilliam/python-2d-game-engine.git
   ```

2. Navigate to the project directory:

   ```bash
   cd your-repository
   ```

3. Install python 3.12.3

4. Install pip:

   ```bash
   sudo apt install python3-pip
   pip3 --version
   ```

5. Install virtualvenv with pip:

   ```bash
   install python3.12-venv
   ```

6. Create a virtual environment:

   ```bash
   python3 -m venv /the/path/to/python-2d-game-engine/venv/
   ```

7. Activate venv:
   ```bash
   source venv/bin/activate
   which python
   which pip
   ```

7. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

8. If you are a developer, you can run the pre-commit install now. Run this again if you update the pre commit yaml file.

   ```bash
   pre-commit install
   ```

9. Run the main script:

   ```bash
   python main.py
   ```

10. Delete the .vscode if you do not want my workplace settings:

## Usage

Read my docs to read the manual on how to use this wrapper.

### Run Immediately

If you want to run this with no hassle I provide docker. Here are the steps to run it without any python setups.

1. Download this if you are using windows: https://sourceforge.net/projects/xming/. Just press next on each part of the installer.

2. If you are using Mac, download XQuartz here https://www.xquartz.org/. Open it, go to Settings > Security > Check “Allow connections from network clients” and quit and re-open the program.

3. Search for and run “XLaunch”

4. If you are using windows, just hit next through each step.

5. If you are using mac, go into your shell and type “xhost +” which will allow clients to connect from any host.

6. Clone this repo and enter its dir. Then do the following:

```bash
docker build -t my-python-app .
```

```bash
docker run -p 4000:80 my-python-app
```

If you need to find the id or name from terminal run this.

```bash
docker ps
```

Use the id to stop and remove it.

```bash
docker stop <id>

```

```bash
docker rm <id>
```

## Contributing

Open issue, fork and pr. Thank you for your help.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
