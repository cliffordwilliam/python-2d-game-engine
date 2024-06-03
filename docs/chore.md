# My Notes

## Commitizen

https://pypi.org/project/commitizen/

Run this to commit from now on:

```bash
cz commit
```

## Pre commit

https://medium.com/@0xmatriksh/how-to-setup-git-hooks-pre-commit-commit-msg-in-my-project-11aaec139536

https://github.com/pre-commit/pre-commit/issues/1550g

pre-commit sample-config | out-file .pre-commit-config.yaml -encoding utf8

## Removed Unused Imports Hotkey

Refs:

- https://stackoverflow.com/questions/53352135/is-there-a-way-to-remove-unused-imports-for-python-in-vs-code
- https://codewithsusan.com/notes/vscode-keyboard-shortcuts#:~:text=All%20of%20your%20keybinding%20customizations,json%20.
- https://stackoverflow.com/questions/56798514/visual-studio-code-unable-to-edit-keybingings-json-cannot-edit-in-read-only-ed

When it is done you can use the `shift + alt + r`.

## Custom VS Code File Icons Using Material Icons

https://gist.github.com/rupeshtiwari/6860fbc1b3e2f6711c780070d6f59748

## After Pip Install

Always update the req txt every after installation.

```bash
pip freeze > requirements.txt
```

## Before Commiting

Run this mypy, this tpye checks everything:

```bash
mypy src
```

Before commiting, I cannot add it to prehook, it is a hassle that I have to run each time before commiting.

## Docker

1. Download this if you are using windows: https://sourceforge.net/projects/xming/. Just press next on each part of the installer.

2. If you are using Mac, download XQuartz here https://www.xquartz.org/. Open it, go to Settings > Security > Check “Allow connections from network clients” and quit and re-open the program.

3. Search for and run “XLaunch”

4. IF you are using windows, just hit next through each step.

5. If you are using mac, go into your shell and type “xhost +” which will allow clients to connect from any host.

6. Install the Docker Desktop.

7. Setup the Dockerfile.

8. Do the following:

```bash
docker build -t my-python-app .
```

```bash
docker run -p 4000:80 my-python-app
```

```bash
docker stop <id>

```

```bash
docker rm <id>
```

This is good to know but it does not work properly when you pull and run. Works fine if you are building from a cloned repo.

Create a docker repo

Then tag the local image

```bash
docker tag python-2d-game-engine cliffordwilliaim/python-2d-game-engine:latest
```

Then login from local, faster if you login via the docker desktop first. Then do this.

```bash
docker login
```

If login is OK then you can push

```bash
docker push cliffordwilliaim/python-2d-game-engine:latest
```

Then anyone can pull it

```bash
docker pull cliffordwilliaim/python-2d-game-engine:latest
```

And run it with this

```bash
docker run cliffordwilliaim/python-2d-game-engine:latest
```

If you need to find the id or name from terminal run this

```bash
docker ps
```

Then do the stop and rm as usual to stop it.

## Before prod

Look for all instances of # REMOVE IN BUILD, then delete all that is not needed for prod.

## Take note

All names should be snake case no matter what, this makes it so that the data name can be anywhere, in json or in py files.

## Todo

- [ ] Find ways on how to save json to anyone computer for saving and loading feature.
- [ ] Create an editor to generate jsons for animation data.
- [ ] Create the main menu flow, from splash, title, main menu, settings, load and save screen then game.
- [ ] Be able to save and load at any room in World scene.
- [x] Find ways to make type safety a thing here. Check below on how I did it.
- [ ] Update the doc svg, Reason for change is because I cannot import everything at the constants, import when it is needed only. Like Vector and so on.
- [ ] In the main menu, add options to go to level editor or animation editor and so on.
- [ ] Always recheck if the typing are all complete in every file.
- [ ] Check if each file has its own doc section in documention.md, make sure that it reflects the code as is too.
- [ ] Always read if there are any more TODO.

## Typesafety

```py
# This only import during coding, not runtime
if TYPE_CHECKING:
    from nodes.game import Game


class CreatedBySplashScreen:
    def __init__(self, game: 'Game'):
        self.game = game
```
