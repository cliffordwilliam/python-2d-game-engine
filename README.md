# Python 2D Game Engine

This is my python 2D game engine project. I will work on it while making a game along side of it as a proof of concept. It comes with json editor, level editor and the game engine itself. There is no GUI but there are helpful classes out of the box you can use for common things like animation, saving, key binding, collision, camera and so much more.

## Motivation

This project is the only thing right now that motivates me to keep going in life, my long term goal is to make a series out of this game. I will share more as I am also working on a blog to showcase my development, devlog.

## Python Version

This project is developed and tested with Python 3.12.3.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install and run the project, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/cliffordwilliam/python-2d-game-engine.git
   ```

2. Navigate to the project directory:

   ```bash
   cd your-repository
   ```

3. Create a virtual environment (optional but recommended):

   Or you can use VSCode ctrl + shift + p to select the python intreperter and create venv. Open and close your terminal and wait until you see a popup saying that the venv is activated. If you are a dev you can run the pre-commit install now. Run this again if you update the pre commit yaml file.

   ```bash
   pre-commit install
   ```

   ```bash
   python3 -m venv venv
   ```

4. Activate the virtual environment:

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS and Linux:

     ```bash
     source venv/bin/activate
     ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run the main script:

   ```bash
   python main.py
   ```

## Usage

Read my docs to read the manual on how to use this, it is still a work in progress.

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
